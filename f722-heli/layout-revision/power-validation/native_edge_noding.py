"""Canonical noding proved against original integer-nm boundary edges.

No epsilon merging: a non-native vertex must prove one unique exact rational
intersection, or a retained subdivision of one straight original source line. Common native lines are split at the same
rational nodes before their one binary64 conversion. Unknown ancestry refuses.
"""
from bisect import bisect_left,bisect_right
from collections import defaultdict
from fractions import Fraction as F
from itertools import combinations
import math
import shapely as s
from shapely.geometry import Polygon,MultiPolygon,LineString,Point
from copper_fem import Refused,parts

NM_PER_MM=1000000
MAX_REPRESENTATION_SHIFT_MM=1/NM_PER_MM/1000  # 1 pm: one thousandth of a native coordinate step.


def integer_nm(point):
    row=tuple(F(str(v))*NM_PER_MM for v in point)
    if any(v.denominator!=1 for v in row):
        raise Refused('Ancestry source vertex is not an exact integer-nm coordinate')
    return tuple(int(v)for v in row)


def cross(a,b):return a[0]*b[1]-a[1]*b[0]
def sub(a,b):return(a[0]-b[0],a[1]-b[1])


def line_key(a,b):
    u=sub(b,a);x,y=u[1],-u[0];z=-(x*a[0]+y*a[1])
    g=math.gcd(math.gcd(abs(x),abs(y)),abs(z))
    if not g:raise Refused('Zero-length ancestry edge')
    row=(x//g,y//g,z//g)
    return tuple(-v for v in row)if next(v for v in row if v)<0 else row


def exact_intersection(a,b,c,d):
    u=sub(b,a);v=sub(d,c);den=cross(u,v)
    if not den:return None
    t=F(cross(sub(c,a),v),den);q=F(cross(sub(c,a),u),den)
    if not(0<=t<=1 and 0<=q<=1):return None
    return(a[0]+t*u[0],a[1]+t*u[1])


def on_segment(p,a,b):
    return cross(sub(p,a),sub(b,a))==0 and all(min(a[i],b[i])<=p[i]<=max(a[i],b[i])for i in [0,1])


def rings(g):
    return [list(p.exterior.coords)[:-1]for p in parts(g)]+[list(h.coords)[:-1]for p in parts(g)for h in p.interiors]


def signed_twice_area(points):
    return sum(cross(a,b)for a,b in zip(points,points[1:]+points[:1]))


def native_edges(snapshot,net,layer):
    """Authoritative polygon edges, including foreign drilled voids and outline."""
    result=[]
    def add(records):
        for p in records:
            for ring in [p['outer']]+p.get('holes',[]):
                result.extend((a,b)for a,b in zip(ring,ring[1:]+ring[:1])if a!=b)
    for obj in snapshot['objects']:
        if obj.get('net')==net:
            for key in ['copper','inside']:add(obj.get(key,{}).get(layer,[]))
        if obj.get('drill')and(obj['kind']!='via'or layer in obj['barrel_layers']):add(obj['drill']['outside'])
    for zone in snapshot['zones']:
        if not zone['rule']and zone['net']==net:add(zone['filled'].get(layer,[]))
    add(snapshot['outline_with_npth']['polygons'])
    return result


def canonicalize(geometries,source_edges,maximum_ulp=16,check_time=None,
                 grid_spacing_mm=None,grid_vertex_limit=None):
    if not isinstance(maximum_ulp,int)or not 1<=maximum_ulp<=32:raise Refused('Invalid ancestry ULP guard')
    if any(not g.is_empty and g.geom_type not in ('Polygon','MultiPolygon')for g in geometries):
        raise Refused('Pre-tiling ancestry requires polygonal inputs; mixed boundary constraints cannot be discarded')
    edges=sorted({tuple(sorted((integer_nm(a),integer_nm(b))))for a,b in source_edges if a!=b})
    if check_time:check_time()
    if not edges:raise Refused('No original boundary edges for exact ancestry')
    native_points={p for edge in edges for p in edge}
    native_float={tuple(float(F(v,NM_PER_MM))for v in p):p for p in native_points}
    if len(native_float)!=len(native_points):raise Refused('Distinct native source vertices collapse in binary64')
    source_rounding_allowance=.5*max(math.hypot(*(math.ulp(v)for v in p))for p in native_float)
    lines=[line_key(a,b)for a,b in edges]
    segments=[LineString([[float(F(v,NM_PER_MM))for v in p]for p in edge])for edge in edges]
    tree=s.STRtree(segments)
    if check_time:check_time()
    originals=sorted({tuple(p)for g in geometries for ring in rings(g)for p in ring})
    neighbors=defaultdict(list)
    for geometry in geometries:
        for ring in rings(geometry):
            for index,p in enumerate(ring):
                neighbors[tuple(p)].append((tuple(ring[index-1]),tuple(ring[(index+1)%len(ring)])))
    rational={};incidence={};shift_rows=[];float_identities={};subdivisions={}

    def subdivision_refusal(reason,point,**proof):
        error=Refused('Single-line subdivision ancestry '+reason)
        error.geometry_reproduction={'stage':'single_line_subdivision','point':point,**proof}
        raise error
    for vertex_index,p in enumerate(originals):
        if check_time and vertex_index%256==0:check_time()
        normal_radius=maximum_ulp*math.hypot(*(math.ulp(v)for v in p))
        # The exact intersection may lie near a segment endpoint. Searching
        # only its line-normal error radius could omit a competing ancestry
        # whose allowed displacement is mostly tangential.
        candidates=[int(i)for i in tree.query(Point(p),predicate='dwithin',
          distance=max(normal_radius,MAX_REPRESENTATION_SHIFT_MM)+source_rounding_allowance)]
        if p in native_float:
            exact=native_float[p]
            for pair_index,(i,j)in enumerate(combinations(candidates,2)):
                if check_time and pair_index%256==0:check_time()
                hit=exact_intersection(*edges[i],*edges[j])
                if hit is not None and hit!=exact and tuple(float(F(v,NM_PER_MM))for v in hit)==p:
                    raise Refused('Distinct exact intersection collapses onto an existing native vertex')
        else:
            matches={};p_nm=tuple(F(v)*NM_PER_MM for v in p)
            for pair_index,(i,j)in enumerate(combinations(candidates,2)):
                if check_time and pair_index%256==0:check_time()
                hit=exact_intersection(*edges[i],*edges[j])
                if hit is None:continue
                a,b=edges[i];c,d=edges[j];u=sub(b,a);v=sub(d,c)
                sine=abs(cross(u,v))/(math.hypot(*u)*math.hypot(*v))
                residuals=[float(abs(cross(sub(p_nm,aa),sub(bb,aa))))/math.dist(aa,bb)/NM_PER_MM
                           for aa,bb in [edges[i],edges[j]]]
                if max(residuals)>normal_radius:continue
                converted=tuple(float(F(k,NM_PER_MM))for k in hit)
                # Two line-normal residuals amplify with the inverse crossing
                # angle. The absolute budget remains 1000x below the source
                # coordinate grid; this is never permission to merge points.
                bound=min(MAX_REPRESENTATION_SHIFT_MM,2*normal_radius/sine+math.hypot(*(math.ulp(k)for k in converted)))
                if math.dist(converted,p)>bound:continue
                proof={'source_edges_nm':[edges[i],edges[j]],'exact_line_residuals_mm':residuals,
                  'line_residual_guard_mm':normal_radius,'sine_crossing_angle':sine,
                  'conditioned_distance_bound_mm':bound,'absolute_distance_cap_mm':MAX_REPRESENTATION_SHIFT_MM}
                if hit not in matches or bound<matches[hit]['conditioned_distance_bound_mm']:matches[hit]=proof
            if len(matches)==1:
                exact=next(iter(matches));admission=matches[exact]
            elif not matches and candidates and len({lines[i]for i in candidates})==1:
                # Boolean overlays may retain a point inside one straight
                # source edge after the intersecting interior edge disappears.
                # Its longitudinal parameter is a subdivision, not a crossing.
                # Retain that node, project only onto its unique exact line,
                # then certify both neighboring boundary edges on that line.
                i=candidates[0];a,b=edges[i];u=sub(b,a);length2=u[0]*u[0]+u[1]*u[1]
                parameter=sum(sub(p_nm,a)[k]*u[k]for k in [0,1])/length2
                exact=tuple(F(a[k])+parameter*u[k]for k in [0,1])
                residual=float(abs(cross(sub(p_nm,a),u)))/math.sqrt(length2)/NM_PER_MM
                interior=any(on_segment(exact,*edges[j])and exact not in edges[j]for j in candidates)
                neighbor_proofs=[]
                if residual>normal_radius or not interior:
                    subdivision_refusal('is outside a strict native interval or normal bound',p,source_edges_nm=[edges[j]for j in candidates],normal_residual_mm=residual,normal_bound_mm=normal_radius,strict_interior=interior)
                for before,after in neighbors[p]:
                    points=[tuple(F(v)*NM_PER_MM for v in q)for q in [before,after]]
                    bounds=[maximum_ulp*math.hypot(*(math.ulp(v)for v in q))for q in [before,after]]
                    errors=[float(abs(cross(sub(q,a),u)))/math.sqrt(length2)/NM_PER_MM for q in points]
                    parameters=[sum(sub(q,a)[k]*u[k]for k in [0,1])/length2 for q in points]
                    if any(error>bound for error,bound in zip(errors,bounds))or not min(parameters)<parameter<max(parameters):
                        subdivision_refusal('is not between collinear boundary neighbors',p,before_mm=before,after_mm=after,line_normal_residuals_mm=errors,line_normal_bounds_mm=bounds)
                    neighbor_proofs.append({'before_mm':before,'after_mm':after,
                      'line_normal_residuals_mm':errors,'line_normal_bounds_mm':bounds})
                converted=tuple(float(v/NM_PER_MM)for v in exact)
                bound=min(MAX_REPRESENTATION_SHIFT_MM,normal_radius+math.hypot(*(math.ulp(v)for v in converted)))
                if math.dist(converted,p)>bound:subdivision_refusal('exceeds representation bound',p,projected_mm=converted,allowed_mm=bound)
                admission={'kind':'retained_single_line_subdivision','source_line':lines[i],
                  'source_edges_nm':[edges[j]for j in candidates],
                  'projected_parameter_from_first_edge':str(parameter),
                  'exact_line_residual_mm':residual,'line_residual_guard_mm':normal_radius,
                  'conditioned_distance_bound_mm':bound,'absolute_distance_cap_mm':MAX_REPRESENTATION_SHIFT_MM,
                  'neighbors':neighbor_proofs}
                subdivisions[p]={'line':lines[i],'proof':admission}
            else:
                error=Refused('Missing or ambiguous exact native-edge vertex ancestry')
                error.geometry_reproduction={'stage':'edge_ancestry','point':p,'candidate_edges':len(candidates),'exact_matches':len(matches)}
                raise error
        incident={lines[i]for i in candidates if on_segment(exact,*edges[i])}
        if not incident:raise Refused('Canonical point has no exact source incidence')
        rational[p]=exact;incidence[exact]=incidence.get(exact,set())|incident
        converted=tuple(float(F(v,NM_PER_MM))for v in exact)
        if converted in float_identities and float_identities[converted]!=exact:
            raise Refused('Distinct rational intersections collapse to one binary64 point')
        float_identities[converted]=exact
        displacement=math.dist(p,converted)
        if p in native_float and converted!=p:raise Refused('Native vertex conversion changed its coordinates')
        if displacement:shift_rows.append({'before_mm':p,'after_mm':converted,'displacement_mm':displacement,
          'rational_point_nm':[str(v)for v in exact],
          'source_edges_nm':[edges[i]for i in candidates if on_segment(exact,*edges[i])],
          'signed_ULP_change':[(converted[k]-p[k])/math.ulp(p[k])for k in [0,1]],
          'admission_certificate':admission})
    subdivision_certificates=[]
    for p,record in subdivisions.items():
        line=record['line'];point=rational[p]
        k=0 if abs(line[1])>=abs(line[0])else 1
        for before,after in neighbors[p]:
            a,b=rational[before],rational[after]
            if line not in incidence[a]or line not in incidence[b]or not min(a[k],b[k])<point[k]<max(a[k],b[k]):
                subdivision_refusal('neighbors lack exact common-line coverage/order',p,before_mm=before,after_mm=after)
        converted=tuple(float(v/NM_PER_MM)for v in point)
        subdivision_certificates.append({'before_mm':p,'after_mm':converted,
          'exact_point_nm':[str(v)for v in point],'displacement_mm':math.dist(p,converted),
          'both_adjacent_edges_on_exact_native_line':True,'node_retained':True,
          'admission_certificate':record['proof']})
    # Node each proved boundary interval at its exact decimal-grid crossings
    # before GEOS clips either copy. Clipping the same native line independently
    # in a domain and ideal land can otherwise return different binary64 points
    # and invent a thin sheet face between identical physical boundaries.
    # These are new subdivisions of the exact line, never moved native points.
    grid_nodes=set();maximum_grid_rounding_error_mm=0.
    if grid_spacing_mm is not None:
        if not math.isfinite(grid_spacing_mm) or grid_spacing_mm<=0:
            raise Refused('Invalid exact grid spacing')
        if grid_vertex_limit is not None and (type(grid_vertex_limit)is not int or grid_vertex_limit<1):
            raise Refused('Invalid exact grid vertex cap')
        step=F(str(grid_spacing_mm))*NM_PER_MM
        intervals=set()
        for geometry in geometries:
            for ring in rings(geometry):
                for a,b in zip(ring,ring[1:]+ring[:1]):
                    p,q=rational[tuple(a)],rational[tuple(b)]
                    common=incidence[p]&incidence[q]
                    if len(common)!=1:raise Refused('Grid interval lacks unique exact native-line ancestry')
                    intervals.add((next(iter(common)),*sorted((p,q))))
        for interval_index,(line,p,q)in enumerate(sorted(intervals)):
            if check_time and interval_index%256==0:check_time()
            for axis in [0,1]:
                if p[axis]==q[axis]:continue
                low,high=sorted((p[axis],q[axis]))
                first=low//step+1
                last=-((-high)//step)-1
                for index in range(first,last+1):
                    if check_time and len(grid_nodes)%256==0:check_time()
                    value=index*step
                    t=(value-p[axis])/(q[axis]-p[axis])
                    hit=tuple(p[k]+t*(q[k]-p[k])for k in [0,1])
                    converted=tuple(float(F(v,NM_PER_MM))for v in hit)
                    maximum_grid_rounding_error_mm=max(maximum_grid_rounding_error_mm,
                      math.hypot(*(float(F(converted[k])-hit[k]/NM_PER_MM)for k in [0,1])))
                    if converted in float_identities and float_identities[converted]!=hit:
                        raise Refused('Distinct exact grid intersections collapse to one binary64 point')
                    float_identities[converted]=hit
                    if hit not in incidence:grid_nodes.add(hit)
                    incidence.setdefault(hit,set()).add(line)
                    if grid_vertex_limit is not None and len(grid_nodes)>grid_vertex_limit:
                        raise Refused('Exact grid intersection cap exceeded')
    line_nodes=defaultdict(set)
    for p,ls in incidence.items():
        for line in ls:line_nodes[line].add(p)
    axis=lambda line:0 if abs(line[1])>=abs(line[0]) else 1
    node_tables={line:sorted(rows,key=lambda p:p[axis(line)])for line,rows in line_nodes.items()}
    parameters={line:[p[axis(line)]for p in rows]for line,rows in node_tables.items()}
    # Coverage is exact, including source edges that share the same line.
    coverage=defaultdict(list)
    for line,(a,b)in zip(lines,edges):coverage[line].append(tuple(sorted((a[axis(line)],b[axis(line)]))))
    for line,intervals in coverage.items():
        merged=[]
        for low,high in sorted(intervals):
            if merged and low<=merged[-1][1]:merged[-1]=(merged[-1][0],max(high,merged[-1][1]))
            else:merged.append((low,high))
        coverage[line]=merged
    inserted=0;ring_certificates=[]
    def rebuild_ring(ring):
        nonlocal inserted
        raw=list(ring.coords)[:-1];out=[];exact_out=[]
        for edge_index,(a,b)in enumerate(zip(raw,raw[1:]+raw[:1])):
            if check_time and edge_index%256==0:check_time()
            p,q=rational[tuple(a)],rational[tuple(b)]
            common=incidence[p]&incidence[q]
            if len(common)!=1:
                raise Refused('Polygon edge lacks unique exact native-line ancestry')
            line=next(iter(common));k=axis(line);low,high=sorted((p[k],q[k]))
            if not any(x<=low and high<=y for x,y in coverage[line]):
                raise Refused('Derived boundary edge crosses an uncovered native interval')
            values=parameters[line];start=bisect_left(values,low);end=bisect_right(values,high)
            selected=node_tables[line][start:end]
            if p[k]>q[k]:selected=list(reversed(selected))
            if selected[0]!=p or selected[-1]!=q:raise Refused('Missing exact interval endpoint')
            converted=[tuple(float(F(v,NM_PER_MM))for v in point)for point in selected]
            direction=1 if p[k]<q[k]else-1
            if any(direction*(bb[k]-aa[k])<=0 for aa,bb in zip(converted,converted[1:])):
                raise Refused('Exact edge node ordering collapses in binary64')
            inserted+=len(selected)-2
            out.extend(converted[:-1])
            exact_out.extend(selected[:-1])
        if not set(raw)<=set(out):
            # Only derived vertices may change their floating representation.
            if any(tuple(p)in native_float and tuple(p)not in out for p in raw):raise Refused('A native vertex was removed')
        exact_before=signed_twice_area([rational[tuple(p)]for p in raw])
        exact_after=signed_twice_area(exact_out)
        if exact_before!=exact_after:raise Refused('Exact rational ring area changed during noding')
        binary_before=signed_twice_area([tuple(F(v)for v in p)for p in raw])
        binary_after=signed_twice_area([tuple(F(v)for v in p)for p in out])
        if binary_before*binary_after<=0:raise Refused('Ring orientation changed or collapsed')
        ring_certificates.append({'rational_twice_area_nm2':str(exact_before),
          'rational_area_preserved_exactly':True,'orientation_preserved':True,
          'binary64_area_delta_mm2_exact_fraction':str((binary_after-binary_before)/2),
          'binary64_area_delta_mm2':float((binary_after-binary_before)/2)})
        if check_time:check_time()
        return out
    outputs=[];checks=[]
    max_shift=max([row['displacement_mm']for row in shift_rows]+[0.])
    for geometry in geometries:
        if check_time:check_time()
        before=parts(geometry)
        after=[Polygon(rebuild_ring(p.exterior),[rebuild_ring(h)for h in p.interiors])for p in before]
        result=after[0]if len(after)==1 else MultiPolygon(after)
        if not result.is_valid:raise Refused('Exact ancestry noding produced invalid binary64 polygons')
        # The rational boundary is unchanged. This bounds its binary64
        # representation change, including newly inserted collinear nodes.
        coord=max([abs(v)for ring in rings(geometry)for p in ring for v in p]+[1.])
        shift_bound=max(max_shift,math.sqrt(2)*math.ulp(coord))
        area_bound=2*geometry.length*shift_bound+64*math.ulp(max(geometry.area,1.))
        delta=result.area-geometry.area
        if abs(delta)>area_bound:raise Refused('Noded area differs beyond the explicit roundoff bound')
        if len(parts(result))!=len(before)or sum(len(p.interiors)for p in parts(result))!=sum(len(p.interiors)for p in before):
            raise Refused('Ancestry noding changed contour/hole topology')
        checks.append({'before_area_mm2':geometry.area,'after_area_mm2':result.area,'area_delta_mm2':delta,
          'area_roundoff_bound_mm2':area_bound,'contours':len(before),'holes':sum(len(p.interiors)for p in before),
          'native_vertices_preserved':True,'rational_boundary_unchanged':True})
        outputs.append(result)
    return outputs,{'status':'EXACT NATIVE-EDGE ANCESTRY NODING','source_edges':len(edges),
      'input_unique_vertices':len(originals),'inserted_seam_vertices':inserted,'changed_derived_vertices':len(shift_rows),
      'maximum_derived_vertex_displacement_mm':max_shift,'line_residual_ulp_guard':maximum_ulp,
      'grid_spacing_mm':grid_spacing_mm,'inserted_exact_grid_vertices':len(grid_nodes),
      'maximum_grid_intersection_rounding_error_mm':maximum_grid_rounding_error_mm,
      'grid_crossings_inserted_before_overlay':grid_spacing_mm is not None,
      'maximum_representation_shift_mm':MAX_REPRESENTATION_SHIFT_MM,
      'coordinate_changes':shift_rows,'geometry_checks':checks,'native_vertices_changed':0,
      'retained_single_line_subdivisions':len(subdivision_certificates),
      'single_line_subdivision_certificates':subdivision_certificates,
      'ring_certificates':ring_certificates,
      'ambiguous_ancestry_allowed':False,'epsilon_vertex_merging':False}
