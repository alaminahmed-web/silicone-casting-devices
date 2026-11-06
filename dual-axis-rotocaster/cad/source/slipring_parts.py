"""Slip ring mounts, v3 -- sized from the DIYmore capsule as measured:

  flange  44-45 OD, three holes, 30-33 mm apart centre to centre
  rotor   small stub, 6-7 mm dia, sticks out 9-10 mm
  F       stub tip to flange front, 13-15 mm
  D       overall, 28-30 mm

The flange is the STATOR and bolts to something fixed. The stub is the ROTOR --
its six wires leave the tip, bundled, and must reach Motor 2 on the frame. They
can't go round the tower, so they go through the middle of the RIGHT trunnion,
which must be 8 mm OD tube with a 3 mm bore. Use gripper 02b (pinch clamp) on
that shaft, not a ground D-flat -- a flat would cut the 2.5 mm wall to 1.5.

Measured ranges, not single values, so the design takes the whole range: the
flange sits in radial slots, and the coupler floats axially.
"""
import math
import cadquery as cq
import rotocaster_v2 as V
P = V.P


def slipring_hub(stub_d=7.0):
    """Part 12. Joins the shaft end to the rotor stub. Carries almost no load --
    just the slip ring's own brush friction.

    v4: a square block, not a cylinder. On an 18 mm cylinder the M3 heads sat on
    the curve -- 6 mm of drop across one head, enough to crack the edge. Flat
    faces and a counterbore now give each head a proper seat.

    The six rotor tails leave the stub tip and pass through the 3.5 mm hole in
    the web straight into the shaft's bore. Two M3 x 12 pinch screws, one per
    socket, self-tapping into the far jaw. No nuts.
    """
    # v6: 25 wide, pinch screws at y = 7.5 -- at 22 / 6.5 the wall to the
    # 8.4 shaft bore was 0.68 mm, under the shop's 1.2 mm minimum.
    B, L = 25.0, 20.0
    SY = 7.5
    b = cq.Workplane("XY").box(B, B, L, centered=(True, True, False))
    b = b.cut(cq.Workplane("XY").circle(4.2).extrude(10.0).translate((0, 0, -0.01)))   # shaft 8.4
    b = b.cut(cq.Workplane("XY").circle(1.75).extrude(2.2).translate((0, 0, 9.9)))     # wires 3.5
    # v5: stub bore per variant - the stub measured 6-7 mm, clamp closes ~0.5.
    b = b.cut(cq.Workplane("XY").circle((stub_d + 0.2) / 2.0).extrude(8.01).translate((0, 0, 12.0)))
    b = b.cut(cq.Workplane("XY").box(1.6, B / 2.0 + 1, L + 2, centered=(True, False, False))
              .translate((0, 0, -1.0)))                                                 # slot to +Y face
    for z in (5.0, 16.0):
        b = b.cut(cq.Workplane("YZ").circle(3.25).extrude(B / 2.0 - 5.0 + 0.01).translate((-B / 2.0 - 0.01, SY, z)))
        b = b.cut(cq.Workplane("YZ").circle(1.7).extrude(4.3).translate((-5.05, SY, z)))
        b = b.cut(cq.Workplane("YZ").circle(1.3).extrude(B / 2.0 - 0.75 + 0.3).translate((0.75, SY, z)))
    return b


def slipring_tab():
    """Part 13. Holds the flange still, coaxial with the shaft.

    v4: the flange now bolts to the plate's OUTBOARD face. Previously it sat on
    the inboard face, trapping all three screws between base and plate with no
    straight approach -- and the slip ring would have had to enter through a
    36 mm side gap past a 44.5 mm flange. Now it goes in from outside, stub
    first, through the 23 mm bore, and the flange stops against the plate.
    Screws drive from outside; nuts sit on the inboard face, reached from the
    open sides.

    Base bolts to the RIGHT tower on the free 56 x 46 M5 pattern. Radial slots
    take any flange hole spacing from 30 to 33 mm, at any rotation.
    """
    BASE_T, REACH, PL_T = 6.0, 36.0, 5.0
    base = cq.Workplane("XY").box(70.0, 72.0, BASE_T, centered=(True, True, False))
    base = base.faces("<Z").workplane().rarray(56.0, 46.0, 2, 2).hole(5.4)
    base = base.cut(cq.Workplane("XY").circle(7.0).extrude(BASE_T + 2).translate((0, 0, -1)))
    arms = None
    for sy in (-1, 1):
        a = (cq.Workplane("XY").box(44.0, 8.0, REACH - BASE_T + 0.5, centered=(True, True, False))
             .translate((0, sy * 30.0, BASE_T - 0.25)))
        arms = a if arms is None else arms.union(a)
    plate = (cq.Workplane("XY").box(44.0, 72.0, PL_T, centered=(True, True, False))
             .translate((0, 0, REACH)))
    b = base.union(arms).union(plate)
    b = b.cut(cq.Workplane("XY").circle(11.5).extrude(PL_T + 2).translate((0, 0, REACH - 1)))
    for k in range(3):
        ang = math.radians(90 + 120 * k)
        slot = (cq.Workplane("XY").slot2D(2.5 + 3.4, 3.4, 0).extrude(PL_T + 2)
                .rotate((0, 0, 0), (0, 0, 1), math.degrees(ang))
                .translate((18.25 * math.cos(ang), 18.25 * math.sin(ang), REACH - 1)))
        b = b.cut(slot)
    return b


PARTS = {"slipring_hub": slipring_hub(), "slipring_tab": slipring_tab()}
