package app.freerouting.board;
import app.freerouting.geometry.planar.*;
import java.util.*;
/** Native pad-only planning contact; recomputes contact from current round trace capsules. */
public final class NativePadContactArea extends ConductionArea {
 private List<NativePadContactArea> nativePeers=List.of();
 void setNativePeers(List<NativePadContactArea> peers){for(var c:peers)if(c.board!=board||!c.nativeGroup.equals(nativeGroup)||!c.shares_net(this))throw new IllegalArgumentException("Invalid native peer index");nativePeers=peers;}
 public final String nativeId,label,nativeGroup; public final boolean groupMulti; public final boolean plated; public final int[] physicalOwners;
 NativePadContactArea(Area area,int layer,int net,int[] owners,String uuid,String key,boolean p,String ng,boolean gm,BasicBoard b){this(area,layer,net,owners,uuid,key,p,ng,gm,0,b);}
 NativePadContactArea(Area area,int layer,int net,int[] owners,String uuid,String key,boolean p,String ng,boolean gm,int id,BasicBoard b){
  super(area,layer,app.freerouting.geometry.planar.Vector.ZERO,0,false,new int[]{net},1,id,0,key,false,FixedState.SYSTEM_FIXED,b);
  nativeId=uuid;label=key;plated=p;nativeGroup=ng;groupMulti=gm;physicalOwners=owners;
 }
 @Override public Item copy(int id){var c=new NativePadContactArea(get_relative_area(),get_layer(),get_net_no(0),physicalOwners,nativeId,label,plated,nativeGroup,groupMulti,id,board);c.nativePeers=nativePeers;return c;}
 private boolean owns(int net){for(int n:physicalOwners)if(n==net)return true;return false;}
 @Override public boolean is_obstacle(int net){return !owns(net);}
 @Override public boolean is_trace_obstacle(int net){return !owns(net);}
 @Override public boolean is_drillable(int net){return false;}
 @Override public boolean is_obstacle(Item other){if(other instanceof Trace||other instanceof Via){for(int i=0;i<other.net_count();i++)if(owns(other.get_net_no(i)))return false;return true;}return false;}
 private static double pointSegment(FloatPoint p,FloatPoint a,FloatPoint b){double dx=b.x-a.x,dy=b.y-a.y;double dd=dx*dx+dy*dy;double t=dd==0?0:Math.max(0,Math.min(1,((p.x-a.x)*dx+(p.y-a.y)*dy)/dd));return Math.hypot(p.x-a.x-t*dx,p.y-a.y-t*dy);}
 private static double orient(FloatPoint a,FloatPoint b,FloatPoint c){return (b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x);}
 private static double segDistance(FloatPoint a,FloatPoint b,FloatPoint c,FloatPoint d){double x=orient(a,b,c),y=orient(a,b,d),u=orient(c,d,a),v=orient(c,d,b);if(x*y<0&&u*v<0)return 0;return Math.min(Math.min(pointSegment(a,c,d),pointSegment(b,c,d)),Math.min(pointSegment(c,a,b),pointSegment(d,a,b)));}
 public boolean touches(Trace trace){
  if(!shares_net(trace)||!shares_layer(trace))return false;
  FloatPoint[] c=trace instanceof PolylineTrace p?p.polyline().corner_approx_arr():new FloatPoint[]{trace.first_corner().to_float(),trace.last_corner().to_float()};
  for(int j=0;j<tile_shape_count();j++){
   TileShape shape=get_tile_shape(j);FloatPoint[] edges=shape.corner_approx_arr();
   for(int i=1;i<c.length;i++){
    if(shape.contains(c[i-1])||shape.contains(c[i]))return true;
    for(int k=0;k<edges.length;k++)if(segDistance(c[i-1],c[i],edges[k],edges[(k+1)%edges.length])<=trace.get_half_width())return true;
   }
  }return false;
 }
 @Override public Set<Item> get_normal_contacts(){
  Set<Item> result=new TreeSet<>();
  for(int i=0;i<tile_shape_count();i++)for(SearchTreeObject ob:board.overlapping_objects(get_tile_shape(i),get_layer())){
   if(!(ob instanceof Item item)||item==this||!shares_net(item))continue;
   if(item instanceof Trace t&&touches(t))result.add(t);
   else if(item instanceof DrillItem d&&get_area().contains(d.get_center()))result.add(d);
   else if(item instanceof NativePadContactArea c&&c.nativeId.equals(nativeId))result.add(c);
  }
  if(groupMulti)for(NativePadContactArea saved:nativePeers){
   if(saved.get_id_no()==get_id_no())continue;
   Item current=saved.board==board&&saved.is_on_the_board()?saved:board.get_item(saved.get_id_no());
   if(current instanceof NativePadContactArea c&&c.board==board&&c.is_on_the_board()&&c.nativeGroup.equals(nativeGroup)&&c.shares_net(this))result.add(c);
  }
  return result;
 }

 public static Set<Item> contactsAt(Trace trace,Point point){
  Set<Item> r=new TreeSet<>();FloatPoint p=point.to_float();
  for(Item i:contacts(trace))if(i instanceof NativePadContactArea c)for(int k=0;k<c.tile_shape_count();k++)if(c.get_tile_shape(k).contains(p)||c.get_tile_shape(k).border_distance(p)<=trace.get_half_width()){r.add(c);break;}
  return r;
 }
 public static Set<Item> contacts(Trace trace){
  Set<Item> r=new TreeSet<>();
  for(int j=0;j<trace.tile_shape_count();j++)for(SearchTreeObject ob:trace.board.overlapping_objects(trace.get_tile_shape(j),trace.get_layer()))if(ob instanceof NativePadContactArea c&&c.touches(trace))r.add(c);
  return r;
 }
}
