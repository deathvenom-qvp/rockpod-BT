"""Plot the board: outline, top and bottom pads, keepouts, labels."""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Rectangle

import design as D
import gen

fig, ax = plt.subplots(figsize=(12, 7.6))
ax.add_patch(Polygon(D.OUTLINE, closed=True, fc="#1f5f3a", ec="k", lw=1.2, alpha=0.9))
ax.add_patch(Polygon(D.ANT_KEEPOUT, closed=True, fc="none", ec="#ffd34d", lw=1, ls="--"))
ax.text(20.2, -2.9, "antenna keep-out\n(no copper pour)", color="#ffd34d", fontsize=6.5, va="bottom")
# exposed iPod pads and original receptacle
ax.add_patch(Rectangle((-10.7, -6.625), 21.4, 6.05, fc="none", ec="#9ad0ff", ls=":", lw=1))
ax.text(-10.6, -6.95, "original 30-pin body", color="#3a6fb0", fontsize=6.5)
for i in range(30):
    x = -7.25 + 0.5 * i
    ax.add_patch(Rectangle((x - 0.175, -0.875), 0.35, 1.75, fc="#c9a227", ec="none", alpha=0.35, zorder=1))
ax.text(-7.4, 1.05, "iPod pads: rear 0.75 mm left exposed for the iron", fontsize=6.5, color="#8a6d00", va="top")
for part in D.PARTS:
    for pd in gen.placed_pads(part):
        x, y, w, h = pd["X"], pd["Y"], pd["W"], pd["H"]
        bottom = pd["layers"][0].startswith("B")
        if pd["kind"] == "np_thru_hole":
            ax.add_patch(Circle((x, y), w / 2, fc="white", ec="k", lw=0.6, zorder=5))
            continue
        col = "#4da3ff" if bottom else ("#e8b04b" if pd["kind"] == "smd" else "#d9d9d9")
        if pd["shape"] == "circle":
            ax.add_patch(Circle((x, y), w / 2, fc=col, ec="k", lw=0.3, zorder=4))
        else:
            ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fc=col, ec="k", lw=0.3,
                                   alpha=0.85 if bottom else 1, zorder=4 if not bottom else 3))
        if pd["kind"] == "thru_hole":
            ax.add_patch(Circle((x, y), 0.3, fc="white", ec="k", lw=0.4, zorder=6))
    if part["ref"] not in ("J2",):
        px, py = part["pos"]
        if part["fp"] == "USB_C_16P_SMD":
            ax.add_patch(Rectangle((px - 4.32, py), 8.64, 7.35, fc="none", ec="white", lw=0.8, ls="--", zorder=6))
            ax.text(px, py + 3.4, "J1 USB-C", ha="center", color="white", fontsize=8, zorder=7)
        elif part["fp"] == "FSC_BT1046":
            ax.add_patch(Rectangle((px - 6.2, py - 6.2), 12.4, 12.4, fc="none", ec="white", lw=0.8, ls="--", zorder=6))
            ax.text(px, py, "U1 FSC-BT1046\n(pin 1 assumed)", ha="center", va="center", color="white", fontsize=8, zorder=7)
        else:
            off = 0.75 if part["rot"] == 0 else 0.0
            ax.text(px + (0.55 if part["rot"] == 90 else 0), py - off, part["ref"], ha="center" if part["rot"] == 0 else "left",
                    va="bottom" if part["rot"] == 0 else "center", color="white", fontsize=5.5, zorder=7)
ax.annotate("castellated\nshield tab 31", (-11.65, -2.475), (-17.5, -5.2), fontsize=6.5,
            arrowprops=dict(arrowstyle="->", lw=0.6))
ax.annotate("plated slot,\nshield tab 32", (11.65, -2.475), (5.0, 5.2), fontsize=6.5,
            arrowprops=dict(arrowstyle="->", lw=0.6))
ax.annotate("USB-C mouth\n(dock opening side)", (0, -7.25), (-6, -9.6), fontsize=6.5,
            arrowprops=dict(arrowstyle="->", lw=0.6))
ax.plot([], [], "s", color="#e8b04b", label="top pads (all parts on top)")
ax.plot([], [], "s", color="#4da3ff", label="bottom pads (solder to iPod)")
ax.plot([], [], "s", color="#c9a227", alpha=0.4, label="iPod receptacle pads")
ax.legend(loc="upper left", fontsize=7, framealpha=0.9)
ax.set_xlim(-19, 27)
ax.set_ylim(15.5, -10.5)
ax.set_aspect("equal")
ax.grid(alpha=0.2)
ax.set_xlabel("mm (origin: centre of the iPod 30-pin pad row)")
ax.set_title("rockpod-bt unified board v0.1 draft: top view, 2 layers, 0.8 mm, %.1f x %.1f mm"
             % (D.EXT_X1 - D.LEFT_X, D.EXT_REAR - D.FRONT_Y))
fig.tight_layout()
fig.savefig(sys.argv[1], dpi=170)
