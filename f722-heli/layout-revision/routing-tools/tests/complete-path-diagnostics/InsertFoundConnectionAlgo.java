package app.freerouting.autoroute;

import app.freerouting.board.*;
import app.freerouting.core.Padstack;
import app.freerouting.geometry.planar.FloatPoint;
import app.freerouting.geometry.planar.IntPoint;
import app.freerouting.geometry.planar.Point;
import app.freerouting.geometry.planar.Polyline;
import app.freerouting.logger.FRLogger;
import app.freerouting.rules.ViaInfo;

import java.util.Arrays;
import java.util.Set;

/**
 * Inserts the traces and vias of the connection found by the autoroute algorithm.
 */
public class InsertFoundConnectionAlgo
{

  private final RoutingBoard board;
  private final AutorouteControl ctrl;
  private IntPoint last_corner;
  private IntPoint first_corner;

  private static Object diagnosticPoint(Point point)
  {
    if (point == null) return null;
    FloatPoint p = point.to_float();
    return new double[]{p.x / 100000.0, -p.y / 100000.0};
  }

  /** Optional read-only witness of the exact located path and forced-insertion rejection. */
  private void diagnostic(String stage, int layer, Point[] requested, Point achieved)
  {
    if (!"1".equals(System.getenv("F722_INSERT_DIAGNOSTICS"))) return;
    java.util.Map<String,Object> record = new java.util.LinkedHashMap<>();
    record.put("stage",stage);
    record.put("net",board.rules.nets.get(ctrl.net_no).name);
    record.put("layer",board.layer_structure.arr[layer].name);
    record.put("half_width_mm",ctrl.trace_half_width[layer] / 100000.0);
    java.util.List<Object> corners = new java.util.ArrayList<>();
    for (Point point : requested) corners.add(diagnosticPoint(point));
    record.put("requested_corners_mm",corners);
    record.put("achieved_point_mm",diagnosticPoint(achieved));
    if (stage.startsWith("failed"))
    {
      Item obstacle = board.get_shove_failing_obstacle();
      record.put("failing_layer_index",board.get_shove_failing_layer());
      if (obstacle != null)
      {
        java.util.Map<String,Object> item = new java.util.LinkedHashMap<>();
        item.put("engine_id",obstacle.get_id_no());
        item.put("class",obstacle.getClass().getName());
        item.put("fixed",obstacle.get_fixed_state().name());
        item.put("clearance_class",obstacle.clearance_class_no());
        java.util.List<String> nets = new java.util.ArrayList<>();
        for (int i=0;i<obstacle.net_count();i++) nets.add(board.rules.nets.get(obstacle.get_net_no(i)).name);
        item.put("nets",nets);
        if (obstacle instanceof ObstacleArea area) item.put("label",area.name);
        if (obstacle instanceof NativePadContactArea contact) item.put("native_uuid",contact.nativeId);
        if (obstacle instanceof Trace trace)
        {
          item.put("first_corner_mm",diagnosticPoint(trace.first_corner()));
          item.put("last_corner_mm",diagnosticPoint(trace.last_corner()));
          item.put("width_mm",2 * trace.get_half_width() / 100000.0);
        }
        if (obstacle instanceof DrillItem drill) item.put("center_mm",diagnosticPoint(drill.get_center()));
        record.put("failing_obstacle",item);
      }
    }
    System.out.println("INSERT_DIAGNOSTIC " + new com.google.gson.Gson().toJson(record));
    System.out.flush();
  }


  /** Snapshot only: a located path is neither inserted copper nor a native validation result. */
  private Object diagnosticEndpoint(Item item, int layer, Point point)
  {
    java.util.Map<String,Object> endpoint = new java.util.LinkedHashMap<>();
    endpoint.put("layer_index",layer);
    endpoint.put("layer",board.layer_structure.arr[layer].name);
    endpoint.put("point_mm",diagnosticPoint(point));
    if (item != null)
    {
      endpoint.put("engine_id",item.get_id_no());
      endpoint.put("class",item.getClass().getName());
      endpoint.put("fixed",item.get_fixed_state().name());
      if (item instanceof ObstacleArea area) endpoint.put("label",area.name);
      if (item instanceof NativePadContactArea contact)
      {
        endpoint.put("native_uuid",contact.nativeId);
        endpoint.put("native_group",contact.nativeGroup);
        endpoint.put("contact_label",contact.name);
      }
    }
    return endpoint;
  }

