#include <WiFi.h>
#include <WebServer.h>
#include <HTTPClient.h>
#include <TridentTD_LineNotify.h>
#include <UrlEncode.h>

#define LINE_TOKEN "FbCTBCptFxcETZ06dwRKpJ9G3I9Ymh5UgIUtvEt32yt"

const char *ssid = "WiFi_314 - 2.4G";
const char *password = "Baramee2303";

int ledPin = 2;     // Pin number for the LED
int ledTogglePin = 23;     // Pin number for the LED
int buttonPin = 21; // Pin number for the button
int buzzer = 22;    // Pin number for the buzzer

WebServer server(80);

volatile bool buttonPressed = false;
volatile bool isRecognize = false;
unsigned long lastFaceRecognizedTime = 0;
const unsigned long recognitionTimeout = 20000; // 20 seconds in milliseconds

void buttonISR() {
  buttonPressed = true;
  Serial.println("BTN press");
}

void getRestartRecognizeProcess() {
  // Send HTTP POST request to restart recognition process
  // Example using HTTPClient:
  HTTPClient http;
  http.begin("http://192.168.1.4:5000/restart_recognize_process");
  int httpCode = http.GET();
  if (httpCode > 0) {
    Serial.println("Recognition process restarted");
    for (int i = 0; i < 2; i++) {
      digitalWrite(buzzer, LOW); // Turn the buzzer on
      delay(100); // Wait for 100 milliseconds
      digitalWrite(buzzer, HIGH); // Turn the buzzer off
      delay(200); // Wait for 100 milliseconds
    }
  } else {
    Serial.println("Error restarting recognition process");
  }
  http.end();
}

void sendDataToSheet(String log) {
  // Encode the string
  String encodedString = urlEncode(log);
  String url = "https://script.google.com/macros/s/AKfycbxgzRnbTXzu4O5_h9gSeHosuph9a3z7Er4OoCG88I05FB024uuXVkyrSWyAwSZLsz17/exec?log=" + encodedString;
  Serial.println("Sending data to Google Apps Script...");
  HTTPClient http;
  http.begin(url);
  int httpCode = http.GET();
  if (httpCode > 0) {
    Serial.printf("HTTP GET request status: %d\n", httpCode);
    String payload = http.getString();
    if(payload != "")
      Serial.println("Response payload: OK");
  } else {
    Serial.printf("HTTP GET request failed, error: %s\n", http.errorToString(httpCode).c_str());
  }
}

void setup() {
  Serial.begin(9600);
  delay(10);

  pinMode(ledPin, OUTPUT);
  digitalWrite(ledPin, LOW);
  pinMode(ledTogglePin, OUTPUT);
  digitalWrite(ledTogglePin, LOW);

  pinMode(buttonPin, INPUT_PULLUP); // Configure button pin as input with internal pull-up resistor
  pinMode(buzzer, OUTPUT);
  digitalWrite(buzzer, HIGH);

  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());

  LINE.setToken(LINE_TOKEN);

  // Setup API routes
  server.on("/api/turn_on_light", HTTP_POST, []() {
    digitalWrite(ledPin, HIGH);
    server.send(200, "text/plain", "Light turned on");
  });

  server.on("/api/turn_off_light", HTTP_POST, []() {
    digitalWrite(ledPin, LOW);
    server.send(200, "text/plain", "Light turned off");
  });

  server.on("/api/toggle_light", HTTP_POST, []() {
    digitalWrite(ledTogglePin, !digitalRead(ledTogglePin));
  server.send(200, "text/plain", "Light is toggle");
  });

  server.on("/api/face_recognized", HTTP_POST, []() {
    server.send(200, "text/plain", "Buzzer turned on");
    digitalWrite(buzzer, LOW);
    delay(500);
    digitalWrite(buzzer, HIGH);
    isRecognize = true;
    LINE.notify(server.arg("message"));
    sendDataToSheet(server.arg("message"));
    lastFaceRecognizedTime = millis(); // Record the time when face recognition occurred
  });

  server.begin();
  attachInterrupt(digitalPinToInterrupt(buttonPin), buttonISR, RISING);
}

void loop() {
  server.handleClient();
  
  if (buttonPressed) {
    buttonPressed = false; // Reset the flag
    getRestartRecognizeProcess();
  }
  
  // Check if it's time to restart recognition process
  if (millis() - lastFaceRecognizedTime >= recognitionTimeout && isRecognize) {
    getRestartRecognizeProcess();
    isRecognize = false;
  }
}
