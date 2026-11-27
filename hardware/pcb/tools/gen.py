"""Generate KiCad 8 schematic + PCB for EasyEDA Pro import, plus checks."""
import math
import os
import sys
import uuid

import design as D
import footprints as F

OUT = sys.argv[1]
NAME = "rockpod-bt-board"
OX, OY = 100.0, 100.0           # PCB offset so coordinates are positive
_u = 0


def uid():
    global _u
    _u += 1
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "rockpod-bt/%d" % _u))


def f(v):
    v = round(v, 4)
    return "%g" % (0.0 if v == 0 else v)


def q(s):
    return '"%s"' % str(s).replace('"', "'")


# ------------------------------------------------------------------ nets
nets = ["GND"]
for p in D.PARTS:
    for n in p["nets"].values():
        if n and n not in nets:
            nets.append(n)
NET_ID = {n: i + 1 for i, n in enumerate(nets)}

# ------------------------------------------------------------------ geometry helpers


def rot(x, y, deg):
    a = math.radians(deg)
    # KiCad rotates counter-clockwise on screen (y down) for positive angles
    return (x * math.cos(a) + y * math.sin(a), -x * math.sin(a) + y * math.cos(a))


def placed_pads(part):
    pads, _ = F.BUILDERS[part["fp"]]()
    out = []
    for pd in pads:
        dx, dy = rot(pd["x"], pd["y"], part["rot"])
        w, h = (pd["h"], pd["w"]) if part["rot"] % 180 == 90 else (pd["w"], pd["h"])
        out.append(dict(pd, X=part["pos"][0] + dx, Y=part["pos"][1] + dy, W=w, H=h))
    return out


# ------------------------------------------------------------------ PCB
LAYERS = """  (layers
    (0 "F.Cu" signal) (31 "B.Cu" signal)
    (32 "B.Adhes" user "B.Adhesive") (33 "F.Adhes" user "F.Adhesive")
    (34 "B.Paste" user) (35 "F.Paste" user)
    (36 "B.SilkS" user "B.Silkscreen") (37 "F.SilkS" user "F.Silkscreen")
    (38 "B.Mask" user) (39 "F.Mask" user)
    (40 "Dwgs.User" user "User.Drawings") (41 "Cmts.User" user "User.Comments")
    (42 "Eco1.User" user "User.Eco1") (43 "Eco2.User" user "User.Eco2")
    (44 "Edge.Cuts" user) (45 "Margin" user)
    (46 "B.CrtYd" user "B.Courtyard") (47 "F.CrtYd" user "F.Courtyard")
    (48 "B.Fab" user) (49 "F.Fab" user)
  )"""


def pad_sexpr(pd, part):
    net = part["nets"].get(pd["name"]) if pd["name"] else None
    s = '    (pad %s %s %s (at %s %s %s) (size %s %s)' % (
        q(pd["name"]), pd["kind"], pd["shape"], f(pd["x"]), f(pd["y"]),
        f(part["rot"]), f(pd["w"]), f(pd["h"]))
    if "drill" in pd:
        d = pd["drill"]
        s += " (drill %s)" % (f(d[1]) if d[0] == "round" else "oval %s %s" % (f(d[1]), f(d[2])))
    if pd.get("castellated"):
        s += " (property pad_prop_castellated)"
    s += " (layers %s)" % " ".join(q(l) for l in pd["layers"])
    if pd["shape"] == "roundrect":
        s += " (roundrect_rratio 0.25)"
    if net:
        s += " (net %d %s)" % (NET_ID[net], q(net))
    s += " (uuid %s))" % q(uid())
    return s


