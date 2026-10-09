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
import java.security.MessageDigest;
import java.util.*;

/** Real-pad target geometry control. No route search, insertion, or PCB modification. */
public final class NativeTargetShapeControl {
  private static final Gson JSON = new GsonBuilder().setPrettyPrinting().create();

  private static void check(boolean condition, String message) {
    if (!condition) throw new AssertionError(message);
  }

  static String sha(byte[] bytes) throws Exception {
    return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
  }

  static String guardsFingerprint(RoutingBoard board) throws Exception {
    JsonArray guards = new JsonArray();
    for (Item item : board.get_items()) {
      if (!(item instanceof NativeGuardFactory.Guard guard)) continue;
      JsonObject record = new JsonObject();
      record.addProperty("id", guard.get_id_no());
      record.addProperty("label", guard.name);
      record.addProperty("layer", guard.get_layer());
      record.addProperty("clearance_class", guard.clearance_class_no());
      record.addProperty("fixed", guard.get_fixed_state().name());
      JsonArray nets = new JsonArray();
      for (int n = 0; n < guard.net_count(); n++) nets.add(guard.get_net_no(n));
      record.add("nets", nets);
      JsonArray polygons = new JsonArray();
      for (int tile = 0; tile < guard.tile_shape_count(); tile++) {
        JsonArray points = new JsonArray();
        for (FloatPoint p : guard.get_tile_shape(tile).corner_approx_arr()) {
          JsonArray xy = new JsonArray(); xy.add(p.x); xy.add(p.y); points.add(xy);
        }
        polygons.add(points);
      }
      record.add("polygons", polygons); guards.add(record);
    }
    check(guards.size() >= 2, "Fixture must retain both real copper guards");
    return sha(JSON.toJson(guards).getBytes(StandardCharsets.UTF_8));
  }

