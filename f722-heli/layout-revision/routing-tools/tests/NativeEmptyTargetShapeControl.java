import app.freerouting.Freerouting;
import app.freerouting.board.*;
import app.freerouting.core.RoutingJob;
import app.freerouting.designforms.specctra.DsnFile;
import app.freerouting.geometry.planar.*;
import app.freerouting.interactive.HeadlessBoardManager;
import app.freerouting.management.analytics.FRAnalytics;
import app.freerouting.settings.GlobalSettings;
import com.google.gson.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;

/** Independent empty-target negative control on two extracted real pads; no router is run. */
public final class NativeEmptyTargetShapeControl {
  private static final Gson JSON = new GsonBuilder().setPrettyPrinting().create();

  private static void check(boolean condition, String message) {
    if (!condition) throw new AssertionError(message);
  }

  private static String classHash(Class<?> type) throws Exception {
    try (var input = type.getResourceAsStream("/" + type.getName().replace('.', '/') + ".class")) {
      check(input != null, "Loaded bytecode must be available for provenance");
      return NativeTargetShapeControl.sha(input.readAllBytes());
    }
  }

  private static String targetFingerprint(List<NativePadContactArea> contacts, ShapeSearchTree tree) throws Exception {
    JsonArray result = new JsonArray();
    for (NativePadContactArea contact : contacts) {
      for (int index = 0; index < contact.tree_shape_count(tree); index++) {
        TileShape target = contact.get_trace_connection_shape(tree, index);
        check(target != null, "Target API must return an explicit shape for every valid entry");
        JsonObject entry = new JsonObject();
        entry.addProperty("contact_id", contact.get_id_no());
        entry.addProperty("entry_index", index);
        entry.addProperty("empty", target.is_empty());
        JsonArray points = new JsonArray();
        if (!target.is_empty()) for (FloatPoint p : target.corner_approx_arr()) {
          JsonArray xy = new JsonArray(); xy.add(p.x); xy.add(p.y); points.add(xy);
        }
        entry.add("corners", points); result.add(entry);
      }
    }
    return NativeTargetShapeControl.sha(JSON.toJson(result).getBytes(StandardCharsets.UTF_8));
  }

