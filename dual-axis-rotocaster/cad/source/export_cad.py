"""v4: STEP exports and projected views for inspection in Fusion."""
import os, sys
import cadquery as cq
from cadquery import exporters
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rotocaster_v2 as V
import connector, lid as lidmod, counterweight as cw, slipring_parts as sr

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
STEP = os.path.join(ROOT, "STEP"); os.makedirs(STEP, exist_ok=True)
VIEW = os.path.join(ROOT, "VIEWS"); os.makedirs(VIEW, exist_ok=True)

PARTS = {
    "00_bearing_fit_gauge":      V.bearing_fit_gauge(),
    "01_bearing_tower":          V.bearing_tower(),
    "02_shaft_gripper":          V.pivot_hub("shaft"),
    "03_top_bridge":             V.bridge_hub(True),
    "04_bottom_bridge":          V.bridge_hub(False),
    "05_motor1_spacer":          V.motor_standoff(),
    "06_plate_shelf":            V.shelf_bracket(),
    "07_balance_weight":         cw.counterweight(),
    "07b_balance_weight_cover":  cw.cover(),
    "08_mould_plate":            connector.connector_plate(),
    "10_mould_lid":              lidmod.lid(),
    "11_pour_plug":              lidmod.plug(),
    "12_slipring_clamp":         sr.slipring_hub(),
    "13_slipring_arm":           sr.slipring_tab(),
    "14_motor2_standoff":        V.motor2_standoff(),
}

for name, shp in PARTS.items():
    exporters.export(shp, os.path.join(STEP, name + ".step"))

asm = V.build()
asm.save(os.path.join(STEP, "ZZ_full_assembly.step"))

# projected views. The SVG exporter puts model +Z to the right, so everything is
# rotated +90 about Y first to stand the machine up on the page.
def upright(shape, spin=0.0):
    w = cq.Workplane(obj=shape if not isinstance(shape, cq.Workplane) else shape.val())
    if spin:
        w = w.rotate((0, 0, 0), (0, 0, 1), spin)
    return w.rotate((0, 0, 0), (0, 1, 0), 90)

def view(shape, path, spin=0.0, d=(0, -1, 0), w=1100, h=1100, sw=0.5):
    exporters.export(upright(shape, spin), path,
                     opt={"projectionDir": d, "showAxes": False,
                          "strokeWidth": sw, "width": w, "height": h})

comp = asm.toCompound()
view(comp, os.path.join(VIEW, "assembly_front.svg"))
view(comp, os.path.join(VIEW, "assembly_side.svg"), spin=90.0)
view(comp, os.path.join(VIEW, "assembly_three_quarter.svg"), spin=35.0)

print("cad export complete")
