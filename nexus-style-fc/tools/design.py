"""Single source of truth for the Nexus-style main board: parts, values, LCSC codes, nets, placement.

The schematic (gen_schematic.py) and the PCB (build_floorplan.py) are both generated from this file.
Pin map follows the Rotorflight RDMS-NEXUS_F7 target (firmware/RDMS-NEXUS_F7.config).

Placement:
  ("xy", x, y, rot, side)               fixed, top-view mm from the PCB top-left corner
  ("near", ref, pad, side)              auto-placed next to that pad by build_floorplan.py
"""

TITLE = "Nexus-style FBL controller - main board"
REV = "0.2"
NX = "NexusFC"
R0402 = "Resistor_SMD:R_0402_1005Metric"
C0402 = "Capacitor_SMD:C_0402_1005Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"

# value -> (LCSC, description) for the passives
RES = {"1k": "C11702", "2.2k": "C25879", "5.1k": "C25905", "10k": "C25744", "21k": "C25766",
       "22k": "C25768", "27k": "C25771", "27.4k": "C26971", "52.3k": "C26982", "100k": "C25741",
       "120k": "C25750"}
CAP = {  # value, footprint -> LCSC
    ("100nF", C0402): "C1525",      # 16 V X7R
    ("10nF", C0402): "C15195",      # 50 V X7R
    ("3.3nF", C0402): "C26404",     # 50 V X7R
    ("30pF", C0402): "C1570",       # 50 V C0G
    ("1uF", C0402): "C52923",       # 25 V X5R
    ("2.2uF", C0402): "C12530",     # 6.3 V X5R
    ("2.2uF", C0603): "C23630",     # 16 V X5R
    ("4.7uF", C0603): "C69335",     # 25 V X5R
    ("10uF", C0603): "C96446",      # 25 V X5R
    ("22uF", C0603): "C86295",      # 10 V X5R
    ("4.7uF", C0805): "C1779",      # 25 V X5R
    ("10uF", C0805): "C15850",      # 25 V X5R
    ("22uF", C0805): "C602037",     # 25 V X5R
}

PARTS = []      # dicts: ref, sym, value, fp, lcsc, pins{pad: net}, place, group, note


def part(ref, sym, value, fp, lcsc, pins, place, group, note=""):
    PARTS.append(dict(ref=ref, sym=sym, value=value, fp=fp, lcsc=lcsc, pins=pins,
                      place=place, group=group, note=note))


_count = {"R": 0, "C": 0}


def R(value, a, b, place, group, note=""):
    _count["R"] += 1
    part(f"R{_count['R']}", "Device:R", value, R0402, RES[value], {"1": a, "2": b}, place, group, note)


def C(value, a, b, place, group, fp=C0402, note=""):
    _count["C"] += 1
    part(f"C{_count['C']}", "Device:C", value, fp, CAP[(value, fp)], {"1": a, "2": b}, place, group, note)


def nc(*pins):
    return {p: None for p in pins}


# ---------------------------------------------------------------- MCU
mcu = {
    "1": "3V3", "2": None, "3": "LED1_K", "4": "LED2_K", "5": "OSC_IN", "6": "OSC_OUT",
    "7": "NRST", "8": None, "9": "VX_SENSE", "10": "5V_SENSE", "11": None, "12": "GND",
    "13": "3V3", "14": "A_RX", "15": "A_TX", "16": "RPM", "17": "SBUS", "18": "GND",
    "19": "3V3", "20": "IMU_CS", "21": "SPI1_SCK", "22": "SPI1_MISO", "23": "SPI1_MOSI",
    "24": None, "25": "S3", "26": None, "27": None, "28": "C_RX", "29": "C_TX", "30": "VCAP",
    "31": "GND", "32": "3V3", "33": "FLASH_CS", "34": "SPI2_SCK", "35": "SPI2_MISO",
    "36": "SPI2_MOSI", "37": "B_RX", "38": "B_TX", "39": None, "40": None, "41": None,
    "42": "DSM_TX", "43": "DSM_DATA", "44": "USB_DM", "45": "USB_DP", "46": "SWDIO",
    "47": "GND", "48": "3V3", "49": "SWCLK", "50": "IMU_INT", "51": None, "52": None,
    "53": None, "54": None, "55": "TAIL", "56": "S1", "57": "S2", "58": "ESC", "59": None,
    "60": "BOOT0", "61": "I2C1_SCL", "62": "I2C1_SDA", "63": "GND", "64": "3V3",
}
part("U1", "NexusFC:STM32F722RET6", "STM32F722RET6", "NexusFC:LQFP-64_L10.0-W10.0-P0.50-LS12.0-BL",
     "C118207", mcu, ("xy", 11.2, 12.8, 0, "B"), "MCU", "Rotorflight RDMS-NEXUS_F7 pinout")
