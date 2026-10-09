package app.freerouting.autoroute;

import app.freerouting.Freerouting;
import app.freerouting.board.*;
import app.freerouting.core.RoutingJob;
import app.freerouting.datastructures.ShapeTree;
import app.freerouting.datastructures.TimeLimit;
import app.freerouting.designforms.specctra.DsnFile;
import app.freerouting.geometry.planar.*;
import app.freerouting.interactive.HeadlessBoardManager;
import app.freerouting.management.analytics.FRAnalytics;
import app.freerouting.settings.*;
import com.google.gson.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;

/** Deterministic timeout at first search expansion. No trace/via insertion or native board is used. */
public final class FailedSearchStateControl {
  static final Gson G = new GsonBuilder().setPrettyPrinting().create();
  static void require(boolean value, String message) { if (!value) throw new AssertionError(message); }
  static String hash(byte[] bytes) throws Exception { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }

  static final class ExpireAtSearch extends TimeLimit {
    boolean triggered;
    ExpireAtSearch() { super(2000); }
    @Override public boolean limit_exceeded() {
      for (StackTraceElement frame : Thread.currentThread().getStackTrace()) {
        if (frame.getClassName().equals(MazeSearchAlgo.class.getName()) && frame.getMethodName().equals("occupy_next_element")) {
          triggered = true; return true;
        }
      }
      return super.limit_exceeded();
    }
  }

  static final class ExpireDuringInit extends TimeLimit {
    AutorouteEngine observed; boolean triggered;
    ExpireDuringInit() { super(2000); }
    @Override public boolean limit_exceeded() {
      if(observed!=null && !rooms(observed).isEmpty()){triggered=true;return true;}
      return super.limit_exceeded();
    }
  }

  static final class Fixture {
    RoutingBoard board; NativePadContactArea a, b; AutorouteControl ctrl; int net;
    Fixture(Path path) throws Exception {
      JsonObject model = JsonParser.parseString(Files.readString(path.resolve("model.json"))).getAsJsonObject();
      require(model.get("synthetic_only").getAsBoolean(), "Synthetic fixture only");
      require(hash(Files.readAllBytes(path.resolve("routing.dsn"))).equals(model.get("dsn_sha256").getAsString()), "DSN identity");
      HeadlessBoardManager manager = new HeadlessBoardManager(Locale.ENGLISH, new RoutingJob());
      try (var stream = Files.newInputStream(path.resolve("routing.dsn"))) {
        require(manager.loadFromSpecctraDsn(stream, new BoardObserverAdaptor(), new ItemIdentificationNumberGenerator()) == DsnFile.ReadResult.OK, "Tiny fixture load");
      }
      board = manager.get_routing_board(); NativeGuardFactory.install(board, model);
      for (Item item : board.get_items()) if (item instanceof NativePadContactArea c) {
        if (c.label.equals("SYNTHETIC_A")) a=c; else if(c.label.equals("SYNTHETIC_B")) b=c;
      }
      require(a!=null && b!=null, "Both synthetic contacts"); net=a.get_net_no(0);
      RouterSettings settings=new RouterSettings(board); settings.set_vias_allowed(false); settings.set_automatic_neckdown(false);
      settings.set_layer_active(0,true); settings.set_layer_active(1,false);
      ctrl=new AutorouteControl(board,net,settings); ctrl.ripup_allowed=false;
    }
    AutorouteEngine engine(boolean slow, TimeLimit limit) { return board.init_autoroute(net,ctrl.trace_clearance_class_no,null,limit,false,slow); }
    Set<Item> starts(boolean reverse) { Set<Item> s=new TreeSet<>();s.add(reverse?b:a);return s; }
    Set<Item> targets(boolean reverse) { Set<Item> s=new TreeSet<>();s.add(reverse?a:b);return s; }
  }