  private Object diagnosticViaTransition(int before_trace_index, Point point, int from_layer, int to_layer)
  {
    java.util.Map<String,Object> transition = new java.util.LinkedHashMap<>();
    transition.put("before_trace_index",before_trace_index);
    transition.put("point_mm",diagnosticPoint(point));
    transition.put("from_layer_index",from_layer);
    transition.put("from_layer",board.layer_structure.arr[from_layer].name);
    transition.put("to_layer_index",to_layer);
    transition.put("to_layer",board.layer_structure.arr[to_layer].name);
    return transition;
  }

  /** Dump the whole target-to-start connection before any forced insertion can refuse. */
  private void diagnosticLocatedConnection(LocateFoundConnectionAlgo connection)
  {
    if (!"1".equals(System.getenv("F722_INSERT_DIAGNOSTICS"))) return;
    java.util.Map<String,Object> record = new java.util.LinkedHashMap<>();
    record.put("stage","located_connection");
    record.put("status","located_only");
    record.put("net",board.rules.nets.get(ctrl.net_no).name);
    record.put("net_no",ctrl.net_no);
    record.put("traversal","target_to_start");
    java.util.List<Object> traces = new java.util.ArrayList<>();
    java.util.List<Object> transitions = new java.util.ArrayList<>();
    Point target_point = null;
    Point start_point = null;
    int previous_layer = connection.target_layer;
    int trace_index = 0;
    for (LocateFoundConnectionAlgoAnyAngle.ResultItem trace : connection.connection_items)
    {
      Point first = trace.corners.length == 0 ? null : trace.corners[0];
      Point last = trace.corners.length == 0 ? null : trace.corners[trace.corners.length - 1];
      if (trace_index == 0) target_point = first;
      java.util.Map<String,Object> polyline = new java.util.LinkedHashMap<>();
      polyline.put("trace_index",trace_index);
      polyline.put("layer_index",trace.layer);
      polyline.put("layer",board.layer_structure.arr[trace.layer].name);
      polyline.put("half_width_mm",ctrl.trace_half_width[trace.layer] / 100000.0);
      java.util.List<Object> corners = new java.util.ArrayList<>();
      for (Point point : trace.corners) corners.add(diagnosticPoint(point));
      polyline.put("requested_corners_mm",corners);
      traces.add(polyline);
      if (previous_layer != trace.layer)
        transitions.add(diagnosticViaTransition(trace_index,first,previous_layer,trace.layer));
      previous_layer = trace.layer;
      start_point = last;
      ++trace_index;
    }
    if (previous_layer != connection.start_layer)
      transitions.add(diagnosticViaTransition(trace_index,start_point,previous_layer,connection.start_layer));
    record.put("target_endpoint",diagnosticEndpoint(connection.target_item,connection.target_layer,target_point));
    record.put("start_endpoint",diagnosticEndpoint(connection.start_item,connection.start_layer,start_point));
    record.put("traces",traces);
    record.put("via_transitions",transitions);
    System.out.println("INSERT_DIAGNOSTIC " + new com.google.gson.Gson().toJson(record));
    System.out.flush();
  }

  /**
   * Creates a new instance of InsertFoundConnectionAlgo
   */
  private InsertFoundConnectionAlgo(RoutingBoard p_board, AutorouteControl p_ctrl)
  {
    this.board = p_board;
    this.ctrl = p_ctrl;
  }

