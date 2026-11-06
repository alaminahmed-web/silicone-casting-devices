"""Counterweight pocket. Two off, one on each bottom rail segment.

v3 FIX: in v2 the ballast pocket was a fully enclosed void -- 2 mm of material
capped it, so the M8 nuts could never be loaded. The pocket is now open at the
top and closed by a screwed cover, because this part inverts every revolution
and loose ballast has to be positively retained.
"""
import cadquery as cq
import importlib, rotocaster_v2
importlib.reload(rotocaster_v2)
import rotocaster_v2 as V
P = V.P

BODY_L, BODY_H = 110.0, 68.0
POCK_L, POCK_W = 82.0, 22.0
POCK_Z0 = 26.0                 # floor of the ballast pocket
REC_D = 3.0                    # cover recess depth
REC_L, REC_W = 96.0, 26.0
COVER_T = 3.0
COVER_CLR = 0.4
SCREW_X, SCREW_Y = 44.0, 10.0  # 4 x M3, into the solid end blocks
CLAMP_X = 46.0                 # existing M5 rail clamp screws


def counterweight():
    e = P["ext"]
    wd = e + 2 * P["wall"]
    b = cq.Workplane("XY").box(BODY_L, wd, BODY_H, centered=(True, True, False))
    b = b.cut(cq.Workplane("XY").box(BODY_L + 2, e + 2 * P["sock_clear"], e,
                                     centered=(True, True, False)))
    rec_z = BODY_H - REC_D
    b = b.cut(cq.Workplane("XY").box(REC_L, REC_W, REC_D + 1,
                                     centered=(True, True, False))
              .translate((0, 0, rec_z)))
    b = b.cut(cq.Workplane("XY").box(POCK_L, POCK_W, rec_z - POCK_Z0,
                                     centered=(True, True, False))
              .translate((0, 0, POCK_Z0)))
    for sx in (-1, 1):
        for sy in (-1, 1):
            b = b.cut(cq.Workplane("XY").circle(1.35).extrude(14.0)
                      .translate((sx * SCREW_X, sy * SCREW_Y, rec_z - 12.0)))
    for sx in (-1, 1):
        b = b.cut(cq.Workplane("XY").circle(2.7).extrude(80.0)
                  .translate((sx * CLAMP_X, 0, -4.0)))
    return b


def cover():
    """Retains the ballast. Sits flush in the recess."""
    c = cq.Workplane("XY").box(REC_L - COVER_CLR, REC_W - COVER_CLR, COVER_T,
                               centered=(True, True, False))
    for sx in (-1, 1):
        for sy in (-1, 1):
            c = c.cut(cq.Workplane("XY").circle(1.7).extrude(COVER_T + 2)
                      .translate((sx * SCREW_X, sy * SCREW_Y, -1)))
    for sx in (-1, 1):
        c = c.cut(cq.Workplane("XY").circle(2.8).extrude(COVER_T + 2)
                  .translate((sx * CLAMP_X, 0, -1)))
    return c.edges("|Z").fillet(3.0)


PARTS = {"counterweight": counterweight(), "counterweight_cover": cover()}