  static Set<CompleteFreeSpaceExpansionRoom> rooms(AutorouteEngine engine) {
    Collection<ShapeTree.TreeEntry> entries=new ArrayList<>();
    engine.autoroute_search_tree.overlapping_tree_entries(engine.board.get_bounding_box(),-1,entries);
    Set<CompleteFreeSpaceExpansionRoom> result=Collections.newSetFromMap(new IdentityHashMap<>());
    for(var e:entries)if(e.object instanceof CompleteFreeSpaceExpansionRoom room)result.add(room);
    return result;
  }

  static JsonObject roomState(AutorouteEngine engine) {
    JsonObject r=new JsonObject();r.addProperty("tree_identity",System.identityHashCode(engine.autoroute_search_tree));
    r.addProperty("engine_identity",System.identityHashCode(engine));r.addProperty("tree_class",engine.autoroute_search_tree.getClass().getName());
    Set<CompleteFreeSpaceExpansionRoom> rooms=rooms(engine);r.addProperty("complete_rooms_in_tree",rooms.size());
    JsonArray ids=new JsonArray();for(var room:rooms)ids.add(System.identityHashCode(room));r.add("room_identities",ids);return r;
  }

  static JsonObject physicalState(Fixture f) throws Exception {
    JsonArray rows=new JsonArray();
    for(Item item:f.board.get_items()){
      require(!(item instanceof Trace) && !(item instanceof Via),"No route insertion is permitted in this control");
      JsonObject row=new JsonObject();row.addProperty("id",item.get_id_no());row.addProperty("identity",System.identityHashCode(item));row.addProperty("class",item.getClass().getName());
      JsonArray nets=new JsonArray();for(int i=0;i<item.net_count();i++)nets.add(item.get_net_no(i));row.add("nets",nets);row.addProperty("fixed",item.get_fixed_state().name());
      JsonArray geometry=new JsonArray();for(int i=0;i<item.tile_shape_count();i++){
        JsonArray tile=new JsonArray();for(FloatPoint p:item.get_tile_shape(i).corner_approx_arr()){JsonArray point=new JsonArray();point.add(p.x);point.add(p.y);tile.add(point);}geometry.add(tile);
      }
      row.add("geometry",geometry);
      if(item instanceof NativePadContactArea c){row.addProperty("label",c.label);row.addProperty("group",c.nativeGroup);JsonArray contacts=new JsonArray();for(Item n:c.get_normal_contacts())contacts.add(n.get_id_no());row.add("normal_contact_ids",contacts);}
      rows.add(row);
    }
    JsonObject r=new JsonObject();r.add("items",rows);r.addProperty("sha256",hash(G.toJson(rows).getBytes(StandardCharsets.UTF_8)));return r;
  }

  static JsonObject contactIdentity(Fixture f, boolean reverse) {
    JsonObject r=new JsonObject();Item start=reverse?f.b:f.a,target=reverse?f.a:f.b;
    r.addProperty("start_id",start.get_id_no());r.addProperty("start_identity",System.identityHashCode(start));r.addProperty("target_id",target.get_id_no());r.addProperty("target_identity",System.identityHashCode(target));return r;
  }

