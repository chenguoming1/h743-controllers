#!/usr/bin/env python3
"""Bounded linear DC sheet FEM. Native polygon geometry is never repaired silently.

This is a new prototype screen, not a reconstruction of a historical solver.
All lengths are mm; material resistivity is ohm.mm. Finite terminal lands are
equipotential on each layer. Barrel resistance is retained between layer lands.
"""
from dataclasses import dataclass
from copy import deepcopy
from fractions import Fraction
import math
import time
import resource
import numpy as np
import shapely as s
from shapely.geometry import Polygon, GeometryCollection, box
from shapely.errors import GEOSException
from scipy.sparse import coo_matrix,diags
from scipy.sparse.csgraph import connected_components
from scipy.sparse.linalg import cg, LinearOperator,splu


class Refused(RuntimeError):
    pass


def positive_finite(value, label):
    if not math.isfinite(value) or value <= 0:
        raise Refused(f'{label} must be finite and positive')


def copper_material(temperature_C=105.0, thickness_mm=0.015,
                    conductivity_IACS=0.95, plating_mm=0.015):
    """Explicit fixed-temperature resistance assumption, never a heat solution."""
    for value, label in [(thickness_mm, 'Copper thickness'),
                         (conductivity_IACS, 'IACS fraction'), (plating_mm, 'Plating')]:
        positive_finite(value, label)
    rho = 1.7241e-5 * (1 + 0.00393 * (temperature_C - 20)) / conductivity_IACS
    positive_finite(rho, 'Copper resistivity')
    return dict(temperature_C=temperature_C, thickness_mm=thickness_mm,
                conductivity_IACS=conductivity_IACS, plating_mm=plating_mm,
                resistivity_ohm_mm=rho, sheet_ohm=rho/thickness_mm,
                thermal_prediction=False)


@dataclass
class Limits:
    max_nodes: int = 160000
    max_triangles: int = 320000
    max_tiles: int = 300000
    max_seconds: float = 120.0
    max_iterations: int = 10000
    max_terminals: int = 128
    max_element_condition: float = 1e12
    linear_solver: str = 'cg'
    max_factor_nonzeros: int = 20000000
    max_factor_bytes: int = 1073741824
    cg_diagnostic_iterations: int = 0


def polygon_set(records):
    polys = [Polygon(p['outer'], p.get('holes', [])) for p in records]
    if any(not p.is_valid for p in polys):
        raise Refused('Invalid native polygon; no make_valid/buffer repair is allowed')
    return s.union_all(polys) if polys else GeometryCollection()


def parts(geom):
    if geom.geom_type == 'Polygon':
        return [geom]
    return [p for g in getattr(geom, 'geoms', []) for p in parts(g)]


def polygonal_area(geom):
    """Keep the unchanged 2D pieces of a clipping result; boundaries carry no area."""
    if geom.geom_type in ('Polygon','MultiPolygon'):
        return geom
    polygons=parts(geom)
    result=polygons[0]if len(polygons)==1 else s.union_all(polygons)if polygons else Polygon()
    if not result.is_valid or result.area!=geom.area:
        raise Refused('Polygon-only decomposition changed area or produced invalid geometry')
    return result


def area_overlay(a,b,operation,where=None):
    """Exact overlay, retaining seam constraints and explicitly handling empties.

    Zero-area lines/points may still node a shared polygon boundary. Retain them
    through partitioning; ``parts`` excludes them only at triangulation. Removing
    them earlier can create hanging mesh nodes despite identical covered area.
    """
    if operation not in ('intersection','difference'):
        raise Refused('Unsupported area overlay operation')
    if a.is_empty:return Polygon()
    if b.is_empty:return a if operation=='difference'else Polygon()
    try:
        result=a.intersection(b)if operation=='intersection'else a.difference(b)
    except GEOSException as exc:
        refusal=Refused('Native area overlay failed without repair: '+str(exc))
        refusal.geometry_reproduction={'operation':operation,'where':where,
          'left_wkb_hex':a.wkb_hex,'right_wkb_hex':b.wkb_hex,
          'left_valid':a.is_valid,'right_valid':b.is_valid}
        raise refusal from exc
    return result