for pad in ("19", "32", "48", "64"):   # 19/32 sit under the 5 V buck strip: decoupled from the top side
    C("100nF", "3V3", "GND", ("near", "U1", pad, "F" if pad in ("19", "32") else "B"), "MCU", note=f"VDD pin {pad}")
C("4.7uF", "3V3", "GND", ("near", "U1", "64", "B"), "MCU", fp=C0603, note="VDD bulk")
C("1uF", "3V3", "GND", ("near", "U1", "13", "B"), "MCU", note="VDDA")
C("100nF", "3V3", "GND", ("near", "U1", "13", "B"), "MCU", note="VDDA")
C("100nF", "3V3", "GND", ("near", "U1", "1", "B"), "MCU", note="VBAT")
C("4.7uF", "VCAP", "GND", ("near", "U1", "30", "F"), "MCU", fp=C0603, note="VCAP_1 (LQFP64: single 4.7uF), top side over the pin")
C("100nF", "NRST", "GND", ("near", "U1", "7", "B"), "MCU", note="NRST")
R("10k", "BOOT0", "GND", ("near", "U1", "60", "B"), "MCU", note="BOOT0 pull-down")
part("Y1", "NexusFC:32258M20PF10PPM", "8MHz 20pF", "NexusFC:CRYSTAL-SMD_4P-L3.2-W2.5-BL", "C5181477",
     {"1": "OSC_IN", "2": "GND", "3": "OSC_OUT", "4": "GND"}, ("xy", 20.1, 11.2, 90, "B"), "MCU",
     "HSE 8 MHz (Rotorflight F7X2 default)")
C("30pF", "OSC_IN", "GND", ("xy", 12.35, 19.7, 90, "B"), "MCU", note="crystal load, CL 20 pF")
C("30pF", "OSC_OUT", "GND", ("xy", 17.45, 19.7, 90, "B"), "MCU", note="crystal load, CL 20 pF")
part("SW1", "NexusFC:TS-1088-AR02016", "BOOT", "NexusFC:SW-SMD_L3.9-W3.0-P4.45", "C720477",
     {"1": "BOOT0", "2": "3V3"}, ("xy", 17.0, 29.0, 0, "F"), "MCU", "DFU button, reachable through the case")
for i, (net, x) in enumerate((("SWDIO", 1.3), ("SWCLK", 3.3))):
    part(f"TP{i + 1}", "Connector:TestPoint", net, "TestPoint:TestPoint_Pad_D1.0mm", "",
         {"1": net}, ("xy", x, 22.6, 0, "B"), "MCU", "SWD")
part("TP3", "Connector:TestPoint", "3V3", "TestPoint:TestPoint_Pad_D1.0mm", "", {"1": "3V3"},
     ("xy", 1.3, 24.6, 0, "B"), "MCU", "SWD")
part("TP4", "Connector:TestPoint", "GND", "TestPoint:TestPoint_Pad_D1.0mm", "", {"1": "GND"},
     ("xy", 3.3, 24.6, 0, "B"), "MCU", "SWD")
part("TP5", "Connector:TestPoint", "NRST", "TestPoint:TestPoint_Pad_D1.0mm", "", {"1": "NRST"},
     ("xy", 1.3, 26.6, 0, "B"), "MCU", "SWD")

# LEDs: PC14/PC15 sit behind the backup-domain switch -> sink only, <= 3 mA
part("D1", "NexusFC:XL-1608SYGC-04", "LED1 yellow-green", "NexusFC:LED0603-RD_GREEN", "C965806",
     {"2": "LED1_A", "1": "LED1_K"}, ("xy", 8.6, 24.2, 0, "F"), "LED", "PC14, active-low")
