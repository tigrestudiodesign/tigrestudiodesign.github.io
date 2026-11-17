/*
  TIGRE SY-5000 · TINKERCAD PROOF OF CONTROLS
  Arduino Uno R3 · 8 keys · 4 knobs · mode button · piezo · note LED
  Paste into Tinkercad Circuits (Code > Text) after wiring per the table below.

  WIRING
  D2..D9   Pushbuttons (keys C D E F G A B C). One leg to the pin, other leg to GND. INPUT_PULLUP, no resistors.
  D10      Pushbutton MODE (PLAY > ARP > DRUM). Pin to GND.
  D11      Piezo +   (piezo - to GND)
  D13      LED anode through 220 ohm to pin, cathode to GND (note on)
  A0       Pot 1 OCTAVE   (outer legs 5V / GND, wiper to A0), 10k
  A1       Pot 2 VIBRATO  depth (also glide in PLAY)
  A2       Pot 3 DECAY    note length in ARP / DRUM
  A3       Pot 4 TEMPO    60..200 BPM for ARP / DRUM
  All grounds common. Power from USB.

  NOTE: tone() makes one square wave at a time, so this is the control surface
  and logic of the SY-5000, not its sound engine.
*/

const byte KEY_PINS[8] = {2, 3, 4, 5, 6, 7, 8, 9};
const byte MODE_PIN = 10;
const byte SPK = 11;
const byte LED = 13;
const int  SEMI[8] = {0, 2, 4, 5, 7, 9, 11, 12};     // C major, one octave

void bootChime(); void runPlay(); void runArp(); void runDrum();   // forward declarations

enum Mode { PLAY, ARP, DRUM };
Mode mode = PLAY;

// --- debounced buttons ---
bool keyState[8], keyRaw[8];
unsigned long keyT[8];
bool modeState = false, modeRaw = false;
unsigned long modeT = 0;
const unsigned long DEBOUNCE = 12;

// --- knobs (smoothed) ---
int pot[4];
void readPots() {
  for (byte i = 0; i < 4; i++) {
    int r = analogRead(A0 + i);
    pot[i] = pot[i] + ((r - pot[i]) >> 2);            // simple IIR smoothing
  }
}

float midiToHz(float m) { return 440.0 * pow(2.0, (m - 69.0) / 12.0); }

// --- PLAY state ---
int heldNote = -1;               // index of lowest held key (mono, low-note priority)
float curHz = 0, targetHz = 0;

// --- ARP / DRUM sequencer ---
unsigned long nextStep = 0;
byte step = 0;
unsigned long ledOff = 0;            // when to turn the note LED off in ARP / DRUM
const char DRUMS[16] = {'K','h','S','h','K','h','S','o','K','K','S','h','K','h','S','o'};

void setup() {
  for (byte i = 0; i < 8; i++) pinMode(KEY_PINS[i], INPUT_PULLUP);
  pinMode(MODE_PIN, INPUT_PULLUP);
  pinMode(SPK, OUTPUT);
  pinMode(LED, OUTPUT);
  for (byte i = 0; i < 4; i++) pot[i] = analogRead(A0 + i);
  Serial.begin(9600);
  Serial.println(F("SY-5000 TINKERCAD READY  MODE: PLAY"));
  bootChime();
}

void bootChime() {
  const int n[3] = {60, 67, 72};
  for (byte i = 0; i < 3; i++) { tone(SPK, midiToHz(n[i]), 70); delay(90); }
  noTone(SPK);
}

bool readButton(byte pin, bool &raw, bool &state, unsigned long &t) {
  bool r = digitalRead(pin) == LOW;                    // pressed = LOW (pull-up)
  if (r != raw) { raw = r; t = millis(); }
  if (millis() - t > DEBOUNCE && state != raw) { state = raw; return true; }  // changed
  return false;
}

int octaveShift() { return map(pot[0], 0, 1023, -2, 2) * 12; }   // -2..+2 octaves
int tempoBpm()    { return map(pot[3], 0, 1023, 60, 200); }
int decayMs(int stepMs) { return map(pot[2], 0, 1023, 15, stepMs - 5); }