def fp_sexpr(part):
    pads, (bw, bh) = F.BUILDERS[part["fp"]]()
    x, y = part["pos"]
    lines = ['  (footprint %s (layer "F.Cu") (uuid %s) (at %s %s %s)' % (
        q("rockpod:" + part["fp"]), q(uid()), f(x + OX), f(y + OY), f(part["rot"]))]
    props = [("Reference", part["ref"], "F.SilkS", False),
             ("Value", part["value"], "F.Fab", False),
             ("Footprint", "rockpod:" + part["fp"], "F.Fab", True),
             ("LCSC", part["lcsc"], "F.Fab", True),
             ("Supplier Part", part["lcsc"], "F.Fab", True),
             ("MPN", part["mpn"], "F.Fab", True)]
    for k, v, layer, hide in props:
        ty = -(bh / 2 + 0.6) if k == "Reference" else (bh / 2 + 0.6 if k == "Value" else 0)
        if part["fp"] == "USB_C_16P_SMD" and k in ("Reference", "Value"):
            ty = 3.0 if k == "Reference" else 4.2
        if part["fp"] == "IPOD_IF" and k in ("Reference", "Value"):
            ty = -4.2 if k == "Reference" else -3.4
        lines.append('    (property %s %s (at 0 %s %s) (layer %s)%s (uuid %s) '
                     '(effects (font (size 0.5 0.5) (thickness 0.08))))' % (
                         q(k), q(v), f(ty), f(part["rot"]), q(layer),
                         " (hide yes)" if hide else "", q(uid())))
    attrs = "smd"
    if part["ref"] == "J2" or part["ref"].startswith("TP"):
        attrs += " exclude_from_pos_files exclude_from_bom"
    if not part["fit"] and not part["ref"].startswith("TP") and part["ref"] != "J2":
        attrs += " dnp"
    lines.append("    (attr %s)" % attrs)
    # fab outline + courtyard
    if part["fp"] == "USB_C_16P_SMD":
        x0, y0, x1, y1 = -bw / 2, 0, bw / 2, bh
    elif part["fp"] == "IPOD_IF":
        x0, y0, x1, y1 = -10.7, -6.625, 10.7, -0.575
    else:
        x0, y0, x1, y1 = -bw / 2, -bh / 2, bw / 2, bh / 2
    for lay, m in (("F.Fab", 0.0), ("F.CrtYd", 0.25)):
        lines.append('    (fp_rect (start %s %s) (end %s %s) (stroke (width 0.05) '
                     '(type default)) (fill none) (layer %s) (uuid %s))' % (
                         f(x0 - m), f(y0 - m), f(x1 + m), f(y1 + m), q(lay), q(uid())))
    if part["fp"] in ("FSC_BT1046", "SOT-23-6", "ANT_1206"):  # pin-1 dot
        p1 = pads[0]
        lines.append('    (fp_circle (center %s %s) (end %s %s) (stroke (width 0.12) '
                     '(type default)) (fill solid) (layer "F.SilkS") (uuid %s))' % (
                         f(p1["x"] - 0.9 if part["fp"] != "SOT-23-6" else p1["x"]),
                         f(p1["y"] + (1.1 if part["fp"] == "SOT-23-6" else 0)),
                         f(p1["x"] - 0.8 if part["fp"] != "SOT-23-6" else p1["x"] + 0.1),
                         f(p1["y"] + (1.1 if part["fp"] == "SOT-23-6" else 0)), q(uid())))
    for pd in pads:
        lines.append(pad_sexpr(pd, part))
    lines.append("  )")
    return "\n".join(lines)


def poly(pts, layer, width=0.05):
    out = []
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        out.append('  (gr_line (start %s %s) (end %s %s) (stroke (width %s) (type default)) '
                   '(layer %s) (uuid %s))' % (f(a[0] + OX), f(a[1] + OY), f(b[0] + OX),
                                               f(b[1] + OY), f(width), q(layer), q(uid())))
    return out


def zone(name, net, layers, pts, keepout=None):
    pts_s = " ".join("(xy %s %s)" % (f(x + OX), f(y + OY)) for x, y in pts)
    s = ['  (zone (net %d) (net_name %s) (layers %s) (uuid %s) (name %s)' % (
        NET_ID.get(net, 0) if net else 0, q(net or ""), " ".join(q(l) for l in layers),
        q(uid()), q(name)),
        '    (hatch edge 0.5)',
        '    (connect_pads (clearance 0.2))',
        '    (min_thickness 0.2) (filled_areas_thickness no)']
    if keepout:
        s.append('    (keepout (tracks %s) (vias not_allowed) (pads allowed) '
                 '(copperpour not_allowed) (footprints allowed))' % keepout)
    s.append('    (fill (thermal_gap 0.3) (thermal_bridge_width 0.3))')
    s.append('    (polygon (pts %s))' % pts_s)
    s.append('  )')
    return s