R("1k", "3V3", "LED1_A", ("near", "D1", "2", "F"), "LED", note="~1.3 mA")
part("D2", "NexusFC:XL-1608SURC-06", "LED2 red", "NexusFC:LED0603-RD_RED", "C965799",
     {"2": "LED2_A", "1": "LED2_K"}, ("xy", 13.8, 24.2, 0, "F"), "LED", "PC15, active-low")
R("1k", "3V3", "LED2_A", ("near", "D2", "2", "F"), "LED", note="~1.3 mA")
part("D3", "NexusFC:XL-1608UBC-04", "Power LED blue", "NexusFC:LED0603-RD_BLUE", "C965807",
     {"2": "LED3_A", "1": "GND"}, ("xy", 11.2, 24.2, 0, "F"), "LED", "5 V bus present")
R("1k", "5V", "LED3_A", ("near", "D3", "2", "F"), "LED", note="~2 mA")

# ---------------------------------------------------------------- sensors
part("U2", "NexusFC:ICM-42688-P", "ICM-42688-P", "NexusFC:LGA-14_L3.0-W2.5-P0.50-TL", "C1850418",
     {"1": "SPI1_MISO", "2": "GND", "3": "GND", "4": "IMU_INT", "5": "3V3_SENS", "6": "GND",
      "7": "GND", "8": "3V3_SENS", "9": None, "10": "GND", "11": "GND", "12": "IMU_CS",
      "13": "SPI1_SCK", "14": "SPI1_MOSI"},
     ("xy", 11.2, 13.6, 0, "F"), "SENSORS", "IMU on SPI1, gyro_1_sensor_align CW90")
C("100nF", "3V3_SENS", "GND", ("near", "U2", "8", "F"), "SENSORS", note="IMU VDD")
C("2.2uF", "3V3_SENS", "GND", ("near", "U2", "8", "F"), "SENSORS", note="IMU VDD")
C("10nF", "3V3_SENS", "GND", ("near", "U2", "5", "F"), "SENSORS", note="IMU VDDIO")
R("10k", "IMU_CS", "3V3_SENS", ("near", "U2", "12", "F"), "SENSORS", note="keeps IMU in SPI mode at boot")
part("U3", "NexusFC:DPS368XTSA1", "DPS368XTSA1", "NexusFC:LGA-8_L2.5-W2.0-P0.65-TR_DPS368", "C3232508",
     {"1": "GND", "2": "3V3_SENS", "3": "I2C1_SDA", "4": "I2C1_SCL", "5": "GND", "6": "3V3_SENS",
      "7": "GND", "8": "3V3_SENS"},
     ("xy", 8.4, 9.0, 0, "F"), "SENSORS", "baro on I2C1, address 0x76 (SDO=GND), CSB=VDDIO selects I2C")
C("100nF", "3V3_SENS", "GND", ("near", "U3", "8", "F"), "SENSORS", note="baro VDD")
C("100nF", "3V3_SENS", "GND", ("near", "U3", "6", "F"), "SENSORS", note="baro VDDIO")
R("2.2k", "I2C1_SCL", "3V3_SENS", ("near", "U3", "4", "F"), "SENSORS", note="I2C pull-up")
R("2.2k", "I2C1_SDA", "3V3_SENS", ("near", "U3", "3", "F"), "SENSORS", note="I2C pull-up")
part("U10", "NexusFC:TPS70933DBVR", "TPS70933DBVR", "NexusFC:SOT-23-5_L3.0-W1.7-P0.95-LS2.8-BL", "C89347",
     {"1": "VSYS", "2": "GND", "3": None, "4": None, "5": "3V3_SENS"},
     ("xy", 14.0, 9.0, 0, "F"), "SENSORS", "3V3 sensor LDO, 30 V input; EN intentionally floating (internal pull-up), never tied to VSYS")
C("1uF", "VSYS", "GND", ("near", "U10", "1", "F"), "SENSORS", note="LDO in")
C("2.2uF", "3V3_SENS", "GND", ("xy", 9.4, 9.0, 0, "F"), "SENSORS", fp=C0603, note="LDO out, >=2 uF effective")

