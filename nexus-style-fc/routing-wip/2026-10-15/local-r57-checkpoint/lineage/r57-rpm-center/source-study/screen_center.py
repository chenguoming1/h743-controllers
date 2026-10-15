from pathlib import Path
import pcbnew as k,json,hashlib,math
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');O=R/'rpm-contact-study';P=R/'routing-continuation/r56-offpad-ground/hardware/nexus-style-fc.kicad_pcb';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();H='64eb0addce9b1ef9c14f29714224834a09e44b96ecd66a967d2f667f9530900f';assert sha(P)==H;b=k.LoadBoard(str(P));uid=lambda x:x.m_Uuid.AsString();xy=lambda p:[p.x/1e6,p.y/1e6];vec=lambda p:k.VECTOR2I(round(p[0]*1e6),round(p[1]*1e6));ts={uid(t):t for t in b.GetTracks()};ps={uid(p):p for f in b.GetFootprints() for p in f.Pads()};u='842641a6-6c0e-4e61-8e31-f9beee7b5389';v='8d4e76ee-941f-4cc6-8549-2fd09506e82a';t=ts[u];via=ts[v];l=t.GetLayer();conn=b.GetConnectivity();ls=list(b.GetEnabledLayers().CuStack())
def hit(a,b,d=0):
 z=k.SHAPE.Collide(a,b,d);return z[0] if isinstance(z,tuple) else bool(z)
ports=[]
for x in list(conn.GetConnectedTracks(t))+list(conn.GetConnectedPads(t)):
 w=uid(x)
 if w==u:continue
 q=ts.get(w) or ps.get(w)
 if q.IsOnLayer(l) and hit(t.GetEffectiveShape(l),q.GetEffectiveShape(l)):ports.append(w)
pts=[xy(via.GetPosition()),xy(t.GetEnd())];q=k.PCB_TRACK(b);q.SetStart(vec(pts[0]));q.SetEnd(vec(pts[1]));q.SetWidth(t.GetWidth());q.SetLayer(l);q.SetNetCode(t.GetNetCode());bad=[]
for w,x in {**ts,**ps}.items():
 if x.GetNetCode()!=q.GetNetCode() and x.IsOnLayer(l) and hit(q.GetEffectiveShape(l),x.GetEffectiveShape(l),127002):bad.append({'uuid':w,'net':x.GetNetname(),'kind':type(x).__name__})
retained=[]
for w in ports:
 x=ts.get(w) or ps.get(w);retained.append({'uuid':w,'kind':type(x).__name__,'new_physical_contact':hit(q.GetEffectiveShape(l),x.GetEffectiveShape(l)),'net':x.GetNetname()})
out={'source_path':str(P),'source_board_sha256':H,'removed_uuid':u,'net':t.GetNetname(),'layer':b.GetLayerName(l),'width_mm':t.GetWidth()/1e6,'old_points':[xy(t.GetStart()),xy(t.GetEnd())],'new_points':pts,'via_uuid':v,'expected_external_ports':sorted(set(ports)),'ports_after_centering':retained,'new_obstructions_at_0_127002_mm':bad,'stopping_bound':'One complete original segment replacement with its via endpoint centered; no via, power, pad or other donor change. Reject any missing full-width port, new/worse native pair or changed main reference/shield topology.'};(O/'center-screen.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2));assert sha(P)==H
