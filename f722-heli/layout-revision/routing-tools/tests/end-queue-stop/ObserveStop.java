import com.sun.jdi.*;
import com.sun.jdi.connect.*;
import com.sun.jdi.event.*;
import com.sun.jdi.request.*;
import com.google.gson.*;
import java.nio.file.*;
import java.io.*;
import java.util.*;

/** Read-only debugger observes the unmodified LocalRouter and stock stop flag. */
public final class ObserveStop {
  static final Gson G = new GsonBuilder().setPrettyPrinting().create();
  static void require(boolean b, String message) { if (!b) throw new AssertionError(message); }
  static Thread drain(InputStream input, Path file) throws Exception {
    OutputStream output=Files.newOutputStream(file);
    Thread t=new Thread(()->{try(input;output){input.transferTo(output);}catch(IOException e){throw new UncheckedIOException(e);}});
    t.start(); return t;
  }
  public static void main(String[] args) throws Exception {
    require(args.length==3,"ObserveStop MODEL PREFIX EXPECTED_ROUTED");
    Path model=Path.of(args[0]).toAbsolutePath(),prefix=Path.of(args[1]).toAbsolutePath();
    int expected=Integer.parseInt(args[2]);
    LaunchingConnector connector=Bootstrap.virtualMachineManager().defaultConnector();
    Map<String,Connector.Argument> config=connector.defaultArguments();
    config.get("main").setValue("LocalRouter "+model+" "+prefix+" 1");
    config.get("options").setValue("-XX:-UsePerfData -Xmx256m -Djava.awt.headless=true -cp build:vendor/freerouting-2.1.0.jar");
    config.get("suspend").setValue("true");
    VirtualMachine vm=connector.launch(config);
    Process child=vm.process();Thread stdout=drain(child.getInputStream(),Path.of(prefix+".stdout.log")),stderr=drain(child.getErrorStream(),Path.of(prefix+".stderr.log"));
    ClassPrepareRequest prepare=vm.eventRequestManager().createClassPrepareRequest();prepare.addClassFilter("app.freerouting.core.StoppableThread");prepare.setSuspendPolicy(EventRequest.SUSPEND_EVENT_THREAD);prepare.enable();
    JsonArray stops=new JsonArray(),returns=new JsonArray();long deadline=System.nanoTime()+20_000_000_000L;boolean disconnected=false;
    try {
      while(!disconnected && System.nanoTime()<deadline) {
        EventSet events=vm.eventQueue().remove(500);if(events==null)continue;
        for(Event event:events) {
          if(event instanceof ClassPrepareEvent ready) {
            Method method=ready.referenceType().methodsByName("request_stop_auto_router").get(0);
            List<Location> locations=method.allLineLocations();require(locations.size()>=2,"Stop method needs assignment and return line locations");
            BreakpointRequest before=vm.eventRequestManager().createBreakpointRequest(locations.get(0));before.putProperty("phase","before");before.setSuspendPolicy(EventRequest.SUSPEND_EVENT_THREAD);before.enable();
            BreakpointRequest after=vm.eventRequestManager().createBreakpointRequest(locations.get(locations.size()-1));after.putProperty("phase","after");after.setSuspendPolicy(EventRequest.SUSPEND_EVENT_THREAD);after.enable();prepare.disable();
          } else if(event instanceof BreakpointEvent entry && "before".equals(entry.request().getProperty("phase"))) {
            JsonObject observation=new JsonObject();JsonArray stack=new JsonArray();
            for(StackFrame frame:entry.thread().frames()){JsonObject loc=new JsonObject();loc.addProperty("class",frame.location().declaringType().name());loc.addProperty("method",frame.location().method().name());loc.addProperty("line",frame.location().lineNumber());stack.add(loc);}
            observation.add("stack",stack);ObjectReference stopThread=entry.thread().frame(0).thisObject();
            observation.addProperty("thread_object_id",stopThread.uniqueID());observation.addProperty("stop_flag_before",((BooleanValue)stopThread.getValue(stopThread.referenceType().fieldByName("stop_auto_router"))).value());
            observation.add("published_progress",JsonParser.parseString(Files.readString(Path.of(prefix+".progress.json"))));
            observation.addProperty("stop_file_present",Files.exists(Path.of(prefix+".stop")));stops.add(observation);
          } else if(event instanceof BreakpointEvent exit && "after".equals(exit.request().getProperty("phase"))) {
            ObjectReference stopThread=exit.thread().frame(0).thisObject();JsonObject observation=new JsonObject();
            observation.addProperty("thread_object_id",stopThread.uniqueID());observation.addProperty("stop_flag_after",((BooleanValue)stopThread.getValue(stopThread.referenceType().fieldByName("stop_auto_router"))).value());returns.add(observation);
          } else if(event instanceof VMDisconnectEvent) disconnected=true;
        }
        events.resume();
      }
    } catch(VMDisconnectedException e) {disconnected=true;}
    finally {if(!disconnected)vm.exit(99);}
    int exit=child.waitFor();stdout.join();stderr.join();
    JsonObject receipt=new JsonObject();receipt.addProperty("child_exit_code",exit);receipt.addProperty("deadline_seconds",20);receipt.addProperty("child_max_heap_mib",256);receipt.addProperty("observer_max_heap_mib",64);receipt.addProperty("requested_passes",1);receipt.addProperty("configured_stop_after_routed",System.getenv("F722_CHECKPOINT_AFTER_ROUTED"));receipt.add("stop_invocations",stops);receipt.add("stop_returns",returns);
    Files.writeString(Path.of(prefix+".debugger.json"),G.toJson(receipt)+"\n");
    require(disconnected&&exit==0,"Production child must exit normally before deadline");
    require(stops.size()>=1&&returns.size()==stops.size(),"All observed stop requests returned");
    JsonObject stop=stops.get(0).getAsJsonObject();JsonObject counters=stop.getAsJsonObject("published_progress").getAsJsonObject("route_counters");
    require(!stop.get("stop_flag_before").getAsBoolean()&&returns.get(0).getAsJsonObject().get("stop_flag_after").getAsBoolean(),"Observed cooperative stop flag transition");
    require(stop.getAsJsonArray("stack").get(1).getAsJsonObject().get("class").getAsString().equals("LocalRouter"),"Stop must originate in the production LocalRouter listener");
    require(counters.get("pass_count").getAsInt()==1&&counters.get("queued_to_be_routed_count").getAsInt()==0,"Requested final pass queue exhausted naturally");
    require(counters.get("routed_count").getAsInt()==expected&&expected<5,"Actual successes below five-route threshold");
    require("5".equals(System.getenv("F722_CHECKPOINT_AFTER_ROUTED"))&&!stop.get("stop_file_present").getAsBoolean(),"Other cooperative stop triggers excluded");
    for(int i=1;i<stops.size();i++) {
      JsonObject later=stops.get(i).getAsJsonObject();
      require(later.get("thread_object_id").getAsLong()==stop.get("thread_object_id").getAsLong()&&later.get("stop_flag_before").getAsBoolean(),"Later calls must reuse the already-stopped thread");
      require(later.getAsJsonArray("stack").get(1).getAsJsonObject().get("class").getAsString().equals("app.freerouting.autoroute.BatchAutorouter"),"Only the batch loop may redundantly request stop");
      require(returns.get(i).getAsJsonObject().get("stop_flag_after").getAsBoolean(),"Stop flag remains set");
    }
    receipt.addProperty("final_queue_stop_branch_observed",true);Files.writeString(Path.of(prefix+".debugger.json"),G.toJson(receipt)+"\n");
    System.out.println("FINAL_QUEUE_STOP_OBSERVED "+prefix);
  }
}
