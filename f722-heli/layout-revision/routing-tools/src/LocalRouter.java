import app.freerouting.Freerouting;
import app.freerouting.settings.*;
import app.freerouting.board.*;
import app.freerouting.core.*;
import app.freerouting.geometry.planar.*;
import app.freerouting.interactive.*;
import app.freerouting.autoroute.*;
import app.freerouting.designforms.specctra.DsnFile;
import app.freerouting.management.analytics.FRAnalytics;
import com.google.gson.*;
import java.io.*;
import java.nio.file.*;
import java.security.*;
import java.util.*;
public final class LocalRouter {
 static final Gson G=new GsonBuilder().setPrettyPrinting().create();
 static String hash(Path p)throws Exception{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(p)));}
 static JsonArray coords(FloatPoint[] ps){JsonArray a=new JsonArray();for(var p:ps){JsonArray c=new JsonArray();c.add(p.x/1e5);c.add(-p.y/1e5);a.add(c);}return a;}
 static JsonArray nets(RoutingBoard b,Item i){JsonArray a=new JsonArray();for(int k=0;k<i.net_count();k++)a.add(b.rules.nets.get(i.get_net_no(k)).name);return a;}
 static JsonObject snapshot(RoutingBoard b){
  JsonObject r=new JsonObject();JsonArray areas=new JsonArray(),routes=new JsonArray(),partitions=new JsonArray();r.add("areas",areas);r.add("routes",routes);r.add("contact_partitions",partitions);
  for(Item i:b.get_items()){
   JsonObject o=new JsonObject();o.add("nets",nets(b,i));o.addProperty("fixed",i.get_fixed_state().toString());
   if(i instanceof ObstacleArea a){o.addProperty("label",a.name);o.addProperty("layer",b.layer_structure.arr[a.get_layer()].name);o.addProperty("kind",i instanceof NativePadContactArea?"contact":i instanceof ViaObstacleArea?"via_guard":"foreign_guard");o.addProperty("clearance_class",i.clearance_class_no());o.add("outer",coords(a.get_area().get_border().corner_approx_arr()));areas.add(o);
    if(i instanceof NativePadContactArea c){o.addProperty("uuid",c.nativeId);o.addProperty("plated",c.plated);o.addProperty("native_group",c.nativeGroup);}
   }else if(i instanceof PolylineTrace t){o.addProperty("kind","track");o.addProperty("layer",b.layer_structure.arr[t.get_layer()].name);o.addProperty("width",2*t.get_half_width()/1e5);o.add("points",coords(t.polyline().corner_approx_arr()));routes.add(o);
   }else if(i instanceof Via v){o.addProperty("kind","via");o.add("xy",coords(new FloatPoint[]{v.get_center().to_float()}).get(0));o.addProperty("diameter",v.get_padstack().get_shape(0).bounding_box().width()/1e5);o.addProperty("drill",.20);routes.add(o);}
  }
  Set<Integer> handled=new HashSet<>();
  for(Item i:b.get_items())if(i instanceof NativePadContactArea c&&!handled.contains(c.get_id_no())){JsonObject part=new JsonObject();part.addProperty("net",b.rules.nets.get(c.get_net_no(0)).name);JsonArray ids=new JsonArray();Set<String> unique=new TreeSet<>();for(Item x:c.get_connected_set(c.get_net_no(0)))if(x instanceof NativePadContactArea q){handled.add(q.get_id_no());unique.add(q.nativeId+":"+b.layer_structure.arr[q.get_layer()].name);}for(String id:unique)ids.add(id);part.add("contacts",ids);partitions.add(part);}
  return r;
 }
 public static void main(String[] args)throws Exception{
  if(args.length!=3)throw new IllegalArgumentException("LocalRouter MODEL_DIR OUT_PREFIX PASSES");Path dir=Path.of(args[0]),prefix=Path.of(args[1]);int passes=Integer.parseInt(args[2]);JsonObject model=JsonParser.parseString(Files.readString(dir.resolve("model.json"))).getAsJsonObject();
  if(!hash(dir.resolve("routing.dsn")).equals(model.get("dsn_sha256").getAsString()))throw new IllegalStateException("DSN hash mismatch");
  if(!hash(Path.of(model.get("physical_board").getAsString())).equals(model.get("board_sha256").getAsString()))throw new IllegalStateException("Native board drift");
  if(!hash(Path.of(model.get("physical_native").getAsString())).equals(model.get("native_sha256").getAsString()))throw new IllegalStateException("Native export drift");
  if(passes>0&&!model.get("support_ready").getAsBoolean())throw new IllegalStateException("Fixed support gate is not ready");
  Freerouting.globalSettings=new GlobalSettings();Freerouting.globalSettings.usageAndDiagnosticData.disableAnalytics=true;Freerouting.globalSettings.apiServerSettings.isEnabled=false;Freerouting.globalSettings.guiSettings.isEnabled=false;FRAnalytics.setEnabled(false);
  RoutingJob job=new RoutingJob();HeadlessBoardManager mgr=new HeadlessBoardManager(Locale.ENGLISH,job);
  if(mgr.loadFromSpecctraDsn(Files.newInputStream(dir.resolve("routing.dsn")),new BoardObserverAdaptor(),new ItemIdentificationNumberGenerator())!=DsnFile.ReadResult.OK)throw new IllegalStateException("DSN rejected");RoutingBoard b=mgr.get_routing_board();
  double scale=b.communication.coordinate_transform.dsn_to_board(1);if(scale!=1e5)throw new IllegalStateException("Unexpected scale "+scale);
  for(var entry:model.getAsJsonObject("adapter_sources").entrySet())if(!hash(Path.of(entry.getKey())).equals(entry.getValue().getAsString()))throw new IllegalStateException("Adapter source changed "+entry.getKey());
  NativeGuardFactory.install(b,model);
  Set<String> allowed=new HashSet<>();for(JsonElement e:model.getAsJsonArray("ordinary_nets"))allowed.add(e.getAsString());JsonObject aliases=model.getAsJsonObject("aliases");var ignored=b.rules.append_net_class("fixed_domain");ignored.is_ignored_by_autorouter=true;
  for(int i=1;i<=b.rules.nets.max_net_no();i++){var n=b.rules.nets.get(i);if(n==null)continue;if(!allowed.contains(aliases.get(n.name).getAsString()))n.set_class(ignored);else{n.get_class().set_trace_half_width(6350);for(int l=0;l<6;l++)n.get_class().set_active_routing_layer(l,l!=1&&l!=4);}}
  job.board=b;job.routerSettings=new RouterSettings(b);job.routerSettings.maxThreads=1;job.routerSettings.set_start_pass_no(1);job.routerSettings.set_stop_pass_no(passes);job.routerSettings.set_automatic_neckdown(false);for(int l=0;l<6;l++)job.routerSettings.set_layer_active(l,l!=1&&l!=4);job.thread=new StoppableThread(){protected void thread_action(){}};
  JsonObject before=snapshot(b);Files.writeString(Path.of(prefix+".before.json"),G.toJson(before));
  if(passes>0){new BatchAutorouter(job).runBatchLoop();b=job.board;mgr.replaceRoutingBoard(b);}
  JsonObject report=snapshot(b);Set<String> fixedBefore=new TreeSet<>(),fixedAfter=new TreeSet<>();for(var e:before.getAsJsonArray("routes"))if(e.getAsJsonObject().get("fixed").getAsString().equals("SYSTEM_FIXED"))fixedBefore.add(G.toJson(e));for(var e:report.getAsJsonArray("routes"))if(e.getAsJsonObject().get("fixed").getAsString().equals("SYSTEM_FIXED"))fixedAfter.add(G.toJson(e));if(!fixedBefore.equals(fixedAfter))throw new IllegalStateException("Fixed engine copper changed");report.addProperty("board_sha256",model.get("board_sha256").getAsString());report.addProperty("model_sha256",hash(dir.resolve("model.json")));report.addProperty("passes_requested",passes);report.addProperty("analytics_disabled",true);report.addProperty("api_disabled",true);Files.writeString(Path.of(prefix+".after.json"),G.toJson(report));
  for(Item i:new ArrayList<>(b.get_items()))if(i instanceof NativePadContactArea)b.remove_item(i);
  if(!mgr.saveAsSpecctraSessionSes(Files.newOutputStream(Path.of(prefix+".ses")),"f722-local"))throw new IllegalStateException("SES failed");System.out.println("LOCAL_ROUTER_COMPLETE "+prefix);
 }
}
