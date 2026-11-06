# Rotocaster controller box: screws and wiring

## 1. Screw schedule (checked against controller_box.py)

| Where | Qty | Screw | Why this size |
|---|---|---|---|
| Lid to corner bosses | 4 | M3 x 10 (or 12), pan/button head, self-tapping into PLA | Lid under head 2.5 mm, pilot 12 mm deep: M3x10 gives 7.5 mm grip, M3x12 gives 9.5 mm. Counterbore is 2.5 mm deep, so a pan head sits flush; a socket-cap head (3 mm tall) sticks out 0.5 mm. |
| Arduino Uno to standoffs | 4 | M3 x 8 (M3 x 10 also works) | Board 1.6 mm + 6.4 mm into the standoff. Pilot is 8 mm deep. Use pan/button heads, nothing taller than 3 mm near the traces. |
| L298N to standoffs | 4 | M3 x 8 (M3 x 10 also works) | Same standoffs as the Uno. |
| Box floor to the plywood base | 4 | Countersunk wood screw, 4 mm x 16 mm (M4 or #8 chipboard screw) | Floor is 3 mm, plywood is 18 mm: 13 mm grip. Holes are 4.5 mm with an 8.5 mm countersink, reached from inside with the lid off, at x = 40 and 120, y = 9 and 81. Your M4 x 12 machine screws will not bite in wood, so buy 4 wood screws. |
| Pots | 2 | Nut supplied with the pot | Nut sits in a 14 mm recess, lid is 2.5 mm thick there. |
| Rocker switch | 0 | Snap-in | Lid is thinned to 1.6 mm around it. |
| OLED | 0 | Hot glue or double-sided tape | Sits in a 36.6 x 34.6 mm pocket. |

Total M3 x 10 needed for the box: 12, plus the motor and slip-ring mounts.

## 2. Wiring order

1. Remove the ENA and ENB jumpers on the L298N. Leave the +12V/5V-EN jumper in place.
2. Mount the Uno and L298N, L298N rotated so the terminal block faces the right wall.
3. Wire power (adapter polarity checked with a multimeter, 2 A fuse in the + line):
   - adapter + -> fuse -> L298N +12V, and a jumper from that +12V terminal to Arduino Vin
   - adapter - -> L298N GND, and a jumper from the GND terminal to Arduino GND
4. Leave the L298N +5V pin unconnected.
5. L298N inputs: D5 -> ENA, D7 -> IN1, D8 -> IN2, D6 -> ENB, D9 -> IN3, D10 -> IN4.
6. Pots: outer ends to 5V and GND, wipers to A0 (outer) and A1 (inner).
7. OLED (pin order GND VCC SCL SDA): GND -> GND, VCC -> 5V, SCL -> A5, SDA -> A4.
8. Switch (ON-OFF-ON): middle pin -> GND, one outer pin -> D2, other outer pin unused.
9. Motors: OUT1/OUT2 -> Motor 1 (outer axis); OUT3/OUT4 -> Motor 2 (inner axis) via the slip ring.
10. 0.1 uF ceramic across each motor, 470-1000 uF across the 12 V input.

## 2b. Fuse and switch details

Fuse (inline blade holder, one red lead each side, no polarity):
- Read the number printed on the fuse. Colour code: gray 2 A, violet 3 A, tan/amber 5 A, red 10 A.
- 5 A only protects against a dead short. It will NOT save a stalled motor. Prefer 2 A or 3 A.
- Adapter + -> holder lead 1. Holder lead 2 -> L298N +12V terminal (the Arduino Vin jumper shares this terminal, so Vin is also fused).
- Put the fuse in last, after the continuity checks. Close the rubber cover.

Switch (3-pin ON-OFF-ON rocker):
- Find the common with a multimeter on continuity: the pin that beeps with a different outer pin in each tilted position. Centre = no beep.
- Common -> GND. The outer pin you want for RUN -> D2. The other outer pin stays free.
- RUN = tilted to the wired side, STOP = centre or the other side.

## 3. First power-up

1. Upload the sketch by USB with the 12 V adapter and motors unplugged.
2. Check 12 V -> GND is not shorted, and GND is common (Arduino, L298N, pots, OLED).
3. Connect 12 V with the motors disconnected. The OLED should show data and follow the pots.
4. Connect Motor 1 off the frame, bench supply 12 V, current limit about 0.5 A.
5. Repeat for Motor 2, then fit on the frame, one axis at a time with the other locked.