part("U4", "NexusFC:W25N01GVZEIG_C907680", "W25N01GVZEIG", "NexusFC:WSON-8_L8.0-W6.10-P1.27-BL-EP", "C907680",
     {"1": "FLASH_CS", "2": "SPI2_MISO", "3": "FLASH_WP", "4": "GND", "5": "SPI2_MOSI",
      "6": "SPI2_SCK", "7": "FLASH_HOLD", "8": "3V3", "9": None},
     ("xy", 18.3, 25.0, 0, "B"), "FLASH", "128MB blackbox on SPI2; EP floating")
C("100nF", "3V3", "GND", ("near", "U4", "8", "B"), "FLASH", note="flash VCC")
R("10k", "FLASH_CS", "3V3", ("near", "U4", "1", "B"), "FLASH", note="CS pull-up")
R("10k", "FLASH_WP", "3V3", ("near", "U4", "3", "B"), "FLASH", note="/WP pull-up")
R("10k", "FLASH_HOLD", "3V3", ("near", "U4", "7", "B"), "FLASH", note="/HOLD pull-up")

# ---------------------------------------------------------------- power
part("D4", "NexusFC:SMF13A_C353315", "SMF13A", "NexusFC:SOD-123FL_L2.8-W1.8-LS3.6-RD", "C353315",
     {"1": "VX", "2": "GND"}, ("xy", 4.6, 4.3, 0, "B"), "POWER", "VX input TVS, 13 V standoff, 200 W")
part("U5", "NexusFC:TPS62130RGTR", "TPS62130RGTR", "NexusFC:QFN-16_L3.0-W3.0-P0.50-TL-EP1.7", "C43590",
     {"1": "SW_5V", "2": "SW_5V", "3": "SW_5V", "4": None, "5": "FB_5V", "6": "GND", "7": "GND",
      "8": "GND", "9": "SS_5V", "10": "VX", "11": "VX", "12": "VX", "13": "VX", "14": "5V_BUCK",
      "15": "GND", "16": "GND", "17": "GND"},
     ("xy", 2.3, 9.2, 0, "B"), "POWER", "5 V / 3 A buck, FSW=GND 2.5 MHz, DEF=GND")
C("10uF", "VX", "GND", ("xy", 5.55, 6.0, 90, "B"), "POWER", fp=C0603, note="buck in, 25 V (TI typical: 10 uF)")
C("100nF", "VX", "GND", ("xy", 5.55, 8.6, 90, "B"), "POWER", note="AVIN")
C("3.3nF", "SS_5V", "GND", ("xy", 5.55, 10.6, 90, "B"), "POWER", note="soft start")
part("L1", "Device:L", "2.2uH 3A", "NexusFC:IND-SMD_L4.6-W4.1", "C142096",
     {"1": "SW_5V", "2": "5V_BUCK"}, ("xy", 2.3, 14.0, 90, "B"), "POWER", "5 V buck inductor")
C("22uF", "5V_BUCK", "GND", ("xy", 2.6, 15.7, 0, "B"), "POWER", fp=C0805, note="buck out (TI typical: 22 uF)")
R("120k", "5V_BUCK", "FB_5V", ("xy", 5.55, 12.6, 90, "B"), "POWER", note="Vout = 0.8 x (1 + 120/22) = 5.16 V")
R("22k", "FB_5V", "GND", ("xy", 5.55, 14.6, 90, "B"), "POWER")

part("U9", "NexusFC:TPS2116DRLR", "TPS2116DRLR", "NexusFC:SOT-583-8_L2.1-W1.6-P0.50-LS1.6-BL", "C3235557",
     {"1": "GND", "2": "5V", "3": "5V_BUCK", "4": "PR1", "5": "5V_BUCK", "6": "VBUS", "7": "5V", "8": None},
     ("xy", 12.0, 24.6, 0, "B"), "POWER", "priority mux: buck (VIN1) first, USB (VIN2) second")
R("100k", "5V_BUCK", "PR1", ("near", "U9", "4", "B"), "POWER", note="switch-over at 1.0 V x 127/27 = 4.7 V")
R("27k", "PR1", "GND", ("near", "U9", "4", "B"), "POWER")
C("1uF", "VBUS", "GND", ("near", "U9", "6", "B"), "POWER", note="VIN2")
C("22uF", "5V", "GND", ("near", "U9", "2", "B"), "POWER", fp=C0805, note="5 V bus bulk")

