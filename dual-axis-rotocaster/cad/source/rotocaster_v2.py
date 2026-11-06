"""
Dual-Axis Silicone Mould Rotating Device - VERSION 2 (buildable)

V2 replaces V1's large one-piece printed frames with 2020 aluminium extrusion
rails joined by SMALL printed brackets. Every printed part fits a 220x220x250
bed with margin. Nothing printed is longer than ~190 mm.

  Outer axis = global X (horizontal, through the uprights)
  Inner axis = global Z (vertical, through the outer frame top/bottom rails)
  Origin     = intersection of both axes = centre of the mould

Run this file to print the derived sizes and the rail cut list.
"""

import cadquery as cq
from cadquery import exporters
import math
import os

# ---------------------------------------------------------------------------
# PARAMETERS
# ---------------------------------------------------------------------------
P = {
    # --- the mould (CHANGE THESE FIRST) ---
    "mould_dia": 300.0,      # Dr Zahran
    "mould_height": 300.0,

    # --- 2020 extrusion ---
    "ext": 20.0,
    "ext_slot": 6.2,
    "ext_bore": 4.2,

    # --- printed joint proportions ---
    "sock_clear": 0.35,        # per-side clearance on extrusion sockets
    "wall": 5.0,               # printed wall around a socket
    "sock_depth": 45.0,        # how far a rail enters a bracket
    "arm": 62.0,               # bracket arm length


    # --- mould holder: ONE plate, the mould bolts onto it ---
    "plate_t": 8.0,
    "plate_sz": 240.0,       # prints on the A1 in one piece

    # --- clearances ---
    "inner_clear_z": 18.0,
    "outer_clear_x": 33.35,
    "outer_clear_z": 24.0,
    "ground_clear": 38.0,

    # --- bearings and shafts ---
    "shaft_dia": 8.0,
    "bearing_od": 22.2,   # v3: set from part 00 gauge, 22.2 pocket was the fit
    "bearing_w": 7.0,

    # --- JGY-370 worm gearmotor ---
    "gm_box_x": 46.0,        # JGY-370 4632 gearbox, measured from the datasheet
    "gm_box_y": 32.0,
    "gm_box_z": 25.2,   # gearbox height from the drawing
    "gm_hole_x": 18.0,       # from the JGY-370 4632 dimensioned drawing
    "gm_hole_y": 33.0,
    "gm_hole_d": 3.4,        # M3 clearance
    "gm_body_dia": 24.4,
    "gm_body_len": 30.8,

    # --- slip ring ---
    "sr_dia": 22.0,
    "sr_len": 40.0,

    # --- base ---
    "base_t": 15.0,
    "base_margin_x": 60.0,
    "base_y": 340.0,
    "post_extra": 0.0,

    # --- printer, used by the self check ---
    "bed": (256.0, 256.0, 256.0),   # Bambu Lab A1
}


def derive(p):
    d = {}
    e = p["ext"]
    mh = p["mould_height"] / 2.0

    # --- single mounting plate, mould bolts onto it ---
    d["plate_sz"] = p["plate_sz"]
    d["plate_bot_z"] = -mh - p["plate_t"]
    d["inner_open_y"] = p["mould_dia"] + 20.0
    d["inner_open_z"] = 2.0 * (mh + p["plate_t"] + 30.0)

    # --- inner frame: 2020 rectangle in the YZ plane, pivots about Z ---
    d["inner_in_y"] = d["inner_open_y"]
    d["inner_in_z"] = d["inner_open_z"]
    d["inner_out_y"] = d["inner_in_y"] + 2 * e
    d["inner_out_z"] = d["inner_in_z"] + 2 * e

    # radius swept about Z (brackets protrude past the rail, so allow for them)
    brk = p["wall"] + p["sock_clear"]
    d["inner_sweep_r"] = max(
        math.hypot(e / 2.0 + brk, d["inner_out_y"] / 2.0),
        p["mould_dia"] / 2.0,
    )

    # --- outer frame: 2020 rectangle in the XZ plane, pivots about X ---
    d["outer_in_x"] = 2.0 * (d["inner_sweep_r"] + p["outer_clear_x"])
    d["hub_proj"] = 16.0
    d["outer_in_z"] = d["inner_out_z"] + 2 * (d["hub_proj"] + p["outer_clear_z"])
    d["outer_out_x"] = d["outer_in_x"] + 2 * e
    d["outer_out_z"] = d["outer_in_z"] + 2 * e

    # --- rail cut lengths ---
    # BOUGHT flat L corner plates: the rails BUTT, so verticals run the full
    # outside height and horizontals fit between them. Nothing is subtracted for
    # bracket overlap - that only applied to the old printed sockets.
    d["rail_outer_v"] = d["outer_out_z"]
    d["rail_outer_h"] = d["outer_out_x"] - 2 * e
    d["outer_seg"] = (d["rail_outer_h"] - 60.0) / 2.0   # 60 mm gap in the bridge hub
    d["rail_inner_v"] = d["inner_out_z"]
    d["rail_inner_h"] = d["inner_out_y"] - 2 * e

    # --- motor 2 on the outer frame top rail ---
    d["m2_rail_z"] = d["outer_out_z"] / 2.0 - e / 2.0 + 17.0 + 34.0 + 33.0  # v4: +33 for part 14
    d["m2_top_z"] = d["m2_rail_z"] + p["gm_box_z"]

    d["outer_sweep_r"] = max(
        math.hypot(e / 2.0 + brk, d["outer_out_z"] / 2.0 + d["hub_proj"]),
        math.hypot(35.0, d["outer_out_z"] / 2.0 - e / 2.0 + 17.0 + 36.0 + 25.0),
        math.hypot(d["inner_out_y"] / 2.0, d["inner_out_z"] / 2.0 + d["hub_proj"]),
    )

    # --- structure ---
    d["axis_height"] = d["outer_sweep_r"] + p["ground_clear"]
    d["base_top_z"] = -d["axis_height"]
    d["upright_x"] = d["outer_out_x"] / 2.0 + d["hub_proj"] + 74.0 / 2.0 + 18.0
    d["post_len"] = d["axis_height"] - 24.0      # cap socket takes the top 52 mm
    d["base_x"] = 2.0 * (d["upright_x"] + p["base_margin_x"])
    return d


