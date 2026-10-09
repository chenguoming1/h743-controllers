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
 static String fixedGeometryHash(RoutingBoard b)throws Exception{
  MessageDigest digest=MessageDigest.getInstance("SHA-256");
  for(Item i:b.get_items())if(i.get_fixed_state()==FixedState.SYSTEM_FIXED){
   JsonObject o=new JsonObject();o.addProperty("class",i.getClass().getName());o.addProperty("id",i.get_id_no());o.add("nets",nets(b,i));
   if(i instanceof ObstacleArea a){o.addProperty("layer",a.get_layer());o.addProperty("label",a.name);o.add("outer",coords(a.get_area().get_border().corner_approx_arr()));if(i instanceof NativePadContactArea c){o.addProperty("uuid",c.nativeId);o.addProperty("native_group",c.nativeGroup);}}
   else if(i instanceof PolylineTrace t){o.addProperty("layer",t.get_layer());o.addProperty("width",t.get_half_width());o.add("points",coords(t.polyline().corner_approx_arr()));}
   else if(i instanceof Via v){o.add("xy",coords(new FloatPoint[]{v.get_center().to_float()}));o.addProperty("padstack",v.get_padstack().name);}
   digest.update(G.toJson(o).getBytes(java.nio.charset.StandardCharsets.UTF_8));
  }
  return HexFormat.of().formatHex(digest.digest());
 }
 static JsonObject snapshot(RoutingBoard b){return snapshot(b,true);}
 static JsonObject snapshot(RoutingBoard b,boolean includeAreas){return snapshot(b,includeAreas,true);}
 static JsonObject snapshot(RoutingBoard b,boolean includeAreas,boolean includePartitions){
  JsonObject r=new JsonObject();JsonArray areas=new JsonArray(),routes=new JsonArray(),partitions=new JsonArray();r.add("areas",areas);r.add("routes",routes);r.add("contact_partitions",partitions);
  for(Item i:b.get_items()){
   JsonObject o=new JsonObject();o.add("nets",nets(b,i));o.addProperty("fixed",i.get_fixed_state().toString());
   if(i instanceof ObstacleArea a){if(!includeAreas)continue;o.addProperty("label",a.name);o.addProperty("layer",b.layer_structure.arr[a.get_layer()].name);o.addProperty("kind",i instanceof NativePadContactArea?"contact":i instanceof ViaObstacleArea?"via_guard":"foreign_guard");o.addProperty("clearance_class",i.clearance_class_no());o.add("outer",coords(a.get_area().get_border().corner_approx_arr()));areas.add(o);
    if(i instanceof NativePadContactArea c){o.addProperty("uuid",c.nativeId);o.addProperty("plated",c.plated);o.addProperty("native_group",c.nativeGroup);}
   }else if(i instanceof PolylineTrace t){o.addProperty("kind","track");o.addProperty("layer",b.layer_structure.arr[t.get_layer()].name);o.addProperty("width",2*t.get_half_width()/1e5);o.add("points",coords(t.polyline().corner_approx_arr()));routes.add(o);
   }else if(i instanceof Via v){o.addProperty("kind","via");o.add("xy",coords(new FloatPoint[]{v.get_center().to_float()}).get(0));o.addProperty("diameter",v.get_padstack().get_shape(0).bounding_box().width()/1e5);o.addProperty("drill",.20);routes.add(o);}
  }
  Set<Integer> handled=new HashSet<>();
  if(includePartitions)for(Item i:b.get_items())if(i instanceof NativePadContactArea c&&!handled.contains(c.get_id_no())){JsonObject part=new JsonObject();part.addProperty("net",b.rules.nets.get(c.get_net_no(0)).name);JsonArray ids=new JsonArray();Set<String> unique=new TreeSet<>();for(Item x:c.get_connected_set(c.get_net_no(0)))if(x instanceof NativePadContactArea q){handled.add(q.get_id_no());unique.add(q.nativeId+":"+b.layer_structure.arr[q.get_layer()].name);}for(String id:unique)ids.add(id);part.add("contacts",ids);partitions.add(part);}
  return r;
 }
 static void publishProgress(Path prefix,JsonObject progress)throws Exception{Files.writeString(Path.of(prefix+".progress.next"),G.toJson(progress));Files.move(Path.of(prefix+".progress.next"),Path.of(prefix+".progress.json"),StandardCopyOption.REPLACE_EXISTING,StandardCopyOption.ATOMIC_MOVE);System.out.println("ROUTE_PROGRESS "+G.toJson(progress).replace("\n"," "));System.out.flush();}
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
  // Native shapes have been copied into the board. Release unused JSON geometry.
  for(String key:new String[]{"guards","contacts","fixed_objects","fixed_zones"})model.remove(key);
  Set<String> allowed=new HashSet<>();for(JsonElement e:model.getAsJsonArray("ordinary_nets"))allowed.add(e.getAsString());Set<String> only=new HashSet<>();for(String n:System.getenv().getOrDefault("F722_ONLY_NETS","").split(","))if(!n.isBlank())only.add(n.trim());if(!allowed.containsAll(only))throw new IllegalArgumentException("Unknown ordinary net filter "+only);if(!only.isEmpty())allowed.retainAll(only);JsonObject aliases=model.getAsJsonObject("aliases");var ignored=b.rules.append_net_class("fixed_domain");ignored.is_ignored_by_autorouter=true;
  for(int i=1;i<=b.rules.nets.max_net_no();i++){var n=b.rules.nets.get(i);if(n==null)continue;if(!allowed.contains(aliases.get(n.name).getAsString()))n.set_class(ignored);else{n.get_class().set_trace_half_width(6350);for(int l=0;l<6;l++)n.get_class().set_active_routing_layer(l,l!=1&&l!=4);}}
  JsonObject runConfig=new JsonObject();runConfig.add("physical_net_filter",G.toJsonTree(new TreeSet<>(only)));runConfig.addProperty("force_slow_tree","1".equals(System.getenv("F722_FORCE_SLOW_TREE")));runConfig.addProperty("insertion_diagnostics","1".equals(System.getenv("F722_INSERT_DIAGNOSTICS")));runConfig.addProperty("connection_budget_ms",Long.parseLong(System.getenv().getOrDefault("F722_CONNECTION_BUDGET_MS","10000")));System.out.println("LOCAL_ROUTER_CONFIG "+G.toJson(runConfig).replace("\n"," "));
  job.board=b;job.routerSettings=new RouterSettings(b);job.routerSettings.maxThreads=1;job.routerSettings.set_start_pass_no(1);job.routerSettings.set_stop_pass_no(passes);job.routerSettings.set_automatic_neckdown(false);for(int l=0;l<6;l++)job.routerSettings.set_layer_active(l,l!=1&&l!=4);job.thread=new StoppableThread(){protected void thread_action(){}};
  final String sourceFixedGeometry=fixedGeometryHash(b);JsonObject before=snapshot(b);Files.writeString(Path.of(prefix+".before.json"),G.toJson(before));
  if(passes>0){
   final String modelHash=hash(dir.resolve("model.json")),sourceHash=model.get("board_sha256").getAsString();
   final Path checkpoints=Path.of(prefix+".checkpoints");Files.createDirectories(checkpoints);
   final Set<String> immutable=new TreeSet<>();for(var e:before.getAsJsonArray("routes"))if(e.getAsJsonObject().get("fixed").getAsString().equals("SYSTEM_FIXED"))immutable.add(G.toJson(e));
   final int[] sequence={0},geometrySequence={0};final long started=System.nanoTime();final String fixedSourceFingerprint=sourceFixedGeometry;
   long budget=Long.parseLong(System.getenv().getOrDefault("F722_CONNECTION_BUDGET_MS","10000"));if(budget<=0)throw new IllegalArgumentException("Positive connection budget required");System.setProperty("f722.connection_budget_ms",Long.toString(budget));
   int stopAfter=Integer.parseInt(System.getenv().getOrDefault("F722_CHECKPOINT_AFTER_ROUTED","0"));
   BatchAutorouter router=new BatchAutorouter(job);
   final String[] lastRoutes={null};final JsonObject[] lastProgress={null};final int[] snapshotRouted={0};final long[] snapshotAt={0};final int checkpointEvery=Integer.parseInt(System.getenv().getOrDefault("F722_CHECKPOINT_EVERY_ROUTED","3"));if(checkpointEvery<1)throw new IllegalArgumentException("Positive checkpoint frequency required");
   router.addBoardUpdatedEventListener(event->{
    try{
     long callbackStart=System.nanoTime();RoutingBoard current=event.getBoard();var counters=event.getRouterCounters();JsonObject state=snapshot(current,false,false);String routeKey=G.toJson(state.get("routes"));boolean changed=!routeKey.equals(lastRoutes[0]);boolean boundedPassComplete=counters.passCount!=null&&counters.passCount>=passes&&counters.queuedToBeRoutedCount!=null&&counters.queuedToBeRoutedCount==0;boolean willStop=boundedPassComplete||Files.exists(Path.of(prefix+".stop"))||(stopAfter>0&&counters.routedCount!=null&&counters.routedCount>=stopAfter);boolean checkpointDue=lastProgress[0]==null||willStop||(counters.routedCount!=null&&counters.routedCount-snapshotRouted[0]>=checkpointEvery)||(System.nanoTime()-snapshotAt[0]>=60000000000L);
     if(!changed||!checkpointDue){if(!fixedSourceFingerprint.equals(fixedGeometryHash(current)))throw new IllegalStateException("Fixed geometry changed before checkpoint reuse");JsonObject progress=lastProgress[0].deepCopy();progress.addProperty("geometry_snapshot_reused",true);progress.addProperty("pending_route_geometry",changed);progress.add("snapshot_route_counters",lastProgress[0].get("route_counters"));progress.addProperty("sequence",++sequence[0]);progress.addProperty("elapsed_seconds",(System.nanoTime()-started)/1e9);progress.addProperty("checkpoint_seconds",(System.nanoTime()-callbackStart)/1e9);progress.add("attempt",G.toJsonTree(router.lastAttempt));progress.add("route_counters",G.toJsonTree(counters));publishProgress(prefix,progress);if(willStop||Files.exists(Path.of(prefix+".stop")))job.thread.request_stop_auto_router();return;}
     state=snapshot(current,false);if(!fixedSourceFingerprint.equals(fixedGeometryHash(current)))throw new IllegalStateException("Fixed geometry changed during routing");
     Set<String> actualFixed=new TreeSet<>();for(var e:state.getAsJsonArray("routes"))if(e.getAsJsonObject().get("fixed").getAsString().equals("SYSTEM_FIXED"))actualFixed.add(G.toJson(e));if(!immutable.equals(actualFixed))throw new IllegalStateException("Fixed copper changed before checkpoint");
     int serial=++sequence[0];String stem=String.format(Locale.ROOT,"latest-%d",(++geometrySequence[0])%2);Path checkpoint=checkpoints.resolve(stem);
     state.addProperty("board_sha256",sourceHash);state.addProperty("model_sha256",modelHash);state.addProperty("passes_requested",passes);state.add("run_configuration",runConfig);state.addProperty("checkpoint_sequence",serial);state.addProperty("connection_budget_ms",budget);state.addProperty("elapsed_seconds",(System.nanoTime()-started)/1e9);state.add("route_counters",G.toJsonTree(counters));
     Path reportPath=Path.of(checkpoint+".after.json"),sessionPath=Path.of(checkpoint+".ses");Files.writeString(Path.of(reportPath+".next"),G.toJson(state));mgr.replaceRoutingBoard(current);try(var out=Files.newOutputStream(Path.of(sessionPath+".next"))){if(!mgr.saveAsSpecctraSessionSes(out,"f722-local"))throw new IllegalStateException("Checkpoint SES failed");}Files.move(Path.of(reportPath+".next"),reportPath,StandardCopyOption.REPLACE_EXISTING,StandardCopyOption.ATOMIC_MOVE);Files.move(Path.of(sessionPath+".next"),sessionPath,StandardCopyOption.REPLACE_EXISTING,StandardCopyOption.ATOMIC_MOVE);
     JsonObject afterSave=snapshot(current,false);if(!G.toJson(state.get("routes")).equals(G.toJson(afterSave.get("routes")))||!G.toJson(state.get("contact_partitions")).equals(G.toJson(afterSave.get("contact_partitions")))||!fixedSourceFingerprint.equals(fixedGeometryHash(current)))throw new IllegalStateException("SES checkpoint changed live geometry or contact partitions");
     lastRoutes[0]=routeKey;snapshotAt[0]=System.nanoTime();snapshotRouted[0]=counters.routedCount==null?0:counters.routedCount;JsonObject progress=new JsonObject();progress.addProperty("geometry_snapshot_reused",false);progress.addProperty("pending_route_geometry",false);progress.addProperty("checkpoint_every_routed",checkpointEvery);progress.addProperty("checkpoint_seconds",(System.nanoTime()-callbackStart)/1e9);progress.add("attempt",G.toJsonTree(router.lastAttempt));progress.addProperty("checkpoint",checkpoint.toString());progress.addProperty("sequence",serial);progress.addProperty("board_sha256",sourceHash);progress.addProperty("model_sha256",modelHash);progress.addProperty("report_sha256",hash(reportPath));progress.addProperty("session_sha256",hash(sessionPath));progress.addProperty("fixed_geometry_sha256",fixedSourceFingerprint);progress.addProperty("ses_save_read_only_verified",true);progress.addProperty("elapsed_seconds",(System.nanoTime()-started)/1e9);progress.add("route_counters",G.toJsonTree(counters));lastProgress[0]=progress;publishProgress(prefix,progress);
     if(willStop||Files.exists(Path.of(prefix+".stop")))job.thread.request_stop_auto_router();
    }catch(Exception e){job.thread.request_stop_auto_router();throw new RuntimeException("Recoverable checkpoint failed",e);}
   });
   router.runBatchLoop();b=job.board;mgr.replaceRoutingBoard(b);
  }
  if(!sourceFixedGeometry.equals(fixedGeometryHash(b)))throw new IllegalStateException("Fixed geometry changed before final export");
  JsonObject report=snapshot(b);Set<String> fixedBefore=new TreeSet<>(),fixedAfter=new TreeSet<>();for(var e:before.getAsJsonArray("routes"))if(e.getAsJsonObject().get("fixed").getAsString().equals("SYSTEM_FIXED"))fixedBefore.add(G.toJson(e));for(var e:report.getAsJsonArray("routes"))if(e.getAsJsonObject().get("fixed").getAsString().equals("SYSTEM_FIXED"))fixedAfter.add(G.toJson(e));if(!fixedBefore.equals(fixedAfter))throw new IllegalStateException("Fixed engine copper changed");report.addProperty("board_sha256",model.get("board_sha256").getAsString());report.addProperty("model_sha256",hash(dir.resolve("model.json")));report.addProperty("passes_requested",passes);report.add("run_configuration",runConfig);report.addProperty("analytics_disabled",true);report.addProperty("api_disabled",true);Files.writeString(Path.of(prefix+".after.json"),G.toJson(report));
  for(Item i:new ArrayList<>(b.get_items()))if(i instanceof NativePadContactArea)b.remove_item(i);
  if(!mgr.saveAsSpecctraSessionSes(Files.newOutputStream(Path.of(prefix+".ses")),"f722-local"))throw new IllegalStateException("SES failed");System.out.println("LOCAL_ROUTER_COMPLETE "+prefix);
 }
}
