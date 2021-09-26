unsigned int now;

int clkpin = 6;
int datapin = 7;


typedef struct {
  int maxbits;
  int curbits;
  int lastclk;
  unsigned int clear_interval;
  unsigned long long int reg;
  unsigned long int lasttime;
  unsigned long words_received;
  unsigned long edgecount = 0;
} shift_register_t;

void assert(int x) {
  if (!x) {
    while (1) {
      Serial.println("ASSERT!");
      delay(1000);
    }
  }
}


void sr_init(shift_register_t *sr, int maxbits, unsigned int clear_interval_millis) {
  assert(maxbits > 0 && maxbits < 64);
  memset(sr, 0, sizeof(*sr));
  sr->lasttime = millis();
  sr->maxbits = maxbits;
  sr->clear_interval = clear_interval_millis;
}

void printreg(unsigned long long reg) {
      unsigned long long upper = reg >> 32;
      unsigned long long lower = reg & 0xFFFFFFFF;
      unsigned int iupper = upper;
      unsigned int ilower = lower;
      char format[30];

      sprintf(format, "0x%08x%08x", iupper, ilower);
      Serial.print(format);
}

void sr_shift(shift_register_t *sr, int clk, int dat) {
  unsigned long now = millis();
  if (clk && (clk != sr->lastclk)) {
    sr->edgecount++;
    // rising edge of clock;
    sr->reg <<= 1;
    sr->reg |= !!dat;
    sr->curbits++;
    if (sr->curbits == sr->maxbits) {
//        Serial.print(sr->edgecount);
//        Serial.print(" ");
//        Serial.print(sr->words_received);
//        Serial.print(" 0x");
        printreg(sr->reg);
        Serial.println();
      sr->curbits=0;
      sr->reg = 0;
      sr->words_received ++;
    }
  }
  if ((now - sr->lasttime) > sr->clear_interval) {
    sr->reg = 0;
    sr->curbits = 0;
  }
  sr->lastclk = clk;
  sr->lasttime = now;
}

shift_register_t sr;
void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  pinMode(clkpin, INPUT);
  pinMode(datapin, INPUT);
  now = millis();
  sr_init(&sr, 40, 30);
  Serial.println(sizeof(sr.reg));
}

void loop() {
  int clk = digitalRead(clkpin);
  int dat = digitalRead(datapin);
  sr_shift(&sr, clk, dat);
}