  /**
   * Creates a new instance of InsertFoundConnectionAlgo . Returns null, if the insertion did not
   * succeed.
   */
  public static InsertFoundConnectionAlgo get_instance(LocateFoundConnectionAlgo p_connection, RoutingBoard p_board, AutorouteControl p_ctrl)
  {
    if (p_connection == null || p_connection.connection_items == null)
    {
      return null;
    }
    int curr_layer = p_connection.target_layer;
    InsertFoundConnectionAlgo new_instance = new InsertFoundConnectionAlgo(p_board, p_ctrl);
    new_instance.diagnosticLocatedConnection(p_connection);
    for (LocateFoundConnectionAlgoAnyAngle.ResultItem curr_new_item : p_connection.connection_items)
    {
      new_instance.diagnostic("located_trace",curr_new_item.layer,curr_new_item.corners,null);
      if (!new_instance.insert_via(curr_new_item.corners[0], curr_layer, curr_new_item.layer))
      {
        FRLogger.debug("InsertFoundConnectionAlgo: insert via failed for net #" + p_ctrl.net_no);
        return null;
      }
      curr_layer = curr_new_item.layer;
      if (!new_instance.insert_trace(curr_new_item))
      {
        FRLogger.debug("InsertFoundConnectionAlgo: insert trace failed for net #" + p_ctrl.net_no);
        return null;
      }
    }
    if (!new_instance.insert_via(new_instance.last_corner, curr_layer, p_connection.start_layer))
    {
      return null;
    }
    if (p_connection.target_item instanceof PolylineTrace to_trace)
    {
      p_board.connect_to_trace(new_instance.first_corner, to_trace, p_ctrl.trace_half_width[p_connection.start_layer], p_ctrl.trace_clearance_class_no);
    }
    if (p_connection.start_item instanceof PolylineTrace to_trace)
    {
      p_board.connect_to_trace(new_instance.last_corner, to_trace, p_ctrl.trace_half_width[p_connection.target_layer], p_ctrl.trace_clearance_class_no);
    }

    try
    {
      p_board.normalize_traces(p_ctrl.net_no);
    } catch (Exception e)
    {
      FRLogger.warn("The normalization of net '" + p_board.rules.nets.get(p_ctrl.net_no).name + "' failed.");
    }

    return new_instance;
  }

  /**
   * Inserts the trace by shoving aside obstacle traces and vias. Returns false, that was not
   * possible for the whole trace.
   */
  private boolean insert_trace(LocateFoundConnectionAlgoAnyAngle.ResultItem p_trace)
  {
    if (p_trace.corners.length == 1)
    {
      if (this.first_corner == null)
      {
        this.first_corner = p_trace.corners[0];
      }
      this.last_corner = p_trace.corners[0];
      return true;
    }
    boolean result = true;

    // switch off correcting connection to pin because it may get wrong in inserting the polygon
    // line for line.
    double saved_edge_to_turn_dist = board.rules.get_pin_edge_to_turn_dist();
    board.rules.set_pin_edge_to_turn_dist(-1);

    // Look for pins att the start and the end of p_trace in case that neckdown is necessary.
    Pin start_pin = null;
    Pin end_pin = null;
    if (ctrl.with_neckdown)
    {
      ItemSelectionFilter item_filter = new ItemSelectionFilter(ItemSelectionFilter.SelectableChoices.PINS);
      Point curr_end_corner = p_trace.corners[0];
      for (int i = 0; i < 2; ++i)
      {
        Set<Item> picked_items = this.board.pick_items(curr_end_corner, p_trace.layer, item_filter);
        for (Item curr_item : picked_items)
        {
          Pin curr_pin = (Pin) curr_item;
          if (curr_pin.contains_net(ctrl.net_no) && curr_pin
              .get_center()
              .equals(curr_end_corner))
          {
            if (i == 0)
            {
              start_pin = curr_pin;
            }
            else
            {
              end_pin = curr_pin;
            }
          }
        }
        curr_end_corner = p_trace.corners[p_trace.corners.length - 1];
      }
    }
    int[] net_no_arr = new int[1];
    net_no_arr[0] = ctrl.net_no;

    int from_corner_no = 0;
    for (int i = 1; i < p_trace.corners.length; ++i)
    {
      Point[] curr_corner_arr = Arrays.copyOfRange(p_trace.corners, from_corner_no, i + 1);
      Polyline insert_polyline = new Polyline(curr_corner_arr);
      Point ok_point = board.insert_forced_trace_polyline(insert_polyline, ctrl.trace_half_width[p_trace.layer], p_trace.layer, net_no_arr, ctrl.trace_clearance_class_no, ctrl.max_shove_trace_recursion_depth, ctrl.max_shove_via_recursion_depth, ctrl.max_spring_over_recursion_depth, Integer.MAX_VALUE, ctrl.pull_tight_accuracy, true, null);
      if (ok_point != insert_polyline.last_corner()) diagnostic("failed_forced_trace_polyline",p_trace.layer,curr_corner_arr,ok_point);
      boolean neckdown_inserted = false;
      if (ok_point != null && ok_point != insert_polyline.last_corner() && ctrl.with_neckdown && curr_corner_arr.length == 2)
      {
        neckdown_inserted = insert_neckdown(ok_point, curr_corner_arr[1], p_trace.layer, start_pin, end_pin);
      }
      if (ok_point == insert_polyline.last_corner() || neckdown_inserted)
      {
        from_corner_no = i;
      }
      else if (ok_point == insert_polyline.first_corner() && i != p_trace.corners.length - 1)
      {
        // if ok_point == insert_polyline.first_corner() the spring over may have failed.
        // Spring over may correct the situation because an insertion, which is ok with clearance
        // compensation
        // may cause violations without clearance compensation.
        // In this case repeating the insertion with more distant corners may allow the spring_over
        // to correct the situation.
        if (from_corner_no > 0)
        {
          // p_trace.corners[i] may be inside the offset for the substitute trace around
          // a spring_over obstacle (if clearance compensation is off).
          if (curr_corner_arr.length < 3)
          {
            // first correction
            --from_corner_no;
          }
        }
        FRLogger.trace("InsertFoundConnectionAlgo: violation corrected");
      }
      else
      {
        result = false;
        break;
      }
    }

    for (int i = 0; i < p_trace.corners.length - 1; ++i)
    {
      Trace trace_stub = board.get_trace_tail(p_trace.corners[i], p_trace.layer, net_no_arr);
      if (trace_stub != null)
      {
        board.remove_item(trace_stub);
      }
    }

    board.rules.set_pin_edge_to_turn_dist(saved_edge_to_turn_dist);
    if (this.first_corner == null)
    {
      this.first_corner = p_trace.corners[0];
    }
    this.last_corner = p_trace.corners[p_trace.corners.length - 1];
    return result;
  }

