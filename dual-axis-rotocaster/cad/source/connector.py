"""Mould plate: central hub with two arms reaching the shelf brackets."""
import math
import cadquery as cq

HUB_D   = 180.0
PCD     = 140.0     # 4 x M6, the published mould interface
ARM_W   = 62.0
SPAN    = 300.0     # 10 mm clear each side of the 320 frame opening
T       = 8.0
COVER_D = 156.0

def connector_plate():
    hub = cq.Workplane("XY").circle(HUB_D/2).extrude(T)
    arm = (cq.Workplane("XY").box(ARM_W, SPAN, T, centered=(True,True,False))
           .edges("|Z").fillet(18))
    p = hub.union(arm)
    p = p.faces(">Z").workplane().circle(COVER_D/2).cutBlind(-3.0)
    for k in range(4):
        a = math.radians(90*k+45)
        x,y = PCD/2*math.cos(a), PCD/2*math.sin(a)
        p = p.cut(cq.Workplane("XY").circle(3.3).extrude(T+6).translate((x,y,-3)))
        p = p.cut(cq.Workplane("XY").circle(6.2).extrude(4.5).translate((x,y,-0.5)))
    p = p.cut(cq.Workplane("XY").circle(2.7).extrude(T+6).translate((0,0,-3)))
    for sy in (-1,1):
        for sx in (-1,1):
            p = p.cut(cq.Workplane("XY").slot2D(14.0,5.4,90).extrude(T+6)
                      .translate((sx*20.0, sy*(SPAN/2-16), -3)))
    return p

PARTS={"connector_plate":connector_plate()}