HUB_PROJ = 16.0
MOTOR_HUB_PROJ = 48.0   # taller hub on the top rail, houses the coupler
TOWER_W = 74.0
D = derive(P)


# ---------------------------------------------------------------------------
# BUILDING BLOCKS
# ---------------------------------------------------------------------------
def extrusion(length, axis="X"):
    """Simplified 2020 profile: square section with a central bore and 4 slots."""
    e = P["ext"]
    prof = (
        cq.Workplane("XY").rect(e, e).extrude(length)
        .faces(">Z").workplane().hole(P["ext_bore"])
    )
    for ang in (0, 90, 180, 270):
        cutter = (
            cq.Workplane("XY")
            .center(0, e / 2.0 - 1.2)
            .rect(P["ext_slot"], 3.0)
            .extrude(length)
            .rotate((0, 0, 0), (0, 0, 1), ang)
        )
        prof = prof.cut(cutter)
    if axis == "X":
        prof = prof.rotate((0, 0, 0), (0, 1, 0), 90)
    elif axis == "Y":
        prof = prof.rotate((0, 0, 0), (1, 0, 0), -90)
    return prof


def safe_fillet(shp, sel="|Z", r=3.0):
    """Fillet if OCCT can manage it, otherwise leave the edges sharp."""
    for rad in (r, r * 0.6, r * 0.3):
        try:
            return shp.edges(sel).fillet(rad)
        except Exception:
            continue
    return shp


def _socket(depth):
    s = P["ext"] + 2 * P["sock_clear"]
    return cq.Workplane("XY").rect(s, s).extrude(depth)


def corner_bracket():
    """Printed L bracket: two sockets at 90 deg. Rails enter along +X and +Y."""
    e, w, arm, dep = P["ext"], P["wall"], P["arm"], P["sock_depth"]
    sec = e + 2 * w
    a = (
        cq.Workplane("XY")
        .box(arm, sec, sec, centered=(False, True, True))
        .union(cq.Workplane("XY").box(sec, arm, sec, centered=(True, False, True)))
    )
    a = a.cut(_socket(dep).rotate((0, 0, 0), (0, 1, 0), 90)
              .translate((arm - dep, 0, 0)))
    a = a.cut(_socket(dep).rotate((0, 0, 0), (1, 0, 0), -90)
              .translate((0, arm - dep, 0)))
    # M5 clamp screws into each rail's end bore
    a = (a.faces(">Z").workplane(centerOption="CenterOfBoundBox")
         .pushPoints([(arm / 2.0 - 4, 0), (0, arm / 2.0 - 4)]).hole(5.4))
    return safe_fillet(a, "|Z", 3.0)


def pivot_hub(mode):
    """Straddles a 2020 rail as a U-channel. Protrudes only HUB_PROJ above it.

    mode='bearing' seats a 608 (receives a shaft), 'shaft' clamps an M8 stub.
    """
    e, w = P["ext"], P["wall"]
    L, cap = 72.0, HUB_PROJ
    wd = e + 2 * w
    body = cq.Workplane("XY").box(L, wd, e + cap, centered=(True, True, False))
    channel = cq.Workplane("XY").box(L + 2, e + 2 * P["sock_clear"], e,
                                     centered=(True, True, False))
    body = body.cut(channel)
    if mode == "bearing":
        body = body.faces(">Z").workplane().hole(P["bearing_od"], 8.0)
        body = body.faces(">Z").workplane().hole(P["shaft_dia"] + 2.0)
    else:
        # D-shaped bore. A plain round hole would let the shaft spin freely and
        # the frame would never turn. The flat is what actually carries torque.
        r = P["shaft_dia"] / 2.0 + 0.15
        flat = r - 1.0                       # 1 mm flat filed on the shaft
        body = body.faces(">Z").workplane().hole(P["shaft_dia"] + 0.3)
        key = (cq.Workplane("XY")
               .box(2 * r, r - flat, e + cap + 2, centered=(True, False, False))
               .translate((0, flat, -1.0)))
        body = body.union(key)
    body = (body.faces(">Z").workplane()
            .pushPoints([(-28, 0), (28, 0)]).hole(5.4))
    return safe_fillet(body, "|Z", 4.0)


