// Rotocaster controller: 2 pots -> 2 worm gearmotors, 1.30" 128x64 I2C OLED
// URM / Biofluid Lab, Dr. Zahran
//
// Hardware: Arduino Uno, L298N driver, SH1106 OLED (SDA=A4, SCL=A5), RUN switch.
// Library:  "U8g2" by olikraus (Tools > Manage Libraries).
// L298N:    remove the ENA and ENB jumpers. Speed = PWM on EN pins, direction = IN pins.
// Switch:   ON-OFF-ON rocker. Middle pin to GND, one outer pin to D2 = RUN.
//
// Memory: the OLED uses the PAGE buffer (_1_), 128 bytes, instead of the full
// buffer (_F_), 1024 bytes. That keeps the Uno's 2 KB of RAM mostly free.

#include <Wire.h>
#include <U8g2lib.h>

// Most 1.30" modules are SH1106. If the picture is shifted right by 2 pixels or
// has a noisy strip at the edge, swap to the SSD1306 line.
U8G2_SH1106_128X64_NONAME_1_HW_I2C u8g2(U8G2_R0, U8X8_PIN_NONE);
// U8G2_SSD1306_128X64_NONAME_1_HW_I2C u8g2(U8G2_R0, U8X8_PIN_NONE);

// Pins
// Wiring corrections without moving wires. Flip true/false, then Upload again.
const bool SWAP_POTS   = true;    // true: the pot on A1 is used as OUTER, the pot on A0 as INNER
const bool SWAP_MOTORS = true;   // true: Outer drives the L298N B channel instead of A
const bool SWAP_SCREEN = true;   // true: the "Outer" and "Inner" screen lines trade places
                                 // (screen labels only, does not change what the motors do)

const uint8_t POT_OUTER = SWAP_POTS ? A1 : A0;
const uint8_t POT_INNER = SWAP_POTS ? A0 : A1;
const uint8_t M1_EN  = SWAP_MOTORS ? 6 : 5,  M1_IN1 = SWAP_MOTORS ? 9 : 7,  M1_IN2 = SWAP_MOTORS ? 10 : 8;   // outer axis
const uint8_t M2_EN  = SWAP_MOTORS ? 5 : 6,  M2_IN1 = SWAP_MOTORS ? 7 : 9,  M2_IN2 = SWAP_MOTORS ? 8 : 10;   // inner axis
const uint8_t RUN_SW = 2;                             // to GND = RUN, open = STOP

// Tuning
const float MAX_RPM   = 18.0;    // nameplate no-load. Display is an estimate (no encoder)
const int   MIN_PWM   = 60;      // lowest PWM that reliably starts a motor. L298N drops ~2 V,
                                 // so this is higher than on a bare driver. Tune on the bench.
const int   MAX_PWM   = 255;
const int   POT_DEAD  = 30;      // pot counts near zero = off
const float RAMP_TIME = 15.0;    // seconds from 0 to full, as in the torque calculation
const unsigned long LOOP_MS = 20;
const unsigned long LCD_MS  = 300;

float outPwm[2] = {0, 0};        // current (ramped) PWM per motor
unsigned long lastLoop = 0, lastLcd = 0;

int readPot(uint8_t pin) {       // 8-sample average to stop jitter
  long s = 0;
  for (uint8_t i = 0; i < 8; i++) s += analogRead(pin);
  return s / 8;
}

int potToPwm(int raw) {
  if (raw < POT_DEAD) return 0;
  return map(raw, POT_DEAD, 1023, MIN_PWM, MAX_PWM);
}

void drive(uint8_t en, uint8_t in1, uint8_t in2, int pwm) {
  digitalWrite(in1, HIGH);       // one direction only; swap HIGH/LOW (or the motor wires) to reverse
  digitalWrite(in2, LOW);
  analogWrite(en, pwm);          // 0 = stopped (worm gear self-locks)
}

void setup() {
  pinMode(RUN_SW, INPUT_PULLUP);
  pinMode(M1_EN, OUTPUT); pinMode(M1_IN1, OUTPUT); pinMode(M1_IN2, OUTPUT);
  pinMode(M2_EN, OUTPUT); pinMode(M2_IN1, OUTPUT); pinMode(M2_IN2, OUTPUT);
  drive(M1_EN, M1_IN1, M1_IN2, 0);
  drive(M2_EN, M2_IN1, M2_IN2, 0);

  u8g2.begin();
  u8g2.setBusClock(400000);      // faster I2C, shorter screen refresh
  u8g2.setFont(u8g2_font_7x13B_tr);
  u8g2.firstPage();
  do {
    u8g2.drawStr(18, 28, "ROTOCASTER");
    u8g2.drawStr(30, 46, "CONTROLLER");
  } while (u8g2.nextPage());
  delay(1200);
}

// Builds "Outer  72%  9.4rpm" into buf
void formatLine(char *buf, size_t n, const char *name, float pwm) {
  int pct = (int)(pwm * 100.0 / MAX_PWM + 0.5);
  float rpm = pwm * MAX_RPM / MAX_PWM;
  char r[8];
  dtostrf(rpm, 4, 1, r);
  snprintf(buf, n, "%s %3d%% %srpm", name, pct, r);
}

void drawScreen(bool run) {
  char l1[24], l2[24];
  uint8_t top = SWAP_SCREEN ? 1 : 0;      // which channel the "Outer" line shows
  formatLine(l1, sizeof(l1), "Outer", outPwm[top]);
  formatLine(l2, sizeof(l2), "Inner", outPwm[1 - top]);

  u8g2.firstPage();
  do {
    u8g2.setFont(u8g2_font_7x13B_tr);
    u8g2.drawStr(0, 12, run ? "RUN" : "STOP  (switch off)");
    u8g2.drawHLine(0, 16, 128);
    u8g2.setFont(u8g2_font_6x12_tr);
    u8g2.drawStr(0, 36, l1);
    u8g2.drawStr(0, 56, l2);
  } while (u8g2.nextPage());
}

void loop() {
  unsigned long now = millis();
  if (now - lastLoop < LOOP_MS) return;
  float dt = (now - lastLoop) / 1000.0;   // real elapsed time, so the ramp stays 15 s
  lastLoop = now;                          // even when the screen redraw takes a while

  bool run = (digitalRead(RUN_SW) == LOW);
  int target[2] = {0, 0};
  if (run) {
    target[0] = potToPwm(readPot(POT_OUTER));
    target[1] = potToPwm(readPot(POT_INNER));
  }

  // Ramp toward target. Stopping is immediate (switch off or pot at zero).
  const float step = (float)MAX_PWM / RAMP_TIME * dt;
  for (uint8_t i = 0; i < 2; i++) {
    if (target[i] == 0)               outPwm[i] = 0;
    else if (outPwm[i] < target[i])   outPwm[i] = min(outPwm[i] + step, (float)target[i]);
    else                              outPwm[i] = max(outPwm[i] - step, (float)target[i]);
    // A running motor never sits below MIN_PWM, so it can't stall in the low range.
    if (target[i] > 0 && outPwm[i] < MIN_PWM) outPwm[i] = MIN_PWM;
  }

  drive(M1_EN, M1_IN1, M1_IN2, (int)outPwm[0]);
  drive(M2_EN, M2_IN1, M2_IN2, (int)outPwm[1]);

  if (now - lastLcd > LCD_MS) {
    lastLcd = now;
    drawScreen(run);                       // blocks ~50 ms; motors keep their last PWM
  }
}
