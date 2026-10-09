package app.freerouting.board;

import app.freerouting.Freerouting;
import app.freerouting.core.RoutingJob;
import app.freerouting.designforms.specctra.DsnFile;
import app.freerouting.geometry.planar.*;
import app.freerouting.interactive.HeadlessBoardManager;
import app.freerouting.management.analytics.FRAnalytics;
import app.freerouting.settings.GlobalSettings;
import com.google.gson.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;

/** Tiny in-memory insertion probes against one source-bound native guard. No maze or PCB export. */
public final class NativeInsertionGapControl {
  static final Gson G = new GsonBuilder().setPrettyPrinting().create();
  static void require(boolean value, String message) { if (!value) throw new AssertionError(message); }
  static String hash(byte[] bytes) throws Exception { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
  static JsonArray xy(FloatPoint p) { JsonArray a = new JsonArray(); a.add(p.x / 1e5); a.add(-p.y / 1e5); return a; }
  static JsonObject shape(TileShape s) {
    JsonObject r = new JsonObject(); r.addProperty("class", s.getClass().getSimpleName());
    IntBox b = s.bounding_box(); JsonArray bb = new JsonArray();
    bb.add(b.ll.x); bb.add(b.ll.y); bb.add(b.ur.x); bb.add(b.ur.y); r.add("bounds_engine", bb);
    JsonArray corners = new JsonArray(); for (FloatPoint p : s.corner_approx_arr()) corners.add(xy(p));
    r.add("corners_mm", corners); return r;
  }
  static JsonArray points(Polyline p) { JsonArray a = new JsonArray(); for (FloatPoint f : p.corner_approx_arr()) a.add(xy(f)); return a; }
  static JsonObject obstacle(Item item) {
    JsonObject r = new JsonObject(); if (item == null) { r.addProperty("present", false); return r; }
    r.addProperty("present", true); r.addProperty("class", item.getClass().getName());
    r.addProperty("id", item.get_id_no()); if (item instanceof ObstacleArea area) r.addProperty("label", area.name);
    return r;
  }
  static RoutingBoard load(Path dir, JsonObject fixture) throws Exception {
    HeadlessBoardManager manager = new HeadlessBoardManager(Locale.ENGLISH, new RoutingJob());
    try (var stream = Files.newInputStream(dir.resolve("routing.dsn"))) {
      require(manager.loadFromSpecctraDsn(stream, new BoardObserverAdaptor(), new ItemIdentificationNumberGenerator()) == DsnFile.ReadResult.OK, "Tiny DSN load");
    }
    RoutingBoard b = manager.get_routing_board(); NativeGuardFactory.install(b, fixture); return b;
  }
  static JsonArray guards(RoutingBoard board) {
    JsonArray result = new JsonArray();
    for (Item item : board.get_items()) if (item instanceof NativeGuardFactory.Guard guard) {
      JsonObject r = obstacle(guard); r.addProperty("layer", guard.get_layer());
      r.addProperty("clearance_class", guard.clearance_class_no()); r.addProperty("fixed", guard.get_fixed_state().name());
      JsonArray nets = new JsonArray(); for (int i=0;i<guard.net_count();i++) nets.add(guard.get_net_no(i)); r.add("nets", nets);
      JsonArray tiles = new JsonArray(); for(int i=0;i<guard.tile_shape_count();i++) tiles.add(shape(guard.get_tile_shape(i))); r.add("tiles",tiles); result.add(r);
    }
    return result;
  }
  public static void main(String[] args) throws Exception {
    require(args.length == 1, "NativeInsertionGapControl FIXTURE_DIR");
    Path dir = Path.of(args[0]); byte[] fixtureBytes = Files.readAllBytes(dir.resolve("model.json"));
    JsonObject fixture = JsonParser.parseString(new String(fixtureBytes, StandardCharsets.UTF_8)).getAsJsonObject();
    require(fixture.get("fixture_only").getAsBoolean() && fixture.getAsJsonArray("guards").size()==1 && fixture.getAsJsonArray("contacts").isEmpty(), "Only the tiny exact one-guard fixture is allowed");
    require(hash(Files.readAllBytes(dir.resolve("routing.dsn"))).equals(fixture.get("dsn_sha256").getAsString()), "DSN identity");
    Freerouting.globalSettings = new GlobalSettings(); Freerouting.globalSettings.usageAndDiagnosticData.disableAnalytics=true;
    Freerouting.globalSettings.apiServerSettings.isEnabled=false; Freerouting.globalSettings.guiSettings.isEnabled=false; FRAnalytics.setEnabled(false);
    JsonObject report = new JsonObject(); report.addProperty("fixture_sha256",hash(fixtureBytes));
    report.add("source_model_sha256",fixture.get("source_model_sha256")); report.add("source_board_sha256",fixture.get("source_board_sha256"));
    report.addProperty("maze_search_used",false); report.addProperty("insertion_scope","isolated in-memory fixture only; fresh board for each shift; no native file mutation");
    JsonArray cases = new JsonArray(); report.add("cases",cases); Integer minimumFullInsertionShift = null;
    for (JsonElement value : fixture.getAsJsonArray("shifts_engine_units")) {
      int shift=value.getAsInt(); RoutingBoard b=load(dir,fixture); ShapeSearchTree tree=b.search_tree_manager.get_default_tree();
      int layer=b.layer_structure.get_no(fixture.get("layer").getAsString());
      int[] net={b.rules.nets.get(fixture.get("trace_net").getAsString(),1).net_number}; int cl=1;
      int width=fixture.get("trace_half_width").getAsInt();
      require(b.rules.clearance_matrix.get_value(cl,cl,layer,false)==12700,"Nominal 0.127 mm clearance must remain unchanged");
      int compensation=tree.clearance_compensation_value(cl,layer), compensated=width+compensation;
      IntPoint p0=(IntPoint)NativeGuardFactory.point(fixture.getAsJsonArray("segment_mm").get(0).getAsJsonArray());
      IntPoint p1=(IntPoint)NativeGuardFactory.point(fixture.getAsJsonArray("segment_mm").get(1).getAsJsonArray());
      Polyline segment=new Polyline(new IntPoint(p0.x+shift,p0.y),new IntPoint(p1.x+shift,p1.y));
      JsonArray before=guards(b); JsonObject r=new JsonObject(); r.addProperty("outward_shift_engine_units",shift);r.addProperty("outward_shift_mm",shift/1e5);r.add("segment_mm",points(segment));
      r.addProperty("native_edge_gap_mm",(p0.x+shift)/1e5-fixture.get("native_guard_max_x_mm").getAsDouble()-width/1e5);
      if(shift==0){
        JsonObject config=new JsonObject(); config.addProperty("default_tree",tree.toString());
        config.addProperty("default_tree_compensation_enabled",tree.is_clearance_compensation_used());
        config.addProperty("trace_compensation_engine_units",compensation);config.addProperty("compensated_half_width_engine_units",compensated);
        config.addProperty("matrix_nominal_engine_units",b.rules.clearance_matrix.get_value(1,1,layer,false));
        config.addProperty("matrix_with_safety_engine_units",b.rules.clearance_matrix.get_value(1,1,layer,true));
        config.addProperty("angle_restriction",b.rules.get_trace_angle_restriction().toString());report.add("configuration",config);
        report.add("guards",before);JsonArray trees=new JsonArray();ShapeSearchTree fast=new ShapeSearchTree45Degree(b,1);
        for(Item item:b.get_items())if(item instanceof NativeGuardFactory.Guard g){JsonObject row=new JsonObject();row.addProperty("id",g.get_id_no());JsonArray defaults=new JsonArray(),mazes=new JsonArray();for(int i=0;i<g.tree_shape_count(tree);i++)defaults.add(shape(g.get_tree_shape(tree,i)));for(int i=0;i<g.tree_shape_count(fast);i++)mazes.add(shape(g.get_tree_shape(fast,i)));row.add("default_sections",defaults);row.add("fast_compensated_sections",mazes);trees.add(row);}report.add("guard_tree_geometry",trees);
      }
      ShoveTraceAlgo shove=new ShoveTraceAlgo(b);b.set_shove_failing_obstacle(null);b.set_shove_failing_layer(-1);
      Polyline sprung=shove.spring_over_obstacles(segment,compensated,layer,net,cl,null);
      r.addProperty("spring_over_result",sprung==null?"null":sprung==segment?"unchanged":"modified");r.add("spring_over_failure",obstacle(b.get_shove_failing_obstacle()));if(sprung!=null)r.add("spring_over_points_mm",points(sprung));
      TileShape[] shapes=segment.offset_shapes(compensated,0,segment.arr.length-1);JsonArray checks=new JsonArray();
      for(int i=0;i<shapes.length;i++){
        TileShape s=shapes[i];b.set_shove_failing_obstacle(null);b.set_shove_failing_layer(-1);
        boolean ok=shove.check(s,new CalcFromSide(segment,i+1,s),null,layer,net,cl,20,5,5,null);
        JsonObject check=new JsonObject();check.addProperty("allowed",ok);check.add("failure",obstacle(b.get_shove_failing_obstacle()));
        check.add("trace_shape",shape(s));JsonArray overlaps=new JsonArray();for(Item ob:tree.overlapping_items_with_clearance(s,layer,new int[0],cl))overlaps.add(obstacle(ob));check.add("overlap_items",overlaps);
        if(shift==0){int h=b.rules.clearance_matrix.get_value(cl,cl,layer,true)/2;check.addProperty("per_shape_extra_half_clearance",h);check.add("expanded_trace_check_shape",shape((TileShape)s.enlarge(h)));}
        checks.add(check);
      }
      r.add("shove_checks_on_original_segment",checks);
      Point achieved=b.insert_forced_trace_polyline(segment,width,layer,net,cl,20,5,5,Integer.MAX_VALUE,500,true,null);
      boolean full=achieved!=null&&achieved.equals(segment.last_corner());r.addProperty("full_insertion",full);if(achieved!=null)r.add("achieved_mm",xy(achieved.to_float()));r.add("insertion_failure",obstacle(b.get_shove_failing_obstacle()));
      r.addProperty("guard_geometry_unchanged",before.equals(guards(b)));require(before.equals(guards(b)),"Insertion changed guard geometry");
      JsonArray tracks=new JsonArray();for(Item item:b.get_items())if(item instanceof PolylineTrace t)tracks.add(points(t.polyline()));r.add("inserted_trace_points_mm",tracks);
      if(full&&minimumFullInsertionShift==null)minimumFullInsertionShift=shift;cases.add(r);
    }
    require(minimumFullInsertionShift!=null,"Outward shift scan did not resolve isolated insertion");report.addProperty("minimum_successful_outward_shift_engine_units",minimumFullInsertionShift);
    report.addProperty("minimum_successful_outward_shift_mm",minimumFullInsertionShift/1e5);report.addProperty("completed",true);
    JsonObject sources=new JsonObject();for(String source:new String[]{"src/app/freerouting/board/NativeGuardFactory.java","tests/app/freerouting/board/NativeInsertionGapControl.java","vendor/freerouting-2.1.0.jar"})sources.addProperty(source,hash(Files.readAllBytes(Path.of(source))));report.add("source_files_sha256",sources);
    System.out.println(G.toJson(report));
  }
}