def pivot_hub_clamp():
    """Part 02 alternative: PINCH CLAMP, for plain round shaft with no D-flat.

    Grips a plain 8 mm shaft by squeezing a split bore, the same principle the
    slip ring clamp uses. Needs no machining on the shaft at all.

    Honest limits: a printed clamp on hardened steel gives roughly 1-2 N.m.
    Motor 1 makes 1.27 N.m loaded and 2.06 N.m stalled, so this holds in normal
    running but can slip on a stall. It also self-limits, which is not the worst
    failure mode -- but you lose position.

    The bore keeps a shallow D-relief at 3.4 mm from the axis. If you manage even
    a rough 0.6 mm ground flat, it drops in and you get positive drive on top of
    the clamp. Round shaft still fits; the relief just sits empty.
    """
    e, w, cap = P["ext"], P["wall"], HUB_PROJ
    # v16: 34 wide, not 30. At 30 the side walls under the cap were only
    # 4.65 mm, and the pinch peeled them off the cap along the z = 20 layer
    # line on the first test print. Now 6.65 mm. Clearance checked: the
    # trunnion grippers sit at |x| >= 214, outside the inner frame's 180.65
    # sweep, and the inner-stub grippers are 17 mm below part 03.
    L, wd = 72.0, 34.0
    CAP_L, BORE = 40.0, 8.4
    base = cq.Workplane("XY").box(L, wd, e, centered=(True, True, False))
    top = (cq.Workplane("XY").box(CAP_L, wd, cap, centered=(True, True, False))
           .translate((0, 0, e)))
    b = base.union(top)
    b = b.cut(cq.Workplane("XY").box(L + 2, e + 2 * P["sock_clear"], e,
                                     centered=(True, True, False)))
    b = b.cut(cq.Workplane("XY").circle(BORE / 2.0).extrude(cap + 2)
              .translate((0, 0, e - 1.0)))
    # shallow D-relief: engages a 0.6 mm flat, ignored by round shaft
    b = b.cut(cq.Workplane("XY")
              .box(BORE, BORE / 2.0 - 3.4, cap + 2, centered=(True, False, False))
              .translate((0, 3.4, e - 1.0)))
    # radial slot, opening the bore to the +Y face. Runs 2 mm past the axis so
    # the hinge web is thin enough to actually close.
    # v16: the slot starts AT the cap (z = e), not 1 mm into the side walls.
    # That 1 mm notch sat exactly on the joint that failed.
    b = b.cut(cq.Workplane("XY").box(1.6, wd / 2.0 + 3.0, cap + 1, centered=(True, False, False))
              .translate((0, -2.0, e)))
    # M4 pinch screw across the slot, head recessed one end, nut the other
    b = b.cut(cq.Workplane("XY").circle(2.2).extrude(CAP_L + 4)
              .rotate((0, 0, 0), (0, 1, 0), 90).translate((-CAP_L / 2.0 - 2, 9.0, e + 8.0)))
    b = b.cut(cq.Workplane("XY").circle(4.0).extrude(9.0)
              .rotate((0, 0, 0), (0, 1, 0), 90).translate((-CAP_L / 2.0 - 1, 9.0, e + 8.0)))
    # M5 into the rail slot. Moved in to +-15 so they clear the shortened cap.
    b = (b.faces(">Z").workplane(centerOption="CenterOfBoundBox")
         .pushPoints([(-15, 0), (15, 0)]).hole(5.4))
    return b


def bridge_hub(with_motor=False):
    """Joins two SHORT rails end to end and carries the inner pivot bearing.

    v4, fault #18. The old with_motor variant put two legs 8.0 mm apart and
    expected the 6->8 coupler to live between them. An 8.0 mm slot will not pass
    an 8.0 mm shaft, let alone a ~20 mm coupler, and the grub screws were
    unreachable. The coupler now lives ABOVE the top plate on part 14, so the
    space between the legs is no longer needed for anything.

    The legs are therefore replaced by a solid pillar with the shaft bore running
    straight through it, and a SECOND 608 goes in the top plate. The shaft is now
    carried on two bearings 53 mm apart instead of cantilevering off one.
    """
    e = P["ext"]
    sec = e + 14.0                 # 34 mm square section, 6 mm wall round the bearing
    L, sock = 150.0, 45.0
    body = cq.Workplane("XY").box(L, sec, sec, centered=(True, True, True))
    for sx in (-1, 1):
        sk = (cq.Workplane("XY")
              .box(2 * sock, e + 2 * P["sock_clear"], e + 2 * P["sock_clear"],
                   centered=(True, True, True))
              .translate((sx * L / 2.0, 0, 0)))
        body = body.cut(sk)
    # v3 FIX: fillet the main body HERE, before the motor mount is added.
    # Filleting "|Z" at the very end caught the top plate's overhang edges and
    # produced a solid OCCT calls valid but that tessellates with naked edges.
    body = safe_fillet(body, "|Z", 3.0)
    if with_motor:
        # v4: solid pillar, not two legs. 30 mm in y so it stays INSIDE the
        # body's 34 mm width -- coincident coplanar faces in a union are what
        # produced the earlier mesh defect. 7 mm of wall round the 16 mm bore.
        pillar = (cq.Workplane("XY").box(50.0, 30.0, 28.0, centered=(True, True, False))
                  .translate((0, 0, sec / 2.0 - 2.0)))
        body = body.union(pillar)
        top = (cq.Workplane("XY").box(70.0, 62.0, 10.0, centered=(True, True, False))
               .translate((0, 0, sec / 2.0 + 24.0)))
        body = body.union(top)
        # v8: 4 x M4 at (+-15, +-24.5) to carry part 14. These used to copy the
        # motor's 18 x 33 pattern, but with the shaft offset the near pair would
        # land on the upper 608 seat. Out here the radius is 28.7 and nothing
        # collides; the nuts go under the plate, clear of the 50 x 30 pillar.
        body = body.faces(">Z").workplane().rarray(50.0, 49.0, 2, 2).hole(4.5)
    body = body.faces(">Z").workplane().hole(P["shaft_dia"] + 8.0)
    if with_motor:
        # v4: upper 608, seated from the top face of the plate
        body = (body.faces(">Z").workplane()
                .hole(P["bearing_od"], P["bearing_w"] + 1.0))
    body = (body.faces("<Z").workplane()
            .hole(P["bearing_od"], P["bearing_w"] + 1.0))
    body = (body.faces(">Z").workplane()
            .pushPoints([(-52, 0), (52, 0)]).hole(5.4))
    return body