void loop() {
  readPots();

  for (byte i = 0; i < 8; i++) readButton(KEY_PINS[i], keyRaw[i], keyState[i], keyT[i]);
  if (readButton(MODE_PIN, modeRaw, modeState, modeT) && modeState) {
    mode = (Mode)((mode + 1) % 3);
    noTone(SPK); digitalWrite(LED, LOW); step = 0; nextStep = millis();
    Serial.print(F("MODE: ")); Serial.println(mode == PLAY ? F("PLAY") : mode == ARP ? F("ARP") : F("DRUM"));
  }

  if (mode == PLAY) runPlay();
  else if (mode == ARP) runArp();
  else runDrum();
}

void runPlay() {
  int low = -1;
  for (byte i = 0; i < 8; i++) if (keyState[i]) { low = i; break; }
  if (low < 0) {
    if (heldNote >= 0) { noTone(SPK); digitalWrite(LED, LOW); heldNote = -1; curHz = 0; }
    return;
  }
  float base = midiToHz(60 + SEMI[low] + octaveShift());
  if (low != heldNote) {
    heldNote = low; targetHz = base;
    if (curHz == 0) curHz = base;                        // first note: no glide
    digitalWrite(LED, HIGH);
  }
  // glide toward target, then vibrato around it (pot 2)
  float depth = pot[1] / 1023.0;                         // 0..1
  curHz += (targetHz - curHz) * (0.08 + (1.0 - depth) * 0.6);
  float vib = sin(millis() * 0.0345) * depth * 0.03;     // ~5.5 Hz, up to +-3 %
  tone(SPK, max(31, (int)(curHz * (1.0 + vib))));
  delay(4);
}

void runArp() {
  // arpeggiate every held key, up then down; with nothing held, play a C major arp
  int held[8], n = 0;
  for (byte i = 0; i < 8; i++) if (keyState[i]) held[n++] = i;
  if (n == 0) { held[0] = 0; held[1] = 2; held[2] = 4; held[3] = 7; n = 4; }
  unsigned long now = millis();
  int stepMs = 60000L / tempoBpm() / 4;                  // 16th notes
  if ((long)(now - nextStep) >= 0) {
    int cyc = n > 1 ? 2 * n - 2 : 1;
    int k = step % cyc; int idx = k < n ? k : cyc - k;
    float hz = midiToHz(60 + SEMI[held[idx]] + octaveShift());
    tone(SPK, (int)hz, decayMs(stepMs));
    digitalWrite(LED, HIGH); ledOff = now + decayMs(stepMs);
    step++; nextStep = now + stepMs;
  }
  if ((long)(now - ledOff) >= 0) digitalWrite(LED, LOW);
}

void runDrum() {
  // tone() can't make noise, so drums are short pitched clicks: kick low sweep, snare mid, hats high
  unsigned long now = millis();
  int stepMs = 60000L / tempoBpm() / 4;
  if ((long)(now - nextStep) >= 0) {
    char d = DRUMS[step % 16];
    int len = decayMs(stepMs);
    if (d == 'K') { tone(SPK, 90 + (pot[0] >> 4), min(len, 60)); digitalWrite(LED, HIGH); ledOff = now + 60; }
    else if (d == 'S') { tone(SPK, 420, min(len, 45)); digitalWrite(LED, HIGH); ledOff = now + 45; }
    else if (d == 'h') { tone(SPK, 3800, 8); }
    else if (d == 'o') { tone(SPK, 3200, min(len, 30)); }
    // keys add fills: any held key replaces the hat with that note's pitch
    for (byte i = 0; i < 8; i++) if (keyState[i] && (d == 'h' || d == 'o')) tone(SPK, (int)midiToHz(72 + SEMI[i]), 25);
    step++; nextStep = now + stepMs;
  }
  if ((long)(now - ledOff) >= 0) digitalWrite(LED, LOW);
}
