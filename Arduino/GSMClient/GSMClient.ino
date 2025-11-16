#include <GSM.h>
#include <Arduino_DebugUtils.h>
#include "arduino_secrets.h"

// SIM credentials
char pin[]      = SECRET_PIN;
char apn[]      = SECRET_APN;
char username[] = SECRET_USERNAME;
char pass[]     = SECRET_PASSWORD;

// Server details
const char server[] = "api.restful-api.dev";
const int port = 80;

// PIR sensor
#define PIR_PIN A0

GSMClient client;

void setup() {
  Serial.begin(9600);
  while(!Serial) {}
  
  pinMode(PIR_PIN, INPUT);
  
  Serial.println("=== PIR + Cellular System ===");
  
  Serial.println("Waiting 30 seconds for PIR to stabilize...");
  delay(30000);
  Serial.println("✓ PIR ready");
  
  // Connect to network AFTER PIR is stable
  Serial.println("\nConnecting to cellular network...");
  if(!GSM.begin(pin, apn, username, pass, CATNB)){
    Serial.println("Failed to connect to network");
    while(1);
  }
  
  Serial.println("✓ Connected to network");
  Serial.print("✓ Local IP: ");
  Serial.println(GSM.localIP());
  
  Serial.println("\nSystem ready. Monitoring for motion...");
}

void loop() {
  // Check for motion
  if (digitalRead(PIR_PIN) == HIGH) {
    Serial.println("\n>>> Motion detected! Sending data...");
    
    if (sendMotionData()) {
      Serial.println("✓ Data sent successfully");
    } else {
      Serial.println("✗ Failed to send data");
    }
    
    // Wait 10 seconds before detecting again
    delay(10000);
  }
  
  delay(100);
}

bool sendMotionData() {
  // Wait for modem to stabilize if it was re-registering
  Serial.println("Waiting 3 seconds for network to stabilize...");
  delay(3000);
  
  // Check network status
  Serial.println("Checking network status...");
  Serial.print("  IP Address: ");
  Serial.println(GSM.localIP());
  
  IPAddress serverIP;
  
  // Try to resolve DNS
  Serial.print("Resolving DNS for ");
  Serial.print(server);
  Serial.println("...");
  
  int dnsResult = GSM.hostByName(server, serverIP);
  if (dnsResult == 1) {
    Serial.print("  ✓ Resolved to: ");
    Serial.println(serverIP);
  } else {
    Serial.print("  ✗ DNS resolution failed, error code: ");
    Serial.println(dnsResult);
    return false;
  }
  
  // Try to connect
  Serial.print("Connecting to ");
  Serial.print(serverIP);
  Serial.print(":");
  Serial.print(port);
  Serial.println("...");
  
  if (!client.connect(serverIP, port)) {
    Serial.println("  ✗ TCP connection failed");
    Serial.println("  This might be a firewall/NB-IoT TCP restriction");
    return false;
  }
  
  Serial.println("  ✓ Connected to server");
  
  // Build JSON payload
  String jsonData = "{";
  jsonData += "\"name\":\"PIR Motion Sensor\",";
  jsonData += "\"data\":{";
  jsonData += "\"motion\":true,";
  jsonData += "\"timestamp\":\"" + String(millis()) + "\"";
  jsonData += "}";
  jsonData += "}";
  
  Serial.println("Sending HTTP POST...");
  
  // Send HTTP POST request
  client.println("POST /objects HTTP/1.1");
  client.print("Host: ");
  client.println(server);
  client.println("Content-Type: application/json");
  client.print("Content-Length: ");
  client.println(jsonData.length());
  client.println("Connection: close");
  client.println();
  client.println(jsonData);
  
  Serial.println("  Request sent, waiting for response...");
  
  // Wait for response
  unsigned long timeout = millis();
  bool gotResponse = false;
  while (client.connected() && millis() - timeout < 10000) {
    if (client.available()) {
      String line = client.readStringUntil('\n');
      Serial.println(line);
      gotResponse = true;
    }
  }
  
  if (!gotResponse) {
    Serial.println("  ✗ No response received (timeout)");
  }
  
  client.stop();
  return gotResponse;
}