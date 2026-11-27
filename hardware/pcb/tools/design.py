"""Netlist, parts and placement for the rockpod-bt unified board.

Coordinates are in mm. Origin is the centre of the iPod 30-pin pad row;
-y points out of the iPod (towards the dock opening), +y into the case.
Everything here is a first pass that has to be checked against real iPods.
"""

# ---------------------------------------------------------------- geometry
FRONT_Y = -6.8      # board front edge
REAR_Y = 0.125      # board rear edge over the pad row (leaves 0.75 mm exposed)
LEFT_X = -11.65     # left edge, through the castellated shield tab
EXT_X0 = 9.0        # extension starts here (right side)
EXT_X1 = 24.8       # extension right edge
EXT_REAR = 14.0     # extension rear edge
USB_FACE_Y = -7.25  # USB-C mouth (0.45 mm past the board front edge)
MOD_C = (17.6, 6.9)  # Bluetooth module centre

OUTLINE = [(LEFT_X, FRONT_Y), (EXT_X1, FRONT_Y), (EXT_X1, EXT_REAR),
           (EXT_X0, EXT_REAR), (EXT_X0, REAR_Y), (LEFT_X, REAR_Y)]

ANT_KEEPOUT = [(20.0, FRONT_Y), (EXT_X1, FRONT_Y), (EXT_X1, -2.6), (20.0, -2.6)]

# ---------------------------------------------------------------- module pins
NC = None
BT_PINS = {
    1: ("SPK_R_P", NC), 2: ("SPK_R_N", NC), 3: ("SPK_L_N", NC),
    4: ("SPK_L_P", NC), 5: ("GND", "GND"), 6: ("GND", "GND"),
    7: ("RF_IO", "RF_MOD"), 8: ("GND", "GND"), 9: ("AIO2/LED2", NC),
    10: ("AIO1/LED1", NC), 11: ("AIO0/LED0", NC), 12: ("SPI_CLK", NC),
    13: ("SPI_MOSI", NC), 14: ("NC", NC), 15: ("SPI_MISO", NC),
    16: ("RST#", "MOD_RST"), 17: ("UART_RX", "UART_TO_MOD"),
    18: ("UART_TX", "UART_FROM_MOD"), 19: ("PIO_POWER", "VACC"),
    20: ("PIO0", NC), 21: ("PIO1", NC), 22: ("GND", "GND"),
    23: ("PIO2", NC), 24: ("PIO3", NC), 25: ("PIO4", NC), 26: ("PIO5", NC),
    27: ("PIO6", NC), 28: ("PIO7", NC), 29: ("VCHG", NC),
    30: ("VBAT", "VACC"), 31: ("USB_DP", "MOD_USB_DP"),
    32: ("USB_DN", "MOD_USB_DN"), 33: ("GND", "GND"), 34: ("NC", NC),
    35: ("NC", NC), 36: ("VREG_ENABLE", "MOD_VREG_EN"),
    37: ("1V8_SMPS", "MOD_1V8"), 38: ("MIC_RP", "AUD_R_P"),
    39: ("MIC_RN", "AUD_R_N"), 40: ("MIC_BIAS", NC), 41: ("MIC_LP", "AUD_L_P"),
    42: ("MIC_LN", "AUD_L_N"), 43: ("MIC_BIAS", NC), 44: ("GND", "GND"),
}

USB_PINS = {  # USB-C 16P receptacle (USB 2.0)
    "A1B12": "GND", "A4B9": "VBUS", "B8": NC, "A5": "CC1", "B7": "USB_DN",
    "A6": "USB_DP", "A7": "USB_DN", "B6": "USB_DP", "A8": NC, "B5": "CC2",
    "B4A9": "VBUS", "B1A12": "GND", "SH": "GND",
}

IPOD_PINS = {  # pads on our board's underside (iPod pin number -> net)
    "1": "GND", "2": "AGND", "3": "LINE_R", "4": "LINE_L",
    "12": "IPOD_TX", "13": "IPOD_RX", "15": "GND", "18": "VACC",
    "21": "ACC_ID", "23": "VBUS", "25": "USB_DN", "27": "USB_DP",
    "29": "GND", "31": "GND", "32": "GND",
}

# ---------------------------------------------------------------- parts
# ref, value, footprint, lcsc, (x, y), rotation, {pad: net}, fitted
def two(n1, n2):
    return {"1": n1, "2": n2}


