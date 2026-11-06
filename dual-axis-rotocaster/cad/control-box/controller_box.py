"""
Rotocaster controller box: Arduino Uno + L298N + 1.30" OLED + 2 pots + run switch.

Run:  python controller_box.py        -> writes body.stl, lid_print.stl, assembly.step
All dimensions in mm. Edit the PARAMETERS block, re-run, reprint.

Coordinates: inner cavity origin (0,0) at the lower-left inside corner, x along the
length, y along the width, z up from the OUTER bottom of the box.
Left wall (x<0): USB hole.  Right wall (x>IL): adapter-cable and motor-cable holes.
"""
import cadquery as cq
import os

OUT = os.path.dirname(os.path.abspath(__file__))

# ------------------------------ PARAMETERS ---------------------------------
# Box
IL, IW, IH = 160.0, 90.0, 60.0     # inner length, width, height (roomy on purpose)
WALL, FLOOR, LID_T = 3.0, 3.0, 5.0
BOSS_D, BOSS_PILOT = 8.0, 2.6       # corner screw bosses (M3 self-tapping)
CORNER = 4.5                        # boss centre distance from inner corner

# Arduino Uno (68.6 x 53.4). USB end faces the left wall.
UNO_L, UNO_W = 68.6, 53.4
UNO_X0 = 7.0
UNO_Y0 = (IW - UNO_W) / 2
UNO_HOLES = [(14.0, 2.5), (15.3, 50.7), (66.1, 7.6), (66.1, 35.5)]
UNO_USB_Y = 38.1                    # USB-B centre, from board bottom edge   (CHECK)
STANDOFF_H = 6.0
STANDOFF_D = 6.5
USB_HOLE_W, USB_HOLE_H = 16.0, 14.0 # generous: cable boots are bigger than the jack

# L298N module 43 x 43, rotated so its power terminals face the right wall
L_SIZE = 43.0
L_X0 = 95.0
L_Y0 = (IW - L_SIZE) / 2
L_HOLE_SPACING = 37.0               # mounting holes square          (CHECK WITH CALIPER)

# Cables through right wall
ADAPTER_D, ADAPTER_Y = 10.0, 28.0
MOTOR_D, MOTOR_Y = 16.0, 68.0
CABLE_Z = FLOOR + STANDOFF_H + 12.0

# OLED 1.30" board 36 x 34 mm, glass window
OLED_PCB = (36.0, 34.0)
OLED_POCKET = (36.6, 34.6)          # pocket = board + clearance
OLED_POCKET_DEPTH = 2.8
OLED_WIN = (32.0, 17.5)             # screen is 14.7 mm tall; window gives margin
OLED_WIN_DY = 2.2                   # active area sits towards the pin-header edge
OLED_XY = (32.0, IW / 2)

# Controls on the lid (x, y in cavity coordinates)
POT_D = 7.5                         # panel pot bushing, M7                (CHECK)
POT_XY = [(85.0, IW / 2), (115.0, IW / 2)]
POT_NUT_RECESS = (14.0, 2.5)        # dia, depth: nut sits in a recess so short bushing threads still reach
SW_HOLE = (15.2, 10.3)              # 15 x 10 mm snap-in rocker (x along the length)
SW_PANEL_T = 1.6                    # snap-in tabs need a thin panel: lid is thinned here
SW_RECESS = (23.0, 18.0)            # recess behind the switch on the inner face
SW_XY = (145.0, IW / 2)

# Title text engraved on the lid, centred at x = lid centre, above the controls
ENGRAVE = 0.6
TITLE_LINES = ["URM / BIOFLUID LAB", "SILICON ROTOCASTER CONTROLLER", "DR. ZAHRAN"]
TITLE_POS = [(IL / 2, 86.0, 6.0), (IL / 2, 77.0, 6.0), (IL / 2, 68.5, 5.0)]   # x, y, size

# 2020-rail mounting ears (M5 T-nuts), along the long axis
EARS = False                        # no rail ears: box is screwed to the wooden base instead

