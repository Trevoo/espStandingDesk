#include <Arduino.h>
#include <BluetoothSerial.h>

// --- Pin Definitions ---
const int motor1Pin1 = 27;  // IN1 on the H-Bridge
const int motor1Pin2 = 26;  // IN2 on the H-Bridge
const int enable1Pin = 14;  // ENA on the H-Bridge (for PWM speed control)
const int buttonUp   = 25;  // Moves motor "forward"
const int buttonDown = 33;  // Moves motor "backward"

// --- PWM Configuration ---
const int PWM_FREQ        = 5000;
const int PWM_CHANNEL     = 0;
const int PWM_RESOLUTION  = 8;
const int MAX_DUTY_CYCLE  = 255;
const unsigned int RAMP_DURATION = 1000; // Ramp-up time in milliseconds

// --- Bluetooth Configuration ---
BluetoothSerial SerialBT;
const char* bluetoothPin = "2144";

// --- Motor State Machine ---
enum MotorState { STOPPED, RAMPING, RUNNING };
enum MotorDirection { FORWARD, BACKWARD };
MotorState motorState = STOPPED;
MotorDirection motorDirection;
unsigned long rampStartTime;

// Variables to track button states for press/release events
bool btnUpActive = false;
bool btnDownActive = false;

// --- Setup Function ---
void setup() {
  Serial.begin(115200);

  // --- Pin Modes ---
  pinMode(motor1Pin1, OUTPUT);
  pinMode(motor1Pin2, OUTPUT);
  pinMode(buttonUp, INPUT_PULLDOWN);
  pinMode(buttonDown, INPUT_PULLDOWN);

  // --- PWM Setup ---
  ledcSetup(PWM_CHANNEL, PWM_FREQ, PWM_RESOLUTION);
  ledcAttachPin(enable1Pin, PWM_CHANNEL);
  ledcWrite(PWM_CHANNEL, 0); // Start with motor off

  // --- Bluetooth Setup ---
  Serial.println("Starting Bluetooth...");
  SerialBT.setPin(bluetoothPin);
  SerialBT.begin("ESP32_Motor_Control");
  Serial.println("Bluetooth started. Device is ready to pair.");
  Serial.println("Ready for button or Bluetooth control.");
}


// --- Motor Control Logic ---

// Function to start the motor moving in a specific direction
void startMotor(MotorDirection dir) {
  // Only start if currently stopped
  if (motorState == STOPPED) {
    motorDirection = dir;
    motorState = RAMPING;
    rampStartTime = millis();

    if (dir == FORWARD) {
      Serial.println("Command: FORWARD");
      digitalWrite(motor1Pin1, HIGH);
      digitalWrite(motor1Pin2, LOW);
    } else { // BACKWARD
      Serial.println("Command: BACKWARD");
      digitalWrite(motor1Pin1, LOW);
      digitalWrite(motor1Pin2, HIGH);
    }
  }
}

// Function to stop the motor
void stopMotor() {
  if (motorState != STOPPED) {
    Serial.println("Command: STOP");
    motorState = STOPPED;
    digitalWrite(motor1Pin1, LOW);
    digitalWrite(motor1Pin2, LOW);
    ledcWrite(PWM_CHANNEL, 0);
  }
}

// --- Input Handling ---

void handlePhysicalButtons() {
  // Check FORWARD button
  if (digitalRead(buttonUp) && !btnUpActive) {
    btnUpActive = true;
    startMotor(FORWARD);
  } else if (!digitalRead(buttonUp) && btnUpActive) {
    btnUpActive = false;
    stopMotor();
  }

  // Check BACKWARD button
  if (digitalRead(buttonDown) && !btnDownActive) {
    btnDownActive = true;
    startMotor(BACKWARD);
  } else if (!digitalRead(buttonDown) && btnDownActive) {
    btnDownActive = false;
    stopMotor();
  }
}

void handleBluetoothCommands() {
  if (SerialBT.available()) {
    char cmd = SerialBT.read();
    if (cmd == 'F' || cmd == 'f') {
      startMotor(FORWARD);
    } else if (cmd == 'B' || cmd == 'b') {
      startMotor(BACKWARD);
    } else if (cmd == 'S' || cmd == 's') {
      stopMotor();
    }
  }
}

// --- Main State Machine Logic ---
// This function runs every loop and updates the motor speed during ramp-up
void updateMotor() {
  if (motorState == RAMPING) {
    unsigned long elapsedTime = millis() - rampStartTime;
    if (elapsedTime >= RAMP_DURATION) {
      // Ramp finished, go to full speed
      ledcWrite(PWM_CHANNEL, MAX_DUTY_CYCLE);
      motorState = RUNNING;
    } else {
      // Calculate intermediate speed
      int dutyCycle = map(elapsedTime, 0, RAMP_DURATION, 0, MAX_DUTY_CYCLE);
      ledcWrite(PWM_CHANNEL, dutyCycle);
    }
  }
}

// --- Main Loop ---
void loop() {
  // Handle all inputs
  handleBluetoothCommands();    // Listen for Bluetooth commands
  handlePhysicalButtons();      // Check physical button presses

  // Update motor state (manages the speed ramp)
  updateMotor();
}