PARTS = [
    dict(ref="J1", value="GT-USB-7010ASV", fp="USB_C_16P_SMD",
         lcsc="C2988369", pos=(0.0, USB_FACE_Y), rot=0, nets=USB_PINS,
         fit=True, mpn="GT-USB-7010ASV"),
    dict(ref="U1", value="FSC-BT1046", fp="FSC_BT1046", lcsc="C9900132912",
         pos=MOD_C, rot=0, nets={str(k): v[1] for k, v in BT_PINS.items()},
         fit=True, mpn="FSC-BT1046"),
    dict(ref="U2", value="USBLC6-2SC6", fp="SOT-23-6", lcsc="C7519",
         pos=(7.2, -4.8), rot=0,
         nets={"1": "USB_DN", "2": "GND", "3": "USB_DP", "4": "USB_DP",
               "5": "VBUS", "6": "USB_DN"}, fit=True, mpn="USBLC6-2SC6"),
    dict(ref="J2", value="iPod 30-pin pads", fp="IPOD_IF", lcsc="",
         pos=(0.0, 0.0), rot=0, nets=IPOD_PINS, fit=False, mpn=""),
    dict(ref="ANT1", value="RFANT3216120A5T", fp="ANT_1206", lcsc="C127629",
         pos=(22.6, -5.3), rot=0, nets={"1": "RF_ANT", "2": NC}, fit=True,
         mpn="RFANT3216120A5T"),
    # USB-C
    dict(ref="R1", value="5.1k", fp="0402", lcsc="C25905", pos=(6.0, -0.75),
         rot=0, nets=two("CC1", "GND"), fit=True, mpn="0402WGF5101TCE"),
    dict(ref="R2", value="5.1k", fp="0402", lcsc="C25905", pos=(7.9, -0.75),
         rot=0, nets=two("CC2", "GND"), fit=True, mpn="0402WGF5101TCE"),
    dict(ref="C5", value="100n", fp="0402", lcsc="C307331", pos=(9.8, -0.6),
         rot=0, nets=two("VBUS", "GND"), fit=True, mpn="CL05B104KB54PNC"),
    # module supply
    dict(ref="C1", value="22u", fp="0603", lcsc="C59461", pos=(13.6, -5.7),
         rot=0, nets=two("VACC", "GND"), fit=True, mpn="CL10A226MQ8NRNC"),
    dict(ref="C2", value="22u", fp="0603", lcsc="C59461", pos=(13.6, -4.4),
         rot=0, nets=two("VACC", "GND"), fit=True, mpn="CL10A226MQ8NRNC"),
    dict(ref="C3", value="100n", fp="0402", lcsc="C307331", pos=(13.4, -3.0),
         rot=0, nets=two("VACC", "GND"), fit=True, mpn="CL05B104KB54PNC"),
    dict(ref="C4", value="100n", fp="0402", lcsc="C307331", pos=(13.4, -2.0),
         rot=0, nets=two("VACC", "GND"), fit=True, mpn="CL05B104KB54PNC"),
    dict(ref="C14", value="1u DNP", fp="0402", lcsc="C52923", pos=(13.4, -1.0),
         rot=0, nets=two("MOD_1V8", "GND"), fit=False, mpn="CL05A105KA5NQNC"),
    dict(ref="R11", value="10k", fp="0402", lcsc="C25744", pos=(15.2, -3.0),
         rot=0, nets=two("VACC", "MOD_VREG_EN"), fit=True, mpn="0402WGF1002TCE"),
    dict(ref="R12", value="10k", fp="0402", lcsc="C25744", pos=(15.2, -2.0),
         rot=0, nets=two("VACC", "MOD_RST"), fit=True, mpn="0402WGF1002TCE"),
    # UART
    dict(ref="R3", value="1k", fp="0402", lcsc="C11702", pos=(15.9, -5.7),
         rot=0, nets=two("IPOD_TX", "UART_TO_MOD"), fit=True,
         mpn="0402WGF1001TCE"),
    dict(ref="R4", value="1k", fp="0402", lcsc="C11702", pos=(15.9, -4.5),
         rot=0, nets=two("UART_FROM_MOD", "IPOD_RX"), fit=True,
         mpn="0402WGF1001TCE"),
    # RF
    dict(ref="C10", value="DNP", fp="0402", lcsc="", pos=(17.0, -0.6), rot=0,
         nets=two("RF_MOD", "GND"), fit=False, mpn="tune"),
    dict(ref="R9", value="0R", fp="0402", lcsc="C17168", pos=(18.4, -1.6),
         rot=90, nets=two("RF_ANT", "RF_MOD"), fit=True, mpn="0402WGF0000TCE"),
    dict(ref="C11", value="DNP", fp="0402", lcsc="", pos=(18.4, -3.3), rot=0,
         nets=two("RF_ANT", "GND"), fit=False, mpn="tune"),
    # audio: series R + DC block near the pads, RF caps at the module
    dict(ref="R5", value="100R", fp="0402", lcsc="C25076", pos=(-9.8, -5.9),
         rot=0, nets=two("LINE_L", "AUD_L_P_R"), fit=True, mpn="0402WGF1000TCE"),
    dict(ref="R6", value="100R", fp="0402", lcsc="C25076", pos=(-9.8, -4.8),
         rot=0, nets=two("AGND", "AUD_L_N_R"), fit=True, mpn="0402WGF1000TCE"),
    dict(ref="R7", value="100R", fp="0402", lcsc="C25076", pos=(-9.8, -3.7),
         rot=0, nets=two("LINE_R", "AUD_R_P_R"), fit=True, mpn="0402WGF1000TCE"),
    dict(ref="R8", value="100R", fp="0402", lcsc="C25076", pos=(-9.8, -2.6),
         rot=0, nets=two("AGND", "AUD_R_N_R"), fit=True, mpn="0402WGF1000TCE"),
    dict(ref="C6", value="1u", fp="0402", lcsc="C52923", pos=(-8.0, -5.9),
         rot=0, nets=two("AUD_L_P_R", "AUD_L_P"), fit=True, mpn="CL05A105KA5NQNC"),
    dict(ref="C7", value="1u", fp="0402", lcsc="C52923", pos=(-8.0, -4.8),
         rot=0, nets=two("AUD_L_N_R", "AUD_L_N"), fit=True, mpn="CL05A105KA5NQNC"),
    dict(ref="C8", value="1u", fp="0402", lcsc="C52923", pos=(-8.0, -3.7),
         rot=0, nets=two("AUD_R_P_R", "AUD_R_P"), fit=True, mpn="CL05A105KA5NQNC"),
    dict(ref="C9", value="1u", fp="0402", lcsc="C52923", pos=(-8.0, -2.6),
         rot=0, nets=two("AUD_R_N_R", "AUD_R_N"), fit=True, mpn="CL05A105KA5NQNC"),
    dict(ref="C12", value="100p", fp="0402", lcsc="C1546",
         pos=(9.9, MOD_C[1] - 2.5), rot=90, nets=two("AUD_L_N", "AUD_L_P"),
         fit=True, mpn="0402CG101J500NT"),
    dict(ref="C13", value="100p", fp="0402", lcsc="C1546",
         pos=(9.9, MOD_C[1] + 0.5), rot=90, nets=two("AUD_R_N", "AUD_R_P"),
         fit=True, mpn="0402CG101J500NT"),
    # accessory ID (unfitted)
    dict(ref="R10", value="DNP", fp="0402", lcsc="", pos=(11.0, -5.9), rot=0,
         nets=two("ACC_ID", "GND"), fit=False, mpn="value TBD"),
    # test pads for module firmware / debug
    dict(ref="TP1", value="MOD_USB_DP", fp="TP_1MM", lcsc="", pos=(9.8, 9.3),
         rot=0, nets={"1": "MOD_USB_DP"}, fit=False, mpn=""),
    dict(ref="TP2", value="MOD_USB_DN", fp="TP_1MM", lcsc="", pos=(9.8, 10.55),
         rot=0, nets={"1": "MOD_USB_DN"}, fit=False, mpn=""),
    dict(ref="TP3", value="MOD_RST", fp="TP_1MM", lcsc="", pos=(9.8, 11.8),
         rot=0, nets={"1": "MOD_RST"}, fit=False, mpn=""),
    dict(ref="TP4", value="GND", fp="TP_1MM", lcsc="", pos=(9.8, 13.05),
         rot=0, nets={"1": "GND"}, fit=False, mpn=""),
]