part("D5", "NexusFC:B5819WS_C22624", "B5819WS", "NexusFC:SOD-323_L1.8-W1.3-LS2.5-RD", "C22624",
     {"2": "VX", "1": "VSYS"}, ("xy", 19.1, 16.0, 90, "B"), "POWER", "VX -> VSYS")
part("D6", "NexusFC:B5819WS_C22624", "B5819WS", "NexusFC:SOD-323_L1.8-W1.3-LS2.5-RD", "C22624",
     {"2": "VBUS", "1": "VSYS"}, ("xy", 21.2, 16.0, 90, "B"), "POWER", "VBUS -> VSYS (USB-only boot)")
part("U14", "NexusFC:TPS629210DRLR", "TPS629210DRLR", "NexusFC:SOT-5X3-8_L2.1-W1.2-P0.50-LS1.6-BL_DRL0008A",
     "C5219301", {"1": None, "2": None, "3": "3V3", "4": "SW_3V3", "5": "GND", "6": "VSYS", "7": "VSYS",
                  "8": "SCONF"},
     ("xy", 20.1, 4.6, 0, "B"), "POWER", "3V3 MCU buck; S-CONF 27.4k = VSET mode, FB/VSET open = 3.3 V")
R("27.4k", "SCONF", "GND", ("xy", 7.4, 21.0, 90, "B"), "POWER", note="S-CONF #9: VSET, auto PFM, discharge")
C("4.7uF", "VSYS", "GND", ("xy", 2.0, 23.3, 0, "B"), "POWER", fp=C0603, note="buck in, 25 V")
part("L2", "Device:L", "2.2uH", "NexusFC:IND-SMD_L2.0-W1.6", "C5291913",
     {"1": "SW_3V3", "2": "3V3"}, ("xy", 20.1, 7.0, 0, "B"), "POWER", "3V3 buck inductor")
C("22uF", "3V3", "GND", ("xy", 5.0, 23.3, 0, "B"), "POWER", fp=C0603, note="buck out (TI typical 22 uF), 10 V")

# DSM 3.3 V from the MCU 3V3 buck (TPS629210, 1 A), as Rotorflight allows; PTC limits a shorted satellite
part("F2", "NexusFC:SMD0805P050TF", "0.5A PTC", "NexusFC:F0805", "C20978",
     {"1": "3V3", "2": "3V3_DSM"}, ("near", "J2", "1", "F"), "POWER", "DSM 3.3 V port fuse, 0.5 A hold")

R("52.3k", "VX", "VX_SENSE", ("near", "U1", "9", "F"), "POWER", note="BEC sense x0.161 (vbec_divider 160)")
R("10k", "VX_SENSE", "GND", ("near", "U1", "9", "F"), "POWER")
C("100nF", "VX_SENSE", "GND", ("near", "U1", "9", "F"), "POWER", note="ADC filter")
R("21k", "5V", "5V_SENSE", ("near", "U1", "10", "F"), "POWER", note="5 V bus sense x0.323 (vbus_divider 320)")
R("10k", "5V_SENSE", "GND", ("near", "U1", "10", "F"), "POWER")
C("100nF", "5V_SENSE", "GND", ("near", "U1", "10", "F"), "POWER", note="ADC filter")

# ---------------------------------------------------------------- USB
part("J6", "NexusFC:TYPE-C-31-D-06", "USB-C vertical", "NexusFC:USB-C-SMD_TYPE-C-31-D-06", "C2689964",
     {"A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND", "A4": "VBUS_C", "A9": "VBUS_C",
      "B4": "VBUS_C", "B9": "VBUS_C", "A5": "CC1", "B5": "CC2", "A6": "USB_DP", "B6": "USB_DP",
      "A7": "USB_DM", "B7": "USB_DM", "A8": None, "B8": None, "EP": "GND"},
     ("xy", 8.4, 29.0, 0, "F"), "USB", "top-entry USB-C")
R("5.1k", "CC1", "GND", ("near", "J6", "A5", "B"), "USB", note="UFP Rd")
R("5.1k", "CC2", "GND", ("near", "J6", "B5", "B"), "USB", note="UFP Rd")
part("F1", "NexusFC:SMD0805P050TF", "0.5A PTC", "NexusFC:F0805", "C20978",
     {"1": "VBUS_C", "2": "VBUS"}, ("xy", 5.6, 24.6, 0, "B"), "USB", "VBUS resettable fuse")