# Four countersunk holes through the floor for wood screws into the plywood base.
# Reached from inside with the lid off; positions clear both boards (y < 18 or y > 72).
FLOOR_SCREWS = [(40.0, 9.0), (40.0, IW - 9.0), (120.0, 9.0), (120.0, IW - 9.0)]
FLOOR_SCREW_D, FLOOR_SCREW_HEAD = 4.5, 8.5   # shank clearance, countersink head dia
EAR_L, EAR_W, EAR_T, EAR_HOLE = 18.0, 26.0, 4.0, 5.5

# Ventilation slots on front and back walls (L298N heats up)
VENTS = True
# ---------------------------------------------------------------------------

TOP_Z = FLOOR + IH


def box(x0, x1, y0, y1, z0, z1):
    return (cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False)
            .translate((x0, y0, z0)))


def cyl_z(x, y, z0, h, d):
    return cq.Workplane("XY").workplane(offset=z0).center(x, y).circle(d / 2).extrude(h)


def hole_x(x0, length, y, z, d=None, w=None, h=None):
    wp = cq.Workplane("YZ").workplane(offset=x0).center(y, z)
    wp = wp.circle(d / 2) if d else wp.rect(w, h)
    return wp.extrude(length)


def hole_y(y0, length, x, z, w, h):
    return (cq.Workplane("XZ").workplane(offset=-y0).center(x, z).rect(w, h)
            .extrude(-length))


def corners():
    return [(CORNER, CORNER), (IL - CORNER, CORNER),
            (CORNER, IW - CORNER), (IL - CORNER, IW - CORNER)]


def uno_hole_xy():
    return [(UNO_X0 + hx, UNO_Y0 + hy) for hx, hy in UNO_HOLES]


def l298_hole_xy():
    cx, cy = L_X0 + L_SIZE / 2, L_Y0 + L_SIZE / 2
    s = L_HOLE_SPACING / 2
    return [(cx - s, cy - s), (cx + s, cy - s), (cx - s, cy + s), (cx + s, cy + s)]


# ------------------------------- BODY --------------------------------------
def make_body():
    b = box(-WALL, IL + WALL, -WALL, IW + WALL, 0, TOP_Z)
    b = b.cut(box(0, IL, 0, IW, FLOOR, TOP_Z + 1))

    for x, y in corners():                                   # lid screw bosses
        b = b.union(cyl_z(x, y, FLOOR, IH, BOSS_D))
    for x, y in corners():
        b = b.cut(cyl_z(x, y, TOP_Z - 12, 13, BOSS_PILOT))

    for x, y in uno_hole_xy() + l298_hole_xy():              # board standoffs
        b = b.union(cyl_z(x, y, FLOOR, STANDOFF_H, STANDOFF_D))
        b = b.cut(cyl_z(x, y, FLOOR + STANDOFF_H - 8, 9, BOSS_PILOT))

    # USB hole in the left wall, aligned with the Uno USB-B jack
    usb_y = UNO_Y0 + UNO_USB_Y
    usb_z = FLOOR + STANDOFF_H + 1.6 + 5.5
    b = b.cut(hole_x(-WALL - 1, WALL + 2, usb_y, usb_z, w=USB_HOLE_W, h=USB_HOLE_H))

    # Cable holes in the right wall
    b = b.cut(hole_x(IL - 1, WALL + 2, ADAPTER_Y, CABLE_Z, d=ADAPTER_D))
    b = b.cut(hole_x(IL - 1, WALL + 2, MOTOR_Y, CABLE_Z, d=MOTOR_D))

    if VENTS:
        for i in range(6):
            x = 100 + i * 7
            for wall_y in (-WALL - 1, IW - 1):
                b = b.cut(hole_y(wall_y, WALL + 2, x, FLOOR + 38, 3.0, 20.0))

    for x, y in FLOOR_SCREWS:
        b = b.cut(cyl_z(x, y, -1, FLOOR + 2, FLOOR_SCREW_D))
        cone = cq.Solid.makeCone(FLOOR_SCREW_D / 2, FLOOR_SCREW_HEAD / 2, 2.0,
                                 cq.Vector(x, y, FLOOR - 2.0), cq.Vector(0, 0, 1))
        b = b.cut(cone)

    if EARS:
        for side in (-1, 1):
            if side < 0:
                x0, x1 = -WALL - EAR_L, -WALL + 0.5
                hx = -WALL - EAR_L / 2
            else:
                x0, x1 = IL + WALL - 0.5, IL + WALL + EAR_L
                hx = IL + WALL + EAR_L / 2
            ear = box(x0, x1, IW / 2 - EAR_W / 2, IW / 2 + EAR_W / 2, 0, EAR_T)
            slot = (cq.Workplane("XY").center(hx, IW / 2).slot2D(EAR_HOLE + 5, EAR_HOLE, 0)
                    .extrude(EAR_T + 2).translate((0, 0, -1)))
            b = b.union(ear).cut(slot)
    return b


