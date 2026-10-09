package app.freerouting.board;
import app.freerouting.geometry.planar.*;
import com.google.gson.*;
import java.math.BigInteger;
import java.util.*;
public final class NativeGuardFactory {
 public static Point point(JsonArray p){return new IntPoint((int)Math.round(p.get(0).getAsDouble()*1e5),-(int)Math.round(p.get(1).getAsDouble()*1e5));}
 public static PolygonShape polygon(JsonArray a){Point[] p=new Point[a.size()];for(int i=0;i<p.length;i++)p[i]=point(a.get(i).getAsJsonArray());return new PolygonShape(p);}
 public static int[] owners(RoutingBoard b,JsonArray a){int[] n=new int[a.size()];for(int i=0;i<n.length;i++){var net=b.rules.nets.get(a.get(i).getAsString(),1);if(net==null)throw new IllegalArgumentException("Missing native net "+a.get(i));n[i]=net.net_number;}return n;}
 public static void install(RoutingBoard b,JsonObject model){
  for(JsonElement e:model.getAsJsonArray("guards")){
   JsonObject g=e.getAsJsonObject();int layer=b.layer_structure.get_no(g.get("layer").getAsString());String name=g.get("label").getAsString();boolean via=g.get("kind").getAsString().equals("via");int cl=g.get("clearance").getAsDouble()==0?0:1;int[] nets=owners(b,g.getAsJsonArray("owners"));
   for(JsonElement p:g.getAsJsonArray("convex")){
    PolygonShape shape=polygon(p.getAsJsonArray());
    if(via)b.insert_item(new ViaObstacleArea(shape,layer,app.freerouting.geometry.planar.Vector.ZERO,0,false,cl,0,0,name,FixedState.SYSTEM_FIXED,b));
    else b.insert_item(new Guard(shape,layer,nets,cl,name,b));
   }
  }
  Map<String,List<NativePadContactArea>> nativePeers=new HashMap<>();
  for(JsonElement e:model.getAsJsonArray("contacts")){
   JsonObject c=e.getAsJsonObject();int layer=b.layer_structure.get_no(c.get("layer").getAsString());int net=b.rules.nets.get(c.get("net").getAsString(),1).net_number;int[] owners=owners(b,c.getAsJsonArray("owners"));
   for(JsonElement p:c.getAsJsonArray("convex")){var item=new NativePadContactArea(polygon(p.getAsJsonArray()),layer,net,owners,c.get("uuid").getAsString(),c.get("key").getAsString(),c.get("plated").getAsBoolean(),c.get("native_group").getAsString(),c.get("native_group_multi").getAsBoolean(),b);b.insert_item(item);nativePeers.computeIfAbsent(net+":"+item.nativeGroup,k->new ArrayList<>()).add(item);}
  }
  for(var peers:nativePeers.values()){List<NativePadContactArea> immutablePeers=Collections.unmodifiableList(new ArrayList<>(peers));for(var c:peers)c.setNativePeers(immutablePeers);}
 }
 public static final class Guard extends ObstacleArea {
  Guard(Area a,int l,int[] n,int cl,String name,BasicBoard b){this(a,l,n,cl,name,0,b);}
  Guard(Area a,int l,int[] n,int cl,String name,int id,BasicBoard b){super(a,l,app.freerouting.geometry.planar.Vector.ZERO,0,false,n,cl,id,0,name,FixedState.SYSTEM_FIXED,b);}
  @Override public boolean is_drillable(int n){return contains_net(n);}
  @Override public Item copy(int id){return new Guard(get_relative_area(),get_layer(),net_no_arr,clearance_class_no(),name,id,board);}
 }
}