def motor2_standoff():
    """Part 14. Carries Motor 2 above part 03's top plate so the coupler sits in
    open air with hex access.

    v8, reworked twice over. Two things forced it:

    1. The JGY-370's shaft is 7.5 mm off the centre of its own bolt pattern, so
       the M3 move to y = +9 / -24. They used to double as the wall positions;
       a wall at y = +9 would leave 4 mm to the axis and the 14 mm coupler needs
       7. Walls are now at +-24.5, independent of the holes.
    2. A single long screw through motor, standoff and plate is no longer
       possible: at (9, +9) it lands on radius 12.73 and the upper 608 seat in
       part 03 reaches 11.10. They overlap. So the two joints are now separate.

    Motor bolts to the cap with 4 x M3 x 16 driven UP from inside, through the
    open underside, into the motor's own tapped holes. Then the whole assembly
    drops onto part 03 and is held by 4 x M4 at the wall feet, out at radius
    28.7 where nothing collides.
    """
    WALL_T, WALL_H, CAP_T = 10.0, 30.0, 4.0
    WALL_Y, LEN_X = 24.5, 40.0
    MOT_Y = (9.0, -24.0)          # the offset motor pattern
    FIX_X, FIX_Y = 15.0, 24.5     # down-fixings into part 03

    # v11: the lower wall is thicker, inner face moved in to y = -12, so the
    # far M3 pair at y = -24 sits in solid wall with room for an access bore.
    # Before, it sat in a 10 mm wall with nothing to reach it from below.
    upper = (cq.Workplane("XY").box(LEN_X, WALL_T, WALL_H, centered=(True, True, False))
             .translate((0, WALL_Y, 0)))
    lower = (cq.Workplane("XY").box(LEN_X, 19.0, WALL_H, centered=(True, True, False))
             .translate((0, -21.5, 0)))
    body = upper.union(lower)
    cap = (cq.Workplane("XY").box(LEN_X, 66.0, CAP_T, centered=(True, True, False))
           .translate((0, 0, WALL_H - 1.0)))
    body = body.union(cap)
    # 19 mm bore, as on part 05 -- the maker never dimensions the shaft boss
    body = body.cut(cq.Workplane("XY").circle(9.5).extrude(CAP_T + 4)
                    .translate((0, 0, WALL_H - 2.0)))
    # motor holes, cap only -- plus access bores for the far pair
    for sx in (-1, 1):
        for py in MOT_Y:
            px = sx * P["gm_hole_x"] / 2.0
            body = body.cut(cq.Workplane("XY").circle(P["gm_hole_d"] / 2.0)
                            .extrude(CAP_T + 6).translate((px, py, WALL_H - 3.0)))
            if py < 0:
                body = body.cut(cq.Workplane("XY").circle(3.5).extrude(WALL_H)
                                .translate((px, py, -1.0)))
    # v9: the down-fixings move OUT onto flat feet at x = +-25. They used to run
    # the wall's full 30 mm height, which needed an M4 x 45 and was blind under
    # the cap anyway. Worse, the motor gearbox covers x +-16 / y -31..+15, so a
    # hole at x = 15 sat under the motor. The feet stick out past the 40 mm cap,
    # so the screws are reachable from directly above with the motor fitted.
    for sx in (-1, 1):
        for sy in (-1, 1):
            foot = (cq.Workplane("XY").box(20.0, WALL_T, 8.0, centered=(True, True, False))
                    .translate((sx * 25.0, sy * WALL_Y, 0)))
            body = body.union(foot)
    for sx in (-1, 1):
        for sy in (-1, 1):
            body = body.cut(cq.Workplane("XY").circle(2.25).extrude(10.0)
                            .translate((sx * 25.0, sy * WALL_Y, -1.0)))
    return body


def bearing_fit_gauge():
    """PRINT THIS FIRST. Four pockets: 21.8 / 22.0 / 22.2 / 22.4 mm.
    FDM holes come out undersized. Find the pocket that takes a 608 with a firm
    thumb push, set P["bearing_od"] to that number, then print everything else."""
    g = cq.Workplane("XY").box(150.0, 40.0, 12.0, centered=(True, True, False))
    for i, dia in enumerate([21.8, 22.0, 22.2, 22.4]):
        g = g.cut(cq.Workplane("XY").circle(dia / 2.0).extrude(20.0)
                  .translate((-56.0 + i * 37.0, 0, 3.0)))
    return safe_fillet(g, "|Z", 4.0)


def motor_standoff():
    """Part 05. Spaces Motor 1 off the bearing tower so the coupler fits.

    v11, two faults found at the bench:

    1. The motor's offset pattern put the far pair of M3 at y = -24, directly
       over the lower leg -- 31 mm of solid plastic underneath. Only two of
       the four screws could be driven. The lower leg is now thicker, with its
       inner face moved in to y = -12, and has 7 mm access bores at (+-9, -24)
       running its full height, so a hex key reaches all four from below.

    2. The M5 nut pockets were sealed: a 0.8 mm membrane toward the cavity and
       a 5.4 mm hole below, against an 8 mm nut. Same fault as the original
       counterweight. Each pocket now has a slot out to the cavity, 8.6 mm
       wide so the nut slides in flat-first and cannot turn once seated.
    """
    PLATE_T, CAV = 6.0, 34.0
    MOT_Y = (9.0, -24.0)
    base = cq.Workplane("XY").box(70.0, 62.0, 6.0, centered=(True, True, False))
    upper = (cq.Workplane("XY").box(70.0, 13.0, CAV, centered=(True, True, False))
             .translate((0, 24.5, 6.0)))
    lower = (cq.Workplane("XY").box(70.0, 19.0, CAV, centered=(True, True, False))
             .translate((0, -21.5, 6.0)))                    # y -31 .. -12
    top = (cq.Workplane("XY").box(70.0, 62.0, PLATE_T, centered=(True, True, False))
           .translate((0, 0, 6.0 + CAV)))
    b = base.union(upper).union(lower).union(top)
    b = b.cut(cq.Workplane("XY").circle(9.5).extrude(PLATE_T + 4)
              .translate((0, 0, 6.0 + CAV - 2.0)))
    b = b.cut(cq.Workplane("XY").box(40.0, 50.0, 7.0, centered=(True, True, False))
              .translate((0, 0, -1.0)))
    for sx in (-1, 1):
        for py in MOT_Y:
            px = sx * P["gm_hole_x"] / 2.0
            b = b.cut(cq.Workplane("XY").circle(P["gm_hole_d"] / 2.0)
                      .extrude(PLATE_T + 4).translate((px, py, 6.0 + CAV - 2.0)))
            if py < 0:     # access bore up through the lower leg
                b = b.cut(cq.Workplane("XY").circle(3.5).extrude(CAV + 1.0)
                          .translate((px, py, 5.5)))
    for sx in (-1, 1):
        for sy in (-1, 1):
            px, py = sx * 28.0, sy * 23.0
            # v19: the M5 hole now runs on PAST the nut pocket, to z = 22. It
            # used to stop at the base (z = 7), so above the 4.4 mm pocket
            # was solid leg -- and an M5 x 45 from the tower put its tip
            # 0.6 mm into that plastic before the head could clamp. The screw
            # bottomed out, the joint never pulled tight. The tip now has
            # 11.6 mm of free hole beyond the nut.
            b = b.cut(cq.Workplane("XY").circle(2.7).extrude(23.0).translate((px, py, -1.0)))
            inner = 18.0 if sy > 0 else -12.0          # this leg's inner face
            y0, y1 = sorted((inner, py + sy * 4.2))
            b = b.cut(cq.Workplane("XY").box(8.6, y1 - y0, 4.4, centered=(True, False, False))
                      .translate((px, y0, 6.0)))
    return b


