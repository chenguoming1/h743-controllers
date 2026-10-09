import app.freerouting.Freerouting;import app.freerouting.settings.*;import app.freerouting.board.*;import app.freerouting.core.*;import app.freerouting.geometry.planar.*;import app.freerouting.interactive.*;import app.freerouting.designforms.specctra.DsnFile;import com.google.gson.*;import java.nio.file.*;import java.util.*;
public class NativeContactRegression {
 static void check(boolean p,String s){if(!p)throw new AssertionError(s);}
 public static void main(String[] args)throws Exception {
  Path dir=Path.of(args[0]);JsonObject model=JsonParser.parseString(Files.readString(dir.resolve("model.json"))).getAsJsonObject();JsonArray cs=new JsonArray();
  for(JsonElement e:model.getAsJsonArray("contacts"))if(e.getAsJsonObject().get("key").getAsString().equals("U14.4"))cs.add(e);
  check(cs.size()==2,"Two independent U14 actual-IO branch contacts required");model.add("contacts",cs);model.add("guards",new JsonArray());
  Freerouting.globalSettings=new GlobalSettings();Freerouting.globalSettings.usageAndDiagnosticData.disableAnalytics=true;Freerouting.globalSettings.apiServerSettings.isEnabled=false;
  RoutingJob job=new RoutingJob();HeadlessBoardManager mgr=new HeadlessBoardManager(Locale.ENGLISH,job);check(mgr.loadFromSpecctraDsn(Files.newInputStream(dir.resolve("routing.dsn")),new BoardObserverAdaptor(),new ItemIdentificationNumberGenerator())==DsnFile.ReadResult.OK,"DSN load");RoutingBoard b=mgr.get_routing_board();NativeGuardFactory.install(b,model);
  var contacts=new ArrayList<NativePadContactArea>();for(Item i:b.get_items())if(i instanceof NativePadContactArea c)contacts.add(c);
  NativePadContactArea a=contacts.get(0),other=contacts.stream().filter(c->!c.shares_net(a)).findFirst().orElseThrow();var bb=a.bounding_box();int x=bb.ll.x-3000,y=(bb.ll.y+bb.ur.y)/2;
  Trace t=b.insert_trace_without_cleaning(new Polyline(new Point[]{new IntPoint(x,y-1000),new IntPoint(x,y+1000)}),a.get_layer(),6350,new int[]{a.get_net_no(0)},1,FixedState.NOT_FIXED);
  check(a.touches(t),"Actual capsule reaches pad although centerline/endpoints lie outside");check(a.get_normal_contacts().contains(t),"Contact sees live capsule");check(t.get_normal_contacts().contains(a),"Trace sees live capsule symmetrically");check(!other.get_normal_contacts().contains(t),"Separate logical alias must not become connected");
  b.remove_item(t);check(!a.get_normal_contacts().contains(t),"Removed trace must not leave stale virtual contact");
  Trace far=b.insert_trace_without_cleaning(new Polyline(new Point[]{new IntPoint(x-20000,y-1000),new IntPoint(x-20000,y+1000)}),a.get_layer(),6350,new int[]{a.get_net_no(0)},1,FixedState.NOT_FIXED);check(!a.touches(far),"Distant capsule must not contact");
  System.out.println("PASS: off-centre capsule, symmetric live contact, logical isolation, removal invalidation, distant rejection; no routing solver used.");
 }
}