part("U7", "NexusFC:USBLC6-2SC6", "USBLC6-2SC6", "NexusFC:SOT-23-6_L2.9-W1.6-P0.95-LS2.8-BL", "C7519",
     {"1": "USB_DM", "6": "USB_DM", "3": "USB_DP", "4": "USB_DP", "2": "GND", "5": "VBUS"},
     ("xy", 9.2, 24.6, 90, "B"), "USB", "USB ESD")

# ---------------------------------------------------------------- receiver ports
gh = "NexusFC:CONN-SMD_4P-P1.25_BM04B-GHS-TBT-LF-SN"
for ref, lbl, rx, tx, xy in (("J3", "A-CRSF (UART4)", "A_RX", "A_TX", (19.0, 12.4, 90)),
                             ("J4", "C (UART3)", "C_RX", "C_TX", (6.0, 20.0, 0)),
                             ("J5", "B (UART6)", "B_RX", "B_TX", (16.4, 20.0, 0))):
    part(ref, "NexusFC:BM04B-GHS-TBT", lbl, gh, "C161692",
         {"1": "GND", "2": "5V", "3": rx, "4": tx, "5": "GND", "6": "GND"},
         ("xy", xy[0], xy[1], xy[2], "F"), "PORTS", "JST-GH [GND, 5V, RX, TX] (Rotorflight)")
part("J2", "NexusFC:B3B-ZR-SM4-TF", "DSM (UART1)", "NexusFC:CONN-SMD_B3B-ZR-SM4-TF", "C489717",
     {"1": "3V3_DSM", "2": "GND", "3": "DSM_DATA", "4": "GND", "5": "GND"},
     ("xy", 3.05, 12.4, 270, "F"), "PORTS", "JST-ZH [3.3V, GND, DATA] (Rotorflight)")
R("1k", "DSM_TX", "DSM_DATA", ("near", "J2", "3", "F"), "PORTS",
  note="UART1 TX joins DATA for SRXL2 half-duplex; isolates TX in RX-only DSM mode")
srv = "NexusFC:SOT-23-6_L2.9-W1.6-P0.95-LS2.8-BR"
part("U13", "NexusFC:SRV05-4.TCT", "SRV05-4", srv, "C13612",
     {"1": "A_RX", "3": "A_TX", "4": "B_RX", "6": "B_TX", "2": "GND", "5": "5V"},
     ("xy", 13.4, 21.3, 90, "B"), "PORTS", "ESD: A + B ports")
part("U15", "NexusFC:SRV05-4.TCT", "SRV05-4", srv, "C13612",
     {"1": "C_RX", "3": "C_TX", "4": "DSM_DATA", "6": None, "2": "GND", "5": "5V"},
     ("xy", 2.3, 19.4, 0, "B"), "PORTS", "ESD: C port + DSM")

# ---------------------------------------------------------------- servo header child board
part("J1", "Connector_Generic:Conn_01x09", "Header child board", "NexusFC:HeaderBoard_Joint", "",
     {"1": "VX", "2": "GND", "3": "SBUS", "4": "RPM", "5": "ESC", "6": "TAIL", "7": "S3",
      "8": "S2", "9": "S1"},
     ("xy", 0, 0, 0, "F"), "HEADER", "2 slots (VX, GND) + 7 fillet pads to the child board")
part("U11", "NexusFC:SRV05-4.TCT", "SRV05-4", srv, "C13612",
     {"1": "SBUS", "3": "RPM", "4": "ESC", "6": "TAIL", "2": "GND", "5": "5V"},
     ("xy", 6.6, 5.6, 0, "F"), "HEADER", "clamp: SBUS RPM ESC TAIL (Rotorflight: RPM needs OV diodes)")
part("U12", "NexusFC:SRV05-4.TCT", "SRV05-4", srv, "C13612",
     {"1": "S3", "3": "S2", "4": "S1", "6": None, "2": "GND", "5": "5V"},
     ("xy", 15.8, 5.6, 0, "F"), "HEADER", "clamp: S3 S2 S1")

PWR_FLAGS = ["VX", "GND", "VBUS_C"]


def nets():
    out = {}
    for p in PARTS:
        for pad, net in p["pins"].items():
            if net:
                out.setdefault(net, []).append((p["ref"], pad))
    return out


