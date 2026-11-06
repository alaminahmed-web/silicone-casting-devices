"""Mould lid and pour plug."""
import math
import cadquery as cq

RIM_D    = 300.0    # flush with the mould, clears the 320 frame opening
RIM_PCD  = 280.0    # 6 x M5 into the mould rim
LID_T    = 5.0
PORT     = 45.0
PLUG_PCD = 58.0     # 3 x M4 holding the plug down
Z_RIM    = 172.0

def lid():
    l = cq.Workplane("XY").workplane(offset=Z_RIM).circle(RIM_D/2).extrude(LID_T)
    l = l.union(cq.Workplane("XY").workplane(offset=Z_RIM-5)
                .circle(RIM_D/2-21).extrude(5))          # spigot, locates in the rim
    l = l.faces(">Z").workplane().hole(PORT)
    for k in range(6):
        a=math.radians(60*k)
        l = l.cut(cq.Workplane("XY").circle(2.9).extrude(LID_T+12)
                  .translate((RIM_PCD/2*math.cos(a), RIM_PCD/2*math.sin(a), Z_RIM-6)))
    for k in range(3):
        a=math.radians(120*k)
        l = l.cut(cq.Workplane("XY").circle(2.2).extrude(LID_T+12)
                  .translate((PLUG_PCD/2*math.cos(a), PLUG_PCD/2*math.sin(a), Z_RIM-6)))
    return l

def plug():
    head = cq.Workplane("XY").workplane(offset=Z_RIM+LID_T).circle(PORT/2+16).extrude(8)
    spig = cq.Workplane("XY").workplane(offset=Z_RIM+LID_T-11).circle(PORT/2-0.4).extrude(11)
    p = head.union(spig)
    p = p.cut(cq.Workplane("XY").workplane(offset=Z_RIM+LID_T)
              .circle(PORT/2+7).circle(PORT/2+4).extrude(1.8))   # O-ring groove
    for k in range(3):
        a=math.radians(120*k)
        p = p.cut(cq.Workplane("XY").circle(2.2).extrude(20)
                  .translate((PLUG_PCD/2*math.cos(a), PLUG_PCD/2*math.sin(a), Z_RIM+LID_T-2)))
    return p

PARTS={"lid":lid(),"plug":plug()}
