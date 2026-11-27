"""Footprint geometry. Pads: dict(name, kind, shape, x, y, w, h, layers, drill)."""
import design as D

TOP = ["F.Cu", "F.Paste", "F.Mask"]
BOT = ["B.Cu", "B.Mask"]
THRU = ["*.Cu", "*.Mask"]


def smd(name, x, y, w, h, layers=TOP, shape="roundrect"):
    return dict(name=name, kind="smd", shape=shape, x=x, y=y, w=w, h=h,
                layers=layers)


def chip(size):
    if size == "0402":
        return [smd("1", -0.48, 0, 0.56, 0.62), smd("2", 0.48, 0, 0.56, 0.62)], (1.0, 0.5)
    if size == "0603":
        return [smd("1", -0.775, 0, 0.8, 0.95), smd("2", 0.775, 0, 0.8, 0.95)], (1.6, 0.8)
    raise ValueError(size)


def sot23_6():
    p = []
    for i, x in enumerate((-0.95, 0.0, 0.95)):
        p.append(smd(str(i + 1), x, 1.15, 0.6, 1.0))
    for i, x in enumerate((0.95, 0.0, -0.95)):
        p.append(smd(str(i + 4), x, -1.15, 0.6, 1.0))
    return p, (2.9, 1.6)


def usb_c():
    """Generic USB-C 16P USB 2.0 land pattern, all-SMD shell.

    Origin at the centre of the mouth; the body extends +y. Placeholder:
    replace with the EasyEDA library footprint of the part you buy.
    """
    sig = [("A1B12", -3.25, 0.6), ("A4B9", -2.45, 0.6), ("B8", -1.75, 0.3),
           ("A5", -1.25, 0.3), ("B7", -0.75, 0.3), ("A6", -0.25, 0.3),
           ("A7", 0.25, 0.3), ("B6", 0.75, 0.3), ("A8", 1.25, 0.3),
           ("B5", 1.75, 0.3), ("B4A9", 2.45, 0.6), ("B1A12", 3.25, 0.6)]
    p = [smd(n, x, 6.4, w, 1.15, shape="rect") for n, x, w in sig]
    for sx in (-4.6, 4.6):
        for sy in (1.6, 5.0):
            p.append(smd("SH", sx, sy, 1.0, 1.6, shape="rect"))
    return p, (8.94, 7.35)


def bt1046():
    """FSC-BT1046, 44 pads, 1.0 mm pitch, 12.4 mm square. PIN-1 POSITION IS
    ASSUMED (front-left corner, numbering counter-clockwise from the top).
    Replace with the EasyEDA footprint for C9900132912 before routing."""
    p, e, L, W = [], 6.2, 1.2, 0.6
    for i in range(11):
        o = -5 + i
        p.append(smd(str(1 + i), o, -e, W, L, shape="rect"))        # front
        p.append(smd(str(12 + i), e, o, L, W, shape="rect"))        # right
        p.append(smd(str(23 + i), -o, e, W, L, shape="rect"))       # rear
        p.append(smd(str(34 + i), -e, -o, L, W, shape="rect"))      # left
    return p, (12.4, 12.4)


def ant_1206():
    return [smd("1", -1.35, 0, 0.9, 1.7, shape="rect"),
            smd("2", 1.35, 0, 0.9, 1.7, shape="rect")], (3.2, 1.6)


def tp():
    return [dict(name="1", kind="smd", shape="circle", x=0, y=0, w=1.0, h=1.0,
                 layers=["F.Cu", "F.Mask"])], (1.0, 1.0)


def ipod_if():
    """Underside pads that land on the iPod's 30-pin receptacle pads."""
    p = []
    single = {"1": -7.25, "2": -6.75, "3": -6.25, "4": -5.75, "12": -1.75,
              "13": -1.25, "18": 1.25, "21": 2.75, "23": 3.75, "25": 4.75,
              "27": 5.75}
    for n, x in single.items():
        p.append(smd(n, x, -0.525, 0.28, 0.8, layers=BOT, shape="rect"))
    p.append(smd("15", 0.0, -0.525, 0.78, 0.8, layers=BOT, shape="rect"))   # 15+16
    p.append(smd("29", 7.0, -0.525, 0.78, 0.8, layers=BOT, shape="rect"))   # 29+30
    # shield tabs: castellated on the left edge, plated slot on the right
    p.append(dict(name="31", kind="thru_hole", shape="rect", x=D.LEFT_X,
                  y=-2.475, w=1.4, h=2.05, layers=THRU, drill=("round", 1.0),
                  castellated=True))
    p.append(dict(name="32", kind="thru_hole", shape="rect", x=11.65,
                  y=-2.475, w=1.4, h=2.05, layers=THRU,
                  drill=("oval", 0.6, 1.2)))
    for sx in (-6.25, 6.25):  # alignment holes matching the iPod's locating holes
        p.append(dict(name="", kind="np_thru_hole", shape="circle", x=sx,
                      y=-2.125, w=1.1, h=1.1, layers=THRU, drill=("round", 1.1)))
    return p, (23.3, 7.0)


BUILDERS = {"0402": lambda: chip("0402"), "0603": lambda: chip("0603"),
            "SOT-23-6": sot23_6, "USB_C_16P_SMD": usb_c,
            "FSC_BT1046": bt1046, "ANT_1206": ant_1206, "TP_1MM": tp,
            "IPOD_IF": ipod_if}
