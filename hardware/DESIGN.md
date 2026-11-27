# Board design notes

How the unified USB-C + Bluetooth board attaches to the iPod and how its audio path is laid out. Pad positions come from the reference land pattern in [`reference/ipod-30pin`](reference/ipod-30pin), which still has to be checked against real 5G, 6G and 7G logic boards.

## Attaching to the iPod

The board replaces the 30-pin receptacle and solders straight onto its pads on the logic board. No other soldering to the logic board.

**Why not castellations everywhere.** The iPod's signal pads are on a 0.5 mm pitch. Castellated holes need at least 0.6 mm diameter and 0.6 mm between holes (JLCPCB), so about 1.2 mm center to center, and their copper would reach the neighboring pads. The pins we need also sit in adjacent pairs (3/4, 12/13), and pin 18 (3.3 V) is next to pin 19 (FireWire 12 V).

**Hybrid attach:**

1. **Castellated shield tabs.** The receptacle's two shield pads (31/32, 1.4 × 2.05 mm at x = ±11.65 mm) are large and isolated. The board's side edges carry castellated half-holes over them. They take the mechanical load and are easy to inspect and rework. Confirm with a meter that they are ground on each generation.
2. **Bottom-side pad row for signals.** The board's underside mirrors the iPod's land pattern, but only where a connection is needed (table below). Unneeded positions are covered by solder mask.
3. **Pads left partly exposed.** The board stops short of covering the iPod pads: it overlaps about 1.0 mm of each 1.75 mm pad and leaves about 0.7 mm exposed. A fine-tip iron on the exposed end reflows the pre-tinned joint underneath. Our bottom pads are about 0.25–0.3 mm × 0.8 mm, starting 0.2–0.3 mm in from the edge.
4. **Optional holes in the pads.** A 0.2 mm plated hole in each bottom pad, not covered by solder mask, lets heat and solder in from the top and shows when a joint has taken. Try it on the first prototype.
5. **Alignment.** Pins through the iPod board's two 1.1 mm locating holes set the position before soldering.
6. **Plug force.** USB-C insertion force goes into the case through the bezel insert, not into the fine-pitch joints.

Board thickness: 0.6–0.8 mm, to heat through faster, sit flat and save height.

## Pads on our board

Pad 1 is at x = −7.25 mm, 0.5 mm pitch.

| iPod pin(s) | Signal | Net on our board | x (mm) | Pad |
| --- | --- | --- | --- | --- |
| 1 | Ground | GND | −7.25 | Single |
| 2 | Audio ground | **AGND, isolated** | −6.75 | Single |
| 3 | Line out R | AUD_R+ | −6.25 | Single |
| 4 | Line out L | AUD_L+ | −5.75 | Single |
| 12 | Serial TX (iPod → module) | UART_RX | −1.75 | Single |
| 13 | Serial RX (module → iPod) | UART_TX | −1.25 | Single |
| 15, 16 | Ground, USB ground | GND | −0.25, 0.25 | Merged |
| 18 | 3.3 V accessory power | VACC | 1.25 | Single |
| 21 (optional) | Accessory ID | ACC_ID | 2.75 | Single, only if needed |
| 23 | USB 5 V | VBUS | 3.75 | Single |
| 25 | USB D− | USB_DN | 4.75 | Single |
| 27 | USB D+ | USB_DP | 5.75 | Single |
| 29, 30 | FireWire ground | GND | 6.75, 7.25 | Merged |
| 31, 32 | Shield | GND (verify) | ±11.65 | Castellated |

Pads 1 and 2 are **not** merged: see audio ground below.

## Audio path

**Audio ground stays isolated.** Pin 2 is the iPod's line-out ground. The iPod ties pins 1 and 2 together on its own board, at one point. On our board, pin 2 is its own net (AGND) and never touches the ground plane. Tying it to GND here would put the module's radio and the USB current on the audio reference, and make a ground loop.

**Pseudo-differential pairs.** The iPod's line out is single-ended. The module's line inputs are differential (confirmed for the FSC-BT1035; check the FSC-BT1046 with Feasycom), so each channel is wired as a pair:

```
pad 4 (L) ──R5 100Ω──C6 1µF──┬── MIC_LP
                             C12 100pF
pad 2 (AGND) ─R6 100Ω─C7 1µF─┴── MIC_LN

pad 3 (R) ──R7 100Ω──C8 1µF──┬── MIC_RP
                             C13 100pF
pad 2 (AGND) ─R8 100Ω─C9 1µF─┴── MIC_RN
```

- AGND leaves pad 2 and splits into two return traces, one per channel.
- Route each signal right beside its own return, about equal length, as a tightly coupled pair. Keep the two pairs apart from each other.
- Keep the pairs away from USB D+/D−, the module's RF pin and the antenna. A ground plane underneath is fine as a shield, as long as AGND never connects to it.
- Both legs of each pair get the same parts, so noise picked up along the way stays common-mode and the module's input rejects it.

**RF filter.** R5–R8 (100 Ω) and C12/C13 (100 pF C0G, across each pair at the module pins) form a low-pass filter with a corner around 8 MHz: no effect on audio, but it filters 2.4 GHz picked up from the module's own radio. Fit 0 Ω in place of R5–R8 to bypass it. If line out clips the module's input, R5–R8 can also become an attenuator.

## Checks after soldering

- Continuity from every used iPod pad to its net on our board.
- No shorts: 3–4, 2–3, 1–2 (would undo the AGND isolation), 12–13, and above all 18–19 (3.3 V to FireWire 12 V).
- Pad 18 holds 3.3 V while the module pairs and streams.
