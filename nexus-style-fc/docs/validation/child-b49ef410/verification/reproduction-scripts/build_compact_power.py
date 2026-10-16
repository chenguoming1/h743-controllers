"""Build isolated compact 2oz two-layer copper-only prototype; no release claim.
Standard header and factory-compatible feed contact arrangement are unchanged.
The finished-copper design target is distinct from unresolved contact/harness ratings.
"""
from pathlib import Path
import sys,hashlib,json
import pcbnew
R=Path(__file__).resolve().parents[1];S=R/'source-baseline';C=R/'candidate-compact-two-layer-unfinished';P=C/'hardware/header-board/nexus-header-board.kicad_pcb';sys.path.insert(0,str(C/'tools'));import sexpr as sx
src=S/'hardware/header-board/nexus-header-board.kicad_pcb';assert hashlib.sha256(src.read_bytes()).hexdigest()=='bfec2a120fbda6c97c1f8a36dfff6a35337e13ab1c3af63abb987f529d761403'
a=sx.parse(src.read_text());a=[n for n in a if not(isinstance(n,list) and n[0]=='zone')];P.write_text(sx.dump(a)+'\n');b=pcbnew.LoadBoard(str(P));mm=pcbnew.FromMM
# Move existing VX right-edge branch corner0.0534mm outward to meet2oz0.16mmspacing.
for t in b.GetTracks():
 if t.GetClass()=='PCB_TRACK' and t.GetNetname()=='VX' and t.GetLayer()==pcbnew.F_Cu:
  for getter,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
   q=getter()
   if abs(pcbnew.ToMM(q.x)-119.9966)<.000001:setter(pcbnew.VECTOR2I(mm(120.05),q.y))
# Existing tracks retained as local branches; new filled sheets form the low resistance trunk.
for layer,name,priority,points in [(pcbnew.F_Cu,'VX',0,[(99,99),(123.4,99),(123.4,112),(99,112)]),(pcbnew.F_Cu,'GND',1,[(99,104.9),(123.4,104.9),(123.4,112),(99,112)]),(pcbnew.B_Cu,'GND',0,[(99,99),(123.4,99),(123.4,112),(99,112)])]:
 z=pcbnew.ZONE(b);z.SetLayer(layer);z.SetNet(b.FindNet(name));z.SetZoneName('POWER_'+name+'_'+b.GetLayerName(layer));z.SetAssignedPriority(priority);z.SetLocalClearance(mm(.16));z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL);z.SetThermalReliefGap(mm(.3));z.SetThermalReliefSpokeWidth(mm(.5));z.SetMinThickness(mm(.2));z.Outline().NewOutline()
 for x,y in points:z.Outline().Append(mm(x),mm(y))
 b.Add(z)
for fp in b.GetFootprints():
 for p in fp.Pads():
  if p.GetNetname() in ('VX','GND'):p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
ds=b.GetDesignSettings();ds.m_MinClearance=mm(.16);ds.m_TrackMinWidth=mm(.2);ds.m_CopperEdgeClearance=mm(.254);ds.m_HoleClearance=mm(.25);ds.m_HoleToHoleMin=mm(.25);ds.SetBoardThickness(mm(1.6));nc=ds.m_NetSettings.GetDefaultNetclass();nc.SetClearance(mm(.16));nc.SetTrackWidth(mm(.2));pcbnew.SaveBoard(str(P),b)
t=P.read_text();at=t.index('\t(setup\n')+len('\t(setup\n');stack='''\t\t(stackup
\t\t\t(layer "F.SilkS" (type "Top Silk Screen"))
\t\t\t(layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))
\t\t\t(layer "F.Cu" (type "copper") (thickness 0.07))
\t\t\t(layer "dielectric 1" (type "core") (thickness 1.44) (material "FR4") (epsilon_r 4.6) (loss_tangent 0.02))
\t\t\t(layer "B.Cu" (type "copper") (thickness 0.07))
\t\t\t(layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))
\t\t\t(layer "B.SilkS" (type "Bottom Silk Screen"))
\t\t\t(copper_finish "ENIG") (dielectric_constraints no)
\t\t)
''';P.write_text(t[:at]+stack+t[at:])
pro=C/'hardware/header-board/nexus-header-board.kicad_pro';j=json.loads(pro.read_text());j['board']['design_settings']['rules'].update(min_clearance=.16,min_track_width=.2,min_hole_clearance=.25,min_hole_to_hole=.25,min_through_hole_diameter=.2,min_via_annular_width=.15,min_via_diameter=.6,min_copper_edge_clearance=.254)
for nc in j.get('net_settings',{}).get('classes',[]):nc['clearance']=max(.16,nc.get('clearance',.16));nc['track_width']=max(.2,nc.get('track_width',.2))
pro.write_text(json.dumps(j,indent=2)+'\n')
(C/'hardware/header-board/nexus-header-board.kicad_dru').write_text('''(version 1)
# JLC 2-layer2oz published minimum0.16/0.16; conservative track0.20.
(rule "2oz copper width" (constraint track_width (min 0.20mm)))
(rule "2oz copper spacing" (constraint clearance (min 0.16mm)))
(rule "Child edge" (constraint edge_clearance (min 0.254mm)))
(rule "Hole copper" (constraint hole_clearance (min 0.25mm)))
(rule "Hole hole" (constraint hole_to_hole (min 0.25mm)))
(rule "Via annulus" (constraint annular_width (min 0.15mm)))
''')
(C/'verification').mkdir(exist_ok=True)
print(P)
