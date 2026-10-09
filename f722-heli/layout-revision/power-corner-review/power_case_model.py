#!/usr/bin/env python3
"""Pure case definitions for the disabled plan compiler; no filesystem or solver calls."""

def resistor(name,p,n,ohm,**kw):return dict(name=name,p=p,n=n,ohm=ohm,**kw)

def tie(name,p,n):return {'name':name,'p':p,'n':n,'voltage_V':0,'meaning':'Explicit ideal internal pin/entry tie; package/contact resistance excluded'}

def load(name,p,n,current):return {'name':name,'p':p,'n':n,'current_A':current}


def case_factory(plan):
    profiles = plan['engineering_sensitivity_profiles']
    corners = plan['U6_corners']
    vertex_map = plan['proposed_case_dimensions']['electronics_allocation_vertices']
    ABC = {'AB':['J9','J10'], 'AC':['J9','J11'], 'BC':['J10','J11']}
    feed_examples = {name:{ref:(pair['positive'],pair['return']) for ref,pair in profile['per_conductor_ohm'].items()}
                     for name,profile in plan['same_BEC_illustrative_feed_profiles'].items()}
    servo_definitions = plan['servo_comparison_profiles']
    servo_profiles = {name:profile['connector_currents_A'] for name,profile in servo_definitions.items()}
    def make_case(scope,vin,combo,vertex,profile='baseline',supply='BEC',dsm_override=None):
        pr=profiles[profile];co=corners[pr['u6_corner']]
        electronics=.30 if supply=='USB' else .32
        dsm=(0 if supply=='USB' else .50 if scope=='capacity' else .020) if dsm_override is None else dsm_override
        name=f'{scope}_{supply}{vin:g}_{combo}_{vertex}_{profile}'
        case={'name':name,'execution_enabled':False,'scope':scope,'supply':supply,
              'parameters':{'input_at_defined_source_V':vin,'ABC_ports':ABC.get(combo,[]),'electronics_A':electronics,
                            'DSM_A':dsm,'CORE_aggregate_A':round(electronics+dsm,9),'allocation_vertex':vertex,**pr},
              'reference_node':'SOURCE_GND','sources':[],'resistors':[],'loads':[],'converters':[],'probes':[],
              'report_only_probes':[],
              'assumptions':['New adversarial electronics-current allocation, not a recovered historical load split.',
                             'All CORE-powered logic/bias/quiescent demand is included once in the aggregate electronics allowance.',
                             'Converter eta_total is an engineering assumption including converter operating loss; additive IQ=0 avoids double counting and does not mean zero physical IQ.',
                             'Finite native sheet/barrel paths and actual load returns are required; no nominal-width shortcut.',
                             'Mux selection is prescribed; no startup, hysteresis, switching or backfeed result is implied.',
                             'U8 RON row is specified at VINx>=5V, |IOUT|=200mA. Effective RON outside those tests is a sensitivity assumption.',
                             ('U9 setpoint uses the initial PFM high factor; line/load/ripple and input headroom remain separate guards.' if profile=='upper_initial' else 'U9 setpoint uses the conservative initial PFM low factor; line/load/ripple and input headroom remain separate guards.')],
              'activation_blockers':['Source unfinished and unbound','Grouped U6 contacts require fresh source verification',
                                      'Engineering assumptions/headroom require reviewed materialization']}
        r=case['resistors'];s=case['sources'];ld=case['loads'];cv=case['converters']
        # Native output pins are separately landed but are one internal device OUT.
        s += [tie('U8_OUT1','DEV_U8_OUT','U8.1'),tie('U8_OUT8','DEV_U8_OUT','U8.8'),
              tie('U7_OUT2','DEV_U7_OUT','U7.2'),tie('U7_OUT7','DEV_U7_OUT','U7.7')]
        r += [resistor('U11_selected_path','U11.4','U11.1',.15,condition='150mOhm engineering screen; current limiter dynamics excluded'),
              resistor('ABC_ADC_divider_lumped','R42.1','R44.2',100000,condition='Native68k+16k+16k; internal divider copper and ADC input currents omitted')]
        if supply=='BEC':
            s += [{'name':'BEC_at_J6_pads','p':'J6.2','n':'SOURCE_GND','voltage_V':vin},tie('J6_return_reference','J6.1','SOURCE_GND')]
            r += [resistor('U5_efuse_path','U5.5','U5.6',.045,condition='45mOhm maximum row tested at3A; above3A is explicit extrapolation'),
                  resistor('U7_BEC_selected_path','U7.3','DEV_U7_OUT',.033,condition='TPS2117 33mOhm tested at200mA through105C;2A is explicit extrapolation'),
                  resistor('U8_BEC_selected_path','U8.7','DEV_U8_OUT',pr['U8_effective_RON_ohm']),
                  resistor('R53_protected_bleeder','R53.1','R53.2',4700),resistor('R58_ABC_bleeder','R58.1','R58.2',47000),
                  resistor('R54_feedback_top','R54.1','R54.2',co['R54_ohm']),resistor('R55_feedback_bottom','R55.1','R55.2',co['R55_ohm']),
                  resistor('BEC_ADC_divider_lumped','R40.1','R41.2',125000,condition='Native105k+20k; internal divider copper omitted'),
                  resistor('U8_priority_bias_lumped','R60.1','R61.2',28000,condition='Native18k+10k;330k ST coupling must be bounded separately')]
            # Signed leakage represented as the equivalent feedback-reference shift.
            # This omits only its tiny trace-current field, not the IFB*R54 offset.
            parallel=co['R54_ohm']*co['R55_ohm']/(co['R54_ohm']+co['R55_ohm'])
            feedback=(co['feedback_reference_V']+pr['U6_IFB_sensitivity_A']*parallel)*(1+pr.get('additional_output_error_fraction',0))
            cv += [{'name':'U6_total_efficiency','in_p':'U6.VIN_12_13','in_n':'U6.10','out_p':'U6.OUT_7_8','out_n':'U6.10',
                    'sense_p':'U6.5','sense_n':'U6.4','voltage_V':feedback,'efficiency':pr['efficiency_total'],'quiescent_A':0,
                    'minimum_input_V':2,'maximum_input_V':16,
                    'control_meaning':'Actual R54/R55 and finite ABC_FB copper; regulates FB relative to quiet U6.4, while power enters/returns at real power terminals.',
                    'feedback_leakage_model':'Equivalent-reference IFB*(R54||R55); signed sensitivity is not a guaranteed signed leakage range; 100nA feedback-trace field is omitted.'}]
            case['nets']=['VX_RAW','VX_PROTECTED','+5V_BEC','+5V_PERIPH','CORE_BUCK_IN','+3V3_CORE','+3V3_DSM','ABC_FB','GND']
            ld += [load('U8_IQ_screen','U8.7','U8.12',.0004),
                   load('U5_IQ_table_screen','U5.5','U5.8',.000610),
                   load('U7_IQ_table_screen','U7.3','U7.1',.0000044),
                   load('U8_ST_coupling_reserve','R60.1','R61.2',.000020),
                   load('U8_inactive_leakage_reserve','U8.7','U8.12',.000500)]
            case['assumptions'] += ['Ideal J6 pad-entry source; no unmeasured BEC lead/contact resistance is assigned.',
                                    ('External ABC load is exactly1A on each of the two named ports;2A aggregate, never2A through one GH contact.' if combo in ABC else 'External ABC loads are disconnected in this upper-voltage slice.'),
                                    'At5V raw, U6 can operate in mild boost; the2A output row VOUT/VIN<=1 is not unconditionally applicable.']
        else:
            s += [{'name':'USB_at_ideal_contact_common','p':'USB_SOURCE','n':'SOURCE_GND','voltage_V':vin}]
            s += [tie('USB_VBUS_'+pin,'USB_SOURCE','J1.'+pin)for pin in ['A4','A9','B4','B9']]
            s += [tie('USB_GND_'+pin,'J1.'+pin,'SOURCE_GND')for pin in ['A1','A12','B1','B12']]
            r += [resistor('U10_USB_limiter_path','U10.4','U10.1',.15),
                  resistor('U7_USB_selected_path','U7.6','DEV_U7_OUT',.033),
                  resistor('U8_USB_selected_path','U8.2','DEV_U8_OUT',pr['U8_effective_RON_ohm']),
                  resistor('R68_limited_bleeder','R68.1','R68.2',1000),resistor('R69_raw_bleeder','R69.1','R69.2',10000)]
            ld += [load('U8_IQ_screen','U8.2','U8.12',.0004),
                   load('U7_IQ_table_screen','U7.6','U7.1',.0000045),
                   load('U10_IQ_table_screen','U10.4','U10.5',.000140),
                   load('U8_inactive_leakage_reserve','U8.2','U8.12',.000500)]
            case['nets']=['USB_VBUS_RAW','USB_LIMITED','+5V_PERIPH','CORE_BUCK_IN','+3V3_CORE','+3V3_DSM','GND']
            case['assumptions'] += ['Configuration only: all external ABC, DSM and servo loads are disconnected.',
                                   'USB source is prescribed at ideal common connector contacts; this does not invent cable/contact tolerances.',
                                   '4.33/5.0/5.25V are declared source sensitivity points from project discussion, not proof of USB compliance or pre-enumeration current behavior.']
        core_v=(3.432 if profile=='upper_initial' else 3.1845)*(1+pr.get('additional_output_error_fraction',0))
        cv += [{'name':'U9_total_efficiency','in_p':'U9.2','in_n':'U9.1','out_p':'L2.2','out_n':'U9.1',
                'sense_p':'U9.6','sense_n':'U9.4','voltage_V':core_v,'efficiency':pr['efficiency_total'],'quiescent_A':0,
                'minimum_input_V':3,'maximum_input_V':17,'maximum_output_A':1,
                'control_meaning':'Inject at real inductor output L2.2; U9.6 is a sense terminal only. Conversion loss includes the inductor; no DCR is double-counted.'}]
        if vertex in vertex_map:
            ld += [load('aggregate_electronics_adversarial',vertex_map[vertex]['p'],vertex_map[vertex]['n'],electronics)]
        else:
            ld += [{'name':'aggregate_electronics_adversarial','p':None,'n':None,'current_A':electronics,
                    'pending_selection':'Worst relevant baseline allocation vertex, followed by ranking-sensitivity check'}]
        if dsm:ld += [load('DSM_external','J12.1','J12.2',dsm)]
        for ref in ABC.get(combo,[]):
            if supply=='BEC':
                ld += [load(ref+'_external','J9.3'if ref=='J9'else ref+'.3',ref+'.4',1)]
                case['probes'].append({'name':ref+'_receiver_pad','p':ref+'.3','n':ref+'.4','minimum_V':4.8,
                                       'purpose':'Conditional RP3-H pad floor:4.5V remote +1A*(0.200Ohm contacts + <=0.100Ohm measured cable)'})
        if scope=='classic':
            case['probes'].append({'name':'classic_DSM_pad','p':'J12.1','n':'J12.2','minimum_V':3.1394,'maximum_V':3.465,
                                   'purpose':'Classic20mA remote only; lower floor includes0.120Ohm contacts + <=0.100Ohm measured cable, with no invented dynamic allowance'})
        else:
            case['report_only_probes'].append({'name':'DSM_pad_voltage_no_accuracy_claim','p':'J12.1','n':'J12.2',
                                              'reason':'0.50A capacity has no inherited classic +/-5% voltage guarantee; USB has no external DSM load'})
        case['probes'].append({'name':'U9_operating_input_only','p':'U9.2','n':'U9.1','minimum_V':3,'maximum_V':17,
                               'purpose':'Recommended input operating range only; not a guarantee of3.3V regulation'})
        case['report_only_probes'] += [
            {'name':'U9_input_accuracy_window_headroom','p':'U9.2','n':'U9.1','comparison_floor_V':4.3,
             'reason':'PWM accuracy row condition VIN>=VOUT+1V for nominal3.3V; crossing it ends that assurance, not necessarily chip operation'},
            {'name':'U9_input_relative_to_quiet_AGND','p':'U9.2','n':'U9.4','comparison_floor_V':4.3,
             'reason':'Report both power-ground and quiet-AGND references; internal package ground behavior remains an explicit idealization'},
            {'name':'CORE_actual_adversarial_sink','p':vertex_map.get(vertex,{}).get('p'),'n':vertex_map.get(vertex,{}).get('n'),
             'reason':'Electronics operating-voltage acceptance depends on selected device/mode; do not substitute the classic DSM floor'}]
        case['current_budget_checks']={'electronics_sum_A':electronics,'DSM_external_A':dsm,'CORE_output_external_budget_A':round(electronics+dsm,9),
                                       'ABC_external_sum_A':2 if supply=='BEC'and combo in ABC else 0,
                                       'USB_limiter_reference_min_A':.3512 if supply=='USB'else None,
                                       'note':'CORE includes its known bias/quiescent allowance once; separate upstream bias is outside this CORE total.'}
        if profile in ['auxiliary_added','coupled_adverse']:
            # Explicit added-current envelope at actual external device terminals.
            # These increments represent only demand beyond the already-counted
            # passive, device-table, CORE and converter-loss budgets.
            auxiliary_ports=[('U5.5','U5.8'),('U7.3','U7.1'),('U8.7','U8.12')]if supply=='BEC'else[
                            ('U10.4','U10.5'),('U7.6','U7.1'),('U8.2','U8.12')]
            for p,n in auxiliary_ports:
                ld.append(load('added_auxiliary_'+p,p,n,.002))
        case['auxiliary_current_scope']={
          'device_table_reference_A':{'U5':.000610 if supply=='BEC'else 0,'U7':.0000044 if supply=='BEC'else .0000045,
                                      'U8':.000400,'U10':0 if supply=='BEC'else .000140},
          'added_engineering_current_A':sum(x['current_A']for x in ld if x['name'].startswith('added_auxiliary_')),
          'inactive_U8_leakage_reserve_A':.000500,'BEC_priority_coupling_reserve_A':.000020 if supply=='BEC'else 0,
          'not_counted_again':['U6/U9 operating consumption is already within eta_total; additive converter IQ stays zero.',
                               'U11 and CORE-powered bias remain inside the aggregate 0.32/0.30 A electronics allowance.'],
          'limits':['U5 610 uA is a maximum at 12 V, open OUT, specified control settings; use at other inputs/load states is a modeled screen.',
                    'U7 4.4/4.5 uA are selected-input maximum rows through 105 C under their input-priority conditions.',
                    'U10 140 uA is the 6.5 V, open OUT, 20 kOhm ILIM row; actual voltage and resistor differ, so application is modeled.',
                    'U8 400 uA uses its open-output maximum row. The additional 500 uA covers the published wide-differential inactive-input leakage magnitude as a conservative selected-input demand.',
                    'The U8 leakage reserve omits detailed inactive-rail current direction and return distribution; it cannot establish backfeed behavior.',
                    'The 20 uA BEC priority reserve bounds the magnitude through 330 kOhm for declared PR1/ST voltages within 0 to 6 V, beyond the 28 kOhm divider already counted. CORE bias is not added again.',
                    'The added sensitivity is 2 mA at each of three external device input/return pairs, 6 mA total beyond explicit terms; it is an engineering comparison envelope, not a manufacturer guarantee.']}
        case['regulation_scope']={'initial_device_accuracy_terms_separate':True,
           'additional_output_error_fraction':pr.get('additional_output_error_fraction',0),
           'classification':'Additional 0/1/2% static setpoint error is an engineering sensitivity, not a guaranteed line/load/ripple bound.',
           'required_report':'Report initial-spec-only margins and each added-error result separately; report remaining allowable additional static output error before a receiver floor or headroom boundary.'}
        return case

    def make_feed_case(servo_name,feed_name,receiver_scope):
        case=make_case(receiver_scope,7.4,'BC','SELECT_AFTER_BASELINE')
        case['name']='same_BEC_'+servo_name+'_'+feed_name+'_'+receiver_scope
        case['scope']='same_BEC_illustrative'
        case['receiver_scope']=receiver_scope
        case['parameters'].update({'feed_profile':feed_name,'servo_profile':servo_name,
                                   'servo_subtotal_A':servo_definitions[servo_name]['subtotal_A']})
        case['sources']=[s for s in case['sources']if s['name']not in ['BEC_at_J6_pads','J6_return_reference']]
        case['sources'].append({'name':'one_external_BEC','p':'BEC_POS','n':'SOURCE_GND','voltage_V':7.4})
        for ref,pair in feed_examples[feed_name].items():
            case['resistors'] += [
             resistor(ref+'_positive_lead_contact','BEC_POS',ref+'.2',pair[0],classification='Illustrative, unmeasured'),
             resistor(ref+'_return_lead_contact',ref+'.1','SOURCE_GND',pair[1],classification='Illustrative, unmeasured')]
        for ref,current in servo_profiles[servo_name].items():
            case['loads'].append(load(ref+'_servo_illustration',ref+'.2',ref+'.1',current))
            case['probes'].append({'name':ref+'_servo_board_pad','p':ref+'.2','n':ref+'.1','minimum_V':6.,'maximum_V':8.4,
               'purpose':'PCB pad window only. Output servo harness/contact drop is unmeasured; this cannot establish voltage at the servo.'})
        case['current_budget_checks']['servo_subtotal_A']=servo_definitions[servo_name]['subtotal_A']
        case['current_budget_checks']['source_total_A']=None
        case['assumptions']=[a for a in case['assumptions']if not a.startswith('Ideal J6 pad-entry')]
        case['assumptions'] += [
          'One 7.4 V external BEC drives the actual J6/J8 positive and return pads through four independent finite resistances when both feeds are present.',
          'Feed/contact resistance values are illustrative sensitivity inputs, not measured factory bounds. No 50/50 positive or return sharing is imposed.',
          'The source voltage is an illustrative ideal external BEC terminal condition; actual regulation, source impedance and current limiting remain unbound.',
          'Servo currents are approximate plotted 7.4 V endpoints held constant for the DC comparison. Voltage dependence, startup, reversal and stall are unknown.',
          'The 15.8/15.9 A servo-only endpoint examples already exceed 10 A continuous BEC capability. The 8.9 A cases need newly solved electronics demand before comparison.',
          'No duration is assigned. The BEC 30 A peak number does not establish an allowable PCB, contact, harness or servo pulse envelope.',
          'J8 auxiliary feed requires unused SBUS, an empty signal cavity and verified polarity/fit.',
          'B=C=1 A is the selected representative peripheral loading; expand to A/B/C combinations if allocation or return rankings change.']
        case['required_reports']=['Actual four positive/return feed currents independently, including signs and sharing.',
           'Power loss in each feed/contact resistor and each copper layer/barrel; whole-circuit conservation.',
           'Newly solved total BEC current and its difference from 10 A continuous; report 30 A peak only as duration-unspecified context.',
           'Each actual servo pad voltage; separately flag absent output-harness terminal qualification.',
           'Actual DSM voltage under its declared receiver scope, ABC floors and U9 input/accuracy-window margins.']
        case['activation_blockers'] += ['Select or expand electronics allocation after baseline; servo cases can change the limiting return path',
           'No installed-system acceptance without measured harness/source bounds and bounded servo waveform/temperature evidence']
        return case
    return make_case, make_feed_case
