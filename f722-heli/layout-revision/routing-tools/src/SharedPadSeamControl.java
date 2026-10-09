import app.freerouting.Freerouting;import app.freerouting.settings.*;import app.freerouting.board.*;import app.freerouting.core.*;import app.freerouting.geometry.planar.*;import app.freerouting.interactive.*;import app.freerouting.designforms.specctra.DsnFile;import com.google.gson.*;import java.nio.file.*;import java.util.*;
/** Focused conservative-boundary control. No route search or native edit. */
public class SharedPadSeamControl {
 static void check(boolean p,String s){if(!p)throw new AssertionError(s);}
 public static void main(String[] args)throws Exception {
  Path dir=Path.of(args[0]);JsonObject model=JsonParser.parseString(Files.readString(dir.resolve("model.json"))).getAsJsonObject();JsonArray cs=new JsonArray();
  for(JsonElement e:model.getAsJsonArray("contacts"))if(e.getAsJsonObject().get("key").getAsString().equals("U14.4"))cs.add(e);
  model.add("contacts",cs);model.add("guards",new JsonArray());Freerouting.globalSettings=new GlobalSettings();Freerouting.globalSettings.usageAndDiagnosticData.disableAnalytics=true;Freerouting.globalSettings.apiServerSettings.isEnabled=false;
  RoutingJob job=new RoutingJob();HeadlessBoardManager mgr=new HeadlessBoardManager(Locale.ENGLISH,job);check(mgr.loadFromSpecctraDsn(Files.newInputStream(dir.resolve("routing.dsn")),new BoardObserverAdaptor(),new ItemIdentificationNumberGenerator())==DsnFile.ReadResult.OK,"DSN");RoutingBoard b=mgr.get_routing_board();NativeGuardFactory.install(b,model);
  var contacts=new ArrayList<NativePadContactArea>();for(Item i:b.get_items())if(i instanceof NativePadContactArea c)contacts.add(c);NativePadContactArea a=contacts.get(0),z=contacts.stream().filter(c->!c.shares_net(a)).findFirst().orElseThrow();var bb=a.bounding_box();int x=(bb.ll.x+bb.ur.x)/2,y=(bb.ll.y+bb.ur.y)/2;
  Trace t1=b.insert_trace_without_cleaning(new Polyline(new Point[]{new IntPoint(x,y-3000),new IntPoint(x,y+3000)}),a.get_layer(),6350,new int[]{a.get_net_no(0)},1,FixedState.NOT_FIXED);
  Trace t2=b.insert_trace_without_cleaning(new Polyline(new Point[]{new IntPoint(x,y-3000),new IntPoint(x,y+3000)}),z.get_layer(),6350,new int[]{z.get_net_no(0)},1,FixedState.NOT_FIXED);
  for(int i=0;i<t1.tile_shape_count();i++)for(var c:t1.get_tile_shape(i).corner_approx_arr())check(a.get_area().contains(c),"Inside-overlap fixture must stay inside actual conservative pad window");
  boolean insideRejected=t1.is_obstacle(t2)&&t2.is_obstacle(t1);check(insideRejected,"Current engine is intentionally conservative inside shared pads");check(!t1.get_connected_set(a.get_net_no(0)).contains(t2),"Logical aliases must not merge");b.remove_item(t1);b.remove_item(t2);
  Trace o1=b.insert_trace_without_cleaning(new Polyline(new Point[]{new IntPoint(x,y),new IntPoint(x+100000,y)}),a.get_layer(),6350,new int[]{a.get_net_no(0)},1,FixedState.NOT_FIXED);
  Trace o2=b.insert_trace_without_cleaning(new Polyline(new Point[]{new IntPoint(x,y),new IntPoint(x+100000,y)}),z.get_layer(),6350,new int[]{z.get_net_no(0)},1,FixedState.NOT_FIXED);check(o1.is_obstacle(o2)&&o2.is_obstacle(o1),"Outside-pad overlap must remain forbidden");check(!o1.get_connected_set(a.get_net_no(0)).contains(o2),"Outside overlap must not alias branches");
  JsonObject out=new JsonObject();out.addProperty("actual_pad","U14.4");out.addProperty("inside_only_overlap","conservative_rejection_known_limitation");out.addProperty("outside_pad_overlap_rejected",true);out.addProperty("logical_aliases_separate",true);out.addProperty("physical_impossibility_claim",false);out.addProperty("route_solver_used",false);System.out.println(new GsonBuilder().setPrettyPrinting().create().toJson(out));
 }
}