def grid_coordinate(index,spacing_mm):
    """One rounded conversion of an exact decimal grid coordinate to binary64."""
    spacing=Fraction(str(spacing_mm))
    return float(index*spacing)


def triangle_geometry(xy,max_condition=1e12):
    """Unchanged vertices, local determinant and conservative Jacobian bound.

    ||J||_F^2 / |det J| = cond_2(J) + 1/cond_2(J). Reject an unresolved
    element instead of deleting it, merging its vertices or changing its area.
    This is a numerical refusal guard, not a rigorous FEM error estimate.
    """
    positive_finite(max_condition,'Maximum element condition')
    u=xy[:,1]-xy[:,0];v=xy[:,2]-xy[:,0]
    twice_area=u[:,0]*v[:,1]-v[:,0]*u[:,1]
    with np.errstate(divide='ignore',invalid='ignore',over='ignore'):
        condition_bound=(np.sum(u*u,axis=1)+np.sum(v*v,axis=1))/abs(twice_area)
    bad=np.flatnonzero((~np.isfinite(twice_area))|(~np.isfinite(condition_bound))|
                       (twice_area==0)|(condition_bound>max_condition))
    if len(bad):
        index=int(bad[0]);failure=Refused('Unresolved triangle area/conditioning with unchanged overlay coordinates')
        failure.geometry_reproduction={'stage':'triangle_geometry','index':index,
          'coordinates':xy[index].tolist(),'twice_area_mm2':float(twice_area[index]),
          'condition_bound':float(condition_bound[index])if math.isfinite(condition_bound[index])else None,
          'maximum_condition_bound':max_condition}
        raise failure
    return twice_area,condition_bound


def native_geometry(snapshot, net):
    """Actual copper and saved fills minus every physical drill on its real span."""
    if not snapshot['outline_with_npth']['valid']:
        raise Refused('Native board outline export failed')
    layers = snapshot['copper_layers']
    cu = {l: [] for l in layers}
    void = {l: [] for l in layers}
    pads = {}
    barrels = []
    for obj in snapshot['objects']:
        if obj.get('net') == net:
            for layer, rec in obj.get('copper', {}).items():
                cu[layer].append(polygon_set(rec))
            if obj['kind'] == 'pad':
                pads.setdefault(obj['key'], []).append(obj)
            if obj.get('plated') and obj.get('drill'):
                barrels.append(obj)
        drill = obj.get('drill')
        if drill:
            # PTH/NPTH pass through; vias remove metal only on the drilled span.
            span = obj.get('barrel_layers') if obj['kind'] == 'via' else layers
            for layer in span:
                void[layer].append(polygon_set(drill['outside']))
    for zone in snapshot['zones']:
        if not zone['rule'] and zone['net'] == net:
            for layer, rec in zone['filled'].items():
                cu[layer].append(polygon_set(rec))
    outline = polygon_set(snapshot['outline_with_npth']['polygons'])
    domains = {}
    for layer in layers:
        domains[layer] = s.union_all(cu[layer]).difference(s.union_all(void[layer])).intersection(outline)
        if not domains[layer].is_valid:
            raise Refused(f'Invalid {net}/{layer} after actual drilled-void subtraction')
    return domains, pads, barrels


def contact_geometry(pads, key, layer):
    if key not in pads:
        raise Refused(f'Missing native contact {key}')
    # Duplicate pad numbers are unioned only on the requested physical layer.
    records = [polygon_set(p.get('inside', p['copper']).get(layer, [])) for p in pads[key]]
    geom = s.union_all(records)
    if geom.is_empty:
        raise Refused(f'No finite native copper for {key}/{layer}')
    return geom