def bearing_tower():
    """PRINTED cap on top of the aluminium post. Holds a 608 AND carries Motor 1.

    Bore runs along X, the trunnion axis. Four M5 holes on the outboard face take
    the motor standoff - the motor bolts around the bore, never into it.
    """
    e = P["ext"]
    tw, td, th = 34.0, 74.0, 112.0          # X, Y, Z
    zb = 76.0                                # bearing centre, 52 mm socket below
    t = cq.Workplane("XY").box(tw, td, th, centered=(True, True, False))
    # v5: the post socket is a BLIND 52 mm pocket starting on the build plate,
    # so it suffers first-layer squeeze on top of the usual ~0.2 mm undersize.
    # At the shared 0.35 mm clearance it printed too small to admit the rail,
    # while the through-sockets on parts 02/03/04 were fine. This socket gets
    # its own, larger clearance -- the two clamp screws take up the slack.
    # v6: measured. Modelled 20.7 printed at 20.0 -- 0.7 mm of shrink, not the
    # 0.2 mm the bearing gauge suggested. A deep blind pocket in a 112 mm tall
    # print contracts far more than a shallow circular seat. 0.85 mm modelled
    # clearance lands the printed socket near 21.0 for a 20 mm rail.
    # v18: retuned for the Bambu print shop (was 0.85, set for the lab
    # printer's measured 0.7 mm shrink in this deep pocket). Print on its side.
    post_clear = 0.6
    t = t.cut(cq.Workplane("XY")
              .box(e + 2 * post_clear, e + 2 * post_clear, 52.0,
                   centered=(True, True, False)).translate((0, 0, -1.0)))
    # 2 mm lead-in at the mouth so elephant's foot cannot close the entry
    t = t.cut(cq.Workplane("XY")
              .box(e + 2.4, e + 2.4, 3.0,
                   centered=(True, True, False)).translate((0, 0, -1.0)))
    # 608 seat from the outboard face, then shaft clearance right through
    t = t.cut(cq.Workplane("YZ").workplane(offset=4.0)
              .circle(P["bearing_od"] / 2.0).extrude(20.0).translate((0, 0, zb)))
    t = t.cut(cq.Workplane("YZ").workplane(offset=-30.0)
              .circle((P["shaft_dia"] + 2.0) / 2.0).extrude(70.0)
              .translate((0, 0, zb)))
    # 4 x M5 for the motor standoff, around the bore
    for sy in (-1, 1):
        for sz in (-1, 1):
            t = t.cut(cq.Workplane("YZ").workplane(offset=-30.0).circle(2.7)
                      .extrude(70.0).translate((0, sy * 28.0, zb + sz * 23.0)))
    # v10: the original pair only pinched the post in Y. The socket's clearance
    # (0.85 mm per side, added in both X and Y) was left completely unclamped
    # in X, so the tower could rock side to side even with both screws tight --
    # and X is the direction the trunnion shaft runs, so that slop showed up
    # directly as wobble on the bearing. A second pair, at 90 degrees, pinches
    # X as well. Both pairs sit at z = 14 and 36, inside the socket and clear
    # of the bore (which starts at z=53).
    for zs in (14.0, 36.0):
        t = t.cut(cq.Workplane("XY").circle(2.7).extrude(100.0)
                  .rotate((0, 0, 0), (1, 0, 0), -90).translate((0, -50.0, zs)))
        t = t.cut(cq.Workplane("XY").circle(2.7).extrude(100.0)
                  .rotate((0, 0, 0), (0, 1, 0), 90).translate((-50.0, 0, zs)))
    return t


def motor_bracket():
    """Face plate for a JGY-370, with a 2020 socket on the back."""
    e, w = P["ext"], P["wall"]
    plate = cq.Workplane("XY").box(70.0, 62.0, 8.0, centered=(True, True, False))
    plate = plate.faces(">Z").workplane().hole(P["shaft_dia"] + 6.0)
    plate = (plate.faces(">Z").workplane()
             .rarray(P["gm_hole_x"], P["gm_hole_y"], 2, 2).hole(P["gm_hole_d"]))
    boss = (cq.Workplane("XY").box(e + 2 * w, e + 2 * w, 34.0,
                                   centered=(True, True, False))
            .translate((0, 0, 8.0)))
    boss = boss.cut(_socket(80.0).translate((0, 0, -20.0)))
    return safe_fillet(plate.union(boss), "|Z", 3.0)


def worm_gearmotor():
    """JGY-370 right-angle worm gearmotor, real datasheet envelope.

    Gearbox 46 (L) x 32 (W) x 25 (H). Output shaft leaves the BOTTOM face, so the
    motor body lies flat, perpendicular to the shaft. That is the whole reason for
    choosing a worm unit here - an in-line gearmotor would stand 77 mm tall and the
    gimbal would have to swing that extra height.
    """
    GB_L, GB_W, GB_H = 46.0, 32.0, 25.0
    MB_L, MB_D = 31.0, 24.4
    gearbox = (cq.Workplane("XY").box(GB_L, GB_W, GB_H, centered=(True, True, False))
               .edges("|Z").fillet(3.0))
    body = (cq.Workplane("YZ").workplane(offset=GB_L / 2.0)
            .center(0, GB_H / 2.0).circle(MB_D / 2.0).extrude(MB_L))
    shaft = (cq.Workplane("XY").workplane(offset=-14.0)
             .circle(3.0).extrude(14.0))
    return gearbox.union(body).union(shaft)