# -------------------------------- LID --------------------------------------
# Built in assembled orientation: inner face z=0, outer (top) face z=LID_T.
def make_lid():
    lid = box(-WALL, IL + WALL, -WALL, IW + WALL, 0, LID_T)

    ox, oy = OLED_XY
    lid = lid.cut(box(ox - OLED_POCKET[0] / 2, ox + OLED_POCKET[0] / 2,
                      oy - OLED_POCKET[1] / 2, oy + OLED_POCKET[1] / 2,
                      -1, OLED_POCKET_DEPTH))
    wy = oy + OLED_WIN_DY
    lid = lid.cut(box(ox - OLED_WIN[0] / 2, ox + OLED_WIN[0] / 2,
                      wy - OLED_WIN[1] / 2, wy + OLED_WIN[1] / 2, -1, LID_T + 1))

    for x, y in POT_XY:
        lid = lid.cut(cyl_z(x, y, -1, LID_T + 2, POT_D))
        lid = lid.cut(cyl_z(x, y, LID_T - POT_NUT_RECESS[1], POT_NUT_RECESS[1] + 1,
                            POT_NUT_RECESS[0]))
    sx, sy = SW_XY
    lid = lid.cut(box(sx - SW_RECESS[0] / 2, sx + SW_RECESS[0] / 2,       # thin the panel
                      sy - SW_RECESS[1] / 2, sy + SW_RECESS[1] / 2,
                      -1, LID_T - SW_PANEL_T))
    lid = lid.cut(box(sx - SW_HOLE[0] / 2, sx + SW_HOLE[0] / 2,           # rocker cutout
                      sy - SW_HOLE[1] / 2, sy + SW_HOLE[1] / 2, -1, LID_T + 1))

    for x, y in corners():
        lid = lid.cut(cyl_z(x, y, -1, LID_T + 2, 3.4))
        lid = lid.cut(cyl_z(x, y, LID_T - 2.5, 3, 6.6))      # screw head recess

    # Engraved text (skipped silently if no font is available)
    labels = [(t, x, y, s) for t, (x, y, s) in zip(TITLE_LINES, TITLE_POS)]
    labels += [("OUTER", POT_XY[0][0], POT_XY[0][1] - 20, 4.5),
               ("INNER", POT_XY[1][0], POT_XY[1][1] - 20, 4.5),
               ("RUN", SW_XY[0], SW_XY[1] - 20, 4.5)]
    for txt, x, y, size in labels:
        try:
            t = (cq.Workplane("XY").workplane(offset=LID_T).center(x, y)
                 .text(txt, size, -ENGRAVE, combine=False, kind="bold",
                       halign="center", valign="center"))
            lid = lid.cut(t)
        except Exception as e:
            print("label skipped:", txt, e)
    return lid


def lid_for_print(lid):
    """Outer face down on the bed."""
    return lid.rotate((0, 0, 0), (1, 0, 0), 180).translate((0, 0, LID_T))