  static JsonObject exercise(Path path, boolean slow, boolean expectLeak) throws Exception {
    Fixture f=new Fixture(path);JsonObject physicalBefore=physicalState(f),result=new JsonObject();
    result.addProperty("slow_tree",slow);result.add("physical_before",physicalBefore);result.add("forward_contact_identities",contactIdentity(f,false));result.add("reverse_contact_identities",contactIdentity(f,true));
    ExpireAtSearch limit=new ExpireAtSearch();AutorouteEngine old=f.engine(slow,limit);result.add("before_timeout",roomState(old));
    long started=System.nanoTime();AutorouteAttemptResult attempt=old.autoroute_connection(f.starts(false),f.targets(false),f.ctrl,new TreeSet<>());
    result.addProperty("timeout_attempt_seconds",(System.nanoTime()-started)/1e9);result.addProperty("timeout_triggered_at_first_expansion",limit.triggered);
    result.addProperty("attempt_result",attempt.state.name());result.addProperty("attempt_details",attempt.details);result.add("after_timeout",roomState(old));
    result.add("failure_stage_seconds",G.toJsonTree(old.stageSeconds));
    require(limit.triggered && attempt.state==AutorouteAttemptState.FAILED && attempt.details.contains("no connection was found"),"Control must expire after successful initialization, before insertion");
    require(rooms(old).isEmpty()!=expectLeak,"Search failure room cleanup differs from selected expectation");
    require(physicalBefore.equals(physicalState(f)),"Timeout changed physical/contact state");
    AutorouteEngine replacement=f.engine(slow,new TimeLimit(2000));
    require(replacement!=old && replacement.autoroute_search_tree==old.autoroute_search_tree,"retain=false must replace engine while reusing cached tree");
    result.add("after_engine_replacement",roomState(replacement));
    boolean reusedReverse=MazeSearchAlgo.get_instance(f.starts(true),f.targets(true),replacement,f.ctrl)!=null;
    require(reusedReverse!=expectLeak,"Reverse initialization differs from selected expectation");
    result.addProperty("reverse_initializes_with_reused_tree",reusedReverse);result.add("after_reused_reverse_init",roomState(replacement));
    f.board.finish_autoroute();result.add("after_finish_on_replacement_engine",roomState(replacement));
    old.clear();result.add("after_explicit_old_engine_clear",roomState(old));
    require(rooms(old).isEmpty(),"Explicit old-engine cleanup must remove orphan rooms");
    AutorouteEngine cleaned=f.engine(slow,new TimeLimit(2000));
    boolean cleanedReverse=MazeSearchAlgo.get_instance(f.starts(true),f.targets(true),cleaned,f.ctrl)!=null;
    result.addProperty("reverse_initializes_after_old_engine_clear",cleanedReverse);result.add("after_cleaned_reverse_init",roomState(cleaned));f.board.finish_autoroute();
    result.add("after_final_cleanup",roomState(cleaned));result.add("physical_after",physicalState(f));
    require(physicalBefore.equals(physicalState(f)),"Repeated initialization/cleanup changed physical geometry, contact identity, or contacts");
    Fixture fresh=new Fixture(path);JsonObject freshPhysical=physicalState(fresh);AutorouteEngine freshEngine=fresh.engine(slow,new TimeLimit(2000));
    boolean freshReverse=MazeSearchAlgo.get_instance(fresh.starts(true),fresh.targets(true),freshEngine,fresh.ctrl)!=null;
    result.addProperty("reverse_initializes_on_fresh_board",freshReverse);result.add("fresh_reverse_tree",roomState(freshEngine));fresh.board.finish_autoroute();
    require(freshPhysical.equals(physicalState(fresh)),"Fresh reverse initialization changed physical state");
    Fixture finishFirst=new Fixture(path);JsonObject finishPhysical=physicalState(finishFirst);ExpireAtSearch limit2=new ExpireAtSearch();AutorouteEngine beforeFinish=finishFirst.engine(slow,limit2);
    beforeFinish.autoroute_connection(finishFirst.starts(false),finishFirst.targets(false),finishFirst.ctrl,new TreeSet<>());
    finishFirst.board.finish_autoroute();result.add("finish_before_replacement_tree",roomState(beforeFinish));
    AutorouteEngine afterFinish=finishFirst.engine(slow,new TimeLimit(2000));boolean finishedReverse=MazeSearchAlgo.get_instance(finishFirst.starts(true),finishFirst.targets(true),afterFinish,finishFirst.ctrl)!=null;
    result.addProperty("reverse_initializes_when_finish_precedes_replacement",finishedReverse);finishFirst.board.finish_autoroute();
    require(finishPhysical.equals(physicalState(finishFirst)),"Pre-replacement finish changed physical state");
    result.addProperty("physical_geometry_and_contact_identity_unchanged",true);
    result.addProperty("stale_room_failure_reproduced",!reusedReverse && cleanedReverse && freshReverse && finishedReverse);
    require(result.get("stale_room_failure_reproduced").getAsBoolean()==expectLeak,"Stale-room outcome differs from selected expectation");
    require(cleanedReverse && freshReverse && finishedReverse,"Clean/fresh initialization controls must succeed");
    result.add("maze_initialization_timeout",exerciseInitTimeout(path,slow,expectLeak));
    return result;
  }