def contact_keys(spec):
    """Accept one native key or an explicit, nonempty list of distinct keys."""
    if ('pad' in spec) == ('pads' in spec):
        raise Refused('Contact must provide exactly one of pad or pads')
    keys = [spec['pad']] if 'pad' in spec else spec['pads']
    if not isinstance(keys, list) or not keys or any(not isinstance(k, str) or not k for k in keys):
        raise Refused('Contact pad keys must be a nonempty string list')
    if len(set(keys)) != len(keys):
        raise Refused('Contact contains duplicate native pad keys')
    return keys


def contact_spec_geometry(pads, spec):
    """Finite union of actual pad lands; never bridge separated or point-touch pads."""
    keys = contact_keys(spec)
    geom = s.union_all([contact_geometry(pads, key, spec['layer']) for key in keys])
    if geom.is_empty or not geom.is_valid or geom.geom_type != 'Polygon' or geom.area <= 0:
        raise Refused('Contact union must be one connected finite native polygon')
    return geom


def barrel_resistance(obj, dz_mm, rho_ohm_mm, plating_mm):
    d = obj['drill']
    length = math.dist(d['start'], d['end'])
    if not math.isfinite(length):
        raise Refused('Nonfinite drill centerline')
    # Plated capsule perimeter, including two straight sides of a slot.
    for value, label in [(d['width'], 'Drill width'), (plating_mm, 'Plating'),
                         (rho_ohm_mm, 'Resistivity'), (dz_mm, 'Barrel span')]:
        positive_finite(value, label)
    area = (math.pi * d['width'] + 2 * length) * plating_mm
    if not math.isfinite(area) or min(area, dz_mm) <= 0:
        raise Refused('Nonpositive barrel cross-section or span')
    return rho_ohm_mm * dz_mm / area


class DSU:
    def __init__(self, n):
        self.p = list(range(n))
    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x
    def join(self, ids):
        if not len(ids):
            raise Refused('Empty equipotential region')
        root = self.find(int(ids[0]))
        for i in ids[1:]:
            self.p[self.find(int(i))] = root


