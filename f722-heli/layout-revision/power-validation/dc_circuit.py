#!/usr/bin/env python3
"""Small nodal DC solver with finite-port copper and conserved converter power.

Input is an explicit new case ledger. It has no embedded legacy currents or hidden
ideal-ground shortcuts. Mux selection is explicit in each case; transient selection
and reverse blocking cannot be established by this static model.
"""
import math
import numpy as np
from copper_fem import Refused


def solve_circuit(case, port_networks=(), max_iterations=150):
    ground=case['reference_node']
    if max_iterations < 1:
        raise Refused('Iteration budget must be positive')
    def finite(value, label):
        if not math.isfinite(value):
            raise Refused(f'Nonfinite {label}')
        return value
    for category in ['resistors','loads','sources','converters','probes']:
        entries=case.get(category,[])
        identifiers=[x['name'] for x in entries]
        if len(set(identifiers)) != len(identifiers):
            raise Refused(f'Duplicate {category} names')
        for entry in entries:
            for key,value in entry.items():
                if isinstance(value,(int,float)):
                    finite(value,f'{entry["name"]}/{key}')
    keys=set()
    for category in ['resistors','loads','sources','converters']:
        for x in case.get(category,[]):
            for k in ['p','n','in_p','in_n','out_p','out_n','sense_p','sense_n']:
                if k in x:
                    keys.add(x[k])
    for block in port_networks:
        keys.update(block['contacts'])
    keys.discard(ground)
    names=sorted(keys); nodes={name:i for i,name in enumerate(names)}
    n=len(names)
    if not n or n>1500:
        raise Refused('Empty circuit or circuit node cap exceeded')
    for probe in case.get('probes',[]):
        if set([probe['p'],probe['n']]) - (keys|{ground}):
            raise Refused('Probe references an unmodeled node')
    sources=list(case.get('sources',[]))
    converters=case.get('converters',[])
    for c in converters:
        if not 0<c['efficiency']<=1:
            raise Refused('Invalid converter efficiency')
        if c.get('quiescent_A',0)<0 or c['voltage_V']<=0:
            raise Refused('Invalid converter quiescent current or output voltage')
        sources.append({'name':c['name'],'p':c['out_p'],'n':c['out_n'],
                        'sense_p':c.get('sense_p',c['out_p']),'sense_n':c.get('sense_n',c['out_n']),
                        'voltage_V':c['voltage_V']})
    if len({s['name'] for s in sources}) != len(sources):
        raise Refused('Duplicate source/converter names')
    if n+len(sources)>1500:
        raise Refused('Circuit equation cap exceeded')
    mat=np.zeros((n+len(sources),n+len(sources)))
    rhs=np.zeros(len(mat))
    def stamp(a,b,g):
        if a!=ground:mat[nodes[a],nodes[a]]+=g
        if b!=ground:mat[nodes[b],nodes[b]]+=g
        if a!=ground and b!=ground:
            mat[nodes[a],nodes[b]]-=g;mat[nodes[b],nodes[a]]-=g
    def inject(target,a,b,amps):
        if a!=ground:target[nodes[a]]-=amps
        if b!=ground:target[nodes[b]]+=amps
    for r in case.get('resistors',[]):
        if r['ohm']<=0:raise Refused('Use a zero-volt source for an intentional ideal device tie')
        stamp(r['p'],r['n'],1/r['ohm'])
    for block in port_networks:
        contacts=block['contacts']; z=np.asarray(block['impedance_ohm'])
        if len(contacts)<2 or len(set(contacts))!=len(contacts):
            raise Refused('Port block needs distinct terminals')
        if z.shape!=(len(contacts)-1,len(contacts)-1):
            raise Refused('Port impedance shape mismatch')
        if not np.all(np.isfinite(z)) or not np.allclose(z,z.T,atol=1e-7,rtol=1e-7):
            raise Refused('Nonfinite/nonreciprocal impedance block')
        if np.min(np.linalg.eigvalsh(z))<=0:
            raise Refused('Port impedance is not positive definite')
        y=np.linalg.inv(z)
        lap=np.zeros((len(contacts),len(contacts)))
        lap[1:,1:]=y;lap[0,1:]=-y.sum(axis=0);lap[1:,0]=-y.sum(axis=1);lap[0,0]=y.sum()
        for i,a in enumerate(contacts):
            for j,b in enumerate(contacts):
                if a!=ground and b!=ground:mat[nodes[a],nodes[b]]+=lap[i,j]
    for i,src in enumerate(sources):
        row=n+i
        for key,sign in [('p',1),('n',-1)]:
            if src[key]!=ground:mat[nodes[src[key]],row]+=sign
        for key,default,sign in [('sense_p','p',1),('sense_n','n',-1)]:
            point=src.get(key,src[default])
            if point!=ground:mat[row,nodes[point]]+=sign
        rhs[row]=src['voltage_V']
    for load in case.get('loads',[]):
        if load['current_A']<0:raise Refused('Negative load needs an explicitly modeled source')
        inject(rhs,load['p'],load['n'],load['current_A'])
    input_currents=np.zeros(len(converters))
    solution=None
    def volts(point):return 0.0 if point==ground else float(solution[nodes[point]])
    for it in range(max_iterations):
        b=rhs.copy()
        for c,current in zip(converters,input_currents):inject(b,c['in_p'],c['in_n'],current)
        try:solution=np.linalg.solve(mat,b)
        except np.linalg.LinAlgError as e:raise Refused('Floating/overconstrained DC ledger') from e
        if not np.all(np.isfinite(solution)):
            raise Refused('Nonfinite circuit solution')
        desired=[]
        for i,c in enumerate(converters):
            vin=volts(c['in_p'])-volts(c['in_n'])
            vout=volts(c['out_p'])-volts(c['out_n'])
            iout=-solution[n+len(case.get('sources',[]))+i]
            if vin<=0 or vout<0 or iout<-1e-8:raise Refused('Invalid converter direction or collapsed input')
            desired.append(vout*max(0,iout)/(c['efficiency']*vin)+c.get('quiescent_A',0))
        desired=np.asarray(desired)
        if not len(desired) or max(abs(desired-input_currents))<1e-10:break
        input_currents=0.5*(input_currents+desired)
    else:raise Refused('Conserved-power iteration did not converge')
    residual=float(max(abs(mat@solution-b)))
    if residual>1e-7:raise Refused('Circuit KCL/equation residual too large')
    converter_rows=[]
    for i,c in enumerate(converters):
        vin=volts(c['in_p'])-volts(c['in_n']);vout=volts(c['out_p'])-volts(c['out_n'])
        iout=-float(solution[n+len(case.get('sources',[]))+i])
        if not c.get('minimum_input_V',0) <= vin <= c.get('maximum_input_V',np.inf):
            raise Refused(f'{c["name"]}: input outside explicit model range')
        if iout > c.get('maximum_output_A',np.inf):
            raise Refused(f'{c["name"]}: output exceeds explicit static model current')
        error=vin*(input_currents[i]-c.get('quiescent_A',0))*c['efficiency']-vout*iout
        if abs(error)>1e-8:raise Refused('Converter power balance failed')
        converter_rows.append({'name':c['name'],'input_V':vin,'output_V':vout,'input_A':float(input_currents[i]),'output_A':iout,'conversion_loss_W':float(vin*input_currents[i]-vout*iout),'power_balance_error_W':error})
    measured=[]
    for probe in case.get('probes',[]):
        value=volts(probe['p'])-volts(probe['n'])
        measured.append({'name':probe['name'],'voltage_V':value,'pass':probe.get('minimum_V',-np.inf)<=value<=probe.get('maximum_V',np.inf),**{k:v for k,v in probe.items() if k in ['minimum_V','maximum_V','purpose']}})
    port_currents=[]
    copper_loss=0.0
    for block in port_networks:
        values=np.asarray([volts(p) for p in block['contacts']])
        current=np.linalg.solve(np.asarray(block['impedance_ohm']),values[1:]-values[0])
        copper_loss += float((values[1:]-values[0])@current)
        port_currents.append({'net':block.get('net'),'injections_A':dict(zip(block['contacts'],np.r_[-current.sum(),current].tolist()))})
    resistor_rows=[]
    for resistor in case.get('resistors',[]):
        drop=volts(resistor['p'])-volts(resistor['n'])
        amps=drop/resistor['ohm']
        resistor_rows.append({'name':resistor['name'],'current_A':amps,'loss_W':drop*amps})
    load_power=sum((volts(x['p'])-volts(x['n']))*x['current_A'] for x in case.get('loads',[]))
    if any(volts(x['p'])-volts(x['n']) < 0 for x in case.get('loads',[])):
        raise Refused('Load voltage reversed; constant-current model no longer valid')
    source_power=-sum((volts(src['p'])-volts(src['n']))*float(solution[n+i])
                      for i,src in enumerate(case.get('sources',[])))
    conversion_loss=sum(row['conversion_loss_W'] for row in converter_rows)
    resistive_loss=sum(row['loss_W'] for row in resistor_rows)
    power_error=source_power-load_power-conversion_loss-resistive_loss-copper_loss
    if abs(power_error)>max(1e-8,abs(source_power)*1e-8):
        raise Refused('Whole-circuit power balance failed')
    return {'case':case['name'],'voltage_V':{p:volts(p) for p in [ground]+names},
            'source_current_A':{s['name']:float(solution[n+i]) for i,s in enumerate(sources)},
            'converters':converter_rows,'probes':measured,'port_injections':port_currents,
            'resistors':resistor_rows,
            'power_W':{'source_delivery':source_power,'load_absorption':load_power,
                       'conversion_loss':conversion_loss,'resistor_loss':resistive_loss,
                       'copper_loss':copper_loss,'balance_error':power_error},
            'equation_residual_max':residual,'iterations':it+1,
            'static_probe_pass':all(x['pass'] for x in measured),
            'qualification':'NEW CONDITIONAL STATIC CASE ONLY; no dynamics, thermal, production or flight qualification'}