if __name__ == "__main__":
    n = nets()
    print(len(PARTS), "parts,", len(n), "nets")
    for name, conns in sorted(n.items()):
        if len(conns) < 2:
            print("single-pin net:", name, conns)


# ---------------------------------------------------------------- layout (overrides the per-part placement above)
# Fixed parts, top-view mm from the PCB top-left corner. Everything else is auto-placed next to an anchor pad.
LAYOUT = {
    # top: user-facing connectors (Nexus positions), header clamps, sensors
    "J2": ("xy", 3.3, 12.4, 270, "F"), "J3": ("xy", 18.9, 12.4, 90, "F"),
    "J4": ("xy", 6.0, 20.2, 0, "F"), "J5": ("xy", 16.4, 20.2, 0, "F"),
    "J6": ("xy", 8.4, 29.0, 0, "F"), "SW1": ("xy", 17.0, 29.0, 0, "F"),
    "D1": ("xy", 8.0, 24.3, 0, "F"), "D3": ("xy", 11.2, 24.3, 0, "F"), "D2": ("xy", 14.4, 24.3, 0, "F"),
    "U11": ("xy", 4.9, 5.9, 0, "F"), "U10": ("xy", 9.4, 6.25, 0, "F"), "U3": ("xy", 13.4, 6.1, 0, "F"),
    "U12": ("xy", 17.6, 5.9, 0, "F"), "U2": ("xy", 11.4, 11.6, 0, "F"),
    "U15": ("xy", 8.8, 15.6, 0, "F"), "U13": ("xy", 14.0, 15.6, 0, "F"),
    # bottom: MCU against the lid, power along the VX side, MCU buck + crystal on the right, flash
    # nothing on either side within 4.2 mm of the header edge (HeaderBoard_Joint courtyard)
    "U1": ("xy", 13.6, 11.05, 0, "B"),
    "U5": ("xy", 2.4, 6.5, 0, "B"), "L1": ("xy", 2.6, 11.7, 90, "B"), "D4": ("xy", 2.6, 18.0, 0, "B"),
    "U4": ("xy", 18.9, 26.6, 0, "B"), "Y1": ("xy", 14.9, 19.7, 0, "B"),
    "U14": ("xy", 2.0, 21.0, 0, "B"), "L2": ("xy", 5.0, 21.0, 0, "B"),
    "F1": ("xy", 8.4, 29.0, 90, "B"), "U7": ("xy", 9.7, 24.5, 90, "B"), "U9": ("xy", 13.6, 23.4, 0, "B"),
    # bottom, auto-placed next to the pins they serve
    "D5": ("near", "U14", "6", "B"),
    "D6": ("near", "F1", "2", "B"),
    # SWD / debug pads on the top side, beside the USB socket and the BOOT button (under the cover)
    # SWD pads on the right, the side of the MCU's PA13/PA14; 3V3 / GND / NRST on the left
    "TP1": ("xy", 21.15, 26.2, 0, "F"), "TP2": ("xy", 21.15, 28.4, 0, "F"), "TP5": ("xy", 1.6, 30.4, 0, "F"),
    "TP3": ("xy", 1.6, 26.0, 0, "F"), "TP4": ("xy", 1.6, 28.2, 0, "F"),
}
for _p in PARTS:
    if _p["ref"] in LAYOUT:
        _p["place"] = LAYOUT[_p["ref"]]
# auto-placement priority: regulator parts first, then MCU/crystal support, then the rest, test pads last;
# within a priority, ICs before passives so they get the closest spots
_REG = {"U5", "L1", "U14", "L2"}


def _prio(p):
    if p["place"][0] != "near":
        return (-1, 0)
    if p["ref"].startswith("TP"):
        return (9, 0)
    anchor = p["place"][1]
    if p["note"].startswith(("VCAP", "VDD pin", "crystal load", "VDDA")):
        return (0, 0)                              # MCU-critical decoupling goes first of all
    tier = 0 if anchor in _REG | {"Y1"} or p["ref"] in ("D5",) \
        else 1 if anchor == "U1" else 2
    return (tier, 0 if p["ref"].startswith(("U", "D", "L", "F")) else 1)


PARTS.sort(key=_prio)