  boolean insert_neckdown(Point p_from_corner, Point p_to_corner, int p_layer, Pin p_start_pin, Pin p_end_pin)
  {
    if (p_start_pin != null)
    {
      Point ok_point = try_neck_down(p_to_corner, p_from_corner, p_layer, p_start_pin, true);
      if (ok_point == p_from_corner)
      {
        return true;
      }
    }
    if (p_end_pin != null)
    {
      Point ok_point = try_neck_down(p_from_corner, p_to_corner, p_layer, p_end_pin, false);
      return ok_point == p_to_corner;
    }
    return false;
  }

  private Point try_neck_down(Point p_from_corner, Point p_to_corner, int p_layer, Pin p_pin, boolean p_at_start)
  {
    if (!p_pin.is_on_layer(p_layer))
    {
      return null;
    }
    FloatPoint pin_center = p_pin
        .get_center()
        .to_float();
    double curr_clearance = this.board.rules.clearance_matrix.get_value(ctrl.trace_clearance_class_no, p_pin.clearance_class_no(), p_layer, true);
    double pin_neck_down_distance = 2 * (0.5 * p_pin.get_max_width(p_layer) + curr_clearance);
    if (pin_center.distance(p_to_corner.to_float()) >= pin_neck_down_distance)
    {
      return null;
    }

    int neck_down_halfwidth = p_pin.get_trace_neckdown_halfwidth(p_layer);
    if (neck_down_halfwidth >= ctrl.trace_half_width[p_layer])
    {
      return null;
    }

    FloatPoint float_from_corner = p_from_corner.to_float();
    FloatPoint float_to_corner = p_to_corner.to_float();

    final int TOLERANCE = 2;

    int[] net_no_arr = new int[1];
    net_no_arr[0] = ctrl.net_no;

    double ok_length = board.check_trace_segment(p_from_corner, p_to_corner, p_layer, net_no_arr, ctrl.trace_half_width[p_layer], ctrl.trace_clearance_class_no, true);
    if (ok_length >= Integer.MAX_VALUE)
    {
      return p_from_corner;
    }
    ok_length -= TOLERANCE;
    Point neck_down_end_point;
    if (ok_length <= TOLERANCE)
    {
      neck_down_end_point = p_from_corner;
    }
    else
    {
      FloatPoint float_neck_down_end_point = float_from_corner.change_length(float_to_corner, ok_length);
      neck_down_end_point = float_neck_down_end_point.round();
      // add a corner in case  neck_down_end_point is not exactly on the line from p_from_corner to
      // p_to_corner
      boolean horizontal_first = Math.abs(float_from_corner.x - float_neck_down_end_point.x) >= Math.abs(float_from_corner.y - float_neck_down_end_point.y);
      IntPoint add_corner = LocateFoundConnectionAlgo
          .calculate_additional_corner(float_from_corner, float_neck_down_end_point, horizontal_first, board.rules.get_trace_angle_restriction())
          .round();
      Point curr_ok_point = board.insert_forced_trace_segment(p_from_corner, add_corner, ctrl.trace_half_width[p_layer], p_layer, net_no_arr, ctrl.trace_clearance_class_no, ctrl.max_shove_trace_recursion_depth, ctrl.max_shove_via_recursion_depth, ctrl.max_spring_over_recursion_depth, Integer.MAX_VALUE, ctrl.pull_tight_accuracy, true, null);
      if (curr_ok_point != add_corner)
      {
        return p_from_corner;
      }
      curr_ok_point = board.insert_forced_trace_segment(add_corner, neck_down_end_point, ctrl.trace_half_width[p_layer], p_layer, net_no_arr, ctrl.trace_clearance_class_no, ctrl.max_shove_trace_recursion_depth, ctrl.max_shove_via_recursion_depth, ctrl.max_spring_over_recursion_depth, Integer.MAX_VALUE, ctrl.pull_tight_accuracy, true, null);
      if (curr_ok_point != neck_down_end_point)
      {
        return p_from_corner;
      }
      add_corner = LocateFoundConnectionAlgo
          .calculate_additional_corner(float_neck_down_end_point, float_to_corner, !horizontal_first, board.rules.get_trace_angle_restriction())
          .round();
      if (!add_corner.equals(p_to_corner))
      {
        curr_ok_point = board.insert_forced_trace_segment(neck_down_end_point, add_corner, ctrl.trace_half_width[p_layer], p_layer, net_no_arr, ctrl.trace_clearance_class_no, ctrl.max_shove_trace_recursion_depth, ctrl.max_shove_via_recursion_depth, ctrl.max_spring_over_recursion_depth, Integer.MAX_VALUE, ctrl.pull_tight_accuracy, true, null);
        if (curr_ok_point != add_corner)
        {
          return p_from_corner;
        }
        neck_down_end_point = add_corner;
      }
    }

    Point ok_point = board.insert_forced_trace_segment(neck_down_end_point, p_to_corner, neck_down_halfwidth, p_layer, net_no_arr, ctrl.trace_clearance_class_no, ctrl.max_shove_trace_recursion_depth, ctrl.max_shove_via_recursion_depth, ctrl.max_spring_over_recursion_depth, Integer.MAX_VALUE, ctrl.pull_tight_accuracy, true, null);
    return ok_point;
  }

