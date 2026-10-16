import sys
sys.path.insert(0,'/workspace/shared/nexus-main-placement-fix/scripts');from router import *
p='/workspace/shared/nexus-main-placement-fix/stage36/hardware/nexus-style-fc.kicad_pcb';b=k.LoadBoard(p)
t=next(t for t in b.GetTracks() if t.m_Uuid.AsString()=='b3bcbf59-1c89-5cf2-b4dc-6f5eb5687b30');assert xy(t.GetEnd())==(111.77,119.4)
a=xy(t.GetStart());z=(111.775,119.6);rt=Router(b,k.B_Cu,'GND',t.GetWidth()/1e6);assert rt.free(a,z);t.SetEnd(vec(z));k.SaveBoard(p,b)