  public static void main(String[] args) throws Exception {
    if (args.length != 1) throw new IllegalArgumentException("NativeTargetShapeControl FIXTURE_DIR");
    Path fixture = Path.of(args[0]);
    JsonObject model = JsonParser.parseString(Files.readString(fixture.resolve("model.json"))).getAsJsonObject();
    check(model.get("fixture_only").getAsBoolean(), "Only a tiny extracted fixture is permitted");
    check(model.getAsJsonArray("contacts").size() == 2, "Expected J4.3 and R22.1 on F.Cu only");
    check(sha(Files.readAllBytes(fixture.resolve("routing.dsn"))).equals(model.get("dsn_sha256").getAsString()), "Fixture DSN hash");
    Freerouting.globalSettings = new GlobalSettings();
    Freerouting.globalSettings.usageAndDiagnosticData.disableAnalytics = true;
    Freerouting.globalSettings.apiServerSettings.isEnabled = false;
    Freerouting.globalSettings.guiSettings.isEnabled = false;
    FRAnalytics.setEnabled(false);
    HeadlessBoardManager manager = new HeadlessBoardManager(Locale.ENGLISH, new RoutingJob());
    try (var input = Files.newInputStream(fixture.resolve("routing.dsn"))) {
      check(manager.loadFromSpecctraDsn(input, new BoardObserverAdaptor(), new ItemIdentificationNumberGenerator()) == DsnFile.ReadResult.OK, "Fixture DSN load");
    }
    RoutingBoard board = manager.get_routing_board();
    check(board.communication.coordinate_transform.dsn_to_board(1) == 100000, "Expected native engine grid");
    int halfWidth = model.get("trace_half_width_engine_units").getAsInt();
    int margin = model.get("target_safety_margin_engine_units").getAsInt();
    int platedExtra = model.get("plated_extra_target_depth_engine_units").getAsInt();
    int smtExtra = model.get("smt_extra_target_depth_engine_units").getAsInt();
    check(platedExtra == 10000 && smtExtra == 0, "Fixture policy requires 0.10 mm extra plated depth and no SMT extra depth");
    board.rules.nets.get("SERVO3_EXT", 1).get_class().set_trace_half_width(halfWidth);
    NativeGuardFactory.install(board, model);
    String guardBefore = guardsFingerprint(board);
    ShapeSearchTree tree = new ShapeSearchTree45Degree(board, 1);
    Point badPoint = NativeGuardFactory.point(model.getAsJsonArray("legacy_disconnected_endpoint_mm"));
    int contacts = 0, entries = 0, safeEntries = 0, emptyEntries = 0, checkedCorners = 0, legacyAccepts = 0;
    boolean subdivisionExercised = false;
    double minimumBorderDistance = Double.POSITIVE_INFINITY;
    double legacyGap = Double.NaN;
    JsonArray contactDepths = new JsonArray();
    for (Item item : board.get_items()) {
      if (!(item instanceof NativePadContactArea contact) || !contact.label.equals("J4.3")) continue;
      TileShape nativeTile = contact.get_tile_shape(0);
      check(!nativeTile.contains(badPoint), "Witness must be outside actual conservative J4.3 copper");
      legacyGap = nativeTile.distance(badPoint.to_float()) - halfWidth;
      check(legacyGap > 2000, "Witness must leave a material copper gap, not grid rounding");
      for (int index = 0; index < contact.tree_shape_count(tree); index++) {
        if (contact.get_tree_shape(tree, index).contains(badPoint)) legacyAccepts++;
      }
    }
    check(legacyAccepts > 0, "Original expanded/octagonal connection shape must accept the disconnected witness");
    System.err.println("LEGACY_TARGET_WITNESS entries=" + legacyAccepts + " copper_gap_mm=" + legacyGap / 100000);
    for (Item item : board.get_items()) {
      if (!(item instanceof NativePadContactArea contact)) continue;
      contacts++;
      check(contact.tile_shape_count() == 1, "Fixture contact must be one actual convex polygon");
      check(board.rules.get_trace_half_width(contact.get_net_no(0), contact.get_layer()) == halfWidth, "Configured trace width");
      check(contact.plated == contact.label.equals("J4.3"), "Fixture must distinguish the real plated J4.3 from SMT R22.1");
      int extraDepth = contact.plated ? platedExtra : smtExtra;
      TileShape nativeTile = contact.get_tile_shape(0);
      TileShape safeInterior = (TileShape) nativeTile.offset(-halfWidth - margin - extraDepth);
      check(!safeInterior.is_empty(), "Real convex pad must retain a full-width target interior");
      double contactMinimumBorderDistance = Double.POSITIVE_INFINITY;
      double contactMinimumRoundedDistance = Double.POSITIVE_INFINITY;
      int contactCorners = 0;
      int count = contact.tree_shape_count(tree);
      check(count > 0, "Contact must have search entries");
      if (contact.label.equals("J4.3")) {
        check(count > contact.tile_shape_count(), "J4.3 must exercise subdivision indices beyond native tile count");
      }
      for (int index = 0; index < count; index++) {
        entries++;
        TileShape entry = contact.get_tree_shape(tree, index);
        TileShape target = contact.get_trace_connection_shape(tree, index);
        check(target != null, "Valid entry must return a shape, including an explicit empty shape");
        check(!target.contains(badPoint), "Legacy disconnected endpoint must not be an accepted target");
        TileShape expectedIntersection = safeInterior.intersection(entry);
        if (target.is_empty()) {
          emptyEntries++;
          check(expectedIntersection.is_empty(), "Valid eroded contact section was incorrectly discarded");
          continue;
        }
        check(!expectedIntersection.is_empty(), "Target exists in a clearance-only subdivision");
        check(entry.contains(target), "Target escaped its requested search-tree entry");
        check(nativeTile.contains(target), "Target escaped actual conservative contact geometry");
        for (FloatPoint corner : target.corner_approx_arr()) {
          double distance = nativeTile.border_distance(corner);
          minimumBorderDistance = Math.min(minimumBorderDistance, distance);
          contactMinimumBorderDistance = Math.min(contactMinimumBorderDistance, distance);
          check(nativeTile.contains(corner, 0.01), "Target corner is outside native contact");
          // Line.translate rounds the axis displacement by at most 0.5 unit.
          check(distance >= halfWidth + margin + extraDepth - 0.51,
                "Target lacks configured half-width, per-contact extra depth, and rounded safety margin");
          FloatPoint roundedCorner = corner.round().to_float();
          double roundedDistance = nativeTile.border_distance(roundedCorner);
          contactMinimumRoundedDistance = Math.min(contactMinimumRoundedDistance, roundedDistance);
          check(nativeTile.contains(roundedCorner) && roundedDistance >= halfWidth + extraDepth,
                "Integer-grid endpoint must retain full half-width and the per-contact nominal extra outer-boundary depth");
          checkedCorners++;
          contactCorners++;
        }
        safeEntries++;
        if (index >= contact.tile_shape_count()) subdivisionExercised = true;
      }
      check(contactCorners > 0, "Each real contact must retain and inspect target corners");
      check(contactMinimumBorderDistance <= halfWidth + margin + extraDepth + 0.51,
            "Contact target must not silently acquire a deeper inset than its configured policy");
      JsonObject depth = new JsonObject();
      depth.addProperty("contact", contact.label);
      depth.addProperty("plated", contact.plated);
      depth.addProperty("target_corners_checked", contactCorners);
      depth.addProperty("nominal_extra_outer_boundary_depth_mm", extraDepth / 100000.0);
      depth.addProperty("rounding_margin_mm", margin / 100000.0);
      depth.addProperty("minimum_unrounded_boundary_distance_mm", contactMinimumBorderDistance / 100000);
      depth.addProperty("minimum_rounded_boundary_distance_mm", contactMinimumRoundedDistance / 100000);
      depth.addProperty("minimum_rounded_depth_beyond_half_width_mm", (contactMinimumRoundedDistance - halfWidth) / 100000);
      contactDepths.add(depth);
    }
    check(contacts == 2 && safeEntries > 0 && checkedCorners > 0, "Both fixture contacts must be inspected");
    check(subdivisionExercised, "At least one safe target must use a subdivision index beyond native tile count");
    check(guardBefore.equals(guardsFingerprint(board)), "Target queries changed guard geometry or ownership");
    JsonObject result = new JsonObject();
    result.addProperty("passed", true);
    result.addProperty("fixture_model_sha256", sha(Files.readAllBytes(fixture.resolve("model.json"))));
    result.addProperty("source_board_sha256", model.get("source_board_sha256").getAsString());
    result.addProperty("source_model_sha256", model.get("source_model_sha256").getAsString());
    result.addProperty("contact_source_sha256", sha(Files.readAllBytes(Path.of("src/app/freerouting/board/NativePadContactArea.java"))));
    try (var input = NativePadContactArea.class.getResourceAsStream("/app/freerouting/board/NativePadContactArea.class")) {
      check(input != null, "Loaded contact bytecode must be available for provenance");
      result.addProperty("loaded_native_contact_class_sha256", sha(input.readAllBytes()));
    }
    result.addProperty("contacts", contacts);
    result.addProperty("search_entries", entries);
    result.addProperty("nonempty_target_entries", safeEntries);
    result.addProperty("empty_target_entries", emptyEntries);
    result.addProperty("target_corners_checked", checkedCorners);
    result.addProperty("legacy_entries_accepting_disconnected_endpoint", legacyAccepts);
    result.addProperty("legacy_copper_gap_mm", legacyGap / 100000);
    result.addProperty("minimum_target_border_distance_mm", minimumBorderDistance / 100000);
    result.add("per_contact_outer_boundary_depth", contactDepths);
    result.addProperty("depth_evidence_scope", model.get("depth_evidence_scope").getAsString());
    result.addProperty("guard_geometry_sha256", guardBefore);
    result.addProperty("guard_geometry_unchanged", true);
    result.addProperty("subdivision_indices_exercised", true);
    result.addProperty("route_solver_used", false);
    result.addProperty("caveat", model.get("caveat").getAsString());
    System.out.println(JSON.toJson(result));
  }
}