def silk(text, x, y, size=0.6, layer="F.SilkS"):
    return ('  (gr_text %s (at %s %s) (layer %s) (uuid %s) (effects (font (size %s %s) '
            '(thickness 0.1)) (justify left bottom)))' % (
                q(text), f(x + OX), f(y + OY), q(layer), q(uid()), f(size), f(size)))


def write_pcb():
    o = ['(kicad_pcb (version 20240108) (generator "rockpod-bt") (generator_version "8.0")',
         '  (general (thickness 0.8) (legacy_teardrops no))',
         '  (paper "A4")',
         '  (title_block (title "rockpod-bt unified USB-C + Bluetooth board") '
         '(rev "0.1-draft") (comment 1 "First-pass placement. Not routed. See hardware/pcb/README.md"))',
         LAYERS,
         '  (setup (pad_to_mask_clearance 0.05) (allow_soldermask_bridges_in_footprints no))',
         '  (net 0 "")']
    for n in nets:
        o.append("  (net %d %s)" % (NET_ID[n], q(n)))
    for part in D.PARTS:
        o.append(fp_sexpr(part))
    o += poly(D.OUTLINE, "Edge.Cuts")
    # top ground pour over the whole board except the antenna area
    o += zone("GND_TOP", "GND", ["F.Cu"], D.OUTLINE)
    o += zone("ANT_KEEPOUT", None, ["F.Cu", "B.Cu"], D.ANT_KEEPOUT, keepout="allowed")
    # mark where the exposed iPod pads are (iron access)
    o += poly([(-7.6, D.REAR_Y), (7.6, D.REAR_Y), (7.6, 0.875), (-7.6, 0.875)], "Dwgs.User")
    o.append(silk("iPod pads exposed here (iron access)", -7.6, 1.9, 0.5, "Dwgs.User"))
    o += poly([(-10.7, -6.625), (10.7, -6.625), (10.7, -0.575), (-10.7, -0.575)], "Cmts.User")
    o.append(silk("original 30-pin receptacle body", -10.7, -6.9, 0.5, "Cmts.User"))
    o.append(silk("rockpod-bt v0.1", 14.5, 13.6, 0.7))
    o.append(silk("AGND isolated", -11.0, -6.2 + 0.0, 0.45))
    o.append(silk("ANT", 21.0, -3.0, 0.6))
    o.append(")")
    open(os.path.join(OUT, NAME + ".kicad_pcb"), "w").write("\n".join(o) + "\n")


# ------------------------------------------------------------------ schematic
G = 2.54


def pin_list(part):
    if part["fp"] in ("0402", "0603", "ANT_1206"):
        return [("1", "~", "L"), ("2", "~", "R")]
    if part["fp"] == "TP_1MM":
        return [("1", "~", "L")]
    if part["fp"] == "SOT-23-6":
        return [("1", "IO1", "L"), ("6", "IO1", "R"), ("3", "IO2", "L"),
                ("4", "IO2", "R"), ("5", "VBUS", "R"), ("2", "GND", "L")]
    if part["fp"] == "USB_C_16P_SMD":
        return [(k, k, "R") for k in D.USB_PINS]
    if part["fp"] == "FSC_BT1046":
        return [(str(k), v[0], "L" if k <= 22 else "R") for k, v in D.BT_PINS.items()]
    if part["fp"] == "IPOD_IF":
        names = {"1": "GND", "2": "AUDIO_GND", "3": "LINE_OUT_R", "4": "LINE_OUT_L",
                 "12": "SERIAL_TX", "13": "SERIAL_RX", "15": "GND_15_16",
                 "18": "ACC_3V3", "21": "ACC_ID", "23": "USB_5V", "25": "USB_D-",
                 "27": "USB_D+", "29": "GND_29_30", "31": "SHIELD_L",
                 "32": "SHIELD_R"}
        return [(k, names[k], "L") for k in D.IPOD_PINS]
    raise ValueError(part["fp"])