# --------------------------- fit checks (dummies) ---------------------------
def dummies():
    d = {}
    z_uno = FLOOR + STANDOFF_H
    d["uno_pcb"] = box(UNO_X0, UNO_X0 + UNO_L, UNO_Y0, UNO_Y0 + UNO_W, z_uno, z_uno + 1.6)
    d["uno_headers"] = box(UNO_X0 + 10, UNO_X0 + UNO_L - 10, UNO_Y0 - 1, UNO_Y0 + UNO_W + 1,
                           z_uno + 1.6, z_uno + 1.6 + 9)
    d["usb_jack"] = box(UNO_X0 - 6, UNO_X0 + 10, UNO_Y0 + UNO_USB_Y - 6, UNO_Y0 + UNO_USB_Y + 6,
                        z_uno + 1.6, z_uno + 1.6 + 11)
    # USB plug incl. boot, passing through the wall hole
    d["usb_plug"] = box(-30, UNO_X0 - 6, UNO_Y0 + UNO_USB_Y - 7.5, UNO_Y0 + UNO_USB_Y + 7.5,
                        z_uno + 1.6 + 5.5 - 6.5, z_uno + 1.6 + 5.5 + 6.5)
    z_l = FLOOR + STANDOFF_H
    d["l298_pcb"] = box(L_X0, L_X0 + L_SIZE, L_Y0, L_Y0 + L_SIZE, z_l, z_l + 1.6)
    d["l298_heatsink"] = box(L_X0 + 10, L_X0 + 35, L_Y0 + 5, L_Y0 + 38, z_l + 1.6, z_l + 1.6 + 27)
    d["adapter_cable"] = hole_x(IL - 5, 30, ADAPTER_Y, CABLE_Z, d=ADAPTER_D - 0.5)
    d["motor_cable"] = hole_x(IL - 5, 30, MOTOR_Y, CABLE_Z, d=MOTOR_D - 0.5)
    for i, (x, y) in enumerate(POT_XY):                     # pot body hanging below lid
        d[f"pot{i+1}"] = cyl_z(x, y, TOP_Z - 20, 20, 17)
    d["switch"] = box(SW_XY[0] - 8, SW_XY[0] + 8, SW_XY[1] - 6, SW_XY[1] + 6,
                      TOP_Z - 25, TOP_Z)
    return d


def vol(s):
    return s.val().Volume()


def check(body, lid_assembled):
    ok = True
    lid_pos = lid_assembled.translate((0, 0, TOP_Z))
    for name, solid in dummies().items():
        hit_body = vol(body.intersect(solid))
        hit_lid = vol(lid_pos.intersect(solid))
        # Pots / switch are meant to pass through the lid; skip lid test for those.
        if name.startswith(("pot", "switch")):
            hit_lid = 0
        flag = "OK " if hit_body < 0.5 and hit_lid < 0.5 else "HIT"
        if flag == "HIT":
            ok = False
        print(f"  {flag} {name:14s} body={hit_body:8.1f} mm3  lid={hit_lid:8.1f} mm3")
    # Internal boards vs each other
    d = dummies()
    for a, b in [("uno_headers", "l298_heatsink"), ("uno_pcb", "l298_pcb")]:
        v = vol(d[a].intersect(d[b]))
        print(f"  {'OK ' if v < 0.5 else 'HIT'} {a} vs {b}: {v:.1f}")
        ok &= v < 0.5
    return ok


if __name__ == "__main__":
    import sys
    if "lid" in sys.argv:                       # quick path: lid only, no body, no checks
        lid = make_lid()
        cq.exporters.export(lid_for_print(lid), os.path.join(OUT, "lid_print.stl"),
                            tolerance=0.02, angularTolerance=0.1)
        print("lid written to", OUT)
        sys.exit(0)
    body = make_body()
    lid = make_lid()
    print("Fit checks:")
    ok = check(body, lid)
    print("ALL CLEAR" if ok else "PROBLEMS FOUND")

    cq.exporters.export(body, os.path.join(OUT, "body.stl"), tolerance=0.02, angularTolerance=0.1)
    cq.exporters.export(lid_for_print(lid), os.path.join(OUT, "lid_print.stl"),
                        tolerance=0.02, angularTolerance=0.1)
    asm = cq.Assembly().add(body, name="body").add(lid.translate((0, 0, TOP_Z)), name="lid")
    asm.save(os.path.join(OUT, "assembly.step"))

    bb = body.val().BoundingBox()
    print(f"body  : {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm (with ears)")
    lb = lid.val().BoundingBox()
    print(f"lid   : {lb.xlen:.1f} x {lb.ylen:.1f} x {lb.zlen:.1f} mm")
    print("written to", OUT)