def motor1():
    """Motor 1 on the static left upright, output shaft pointing +X into the trunnion."""
    m = worm_gearmotor()
    m = m.rotate((0, 0, 0), (1, 0, 0), 90)   # gearbox face turns to +Y
    m = m.rotate((0, 0, 0), (0, 1, 0), 90)   # output shaft now faces +X
    return m.translate((-(D["upright_x"] + 37.0 + 40.0), 0, 0))


def motor2():
    """Motor 2 on the outer frame top rail, output shaft pointing -Z (down into pivot)."""
    return worm_gearmotor().translate((0, 0, D["m2_rail_z"]))


def shelf_bracket():
    """Clamps a vertical rail of the inner frame and carries the plate.

    Back plate sits against the rail face with two M5 into T-nuts, so the whole
    bracket slides up or down. The shelf reaches inward under the plate's arm and
    takes two M4 in slots, giving the plate +-6 mm for balancing.
    """
    reach = 34.0
    back  = cq.Workplane("XY").box(60.0, 8.0, 46.0, centered=(True, False, False))
    back  = back.translate((0, -8.0, 0))
    shelf = cq.Workplane("XY").box(60.0, reach, 8.0, centered=(True, False, False))
    shelf = shelf.translate((0, -8.0 - reach, 0))
    b = back.union(shelf)
    # 2 x M5 THROUGH THE BACK PLATE along Y, into T-nuts in the rail slot
    for zs in (13.0, 33.0):
        b = b.cut(cq.Workplane("XY").circle(2.7).extrude(60.0)
                  .rotate((0, 0, 0), (1, 0, 0), -90)
                  .translate((0, -30.0, zs)))
    # 2 slotted M4 in the shelf, elongated along X for balance adjustment
    for sx in (-1, 1):
        b = b.cut(cq.Workplane("XY").slot2D(14.0, 4.4, 0).extrude(20.0)
                  .translate((sx * 20.0, -8.0 - reach / 2.0, -6.0)))
    return safe_fillet(b, "|Z", 4.0)


def shelf_brackets():
    """Two brackets, one on each vertical rail, at the bottom plate height."""
    yr = D["inner_out_y"] / 2.0 - P["ext"]      # inner face of the vertical rail
    z = D["plate_bot_z"] - P["plate_t"] - 2.0
    a = shelf_bracket().translate((0, yr, z))
    b = shelf_bracket().rotate((0, 0, 0), (0, 0, 1), 180).translate((0, -yr, z))
    return a.union(b)


def holder():
    """The PLATE. A flat platform with a grid of M6 holes.

    Different mould shapes bolt onto different holes in the grid. Nothing about
    the plate is specific to one mould, so swapping moulds never means a new plate.
    """
    sz, t = D["plate_sz"], P["plate_t"]
    d = cq.Workplane("XY").rect(sz, sz).extrude(t).edges("|Z").fillet(16)
    # 5 x 5 grid of M6 holes at 50 mm pitch
    for i in range(5):
        for j in range(5):
            x = (i - 2) * 50.0
            y = (j - 2) * 50.0
            d = d.cut(cq.Workplane("XY").circle(3.3).extrude(t + 6)
                      .translate((x, y, -3.0)))
    # slotted edge holes onto the shelf brackets, +-6 mm for balancing
    for sx in (-1, 1):
        for sy in (-1, 1):
            slot = (cq.Workplane("XY").slot2D(14.0, 5.4, 90).extrude(t + 6)
                    .translate((sx * 46.0, sy * (sz / 2.0 - 12.0), -3.0)))
            d = d.cut(slot)
    return d.translate((0, 0, D["plate_bot_z"]))


def mould():
    r, h = P["mould_dia"] / 2.0, P["mould_height"]
    pts = [(0, -h / 2), (r, -h / 2), (r, h * 0.18), (r * 0.80, h * 0.32),
           (r * 0.40, h * 0.43), (r * 0.22, h * 0.47), (r * 0.22, h / 2),
           (0, h / 2)]
    return (cq.Workplane("XZ").polyline(pts).close()
            .revolve(360, (0, 0, 0), (0, 1, 0)))


# ---------------------------------------------------------------------------
# FRAME ASSEMBLIES
# ---------------------------------------------------------------------------
def _frame(out_a, out_b, rail_a, rail_b, plane):
    """Rectangle of 4 rails + 4 corner brackets, built in XY then rotated.

    out_a spans local X, out_b spans local Y.
    """
    e, arm = P["ext"], P["arm"]
    ha, hb = out_a / 2.0, out_b / 2.0
    parts = []
    # horizontal rails at y = +-(hb - e/2)
    for sy in (-1, 1):
        parts.append(extrusion(rail_a, "X")
                     .translate((-rail_a / 2.0, sy * (hb - e / 2.0), 0)))
    for sx in (-1, 1):
        parts.append(extrusion(rail_b, "Y")
                     .translate((sx * (ha - e / 2.0), -rail_b / 2.0, 0)))
    # corner brackets, arms pointing inward
    for sx in (-1, 1):
        for sy in (-1, 1):
            ang = {(-1, -1): 0, (1, -1): 90, (1, 1): 180, (-1, 1): -90}[(sx, sy)]
            b = corner_bracket().rotate((0, 0, 0), (0, 0, 1), ang)
            parts.append(b.translate((sx * (ha - e / 2.0), sy * (hb - e / 2.0), 0)))
    shp = parts[0]
    for q in parts[1:]:
        shp = shp.union(q)
    if plane == "YZ":
        shp = shp.rotate((0, 0, 0), (0, 0, 1), 90).rotate((0, 0, 0), (1, 0, 0), 90)
    elif plane == "XZ":
        shp = shp.rotate((0, 0, 0), (1, 0, 0), 90)
    return shp