  public static void main(String[] args) throws Exception {
    if (args.length != 1) throw new IllegalArgumentException("NativeEmptyTargetShapeControl FIXTURE_DIR");
    Path fixture = Path.of(args[0]);
    byte[] fixtureBytes = Files.readAllBytes(fixture.resolve("model.json"));
    JsonObject model = JsonParser.parseString(new String(fixtureBytes, StandardCharsets.UTF_8)).getAsJsonObject();
    check(model.get("fixture_only").getAsBoolean() && model.getAsJsonArray("contacts").size() == 2,
          "Only the two-pad extracted fixture is permitted");
    String dsnHash = NativeTargetShapeControl.sha(Files.readAllBytes(fixture.resolve("routing.dsn")));
    check(dsnHash.equals(model.get("dsn_sha256").getAsString()), "Fixture DSN hash");
    Freerouting.globalSettings = new GlobalSettings();
    Freerouting.globalSettings.usageAndDiagnosticData.disableAnalytics = true;
    Freerouting.globalSettings.apiServerSettings.isEnabled = false;
    Freerouting.globalSettings.guiSettings.isEnabled = false;
    FRAnalytics.setEnabled(false);
    HeadlessBoardManager manager = new HeadlessBoardManager(Locale.ENGLISH, new RoutingJob());
    try (var input = Files.newInputStream(fixture.resolve("routing.dsn"))) {
      check(manager.loadFromSpecctraDsn(input, new BoardObserverAdaptor(), new ItemIdentificationNumberGenerator()) == DsnFile.ReadResult.OK,
            "Fixture DSN load");
    }
    RoutingBoard board = manager.get_routing_board();
    check(board.communication.coordinate_transform.dsn_to_board(1) == 100000, "Native engine grid");
    var netClass = board.rules.nets.get("SERVO3_EXT", 1).get_class();
    netClass.set_trace_half_width(model.get("trace_half_width_engine_units").getAsInt());
    NativeGuardFactory.install(board, model);
    List<NativePadContactArea> contacts = new ArrayList<>();
    int largestExtent = 0;
    for (Item item : board.get_items()) if (item instanceof NativePadContactArea contact) {
      contacts.add(contact);
      largestExtent = Math.max(largestExtent, (int) Math.ceil(contact.bounding_box().max_width()));
    }
    check(contacts.size() == 2, "Exactly two real contact items");
    ShapeSearchTree tree = new ShapeSearchTree45Degree(board, 1);
    String guardBefore = NativeTargetShapeControl.guardsFingerprint(board);
    String targetBefore = targetFingerprint(contacts, tree);
    int[] savedWidths = new int[netClass.layer_count()];
    for (int layer = 0; layer < savedWidths.length; layer++) savedWidths[layer] = netClass.get_trace_half_width(layer);
    int oversizedHalfWidth = largestExtent + 1000;
    int checkedEntries = 0;
    boolean higherSubdivisionChecked = false;
    try {
      netClass.set_trace_half_width(oversizedHalfWidth);
      for (NativePadContactArea contact : contacts) {
        // Independent impossibility witness: even the axis-aligned pad bounds cannot contain this disk.
        check(2L * oversizedHalfWidth > contact.bounding_box().min_width(), "Oversized trace cannot fit inside pad bounds");
        check(board.rules.get_trace_half_width(contact.get_net_no(0), contact.get_layer()) == oversizedHalfWidth,
              "Temporary width must reach the target API");
        int count = contact.tree_shape_count(tree);
        check(count > 0, "Existing search sections remain available");
        for (int index = 0; index < count; index++) {
          TileShape target = contact.get_trace_connection_shape(tree, index);
          check(target != null, "Empty actual target must be represented by an explicit shape");
          check(target.is_empty(), "Impossible full-width target must be empty for every subdivision");
          checkedEntries++;
          if (index >= contact.tile_shape_count()) higherSubdivisionChecked = true;
        }
      }
      check(guardBefore.equals(NativeTargetShapeControl.guardsFingerprint(board)), "Oversized target query changed a guard");
    } finally {
      for (int layer = 0; layer < savedWidths.length; layer++) netClass.set_trace_half_width(layer, savedWidths[layer]);
    }
    for (int layer = 0; layer < savedWidths.length; layer++) {
      check(netClass.get_trace_half_width(layer) == savedWidths[layer], "Original per-layer width must be restored");
    }
    check(checkedEntries > 2 && higherSubdivisionChecked, "Empty target test must cover real subdivision indices");
    check(targetBefore.equals(targetFingerprint(contacts, tree)), "Restored widths must restore every original target shape");
    check(guardBefore.equals(NativeTargetShapeControl.guardsFingerprint(board)), "Control changed guard geometry or ownership");
    JsonObject sources = new JsonObject();
    for (String source : new String[]{"src/app/freerouting/board/NativePadContactArea.java",
                                     "src/app/freerouting/autoroute/MazeSearchAlgo.java",
                                     "tests/NativeEmptyTargetShapeControl.java",
                                     "tests/NativeTargetShapeControl.java"}) {
      sources.addProperty(source, NativeTargetShapeControl.sha(Files.readAllBytes(Path.of(source))));
    }
    JsonObject result = new JsonObject();
    result.addProperty("passed", true);
    result.addProperty("fixture_model_sha256", NativeTargetShapeControl.sha(fixtureBytes));
    result.addProperty("fixture_dsn_sha256", dsnHash);
    result.addProperty("source_model_sha256", model.get("source_model_sha256").getAsString());
    result.addProperty("source_board_sha256", model.get("source_board_sha256").getAsString());
    result.add("source_file_sha256", sources);
    result.addProperty("loaded_native_contact_class_sha256", classHash(NativePadContactArea.class));
    result.addProperty("loaded_maze_search_class_sha256", classHash(app.freerouting.autoroute.MazeSearchAlgo.class));
    result.addProperty("contacts", contacts.size());
    result.addProperty("oversized_half_width_engine_units", oversizedHalfWidth);
    result.addProperty("plated_extra_target_depth_engine_units", model.get("plated_extra_target_depth_engine_units").getAsInt());
    result.addProperty("smt_extra_target_depth_engine_units", model.get("smt_extra_target_depth_engine_units").getAsInt());
    result.addProperty("depth_evidence_scope", model.get("depth_evidence_scope").getAsString());
    result.addProperty("explicit_empty_subdivisions_checked", checkedEntries);
    result.addProperty("higher_subdivision_indices_checked", higherSubdivisionChecked);
    result.addProperty("all_layer_widths_restored", true);
    result.addProperty("original_target_shapes_restored", true);
    result.addProperty("restored_target_geometry_sha256", targetBefore);
    result.addProperty("guard_geometry_unchanged", true);
    result.addProperty("guard_geometry_sha256", guardBefore);
    result.addProperty("route_solver_used", false);
    System.out.println(JSON.toJson(result));
  }
}
