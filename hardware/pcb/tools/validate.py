"""Parse the generated KiCad files and check structure and connectivity."""
import collections
import re
import sys

d = sys.argv[1]


def parse(text):
    tok = re.findall(r'"(?:[^"\\]|\\.)*"|\(|\)|[^\s()"]+', text)
    stack, cur = [], []
    for t in tok:
        if t == "(":
            stack.append(cur)
            cur = []
        elif t == ")":
            done = cur
            cur = stack.pop()
            cur.append(done)
        else:
            cur.append(t[1:-1] if t.startswith('"') else t)
    assert not stack, "unbalanced"
    assert len(cur) == 1
    return cur[0]


def find(node, head):
    return [c for c in node if isinstance(c, list) and c and c[0] == head]


pcb = parse(open(d + "/rockpod-bt-board.kicad_pcb").read())
assert pcb[0] == "kicad_pcb"
netdefs = {int(n[1]): n[2] for n in find(pcb, "net")}
fps = find(pcb, "footprint")
pad_nets = collections.defaultdict(list)
uuids = []
for fp in fps:
    ref = [p[2] for p in find(fp, "property") if p[1] == "Reference"][0]
    for pad in find(fp, "pad"):
        n = find(pad, "net")
        if n:
            nid, name = int(n[0][1]), n[0][2]
            assert netdefs[nid] == name, (ref, nid, name)
            pad_nets[name].append("%s.%s" % (ref, pad[1]))
edges = find(pcb, "gr_line")
cuts = [e for e in edges if find(e, "layer")[0][1] == "Edge.Cuts"]
print("PCB ok: %d footprints, %d nets, %d Edge.Cuts segments, %d zones" % (
    len(fps), len(netdefs), len(cuts), len(find(pcb, "zone"))))
# outline closed?
pts = collections.Counter()
for e in cuts:
    for k in ("start", "end"):
        xy = tuple(find(e, k)[0][1:3])
        pts[xy] += 1
assert all(v == 2 for v in pts.values()), "outline not closed"
print("outline closed:", len(pts), "corners")

sch = parse(open(d + "/rockpod-bt-board.kicad_sch").read())
assert sch[0] == "kicad_sch"
libs = {s[1] for s in find(find(sch, "lib_symbols")[0], "symbol")}
syms = find(sch, "symbol")
for s in syms:
    assert find(s, "lib_id")[0][1] in libs
labels = find(sch, "label")
wires = find(sch, "wire")
ncs = find(sch, "no_connect")
lab_nets = collections.Counter(l[1] for l in labels)
print("SCH ok: %d symbols, %d lib symbols, %d wires, %d labels, %d no-connects" % (
    len(syms), len(libs), len(wires), len(labels), len(ncs)))
# schematic label nets == pcb nets
sch_nets = set(lab_nets)
pcb_nets = set(pad_nets)
print("nets only in SCH:", sorted(sch_nets - pcb_nets))
print("nets only in PCB:", sorted(pcb_nets - sch_nets))
for n in sorted(pad_nets):
    if len(pad_nets[n]) < 2:
        print("single-pad net:", n, pad_nets[n])
print("AGND pads:", pad_nets["AGND"])
print("GND pad count:", len(pad_nets["GND"]))
