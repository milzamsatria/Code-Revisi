// Pin untuk motor dan encoder
const int enA = 5;
const int in1 = 7;
const int in2 = 6;
const int encoderPin = 2;

// Konstanta
const int PPR = 11; // Pulsa per rotasi encoder
const unsigned long interval = 50; // Interval untuk menghitung RPM

// Variabel global
volatile int pulseCount = 0;
unsigned long previousMillis = 0;
double rpm = 0;
bool motorRunning = false;
bool dataSending = false; // Hanya kirim data jika "START" diterima
double setpoint = 0;
double input = 0;
double output = 0;

// Parameter PID
double kp = 1.0, ki = 0.5, kd = 0.1;
double previousError = 0;
double integral = 0;

void setup() {
  pinMode(enA, OUTPUT);
  pinMode(in1, OUTPUT);
  pinMode(in2, OUTPUT);
  pinMode(encoderPin, INPUT);
  attachInterrupt(digitalPinToInterrupt(encoderPin), countPulse, RISING);

  Serial.begin(9600);
  Serial.println("Sistem siap.");
}

void countPulse() {
  pulseCount++;
}

void loop() {
  // Periksa input serial
  if (Serial.available() > 0) {
    String inputStr = Serial.readStringUntil('\n');
    processInput(inputStr);
  }

  // Hitung RPM
  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;

    float alpha = 0.1; // Koefisien filter (0 < alpha < 1, lebih kecil berarti lebih halus)
    rpm = alpha * ((pulseCount / (double)PPR) / 9.6) * 600.0 + (1 - alpha) * rpm;
    pulseCount = 0; 

    // Hitung PID manual
    input = rpm;
    double error = setpoint - input;
    integral += error * (interval / 1000.0); // Integrasi
    double derivative = (error - previousError) / (interval / 1000.0); // Turunan
    output = (kp * error) + (ki * integral) + (kd * derivative);
    previousError = error;

    // Batasi output agar berada di antara 0 dan 255
    if (output > 255) output = 255;
    if (output < 0) output = 0;

    if (motorRunning) {
      analogWrite(enA, output);
    }

    // Kirim data jika "START"
    if (dataSending) {
      Serial.print("RPM:"); Serial.print(rpm);
      Serial.print(",SETPOINT:"); Serial.print(setpoint);
      Serial.print(",OUTPUT:"); Serial.print(output);
      Serial.print(",KP:"); Serial.print(kp);
      Serial.print(",KI:"); Serial.print(ki);
      Serial.print(",KD:"); Serial.println(kd);
    }
  }
}

void processInput(String input) {
  input.trim();
  input.toUpperCase();

  if (input.startsWith("F")) { // Arah searah jarum jam (Clockwise)
    setpoint = input.substring(1).toFloat();
    if (setpoint >= 0) {
      motorRunning = true;
      dataSending = true; // Mulai kirim data
      digitalWrite(in1, LOW);
      digitalWrite(in2, HIGH);
      Serial.print("Motor bergerak searah jarum jam dengan setpoint: ");
      Serial.println(setpoint);
    }
  } else if (input.startsWith("R")) { // Arah berlawanan jarum jam (Counter Clockwise)
    setpoint = input.substring(1).toFloat();
    if (setpoint >= 0) {
      motorRunning = true;
      dataSending = true; // Mulai kirim data
      digitalWrite(in1, HIGH);
      digitalWrite(in2, LOW);
      Serial.print("Motor bergerak berlawanan jarum jam dengan setpoint: ");
      Serial.println(setpoint);
    }
  } else if (input.startsWith("KP")) {
    kp = input.substring(2).toFloat();
    Serial.print("KP diperbarui menjadi: ");
    Serial.println(kp);
  } else if (input.startsWith("KI")) {
    ki = input.substring(2).toFloat();
    Serial.print("KI diperbarui menjadi: ");
    Serial.println(ki);
  } else if (input.startsWith("KD")) {
    kd = input.substring(2).toFloat();
    Serial.print("KD diperbarui menjadi: ");
    Serial.println(kd);
  } else if (input == "STOP") { // Perintah berhenti
    analogWrite(enA, 0);
    motorRunning = false;
    dataSending = false; // Hentikan pengiriman data
    digitalWrite(in1, LOW);
    digitalWrite(in2, LOW);
    Serial.println("Motor berhenti.");
  } else if (input == "START") {
    motorRunning = true;
    dataSending = true; // Mulai pengiriman data
    Serial.println("Motor mulai.");
  } else {
    Serial.println("Perintah tidak dikenali.");
  }
}
