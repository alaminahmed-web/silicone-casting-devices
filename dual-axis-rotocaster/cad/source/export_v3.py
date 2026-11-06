"""v3 export. Fine tessellation, plus pre-split versions of the plate and lid."""
import os, math, sys
import cadquery as cq
from cadquery import exporters
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import rotocaster_v2 as V
import connector, lid as lidmod, counterweight as cw, slipring_parts as sr

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "PRINTED_PARTS")
TOL, ATOL = 0.008, 0.08          # v3: tighter than the 0.1 default

def ex(shape, name, sub=""):
    d = os.path.join(OUT, sub); os.makedirs(d, exist_ok=True)
    s = shape.val() if isinstance(shape, cq.Workplane) else shape
    exporters.export(cq.Workplane(obj=s), os.path.join(d, name + ".stl"),
                     tolerance=TOL, angularTolerance=ATOL)

def solid(w):
    return w.val() if isinstance(w, cq.Workplane) else w

# ---- single-piece parts -------------------------------------------------
ex(V.bearing_fit_gauge(),        "00_TOOL_bearing_fit_test_PRINT_FIRST_x1")
ex(V.bearing_tower(),            "01_POST_bearing_holder_x2")
ex(V.pivot_hub("shaft"),         "02_SHAFT_gripper_x4")
ex(V.bridge_hub(True),           "03_OUTERFRAME_top_bridge_holds_motor2_x1")
ex(V.bridge_hub(False),          "04_OUTERFRAME_bottom_bridge_x1")
ex(V.motor_standoff(),           "05_POST_motor1_spacer_x1")
ex(V.shelf_bracket(),            "06_INNERFRAME_plate_shelf_x2")
ex(cw.counterweight(),           "07_OUTERFRAME_balance_weight_x2")
ex(cw.cover(),                   "07b_OUTERFRAME_balance_weight_COVER_x2")
ex(lidmod.plug(),                "11_MOULD_pour_plug_x1")
ex(sr.slipring_hub(),            "12_SLIPRING_shaft_to_ring_hub_x1")
ex(sr.slipring_tab(),            "13_SLIPRING_stator_anti_turn_x1")
ex(V.motor2_standoff(),          "14_MOTOR2_coupler_standoff_x1")

# ---- whole reference copies --------------------------------------------
plate = connector.connector_plate()
lid_w = lidmod.lid()
ex(plate, "08_MOULD_plate_WHOLE_REFERENCE_do_not_print")
ex(lid_w, "10_MOULD_lid_WHOLE_REFERENCE_do_not_print")

# ---- plate splits (long axis is Y, 300 mm) ------------------------------
def strip(shape, y0, y1):
    box = cq.Workplane("XY").box(400, y1 - y0, 60, centered=(True, True, True)) \
            .translate((0, (y0 + y1) / 2.0, 0))
    return solid(shape).intersect(solid(box))

for i, (y0, y1) in enumerate([(-150, 0), (0, 150)]):
    ex(strip(plate, y0, y1), f"08_MOULD_plate_HALF_{i+1}of2", "SPLIT_bed_256")
for i, (y0, y1) in enumerate([(-150, -50), (-50, 50), (50, 150)]):
    ex(strip(plate, y0, y1), f"08_MOULD_plate_THIRD_{i+1}of3", "SPLIT_bed_126")

# ---- lid splits (pie sectors) -------------------------------------------
def sector(shape, a0, a1, R=260.0):
    pts = [(0, 0)] + [(R * math.cos(math.radians(a)), R * math.sin(math.radians(a)))
                      for a in [a0 + (a1 - a0) * k / 8.0 for k in range(9)]]
    wedge = cq.Workplane("XY").polyline(pts).close().extrude(400).translate((0, 0, -200))
    piece = solid(shape).intersect(solid(wedge))
    return cq.Workplane(obj=piece).rotate((0, 0, 0), (0, 0, 1), -a0)

# Split lines are CLOCKED off the bolt circles. Unrotated, the 90 deg cuts fall
# straight through an M4 plug hole and two M5 rim holes -- a half hole sitting on
# a glued joint, exactly where a bolt clamps. Rim holes sit every 60 deg and plug
# holes every 120, so a 15 deg clock clears every one of them by 15 deg minimum
# (36 mm at the rim radius). Eighths get 22.5 deg for the same reason.
for k in range(4):
    ex(sector(lid_w, 15 + 90 * k, 15 + 90 * (k + 1)), f"10_MOULD_lid_QUARTER_{k+1}of4", "SPLIT_bed_256")
for k in range(8):
    ex(sector(lid_w, 22.5 + 45 * k, 22.5 + 45 * (k + 1)), f"10_MOULD_lid_EIGHTH_{k+1}of8", "SPLIT_bed_126")

print("export complete")