class Mesh:
    def __init__(self, domains, contacts, spacing_mm, sheet_ohm, thickness_mm,
                 barrels=(), layer_z_mm=None, plating_mm=0.015, limits=None,
                 native_edge_provider=None,geometry_progress=None,geometry_certificate=None):
        self.limits = limits or Limits()
        self.start_time = time.monotonic()
        self.sheet = sheet_ohm
        self.thickness = thickness_mm
        self.spacing = spacing_mm
        for value, label in [(spacing_mm, 'Mesh spacing'), (sheet_ohm, 'Sheet resistance'),
                             (thickness_mm, 'Thickness')]:
            positive_finite(value, label)
        if len(contacts) < 2:
            raise Refused('At least two finite contacts are required')
        if len(contacts) > self.limits.max_terminals:
            raise Refused('Terminal cap exceeded')
        self.xyz, triangles, ids, raw_components = [], [], {}, []
        self.layers = list(domains)
        if set(x[0] for x in contacts.values()) - set(self.layers):
            raise Refused('Contact uses an absent copper layer')
        regions = {layer: [] for layer in domains}
        for layer, region in contacts.values():
            if region.is_empty or not region.is_valid:
                raise Refused('Empty/invalid contact region')
            regions[layer].append(region)
        for obj in barrels:
            for layer, records in obj['copper'].items():
                if layer in regions:
                    regions[layer].append(polygon_set(records))
        # Respect finite terminal boundaries exactly, instead of snapping their
        # extent to the sampling grid. Annuli remain equipotential ideal lands.
        region_union = {layer: s.union_all(value) for layer, value in regions.items()}
        self.native_edge_noding={}
        if native_edge_provider is not None:
            # Keep one layer's spatial index alive at a time. Native polygon
            # objects are immutable; only the proved derived representation is
            # shared by the local domain and ideal-land partition copies.
            from native_edge_noding import canonicalize
            domains=dict(domains)
            for layer in domains:
                if domains[layer].is_empty:continue
                try:
                    noded,receipt=canonicalize([domains[layer],region_union[layer]],
                      native_edge_provider(layer),check_time=self.check_time)
                except Refused as failure:
                    failure.geometry_reproduction={'layer':layer,'stage':'pretiling_native_edge_noding',
                      **getattr(failure,'geometry_reproduction',{})}
                    raise
                domains[layer],region_union[layer]=noded
                self.native_edge_noding[layer]=receipt
                if geometry_certificate:geometry_certificate(layer,receipt)
                if geometry_progress:
                    geometry_progress({'stage':'native_edge_noding_ready','layer':layer,
                      **{k:receipt[k]for k in ['source_edges','input_unique_vertices','inserted_seam_vertices',
                        'changed_derived_vertices','maximum_derived_vertex_displacement_mm']}})
        tile_count = 0
        area_sum = 0.0
        domain_area = sum(g.area for g in domains.values())
        components = [(layer, poly) for layer, geom in domains.items() for poly in parts(geom)]
        grid_step=Fraction(str(spacing_mm))
        anchor=lambda index:float(index*grid_step)
        for component_id, (layer, geom) in enumerate(components):
            if geom.is_empty:
                continue
            if not geom.is_valid:
                raise Refused('Invalid input domain')
            x0,y0,x1,y1 = geom.bounds
            ix0,iy0 = math.floor(x0/spacing_mm),math.floor(y0/spacing_mm)
            ix1,iy1 = math.ceil(x1/spacing_mm),math.ceil(y1/spacing_mm)
            tile_count += (ix1-ix0)*(iy1-iy0)
            if tile_count > self.limits.max_tiles:
                raise Refused(f'Tile cap exceeded before triangulation: {tile_count}')
            for ix in range(ix0,ix1):
                self.check_time()
                # Exact spatial clipping: intersect the large native polygon
                # and ideal-land set once with this aligned strip. Local cells
                # then see only strip geometry. No boundary simplification,
                # hole filling, snapping, or geometric repair is performed.
                strip_box=box(anchor(ix),anchor(iy0),anchor(ix+1),anchor(iy1))
                where={'layer':layer,'component':component_id,'ix':ix,'spacing_mm':spacing_mm}
                strip=area_overlay(geom,strip_box,'intersection',{**where,'stage':'native_strip'})
                if strip.is_empty:
                    continue
                ideal_strip=area_overlay(region_union[layer],strip_box,'intersection',{**where,'stage':'ideal_strip'})
                for iy in range(iy0,iy1):
                    if iy%32==0:self.check_time()
                    location={**where,'iy':iy}
                    cut=area_overlay(strip,box(anchor(ix),anchor(iy),anchor(ix+1),anchor(iy+1)),'intersection',{**location,'stage':'native_cell'})
                    contact_cut=area_overlay(cut,ideal_strip,'intersection',{**location,'stage':'contact_partition'})
                    outside_cut=area_overlay(cut,ideal_strip,'difference',{**location,'stage':'sheet_partition'})
                    for poly in parts(contact_cut) + parts(outside_cut):
                        for tri in s.constrained_delaunay_triangles(poly).geoms:
                            if tri.area == 0:
                                continue
                            indices = []
                            for x,y in list(tri.exterior.coords)[:3]:
                                # Distinct polygons touching at a single point
                                # must not become a fictitious conductive neck.
                                key = (component_id,x,y)
                                if key not in ids:
                                    ids[key] = len(self.xyz)
                                    self.xyz.append((layer, key[1], key[2]))
                                    raw_components.append(component_id)
                                indices.append(ids[key])
                            triangles.append(indices)
                            area_sum += tri.area
                            if len(self.xyz)>self.limits.max_nodes or len(triangles)>self.limits.max_triangles:
                                raise Refused('Mesh cap exceeded; do not silently coarsen the mesh')
        if not triangles:
            raise Refused('No conducting elements')
        if abs(area_sum-domain_area)>max(1e-8,domain_area*1e-8):
            raise Refused('Triangulation does not cover actual copper area')
        self.area_error_mm2 = area_sum-domain_area
        self.triangles = np.asarray(triangles,dtype=np.int32)
        self.xy = np.asarray([[v[1],v[2]] for v in self.xyz],dtype=float)
        self.layer_ids = np.asarray([self.layers.index(v[0]) for v in self.xyz])
        dsu = DSU(len(self.xyz))
        point_array = s.points(self.xy)
        raw_components = np.asarray(raw_components)
        def touching(layer, region):
            if region.intersection(domains[layer]).area <= 1e-16:
                raise Refused('Contact has no finite copper overlap')
            # The tolerance is only for integer/export coordinate roundoff.
            mask = (self.layer_ids==self.layers.index(layer)) & s.covers(region.buffer(2e-8),point_array)
            hits = np.flatnonzero(mask)
            if not len(hits):
                raise Refused(f'Contact unresolved at {spacing_mm} mm; refine, never snap to a nearby trace')
            if len(np.unique(raw_components[hits])) != 1:
                raise Refused('Equipotential contact would short disconnected native copper')
            return hits
        raw_contacts = {}
        for name,spec in contacts.items():
            layer,region = spec
            hit = touching(layer,region)
            dsu.join(hit)
            raw_contacts[name] = int(hit[0])
        raw_barrels = []
        for obj in barrels:
            if layer_z_mm is None:
                raise Refused('Actual stackup centers required for plated barrels')
            span = obj['barrel_layers']
            connection = []
            for layer in span:
                rec = obj['copper'].get(layer)
                if rec:
                    hit = touching(layer,polygon_set(rec))
                    dsu.join(hit)
                    connection.append((layer,int(hit[0])))
            # Non-flashed intermediate layers retain a continuous barrel; link
            # adjacent flashed lands by their actual cumulative separation.
            for (la,a),(lb,b) in zip(connection,connection[1:]):
                r = barrel_resistance(obj,abs(layer_z_mm[lb]-layer_z_mm[la]),sheet_ohm*thickness_mm,plating_mm)
                raw_barrels.append((a,b,r,obj['uuid'],la,lb))
        roots = [dsu.find(i) for i in range(len(self.xyz))]
        unique = {r:i for i,r in enumerate(sorted(set(roots)))}
        self.mapping = np.asarray([unique[r] for r in roots],dtype=np.int32)
        self.contact_nodes = {k:int(self.mapping[v]) for k,v in raw_contacts.items()}
        if len(set(self.contact_nodes.values())) != len(self.contact_nodes):
            raise Refused('Overlapping/equivalent contacts: use one port with explicit circuit aliases')
        self.n = len(unique)
        xy = self.xy[self.triangles]
        twice_area,condition_bound=triangle_geometry(xy,self.limits.max_element_condition)
        self.areas = abs(twice_area)/2
        self.element_geometry={'minimum_area_mm2':float(np.min(self.areas)),
          'maximum_condition_bound':float(np.max(condition_bound)),
          'condition_refusal_limit':self.limits.max_element_condition,
          'coordinates_quantized':False,'positive_area_elements_discarded':0}
        self.grad = np.empty((len(xy),3,2))
        self.grad[:,:,0] = np.stack((xy[:,1,1]-xy[:,2,1],xy[:,2,1]-xy[:,0,1],xy[:,0,1]-xy[:,1,1]),axis=1)/twice_area[:,None]
        self.grad[:,:,1] = np.stack((xy[:,2,0]-xy[:,1,0],xy[:,0,0]-xy[:,2,0],xy[:,1,0]-xy[:,0,0]),axis=1)/twice_area[:,None]
        local = np.einsum('tik,tjk,t->tij',self.grad,self.grad,self.areas)/sheet_ohm
        mapped = self.mapping[self.triangles]
        rows = np.repeat(mapped,3,axis=1).ravel()
        cols = np.tile(mapped,(1,3)).ravel()
        data = local.ravel()
        self.barrels = [(int(self.mapping[a]),int(self.mapping[b]),r,uid,la,lb) for a,b,r,uid,la,lb in raw_barrels]
        if self.barrels:
            rr,cc,dd = [],[],[]
            for a,b,r,*_ in self.barrels:
                rr.extend([a,a,b,b]); cc.extend([a,b,a,b]); dd.extend([1/r,-1/r,-1/r,1/r])
            rows=np.r_[rows,rr];cols=np.r_[cols,cc];data=np.r_[data,dd]
        self.K=coo_matrix((data,(rows,cols)),shape=(self.n,self.n)).tocsr()
        self.K.eliminate_zeros()
        self.components,self.labels=connected_components(self.K,directed=False)
        active={int(self.labels[i]) for i in self.contact_nodes.values()}
        if len(active)!=1:
            raise Refused('Native contacts do not share one copper/barrel component')
        self.active=np.flatnonzero(self.labels==next(iter(active)))
        self.floating_nodes=self.n-len(self.active)

    def check_time(self):
        if time.monotonic()-self.start_time>self.limits.max_seconds:
            raise Refused('Wall-time cap reached')

    def linear_system(self):
        if hasattr(self,'_linear_system'):return self._linear_system
        if self.limits.linear_solver not in ('cg','sparse-direct'):raise Refused('Unknown linear solver')
        if not np.all(np.isfinite(self.K.data)):raise Refused('Nonfinite FEM matrix')
        active=self.K[self.active][:,self.active]
        if connected_components(active,directed=False,return_labels=False)!=1:
            raise Refused('Anchored FEM component is disconnected')
        diagonal=active.diagonal()
        if np.any(~np.isfinite(diagonal))or np.any(diagonal<=0):raise Refused('Nonpositive FEM diagonal')
        difference=active-active.T
        asymmetry=float(max(abs(difference.data),default=0.))
        if asymmetry>max(diagonal)*1e-12:raise Refused('FEM matrix is not numerically symmetric')
        anchor=next(iter(self.contact_nodes.values()))
        free=self.active[self.active!=anchor];A=self.K[free][:,free].tocsr();diag=A.diagonal()
        self.linear_diagnostics={'backend':self.limits.linear_solver,'active_equations':len(self.active),
          'anchored_equations':len(free),'anchored_connected_components':1,'finite_matrix':True,
          'minimum_active_diagonal':float(min(diagonal)),'maximum_active_diagonal':float(max(diagonal)),
          'maximum_asymmetry':asymmetry,'fixed_reference_node':int(anchor),'matrix_nonzeros':int(A.nnz),
          'matrix_storage_bytes':A.data.nbytes+A.indices.nbytes+A.indptr.nbytes}
        self._linear_system=(free,A,diag)
        self.check_time();return self._linear_system

    def iterative_solution(self,A,rhs,diag,max_iterations):
        history=[{'iteration':0,'residual_norm_A':float(np.linalg.norm(rhs))}];iterations=[0]
        def tick(value):
            iterations[0]+=1;self.check_time()
            if iterations[0]%100==0:history.append({'iteration':iterations[0],'residual_norm_A':float(np.linalg.norm(A@value-rhs))})
        pre=LinearOperator(A.shape,matvec=lambda x:x/diag)
        value,info=cg(A,rhs,rtol=1e-10,atol=1e-13,M=pre,maxiter=max_iterations,callback=tick)
        final=float(np.linalg.norm(A@value-rhs));history.append({'iteration':iterations[0],'residual_norm_A':final})
        initial=history[0]['residual_norm_A']
        trend='converged'if info==0 else 'nonfinite'if not math.isfinite(final)else 'residual_growth'if final>10*initial else 'iteration_limit'
        return value,info,{'iterations':iterations[0],'info':int(info),'trend':trend,'residual_history':history,
                           'final_residual_norm_A':final,'diagnostic_only':False}

    def direct_solution(self,A,rhs,diag):
        if not hasattr(self,'_direct_factor'):
            if self.limits.cg_diagnostic_iterations:
                _,_,diagnostic=self.iterative_solution(A,rhs,diag,self.limits.cg_diagnostic_iterations)
                diagnostic['diagnostic_only']=True;self.linear_diagnostics['cg_diagnostic']=diagnostic
            self.check_time();scale=1/np.sqrt(diag);scaled=(diags(scale)@A@diags(scale)).tocsc()
            if scaled.nnz>self.limits.max_factor_nonzeros:raise Refused('Matrix already exceeds sparse-factor nonzero budget')
            started=time.monotonic()
            try:factor=splu(scaled,permc_spec='MMD_AT_PLUS_A',diag_pivot_thresh=0.,options={'SymmetricMode':True,'Equil':False})
            except RuntimeError as exc:raise Refused('Sparse direct factorization failed: '+str(exc))from exc
            lower,upper=factor.L,factor.U
            nonzeros=lower.nnz+upper.nnz
            memory=sum(a.nbytes for matrix in [lower,upper]for a in [matrix.data,matrix.indices,matrix.indptr])+factor.perm_r.nbytes+factor.perm_c.nbytes
            self.linear_diagnostics['factorization']={'ordering':'MMD_AT_PLUS_A','diagonal_scaling':True,
              'seconds':time.monotonic()-started,'factor_nonzeros':int(nonzeros),'factor_stored_array_bytes':int(memory),
              'factor_memory_excludes_native_workspace':True,'process_peak_RSS_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024}
            del lower,upper
            if nonzeros>self.limits.max_factor_nonzeros or memory>self.limits.max_factor_bytes:
                raise Refused('Sparse factor storage cap exceeded')
            self._direct_factor=factor;self._direct_scale=scale;self.check_time()
        factor=self._direct_factor;scale=self._direct_scale
        # Thin exact geometric elements can create large canceling row terms.
        # Retain the original assembled coefficients and double LU, while
        # accumulating both solution and residual in wider arithmetic. This
        # changes no matrix coefficient, geometry or acceptance threshold.
        wide=np.longdouble
        if np.finfo(wide).eps>=np.finfo(float).eps:
            raise Refused('Sparse direct refinement requires wider-than-float64 arithmetic')
        if not hasattr(self,'_direct_matrix_wide'):self._direct_matrix_wide=A.astype(wide)
        matrix=self._direct_matrix_wide;right=rhs.astype(wide)
        value=(scale*factor.solve(scale*rhs)).astype(wide)
        target=max(1e-13,1e-10*float(np.linalg.norm(rhs)));history=[];double_history=[]
        for step in range(5):
            residual=right-matrix@value;norm=float(np.linalg.norm(residual));history.append(norm)
            double_history.append(float(np.linalg.norm(rhs-A@np.asarray(value,dtype=float))))
            # Preserve failed histories too; a refusal is not a usable result.
            self.linear_diagnostics['last_direct_solve']={'refinement_steps':len(history)-1,
              'residual_norm_history_A':list(history),'required_residual_norm_A':target,
              'float64_projection_residual_norm_history_A':list(double_history),
              'residual_and_solution_mantissa_bits':int(np.finfo(wide).nmant),
              'converged':bool(math.isfinite(norm)and norm<=target)}
            if math.isfinite(norm)and norm<=target:break
            if step==4 or not math.isfinite(norm):
                raise Refused('Sparse direct residual did not meet the unchanged linear tolerance')
            correction=scale*factor.solve(scale*np.asarray(residual,dtype=float))
            value+=correction.astype(wide);self.check_time()
        return value,len(history)

    def solve(self,injections,reference=None):
        self.check_time()
        if not injections or not all(math.isfinite(x) for x in injections.values()):
            raise Refused('Empty/nonfinite current injection')
        if abs(sum(injections.values()))>1e-9:
            raise Refused('Terminal current is not conserved')
        if set(injections)-set(self.contact_nodes):
            raise Refused('Unknown injection contact')
        reference = reference or next(iter(self.contact_nodes))
        if reference not in self.contact_nodes:
            raise Refused('Unknown voltage reference contact')
        ref=self.contact_nodes[reference]
        b=np.zeros(self.n)
        for name,current in injections.items():
            b[self.contact_nodes[name]]+=current
        free,A,diag=self.linear_system()
        v=np.zeros(self.n,dtype=np.longdouble if self.limits.linear_solver=='sparse-direct'else float)
        try:
            if self.limits.linear_solver=='cg':
                v[free],info,diagnostic=self.iterative_solution(A,b[free],diag,self.limits.max_iterations)
                self.linear_diagnostics['cg']=diagnostic;iterations=diagnostic['iterations']
                if info!=0:raise Refused(f'CG did not converge ({info}); no result qualifies')
            else:v[free],iterations=self.direct_solution(A,b[free],diag)
        except Refused as failure:
            failure.linear_solver_diagnostics=self.linear_diagnostics
            raise
        residual=self.K@v-b
        max_residual=float(np.max(abs(residual[self.active])))
        if max_residual>max(1e-8,max(abs(x) for x in injections.values())*1e-7):
            raise Refused(f'KCL residual too large: {max_residual} A')
        v[self.active]-=v[ref]
        node_v=v[self.mapping]
        field=np.einsum('ti,tij->tj',node_v[self.triangles],self.grad)
        density=np.linalg.norm(field,axis=1)/(self.sheet*self.thickness)
        sheet_loss=float(np.sum(self.areas*np.sum(field*field,axis=1))/self.sheet)
        element_loss=self.areas*np.sum(field*field,axis=1)/self.sheet
        element_layers=self.layer_ids[self.triangles[:,0]]
        peak=int(np.argmax(density))
        barrel=[]
        for a,bb,r,uid,la,lb in self.barrels:
            current=(v[a]-v[bb])/r
            barrel.append(dict(uuid=uid,layers=[la,lb],resistance_ohm=r,current_A=float(current),loss_W=float(current*current*r)))
        loss=sheet_loss+sum(x['loss_W'] for x in barrel)
        port_power=float(b@v)
        if abs(loss-port_power)>max(1e-9,abs(port_power)*1e-6):
            raise Refused('FEM energy balance failed')
        self.check_time()
        return {'contact_voltage_V':{name:float(v[node]) for name,node in self.contact_nodes.items()},
                'copper_loss_W':loss,'sheet_loss_W':sheet_loss,'port_power_W':port_power,
                'KCL_max_residual_A':max_residual,'iterations':iterations,'linear_solver_diagnostics':deepcopy(self.linear_diagnostics),
                'peak_element_density_A_per_mm2':float(max(density)),
                'peak_element_location':{'layer':self.layers[int(element_layers[peak])],
                                         'centroid_mm':self.xy[self.triangles[peak]].mean(axis=0).tolist()},
                'layer_sheet_loss_W':{layer:float(element_loss[element_layers==i].sum()) for i,layer in enumerate(self.layers)},
                'density_is_ampacity_rating':False,'barrels':barrel,
                'nodes':self.n,'triangles':len(self.triangles),'floating_unloaded_nodes':self.floating_nodes,
                'mesh_spacing_mm':self.spacing,'area_error_mm2':self.area_error_mm2,
                'element_geometry':self.element_geometry,
                'native_edge_noding':self.native_edge_noding,
                'density_limitations':'Piecewise-linear DC field; ideal lands/annuli omit pin/solder/within-land heating. Peak singularities require mesh sensitivity. No thermal rating.'}

    def impedance(self,names=None):
        names=names or list(self.contact_nodes)
        ref=names[0]
        z=np.zeros((len(names)-1,len(names)-1))
        for j,name in enumerate(names[1:]):
            res=self.solve({name:1.0,ref:-1.0},ref)
            z[:,j]=[res['contact_voltage_V'][n] for n in names[1:]]
        error=float(np.max(abs(z-z.T))) if z.size else 0.0
        if error>1e-7:
            raise Refused('Transfer matrix reciprocity failure')
        return {'contacts':names,'reference':ref,'impedance_ohm':z.tolist(),'reciprocity_error_ohm':error,
                'element_geometry':self.element_geometry,'native_edge_noding':self.native_edge_noding}