def sym_key(part):
    return {"0402": "R" if part["ref"].startswith("R") else "C",
            "0603": "C"}.get(part["fp"], part["fp"])


def sym_geom(part):
    pins = pin_list(part)
    two_pin = part["fp"] in ("0402", "0603", "ANT_1206", "TP_1MM")
    if two_pin:
        geo = []
        for num, name, side in pins:
            geo.append((num, name, -5.08 if side == "L" else 5.08, 0.0,
                        0 if side == "L" else 180))
        return geo, (-2.54, 1.016, 2.54, -1.016)
    left = [p for p in pins if p[2] == "L"]
    right = [p for p in pins if p[2] == "R"]
    n = max(len(left), len(right))
    h = (n + 1) * G / 2
    w = 12.7 if part["fp"] in ("FSC_BT1046", "IPOD_IF", "USB_C_16P_SMD") else 7.62
    geo = []
    for side, lst in (("L", left), ("R", right)):
        for i, (num, name, _) in enumerate(lst):
            y = h - G - i * G
            y = round(y / 1.27) * 1.27
            x = -w - G if side == "L" else w + G
            geo.append((num, name, x, y, 0 if side == "L" else 180))
    return geo, (-w, h, w, -h)


def lib_symbol(key, part):
    geo, (x0, y0, x1, y1) = sym_geom(part)
    two_pin = part["fp"] in ("0402", "0603", "ANT_1206", "TP_1MM")
    hide_names = " (pin_names (offset 0.254) hide)" if two_pin else " (pin_names (offset 0.762))"
    s = ['    (symbol %s%s (exclude_from_sim no) (in_bom yes) (on_board yes)' % (q("rockpod:" + key), hide_names),
         '      (property "Reference" %s (at 0 %s 0) (effects (font (size 1.27 1.27))))' % (
             q(part["ref"].rstrip("0123456789")), f(y0 + 1.6)),
         '      (property "Value" %s (at 0 %s 0) (effects (font (size 1.27 1.27))))' % (q(key), f(y1 - 1.6)),
         '      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
         '      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
         '      (symbol %s (rectangle (start %s %s) (end %s %s) (stroke (width 0.254) (type default)) '
         '(fill (type background))))' % (q(key + "_0_1"), f(x0), f(y0), f(x1), f(y1)),
         '      (symbol %s' % q(key + "_1_1")]
    for num, name, x, y, ang in geo:
        s.append('        (pin passive line (at %s %s %s) (length 2.54) (name %s (effects (font (size 1.0 1.0)))) '
                 '(number %s (effects (font (size 1.0 1.0)))))' % (f(x), f(y), ang, q(name), q(num)))
    s.append('      )')
    s.append('    )')
    return "\n".join(s)


# schematic placement (sheet mm), grouped by function
SCH_POS = {
    "J2": (60, 110), "J1": (190, 60), "U2": (190, 130), "U1": (300, 120),
    "R1": (150, 40), "R2": (150, 50), "C5": (150, 60),
    "C1": (240, 200), "C2": (240, 212), "C3": (240, 224), "C4": (240, 236),
    "C14": (240, 248), "R11": (350, 200), "R12": (350, 212),
    "R3": (130, 160), "R4": (130, 172),
    "C10": (380, 50), "R9": (395, 40), "C11": (410, 50), "ANT1": (410, 30),
    "R5": (110, 210), "R6": (110, 222), "R7": (110, 234), "R8": (110, 246),
    "C6": (140, 210), "C7": (140, 222), "C8": (140, 234), "C9": (140, 246),
    "C12": (180, 216), "C13": (180, 240), "R10": (60, 200),
    "TP1": (380, 210), "TP2": (380, 222), "TP3": (380, 234), "TP4": (380, 246),
}


