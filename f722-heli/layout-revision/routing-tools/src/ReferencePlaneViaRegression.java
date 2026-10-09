import app.freerouting.Freerouting;
import app.freerouting.settings.*;
import app.freerouting.board.*;
import app.freerouting.core.*;
import app.freerouting.geometry.planar.*;
import app.freerouting.interactive.*;
import app.freerouting.designforms.specctra.DsnFile;
import app.freerouting.management.analytics.FRAnalytics;
import com.google.gson.*;
import java.nio.file.*;
import java.util.*;
/** Actual engine via-clearance checks; never invokes routing or edits a PCB. */
public final class ReferencePlaneViaRegression {
 public static void main(String[] args)throws Exception {
  Path dir=Path.of(args[0]);JsonObject model=JsonParser.parseString(Files.readString(dir.resolve("model.json"))).getAsJsonObject();
  JsonObject fixture=JsonParser.parseString(Files.readString(Path.of(args[1]))).getAsJsonObject();
  Freerouting.globalSettings=new GlobalSettings();Freerouting.globalSettings.usageAndDiagnosticData.disableAnalytics=true;Freerouting.globalSettings.apiServerSettings.isEnabled=false;Freerouting.globalSettings.guiSettings.isEnabled=false;FRAnalytics.setEnabled(false);
  RoutingJob job=new RoutingJob();HeadlessBoardManager mgr=new HeadlessBoardManager(Locale.ENGLISH,job);
  if(mgr.loadFromSpecctraDsn(Files.newInputStream(dir.resolve("routing.dsn")),new BoardObserverAdaptor(),new ItemIdentificationNumberGenerator())!=DsnFile.ReadResult.OK)throw new IllegalStateException("DSN load failed");
  RoutingBoard b=mgr.get_routing_board();NativeGuardFactory.install(b,model);
  int net=b.rules.nets.get(fixture.get("logical_net").getAsString(),1).net_number;
  var info=b.rules.via_infos.get(0);for(int i=0;i<b.rules.via_infos.count();i++)if(b.rules.via_infos.get(i).get_padstack().name.equals("VIA_450_200"))info=b.rules.via_infos.get(i);
  if(!info.get_padstack().name.equals("VIA_450_200"))throw new IllegalStateException("Ordinary via padstack missing");
  JsonArray results=new JsonArray();
  for(JsonElement e:fixture.getAsJsonArray("cases")){
   JsonObject c=e.getAsJsonObject();JsonArray xy=c.getAsJsonArray("xy");Point point=new IntPoint((int)Math.round(xy.get(0).getAsDouble()*1e5),-(int)Math.round(xy.get(1).getAsDouble()*1e5));
   boolean actual=ForcedViaAlgo.check(info,point,new int[]{net},0,0,b);boolean expected=c.get("allowed").getAsBoolean();
   JsonObject result=c.deepCopy();result.addProperty("actual_allowed",actual);result.addProperty("passed",actual==expected);results.add(result);
  }
  JsonObject out=new JsonObject();out.addProperty("board_sha256",model.get("board_sha256").getAsString());out.addProperty("model_sha256",LocalRouter.hash(dir.resolve("model.json")));out.addProperty("route_solver_used",false);out.addProperty("ordinary_reference_layers_disabled",!model.getAsJsonArray("routable_layers").toString().contains("In1.Cu")&&!model.getAsJsonArray("routable_layers").toString().contains("In4.Cu"));out.add("cases",results);
  boolean passed=true;for(JsonElement e:results)passed&=e.getAsJsonObject().get("passed").getAsBoolean();out.addProperty("passed",passed);Files.writeString(Path.of(args[2]),new GsonBuilder().setPrettyPrinting().create().toJson(out));System.out.println("REFERENCE_PLANE_VIA_CONTROL "+passed);if(!passed)throw new AssertionError("Via obstacle control failed; inspect report");
 }
}