def inner_frame():
    """Rectangle in YZ. Z is the pivot axis, so out_b (local Y) becomes Z."""
    f = _frame(D["inner_out_y"], D["inner_out_z"],
               D["rail_inner_h"], D["rail_inner_v"], "XZ")
    f = f.rotate((0, 0, 0), (0, 0, 1), 90)   # swing the plane from XZ into YZ
    hz = D["inner_out_z"] / 2.0
    hubs = None
    for sz in (-1, 1):
        h = pivot_hub("shaft")
        if sz < 0:
            h = h.rotate((0, 0, 0), (1, 0, 0), 180)
        h = h.translate((0, 0, sz * (hz - P["ext"])))
        hubs = h if hubs is None else hubs.union(h)
    stub = None
    # v17: a shaft cannot start inside the rail. The gripper's bore opens into
    # the rail channel, and the rail fills it, so a shaft stops on the rail's
    # face at hz -- not hz - 8, where every earlier version started it. That
    # 8 mm error ran into every shaft length. Top stub (Motor 2) is 114; the
    # bottom one only has to pass part 04's bearing and uses 60 in practice.
    reach = 114.0
    for sz in (-1, 1):
        s = (cq.Workplane("XY").workplane(offset=sz * hz)
             .circle(P["shaft_dia"] / 2.0).extrude(sz * reach))
        stub = s if stub is None else stub.union(s)
    return f.union(hubs).union(stub)


def outer_frame():
    """Rectangle in XZ. Top and bottom rails are SPLIT, bridged by printed hubs
    that carry the inner frame's pivot bearings."""
    e = P["ext"]
    hx = D["outer_out_x"] / 2.0
    hz = D["outer_out_z"] / 2.0
    span = D["outer_out_x"] - 2 * e          # clear span between the verticals
    gap = 150.0 - 2 * 45.0                   # clear gap inside the bridge hub
    seg = (span - gap) / 2.0
    D["rail_outer_h"] = seg                  # 4 off, not 2

    parts = []
    for sz in (-1, 1):
        for sx in (-1, 1):
            r = extrusion(seg, "X").translate(
                (sx * (gap / 2.0) if sx > 0 else -(gap / 2.0 + seg),
                 0, sz * (hz - e / 2.0)))
            parts.append(r)
    for sx in (-1, 1):
        parts.append(extrusion(D["rail_outer_v"], "Y")
                     .rotate((0, 0, 0), (1, 0, 0), 90)
                     .translate((sx * (hx - e / 2.0), 0, -D["rail_outer_v"] / 2.0)))
    shp = parts[0]
    for q in parts[1:]:
        shp = shp.union(q)

    shp = shp.union(bridge_hub(True).translate((0, 0, hz - e / 2.0)))
    shp = shp.union(bridge_hub(False).translate((0, 0, -(hz - e / 2.0))))

    hubs = None
    for sx in (-1, 1):
        h = (pivot_hub("shaft").rotate((0, 0, 0), (0, 1, 0), 90 * sx)
             .translate((sx * (hx - e), 0, 0)))
        hubs = h if hubs is None else hubs.union(h)
    trun = None
    # v17: starts on the rail face at hx, not hx - 8 (see inner_frame). Left
    # 112 into Motor 1's coupler; right is the 111 tube into part 12.
    for sx in (-1, 1):
        t = (cq.Workplane("YZ").workplane(offset=sx * hx)
             .circle(P["shaft_dia"] / 2.0).extrude(sx * 112.0))
        trun = t if trun is None else trun.union(t)
    return shp.union(hubs).union(trun)


def uprights():
    res = None
    for sx in (-1, 1):
        post = extrusion(D["post_len"], "Y").rotate((0, 0, 0), (1, 0, 0), 90)
        post = post.translate((sx * D["upright_x"], 0, D["base_top_z"]))
        tower = bearing_tower().translate(
            (sx * D["upright_x"], 0, D["base_top_z"] + D["post_len"] - 52.0))
        u = post.union(tower)
        res = u if res is None else res.union(u)
    return res


def base():
    return (cq.Workplane("XY").workplane(offset=D["base_top_z"] - P["base_t"])
            .rect(D["base_x"], P["base_y"]).extrude(P["base_t"])
            .edges("|Z").fillet(20))




def slipring():
    return (cq.Workplane("YZ").workplane(offset=D["upright_x"] + 22.0)
            .circle(P["sr_dia"] / 2.0).extrude(P["sr_len"]))


def control_box():
    """Sits in front of the right upright, clear of the gimbal's swept envelope."""
    cx = D["upright_x"]
    cy = -(P["base_y"] / 2.0 - 75.0)
    b = (cq.Workplane("XY").workplane(offset=D["base_top_z"])
         .center(cx, cy).rect(84.0, 140.0).extrude(62.0)
         .edges("|Z").fillet(6))
    b = b.faces(">Z").workplane().center(0, 30).rect(64, 32).cutBlind(-3.0)
    b = (b.faces(">Z").workplane()
         .pushPoints([(-24, -28), (24, -28), (0, -2)]).hole(9.0))
    return b


def motor_plate(axis="X"):
    """Printed 8 mm plate between a gearmotor face and its mounting surface."""
    pl = (cq.Workplane("XY").box(70.0, 62.0, 8.0, centered=(True, True, False))
          .faces(">Z").workplane().hole(P["shaft_dia"] + 8.0)
          .faces(">Z").workplane().rarray(P["gm_hole_x"], P["gm_hole_y"], 2, 2).hole(P["gm_hole_d"])
          .edges("|Z").fillet(6.0))
    if axis == "X":
        pl = pl.rotate((0, 0, 0), (0, 1, 0), 90)
    return pl