def write_sch():
    root = uid()
    keys = {}
    for part in D.PARTS:
        keys.setdefault(sym_key(part), part)
    o = ['(kicad_sch (version 20231120) (generator "rockpod-bt") (generator_version "8.0")',
         '  (uuid %s)' % q(root), '  (paper "A3")',
         '  (title_block (title "rockpod-bt unified USB-C + Bluetooth board") (rev "0.1-draft") '
         '(comment 1 "Module footprint pin-1 assumed; USB-C needs an all-SMD shell part"))',
         '  (lib_symbols']
    for key, part in keys.items():
        o.append(lib_symbol(key, part))
    o.append('  )')
    body = []
    for part in D.PARTS:
        sx, sy = SCH_POS[part["ref"]]
        geo, (x0, y0, x1, y1) = sym_geom(part)
        key = sym_key(part)
        props = [("Reference", part["ref"], 0, -y0 - 1.6, False),
                 ("Value", part["value"], 0, -y1 + 1.6, False),
                 ("Footprint", "rockpod:" + part["fp"], 0, 0, True),
                 ("Datasheet", "", 0, 0, True),
                 ("LCSC", part["lcsc"], 0, 0, True),
                 ("Supplier Part", part["lcsc"], 0, 0, True),
                 ("MPN", part["mpn"], 0, 0, True)]
        dnp = "yes" if (not part["fit"] and part["ref"] != "J2" and not part["ref"].startswith("TP")) else "no"
        s = ['  (symbol (lib_id %s) (at %s %s 0) (unit 1) (exclude_from_sim no) (in_bom %s) '
             '(on_board yes) (dnp %s) (uuid %s)' % (
                 q("rockpod:" + key), f(sx), f(sy),
                 "no" if part["ref"] == "J2" or part["ref"].startswith("TP") else "yes", dnp, q(uid()))]
        for k, v, px, py, hide in props:
            s.append('    (property %s %s (at %s %s 0) (effects (font (size 1.27 1.27))%s))' % (
                q(k), q(v), f(sx + px), f(sy + py), " (hide yes)" if hide else ""))
        for num, *_ in geo:
            s.append('    (pin %s (uuid %s))' % (q(num), q(uid())))
        s.append('    (instances (project %s (path %s (reference %s) (unit 1))))' % (
            q(NAME), q("/" + root), q(part["ref"])))
        s.append('  )')
        body += s
        # wires + labels / no-connects at each pin
        for num, name, px, py, ang in geo:
            ex, ey = sx + px, sy - py
            net = part["nets"].get(num)
            if net is None:
                body.append('  (no_connect (at %s %s) (uuid %s))' % (f(ex), f(ey), q(uid())))
                continue
            dx = -G if ang == 0 else G
            body.append('  (wire (pts (xy %s %s) (xy %s %s)) (stroke (width 0) (type default)) (uuid %s))' % (
                f(ex), f(ey), f(ex + dx), f(ey), q(uid())))
            just = "right bottom" if ang == 0 else "left bottom"
            body.append('  (label %s (at %s %s %s) (fields_autoplaced yes) (effects (font (size 1.0 1.0)) '
                        '(justify %s)) (uuid %s))' % (q(net), f(ex + dx), f(ey), 180 if ang == 0 else 0,
                                                       just, q(uid())))
    notes = [
        (20, 20, "rockpod-bt unified board, rev 0.1 draft. Nets connect by label name."),
        (20, 26, "AGND (iPod pin 2) is isolated: never tie it to GND on this board."),
        (20, 32, "Audio runs as pseudo-differential pairs: LINE_L/AGND and LINE_R/AGND."),
        (20, 38, "U1 pin numbering from the FSC-BT1046 datasheet; footprint pin-1 position assumed."),
        (20, 44, "J1 must be an all-SMD USB-C (no through-hole shell legs): the underside sits on the iPod."),
    ]
    for x, y, t in notes:
        body.append('  (text %s (exclude_from_sim no) (at %s %s 0) (effects (font (size 1.5 1.5)) '
                    '(justify left bottom)) (uuid %s))' % (q(t), f(x), f(y), q(uid())))
    o += body
    o.append('  (sheet_instances (path "/" (page "1")))')
    o.append(')')
    open(os.path.join(OUT, NAME + ".kicad_sch"), "w").write("\n".join(o) + "\n")


def write_pro():
    open(os.path.join(OUT, NAME + ".kicad_pro"), "w").write(
        '{\n  "meta": {"filename": "%s.kicad_pro", "version": 1},\n'
        '  "board": {"design_settings": {"rules": {"min_clearance": 0.1, '
        '"min_track_width": 0.1, "min_via_diameter": 0.45, "min_through_hole_diameter": 0.2}}}\n}\n' % NAME)


