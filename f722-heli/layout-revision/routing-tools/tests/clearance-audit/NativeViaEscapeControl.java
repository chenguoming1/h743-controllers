package app.freerouting.board;

import app.freerouting.Freerouting;
import app.freerouting.core.RoutingJob;
import app.freerouting.designforms.specctra.DsnFile;
import app.freerouting.geometry.planar.*;
import app.freerouting.interactive.HeadlessBoardManager;
import app.freerouting.management.analytics.FRAnalytics;
import app.freerouting.rules.ViaInfo;
import app.freerouting.settings.GlobalSettings;
import com.google.gson.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;

/** Four native-legal through-via witnesses. No routing, insertion, deletion or PCB export. */
public final class NativeViaEscapeControl {
  private static final Gson G = new GsonBuilder().setPrettyPrinting().create();
  private static void require(boolean value, String message) {
    if (!value) throw new IllegalStateException(message);
  }
  private static String hash(Path path) throws Exception {
    return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path)));
  }
  private static JsonArray coordinates(FloatPoint[] points) {
    JsonArray result = new JsonArray();
    for (FloatPoint point : points) {
      JsonArray xy = new JsonArray(); xy.add(point.x / 1e5); xy.add(-point.y / 1e5); result.add(xy);
    }
    return result;
  }
  private static JsonArray nets(RoutingBoard board, Item item) {
    JsonArray result = new JsonArray();
    for (int n = 0; n < item.net_count(); n++) result.add(board.rules.nets.get(item.get_net_no(n)).name);
    return result;
  }
  private static JsonObject describe(RoutingBoard board, Item item) {
    JsonObject result = new JsonObject();
    if (item == null) { result.addProperty("failure_item_available", false); return result; }
    result.addProperty("failure_item_available", true);
    result.addProperty("class", item.getClass().getName()); result.addProperty("engine_id", item.get_id_no());
    result.addProperty("fixed_state", item.get_fixed_state().toString());
    result.addProperty("clearance_class", item.clearance_class_no()); result.add("nets", nets(board, item));
    JsonArray layers = new JsonArray();
    for (int l = item.first_layer(); l <= item.last_layer(); l++) layers.add(board.layer_structure.arr[l].name);
    result.add("layers", layers);
    IntBox bounds = item.bounding_box();
    JsonArray bb = new JsonArray(); bb.add(bounds.ll.x / 1e5); bb.add(-bounds.ur.y / 1e5);
    bb.add(bounds.ur.x / 1e5); bb.add(-bounds.ll.y / 1e5); result.add("native_bbox_mm", bb);
    if (item instanceof ObstacleArea area) result.addProperty("label", area.name);
    if (item instanceof NativePadContactArea contact) result.addProperty("native_pad_uuid", contact.nativeId);
    if (item instanceof PolylineTrace trace) result.add("native_points_mm", coordinates(trace.polyline().corner_approx_arr()));
    if (item instanceof Via via) result.add("native_center_mm", coordinates(new FloatPoint[]{via.get_center().to_float()}).get(0));
    return result;
  }
  private static JsonObject fingerprints(RoutingBoard board) throws Exception {
    MessageDigest routes = MessageDigest.getInstance("SHA-256"), guards = MessageDigest.getInstance("SHA-256");
    int routeCount = 0, guardCount = 0;
    List<Item> items = new ArrayList<>(board.get_items()); items.sort(Comparator.comparingInt(Item::get_id_no));
    for (Item item : items) {
      JsonObject row = describe(board, item); MessageDigest destination;
      if (item instanceof ObstacleArea area) {
        destination = guards; guardCount++;
        row.add("outer", coordinates(area.get_area().get_border().corner_approx_arr()));
        JsonArray holes = new JsonArray();
        for (Shape hole : area.get_area().get_holes()) holes.add(coordinates(hole.corner_approx_arr()));
        row.add("holes", holes);
      } else if (item instanceof PolylineTrace trace) {
        destination = routes; routeCount++; row.addProperty("half_width", trace.get_half_width());
      } else if (item instanceof Via via) {
        destination = routes; routeCount++; row.addProperty("padstack", via.get_padstack().name);
      } else if (item instanceof BoardOutline outline) {
        destination = guards; guardCount++;
        JsonArray curves = new JsonArray();
        for (int i = 0; i < outline.shape_count(); i++) curves.add(coordinates(outline.get_shape(i).corner_approx_arr()));
        row.add("outline_curves", curves); row.addProperty("outline_half_width", outline.get_half_width());
      } else throw new IllegalStateException("Unhandled geometry fingerprint type: " + item.getClass().getName());
      destination.update(G.toJson(row).getBytes(StandardCharsets.UTF_8));
    }
    JsonObject result = new JsonObject();
    result.addProperty("routes_sha256", HexFormat.of().formatHex(routes.digest()));
    result.addProperty("guards_and_contacts_sha256", HexFormat.of().formatHex(guards.digest()));
    result.addProperty("route_count", routeCount); result.addProperty("guard_contact_count", guardCount);
    return result;
  }
  private static void verifyFiles(Path root, JsonObject expected) throws Exception {
    for (var entry : expected.entrySet())
      require(hash(root.resolve(entry.getKey())).equals(entry.getValue().getAsString()), "Hash mismatch: " + entry.getKey());
  }
  public static void main(String[] args) throws Exception {
    require(args.length == 4, "NativeViaEscapeControl MODEL_DIR FIXTURE_JSON OUTPUT_JSON EXPECTED_FIXTURE_SHA256");
    Path directory = Path.of(args[0]).toAbsolutePath().normalize(), root = directory.getParent();
    Path fixturePath = Path.of(args[1]).toAbsolutePath().normalize(), output = Path.of(args[2]);
    require(hash(fixturePath).equals(args[3]), "Fixture hash mismatch");
    JsonObject fixture = JsonParser.parseString(Files.readString(fixturePath)).getAsJsonObject();
    verifyFiles(root, fixture.getAsJsonObject("bound_files_sha256"));
    JsonObject model = JsonParser.parseString(Files.readString(directory.resolve("model.json"))).getAsJsonObject();
    require(model.get("board_sha256").equals(fixture.get("board_sha256")), "Board identity mismatch");
    require(hash(Path.of(model.get("physical_board").getAsString())).equals(model.get("board_sha256").getAsString()), "Native board drift");
    require(hash(Path.of(model.get("physical_native").getAsString())).equals(model.get("native_sha256").getAsString()), "Native export drift");
    require(hash(directory.resolve("routing.dsn")).equals(model.get("dsn_sha256").getAsString()), "DSN drift");
    verifyFiles(root, model.getAsJsonObject("adapter_sources"));
    JsonObject rules = model.getAsJsonObject("rules");
    require(rules.get("via_diameter").getAsDouble() == .45 && rules.get("via_drill").getAsDouble() == .20, "Via dimensions differ");
    require(rules.get("clearance").getAsDouble() == .127 && rules.get("track_width").getAsDouble() == .127, "Copper rules differ");
    require(model.getAsJsonArray("routable_layers").toString().equals("[\"F.Cu\",\"In2.Cu\",\"In3.Cu\",\"B.Cu\"]"), "Routable layers differ");
    Freerouting.globalSettings = new GlobalSettings();
    Freerouting.globalSettings.usageAndDiagnosticData.disableAnalytics = true;
    Freerouting.globalSettings.apiServerSettings.isEnabled = false;
    Freerouting.globalSettings.guiSettings.isEnabled = false; FRAnalytics.setEnabled(false);
    RoutingJob job = new RoutingJob(); HeadlessBoardManager manager = new HeadlessBoardManager(Locale.ENGLISH, job);
    try (var input = Files.newInputStream(directory.resolve("routing.dsn"))) {
      require(manager.loadFromSpecctraDsn(input, new BoardObserverAdaptor(), new ItemIdentificationNumberGenerator()) == DsnFile.ReadResult.OK, "DSN load failed");
    }
    RoutingBoard board = manager.get_routing_board();
    require(board.communication.coordinate_transform.dsn_to_board(1) == 1e5, "Engine grid differs from 10 nm");
    NativeGuardFactory.install(board, model);
    for (String key : new String[]{"guards", "contacts", "fixed_objects", "fixed_zones"}) model.remove(key);
    require(Path.of(ForcedViaAlgo.class.getProtectionDomain().getCodeSource().getLocation().toURI()).equals(root.resolve("vendor/freerouting-2.1.0.jar")), "ForcedViaAlgo is not the pinned stock class");
    require(Path.of(NativeGuardFactory.class.getProtectionDomain().getCodeSource().getLocation().toURI()).equals(root.resolve("build")), "Guard factory is not the hash-bound build");
    JsonObject before = fingerprints(board), report = new JsonObject();
    report.addProperty("fixture_sha256", args[3]); report.addProperty("board_sha256", fixture.get("board_sha256").getAsString());
    report.add("bound_files_sha256", fixture.get("bound_files_sha256")); report.add("before", before);
    report.addProperty("route_search_used", false); report.addProperty("via_insertion_used", false);
    report.addProperty("check", "pinned stock ForcedViaAlgo.check with zero trace/via shove recursion");
    report.addProperty("drill_representation", "0.20 mm drill enforced by source-bound native guards; stock padstack models 0.45 mm copper");
    JsonArray results = new JsonArray(); report.add("cases", results);
    for (JsonElement element : fixture.getAsJsonArray("cases")) {
      JsonObject test = element.getAsJsonObject(), result = test.deepCopy();
      String logical = test.get("logical_net").getAsString(); var net = board.rules.nets.get(logical, 1);
      require(net != null && model.getAsJsonObject("aliases").get(logical).getAsString().equals(logical), "Unexpected logical net");
      require(model.getAsJsonArray("ordinary_nets").contains(new JsonPrimitive(logical)), "Not an ordinary net");
      ViaInfo info = null; var viaRule = net.get_class().get_via_rule();
      for (int i = 0; i < viaRule.via_count(); i++) if (viaRule.get_via(i).get_padstack().name.equals("VIA_450_200")) info = viaRule.get_via(i);
      require(info != null && !info.attach_smd_allowed(), "Ordinary via padstack missing or attaches to SMT");
      require(info.get_padstack().from_layer() == 0 && info.get_padstack().to_layer() == 5, "Via is not through all six layers");
      for (int layer = 0; layer < 6; layer++) require(info.get_padstack().get_shape(layer).max_width() == 45000, "Via copper diameter differs");
      JsonArray xy = test.getAsJsonArray("quantized_xy_mm"), raw = test.getAsJsonArray("original_xy_mm"), integer = test.getAsJsonArray("engine_xy");
      int x = integer.get(0).getAsInt(), y = integer.get(1).getAsInt();
      require(x == Math.round(raw.get(0).getAsDouble() * 1e5) && y == -Math.round(raw.get(1).getAsDouble() * 1e5), "Witness quantization differs");
      require(Math.abs(x / 1e5 - xy.get(0).getAsDouble()) < 1e-12 && Math.abs(-y / 1e5 - xy.get(1).getAsDouble()) < 1e-12, "Physical and engine points differ");
      require(test.get("native_quantized_allowed").getAsBoolean() && test.get("quantized_minimum_extra_clearance_mm").getAsDouble() > 0, "Native quantized witness is not legal");
      board.set_shove_failing_obstacle(null); board.set_shove_failing_layer(-1);
      long started = System.nanoTime();
      boolean allowed = ForcedViaAlgo.check(info, new IntPoint(x, y), new int[]{net.net_number}, 0, 0, board);
      result.addProperty("engine_allowed", allowed); result.addProperty("native_engine_agree", allowed);
      result.addProperty("seconds", (System.nanoTime() - started) / 1e9);
      if (!allowed) {
        result.add("failure_item", describe(board, board.get_shove_failing_obstacle()));
        int layer = board.get_shove_failing_layer(); result.addProperty("failure_layer_index", layer);
        result.addProperty("failure_layer", layer < 0 ? "unreported" : board.layer_structure.arr[layer].name);
      }
      JsonObject after = fingerprints(board); boolean unchanged = before.equals(after);
      result.add("after", after); result.addProperty("geometry_unchanged", unchanged); results.add(result);
      report.addProperty("geometry_unchanged", unchanged); Files.writeString(output, G.toJson(report) + "\n");
      System.out.println("NATIVE_VIA_ESCAPE " + test.get("pad").getAsString() + " engine_allowed=" + allowed + " geometry_unchanged=" + unchanged);
      require(unchanged, "Via check changed geometry");
    }
    verifyFiles(root, fixture.getAsJsonObject("bound_files_sha256"));
    report.addProperty("completed", true); report.addProperty("source_files_unchanged", true);
    report.addProperty("all_native_witnesses_engine_allowed", results.asList().stream().allMatch(e -> e.getAsJsonObject().get("engine_allowed").getAsBoolean()));
    Files.writeString(output, G.toJson(report) + "\n");
  }
}
