from pathlib import Path
import sys,json
P=Path(__file__).parent;sys.path.insert(0,str(P/'work/nexus-style-fc/tools'))
import pcbnew
from pcbutil import Board
import make_footprints as mf,design
lib=P/'work/nexus-style-fc/hardware/library/NexusFC.pretty'
b=Board(100,100,4)
expected={'C27':((101.870,124.320),180,{'1':(102.740,124.320),'2':(101.000,124.320)}),'C31':((105.820,126.300),0,{'1':(104.950,126.300),'2':(106.690,126.300)}),'D5':((102.280,126.180),180,{'1':(103.450,126.180),'2':(101.110,126.180)})};records={}
for ref in expected:
 _,x,y,rot,side=design.MAIN_INPUT_CAP_PLACEMENT[ref]
 name='C_0805_2012Metric_Samsung_CL21_MinLand' if ref.startswith('C') else 'SOD-323_L1.8-W1.3-LS2.5-RD'
 f=pcbnew.FootprintLoad(str(lib),name);assert f
 b.board.Add(f);b.put(f,x,y+mf.DESIGN_SHIFT,rot,'B');print(ref,'tuple rotation',rot,'native rotation',f.GetOrientationDegrees(),'pos',pcbnew.ToMM(f.GetPosition()),'pads',[(p.GetNumber(),pcbnew.ToMM(p.GetPosition())) for p in f.Pads()])

 # Native transformation proof from actual shared Board.put, without board regeneration.
 pos=tuple(pcbnew.ToMM(f.GetPosition()));pads={p.GetNumber():tuple(pcbnew.ToMM(p.GetPosition())) for p in f.Pads()};actual=(pos,f.GetOrientationDegrees()%360,pads);assert actual==expected[ref],(ref,actual,expected[ref]);records[ref]={'source_place':design.MAIN_INPUT_CAP_PLACEMENT[ref],'native_position':pos,'native_rotation':actual[1],'native_pads':pads,'layer':'B.Cu'}
(P/'native-placement-proof.json').write_text(json.dumps({'result':'PASS','origin':[100,100],'design_shift':mf.DESIGN_SHIFT,'records':records,'no_board_written':True},indent=2)+'\n')