  static JsonObject exerciseInitTimeout(Path path,boolean slow,boolean expectLeak)throws Exception{
    Fixture f=new Fixture(path);JsonObject before=physicalState(f),r=new JsonObject();ExpireDuringInit limit=new ExpireDuringInit();
    AutorouteEngine old=f.engine(slow,limit);limit.observed=old;r.add("before",roomState(old));
    AutorouteAttemptResult attempt=old.autoroute_connection(f.starts(false),f.targets(false),f.ctrl,new TreeSet<>());
    r.addProperty("timeout_triggered_after_room_creation",limit.triggered);r.addProperty("result",attempt.state.name());r.addProperty("details",attempt.details);r.add("after_failure",roomState(old));r.add("failure_stage_seconds",G.toJsonTree(old.stageSeconds));
    require(limit.triggered&&attempt.state==AutorouteAttemptState.FAILED&&attempt.details.contains("maze search algorithm could not be created"),"Initialization-timeout control must hit null-maze early return");
    require(rooms(old).isEmpty()!=expectLeak,"Null-maze cleanup differs from selected expectation");
    AutorouteEngine next=f.engine(slow,new TimeLimit(2000));boolean initialized=MazeSearchAlgo.get_instance(f.starts(true),f.targets(true),next,f.ctrl)!=null;
    r.addProperty("reverse_initializes_after_replacement",initialized);r.add("after_reverse_init",roomState(next));require(initialized!=expectLeak,"Null-maze reverse result differs from selected expectation");
    f.board.finish_autoroute();old.clear();r.add("after_cleanup",roomState(old));require(rooms(old).isEmpty(),"Control must leave no temporary rooms");
    require(before.equals(physicalState(f)),"Initialization failure changed physical/contact state");r.addProperty("physical_geometry_and_contact_identity_unchanged",true);return r;
  }

  public static void main(String[] args) throws Exception {
    require(args.length==2,"FailedSearchStateControl FIXTURE_DIR unrepaired|repaired");Path path=Path.of(args[0]);
    require(args[1].equals("unrepaired")||args[1].equals("repaired"),"Expected mode must be unrepaired or repaired");boolean expectLeak=args[1].equals("unrepaired");
    Freerouting.globalSettings=new GlobalSettings();Freerouting.globalSettings.usageAndDiagnosticData.disableAnalytics=true;
    Freerouting.globalSettings.apiServerSettings.isEnabled=false;Freerouting.globalSettings.guiSettings.isEnabled=false;FRAnalytics.setEnabled(false);
    JsonObject report=new JsonObject();report.addProperty("fixture_sha256",hash(Files.readAllBytes(path.resolve("model.json"))));
    report.addProperty("fixture_dsn_sha256",hash(Files.readAllBytes(path.resolve("routing.dsn"))));
    report.addProperty("timeout_strategy","Synthetic TimeLimit expires at first MazeSearchAlgo.occupy_next_element call, after initialization has created rooms");
    report.addProperty("native_board_used",false);report.addProperty("trace_or_via_insertion_used",false);
    report.addProperty("expected_mode",args[1]);
    JsonArray cases=new JsonArray();cases.add(exercise(path,true,expectLeak));cases.add(exercise(path,false,expectLeak));report.add("cases",cases);
    JsonObject sources=new JsonObject();for(String p:new String[]{"src/app/freerouting/autoroute/AutorouteEngine.java","src/app/freerouting/autoroute/MazeSearchAlgo.java","tests/failed-search-state/FailedSearchStateControl.java","vendor/freerouting-2.1.0.jar"})sources.addProperty(p,hash(Files.readAllBytes(Path.of(p))));report.add("source_sha256",sources);
    try(var bytes=AutorouteEngine.class.getResourceAsStream("/app/freerouting/autoroute/AutorouteEngine.class")){report.addProperty("loaded_engine_class_sha256",hash(bytes.readAllBytes()));}
    report.addProperty("completed",true);System.out.println(G.toJson(report));
  }
}