def motor_plates():
    p1 = (motor_standoff().rotate((0, 0, 0), (0, 1, 0), -90)
          .translate((-(D["upright_x"] + 37.0), 0, 0)))
    return p1


PRINTED = {
    "corner_bracket": corner_bracket,
    "pivot_hub_bearing": lambda: pivot_hub("bearing"),
    "pivot_hub_shaft": lambda: pivot_hub("shaft"),
    "bearing_tower": bearing_tower,
    "motor_bracket": motor_bracket,
    "bridge_hub_motor": lambda: bridge_hub(True),
    "bridge_hub_plain": lambda: bridge_hub(False),
    "motor_standoff": motor_standoff,
    "shelf_bracket": shelf_bracket,
    "mould_holder": holder,
    "control_enclosure": control_box,
}


def build():
    a = cq.Assembly(name="rotocaster_v2")
    a.add(base(), name="base", color=cq.Color(0.72, 0.60, 0.42))
    a.add(uprights(), name="uprights", color=cq.Color(0.62, 0.64, 0.66))
    a.add(outer_frame(), name="outer_frame", color=cq.Color(0.24, 0.42, 0.62))
    a.add(inner_frame(), name="inner_frame", color=cq.Color(0.11, 0.62, 0.46))
    a.add(shelf_brackets(), name="shelf_brackets", color=cq.Color(0.75, 0.45, 0.12))
    import connector
    a.add(connector.connector_plate().translate((0, 0, D["plate_bot_z"])),
          name="mould_plate", color=cq.Color(0.85, 0.62, 0.18))
    a.add(mould(), name="mould", color=cq.Color(0.92, 0.92, 0.88))
    a.add(motor_plates(), name="motor_plates", color=cq.Color(0.90, 0.55, 0.15))
    a.add(motor1(), name="motor1", color=cq.Color(0.18, 0.18, 0.20))
    a.add(motor2(), name="motor2", color=cq.Color(0.18, 0.18, 0.20))
    a.add(motor2_standoff().translate((0, 0, D["m2_rail_z"] - 33.0)),
          name="motor2_standoff", color=cq.Color(0.75, 0.45, 0.12))
    a.add(slipring(), name="slip_ring", color=cq.Color(0.62, 0.30, 0.55))
    a.add(control_box(), name="control_enclosure", color=cq.Color(0.45, 0.47, 0.50))
    return a


def posed_parts(outer_deg=0.0, inner_deg=0.0):
    grp_in = [("inner_frame", inner_frame(), "#1d9e75"),
              ("shelf_brackets", shelf_brackets(), "#b8730f"),
              ("holder", holder(), "#e0a020"),
              ("mould", mould(), "#e8e6df")]
    grp_gb = [("outer_frame", outer_frame(), "#2f6ba8"),
              ("motor2", motor2(), "#d13b3b"),
  ]
    stat = [("base", base(), "#b89a6b"), ("uprights", uprights(), "#9ea3a8"),
            ("plate1", motor_plates(), "#ef9f27"),
            ("motor1", motor1(), "#2b2b30"), ("slipring", slipring(), "#a24d8e"),
            ("control", control_box(), "#6f757b")]
    out = {}
    for n, s, c in grp_in:
        out[n] = (s.rotate((0, 0, 0), (0, 0, 1), inner_deg)
                   .rotate((0, 0, 0), (1, 0, 0), outer_deg), c)
    for n, s, c in grp_gb:
        out[n] = (s.rotate((0, 0, 0), (1, 0, 0), outer_deg), c)
    for n, s, c in stat:
        out[n] = (s, c)
    return out


def cut_list():
    e = P["ext"]
    return [
        ("Outer frame horizontal segment", 4, D["outer_seg"]),
        ("Outer frame vertical", 2, D["rail_outer_v"]),
        ("Inner frame horizontal", 2, D["rail_inner_h"]),
        ("Inner frame vertical", 2, D["rail_inner_v"]),
        ("Upright post", 2, D["post_len"]),
    ]


def selfcheck():
    bed = sorted(P["bed"], reverse=True)
    rows = []
    for name, fn in PRINTED.items():
        bb = fn().val().BoundingBox()
        dims = sorted([bb.xlen, bb.ylen, bb.zlen], reverse=True)
        ok = all(dims[i] <= bed[i] for i in range(3))
        rows.append((name, dims, ok))
    return rows


if __name__ == "__main__":
    print("DERIVED ENVELOPE")
    print(f"  mould                 : {P['mould_dia']:.0f} dia x {P['mould_height']:.0f}")
    print(f"  inner frame           : {D['inner_out_y']:.0f} (Y) x {D['inner_out_z']:.0f} (Z)")
    print(f"  outer frame           : {D['outer_out_x']:.0f} (X) x {D['outer_out_z']:.0f} (Z)")
    print(f"  gimbal sweep radius   : {D['outer_sweep_r']:.1f}")
    print(f"  axis height           : {D['axis_height']:.1f}")
    print(f"  base board            : {D['base_x']:.0f} x {P['base_y']:.0f} x {P['base_t']:.0f}")
    print(f"  overall height        : {D['axis_height'] + 40:.0f}")

    print("\n2020 EXTRUSION CUT LIST")
    tot = 0.0
    for name, qty, ln in cut_list():
        print(f"  {qty} x {ln:6.1f} mm   {name}")
        tot += qty * ln
    print(f"  total {tot/1000.0:.2f} m  (buy {math.ceil(tot/1000.0*1.15)} m)")

    print("\nPRINTED PARTS vs BED "
          f"{P['bed'][0]:.0f}x{P['bed'][1]:.0f}x{P['bed'][2]:.0f}")
    for name, dims, ok in selfcheck():
        print(f"  {name:20s} {dims[0]:6.1f} {dims[1]:6.1f} {dims[2]:6.1f}   "
              f"{'OK' if ok else 'TOO BIG'}")