  /**
   * Searches the cheapest via masks containing p_from_layer and p_to_layer, so that a forced via is
   * possible at p_location with this mask and inserts the via. Returns false, if no suitable via
   * mask was found or if the algorithm failed.
   */
  private boolean insert_via(Point p_location, int p_from_layer, int p_to_layer)
  {
    if (p_from_layer == p_to_layer)
    {
      return true; // no via necessary
    }
    int from_layer;
    int to_layer;
    // sort the input layers
    if (p_from_layer < p_to_layer)
    {
      from_layer = p_from_layer;
      to_layer = p_to_layer;
    }
    else
    {
      from_layer = p_to_layer;
      to_layer = p_from_layer;
    }
    int[] net_no_arr = new int[1];
    net_no_arr[0] = ctrl.net_no;
    ViaInfo via_info = null;
    for (int i = 0; i < this.ctrl.via_rule.via_count(); ++i)
    {
      ViaInfo curr_via_info = this.ctrl.via_rule.get_via(i);
      Padstack curr_via_padstack = curr_via_info.get_padstack();
      if (curr_via_padstack.from_layer() > from_layer || curr_via_padstack.to_layer() < to_layer)
      {
        continue;
      }
      if (ForcedViaAlgo.check(curr_via_info, p_location, net_no_arr, this.ctrl.max_shove_trace_recursion_depth, this.ctrl.max_shove_via_recursion_depth, this.board))
      {
        via_info = curr_via_info;
        break;
      }
    }
    if (via_info == null)
    {
      diagnostic("failed_via_mask_check",p_from_layer,new Point[]{p_location},null);
      FRLogger.debug("InsertFoundConnectionAlgo: via mask not found for net #" + ctrl.net_no);
      return false;
    }
    // insert the via
    if (!ForcedViaAlgo.insert(via_info, p_location, net_no_arr, this.ctrl.trace_clearance_class_no, this.ctrl.trace_half_width, this.ctrl.max_shove_trace_recursion_depth, this.ctrl.max_shove_via_recursion_depth, this.board))
    {
      diagnostic("failed_forced_via",p_from_layer,new Point[]{p_location},null);
      FRLogger.debug("InsertFoundConnectionAlgo: forced via failed for net #" + ctrl.net_no);
      return false;
    }
    return true;
  }
}