# ------------------------------------------------------------------ checks


def checks():
    problems = []
    allp = []
    for part in D.PARTS:
        for pd in placed_pads(part):
            allp.append((part["ref"], pd))
    # pads overlapping between different parts on the same copper side
    for i in range(len(allp)):
        ra, a = allp[i]
        for j in range(i + 1, len(allp)):
            rb, b = allp[j]
            if ra == rb:
                continue
            la = "B" if a["layers"][0].startswith("B") else ("T" if a["kind"] == "smd" else "*")
            lb = "B" if b["layers"][0].startswith("B") else ("T" if b["kind"] == "smd" else "*")
            if la != lb and "*" not in (la, lb):
                continue
            gx = abs(a["X"] - b["X"]) - (a["W"] + b["W"]) / 2
            gy = abs(a["Y"] - b["Y"]) - (a["H"] + b["H"]) / 2
            gap = max(gx, gy)
            if gap < 0.2:
                problems.append("clearance %.2f mm: %s.%s - %s.%s" % (gap, ra, a["name"], rb, b["name"]))
    # pads inside the outline (USB-C mouth and castellation excepted)
    xs = [p[0] for p in D.OUTLINE]

    def inside(x, y):
        if D.LEFT_X <= x <= D.EXT_X0 and D.FRONT_Y <= y <= D.REAR_Y:
            return True
        return D.EXT_X0 <= x <= D.EXT_X1 and D.FRONT_Y <= y <= D.EXT_REAR

    for ref, pd in allp:
        if pd.get("castellated"):
            continue
        for cx in (-1, 1):
            for cy in (-1, 1):
                x = pd["X"] + cx * (pd["W"] / 2 + 0.2)
                y = pd["Y"] + cy * (pd["H"] / 2 + 0.2)
                if not inside(x, y):
                    problems.append("near/over board edge: %s.%s at (%.2f, %.2f)" % (ref, pd["name"], pd["X"], pd["Y"]))
                    break
            else:
                continue
            break
    # every net has at least two connections
    count = {}
    for ref, pd in allp:
        part = next(p for p in D.PARTS if p["ref"] == ref)
        n = part["nets"].get(pd["name"])
        if n:
            count.setdefault(n, set()).add(ref)
    for n, refs in count.items():
        if len(refs) < 2:
            problems.append("net %s only on %s" % (n, sorted(refs)))
    return problems, allp, count


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    write_pcb()
    write_sch()
    write_pro()
    probs, allp, count = checks()
    print("nets:", len(nets), "parts:", len(D.PARTS), "pads:", len(allp))
    for p in probs:
        print("CHECK:", p)


def courtyard_check():
    boxes = []
    for part in D.PARTS:
        if part["ref"] == "J2":
            continue
        _, (bw, bh) = F.BUILDERS[part["fp"]]()
        pads = placed_pads(part)
        xs = [p["X"] - p["W"] / 2 for p in pads] + [p["X"] + p["W"] / 2 for p in pads]
        ys = [p["Y"] - p["H"] / 2 for p in pads] + [p["Y"] + p["H"] / 2 for p in pads]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        if part["fp"] == "USB_C_16P_SMD":
            px, py = part["pos"]
            x0, x1, y0, y1 = px - bw / 2, px + bw / 2, py, py + bh
        if part["fp"] == "FSC_BT1046":
            px, py = part["pos"]
            x0, x1, y0, y1 = min(x0, px - 6.2), max(x1, px + 6.2), min(y0, py - 6.2), max(y1, py + 6.2)
        boxes.append((part["ref"], x0 - 0.1, x1 + 0.1, y0 - 0.1, y1 + 0.1))
    bad = []
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i], boxes[j]
            if a[1] < b[2] and b[1] < a[2] and a[3] < b[4] and b[3] < a[4]:
                bad.append("courtyard overlap: %s / %s" % (a[0], b[0]))
    return bad


if __name__ == "__main__":
    for b in courtyard_check():
        print("CHECK:", b)
