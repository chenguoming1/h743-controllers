import app.freerouting.Freerouting;import app.freerouting.settings.*;import app.freerouting.board.*;import app.freerouting.core.*;import app.freerouting.geometry.planar.*;import app.freerouting.interactive.*;import app.freerouting.designforms.specctra.DsnFile;import app.freerouting.management.analytics.FRAnalytics;import com.google.gson.*;import java.nio.file.*;import java.util.*;
/** Real engine insertion into a shared physical pad; isolated native geometry fixture. */
public final class PhysicalOwnerInsertionControl {
 static void check(boolean p,String s){if(!p)throw new AssertionError(s);}
 public static void main(String[] args)throws Exception{
  Path dir=Path.of(args[0]);JsonObject model=JsonParser.parseString(Files.readString(dir.resolve("model.json"))).getAsJsonObject();JsonArray cs=new JsonArray(),gs=new JsonArray();String uid=null;
  for(var e:model.getAsJsonArray("contacts"))if(e.getAsJsonObject().get("key").getAsString().equals("U14.4")){cs.add(e);uid=e.getAsJsonObject().get("uuid").getAsString();}
  check(cs.size()==2,"Two independent U14.4 contacts required");for(var e:model.getAsJsonArray("guards"))if(e.getAsJsonObject().get("label").getAsString().equals(uid+":copper"))gs.add(e);check(gs.size()==1,"Physical guard required");model.add("contacts",cs);model.add("guards",gs);
  Freerouting.globalSettings=new GlobalSettings();Freerouting.globalSettings.usageAndDiagnosticData.disableAnalytics=true;Freerouting.globalSettings.apiServerSettings.isEnabled=false;FRAnalytics.setEnabled(false);RoutingJob job=new RoutingJob();HeadlessBoardManager mgr=new HeadlessBoardManager(Locale.ENGLISH,job);check(mgr.loadFromSpecctraDsn(Files.newInputStream(dir.resolve("routing.dsn")),new BoardObserverAdaptor(),new ItemIdentificationNumberGenerator())==DsnFile.ReadResult.OK,"DSN");RoutingBoard b=mgr.get_routing_board();NativeGuardFactory.install(b,model);
  var contacts=new ArrayList<NativePadContactArea>();Set<Integer> sourceIds=new HashSet<>();for(Item i:b.get_items()){sourceIds.add(i.get_id_no());if(i instanceof NativePadContactArea c)contacts.add(c);}
  NativePadContactArea a=contacts.get(0),other=contacts.stream().filter(c->!c.shares_net(a)).findFirst().orElseThrow();var bb=a.bounding_box();int x=(bb.ll.x+bb.ur.x)/2,y=(bb.ll.y+bb.ur.y)/2;Point start=new IntPoint(x,y-3000),end=new IntPoint(x,y+3000);JsonArray tests=new JsonArray();
  for(int net:new int[]{a.get_net_no(0),other.get_net_no(0),b.rules.nets.get("SWCLK",1).net_number}){
   boolean expected=net==a.get_net_no(0)||net==other.get_net_no(0);Polyline line=new Polyline(new Point[]{start,end});Point ok=b.insert_forced_trace_polyline(line,6350,a.get_layer(),new int[]{net},1,0,0,0,Integer.MAX_VALUE,500,true,null);boolean actual=ok!=null&&ok.equals(end);check(actual==expected,"Shared-pad insertion/foreign guard mismatch for "+net);
   if(expected){check(!a.get_connected_set(a.get_net_no(0)).contains(other),"Logical aliases merged");}
   JsonObject t=new JsonObject();t.addProperty("logical_net",b.rules.nets.get(net).name);t.addProperty("expected_allowed",expected);t.addProperty("actual_allowed",actual);t.addProperty("passed",actual==expected);tests.add(t);
   for(Item i:new ArrayList<>(b.get_items()))if(!sourceIds.contains(i.get_id_no()))b.remove_item(i);
  }
  for(Item i:b.get_items())if(i instanceof NativePadContactArea||i instanceof NativeGuardFactory.Guard)check(i.copy(i.get_id_no()).get_id_no()==i.get_id_no(),"copy must preserve requested identity");
  RoutingBoard copy=b.deepCopy();for(Item i:copy.get_items())if(i instanceof NativePadContactArea c)for(Item q:c.get_normal_contacts())check(copy.get_items().contains(q),"Native peers must stay board-local after serialization");
  JsonObject out=new JsonObject();out.addProperty("passed",true);out.addProperty("model_sha256",LocalRouter.hash(dir.resolve("model.json")));out.addProperty("board_sha256",model.get("board_sha256").getAsString());out.addProperty("logical_aliases_separate",true);out.addProperty("fixed_copy_ids_preserved",true);out.addProperty("route_solver_used",false);out.add("cases",tests);Files.writeString(Path.of(args[1]),new GsonBuilder().setPrettyPrinting().create().toJson(out));System.out.println("PHYSICAL_OWNER_INSERTION_CONTROL PASS");
 }
}
