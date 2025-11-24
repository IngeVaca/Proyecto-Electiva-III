/* MIT License

Copyright (c) 2025 Jhon Jaime Vaca Hincapie

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Para publicar en Thingspeak se debe acceder a una red WIFI con internet, para leer en modo local el borcker,
el dispisitivo que aloja el servidor web y la esp32 deben estar en la misma red WIFI
*/
  

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <PubSubClient.h>
#include "DHT.h"

float k = 2.85; // Constante para calibración de tensión eléctrica 

// --- CONFIGURACIÓN WIFI ---
const char* ssid = "RED WIFI";
const char* password = "CLAVE WIFI";

// --- CONFIGURACIÓN THINGSPEAK ---
const char* server = "http://api.thingspeak.com/update";
String apiKey = "API KEY DEL PROYECTO EN THINGSPEAK";   // API Key

// --- CONFIGURACIÓN EMQX MQTT ---
const char* mqttServer = "IP Brocker"; // IP de tu broker EMQX
const int mqttPort = 1883;
const char* mqttTopic = "FULL/panel";
const char* mqttClientId = "ESP32_Energy_Monitor";

// --- SENSOR DHT22 ---
#define DHTPIN 4
DHT dht4(DHTPIN, DHT22);

// --- Pines y parámetros eléctricos ---
#define PIN_VOLT 35
#define PIN_CURR 34
#define REF_VOLTAGE 3.3
#define ADC_RESOLUTION 4095.0
#define R1 30000.0
#define R2 7500.0

// Sensibilidad ACS712 ajustada para divisor 2/3
const float mVperAmp = 185.0 * (2.0 / 3.0);  // ~123.3 mV/A

// Factor de calibración manual
const float factorCalibracion = 16.2;

// EMA
const float alfa = 0.5;
float IDC_ema = 0.0;  // corriente suavizada

// Buffer para promedio de 50 muestras
const int bufferSize = 50;
float bufferEMA[bufferSize] = {0};
int bufferIndex = 0;
bool bufferLleno = false;

float Vref = 0.0;

unsigned long ultimaPublicacion = 0;
const unsigned long intervaloPublicacion = 30000;  // 30 segundos
const unsigned long intervaloLectura = 5000;       // 5 segundos

// Manejo de errores DHT22
int dhtErrorCount = 0;
const int maxDhtErrors = 5;  // reinicia si hay 5 errores consecutivos

// Clientes WiFi y MQTT
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

void conectarWiFi() {
  Serial.println("\n=== Conectando a WiFi ===");
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  int intentos = 0;
  while (WiFi.status() != WL_CONNECTED && intentos < 20) {
    Serial.print(".");
    delay(500);
    intentos++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nConectado a WiFi");
    Serial.print("Dirección IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nNo se pudo conectar. Reiniciando...");
    delay(5000);
    ESP.restart();
  }
}

void reconnectMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("Conectando a EMQX MQTT...");
    
    if (mqttClient.connect(mqttClientId)) {
      Serial.println("conectado!");
    } else {
      Serial.print("falló, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" intentando en 5 segundos...");
      delay(5000);
    }
  }
}

// Función para publicar en MQTT
void publicarMQTT(float temperatura, float humedad, float VDC, float IDC_promedio, float potencia) {
  if (!mqttClient.connected()) {
    reconnectMQTT();
  }
  
  // Crear documento JSON
  StaticJsonDocument<512> doc;
  
  // Agregar timestamp
  doc["timestamp"] = millis();
  
  // Agregar datos de sensores
  doc["temperatura"] = round(temperatura * 10) / 10.0;  // 1 decimal
  doc["humedad"] = round(humedad * 10) / 10.0;          // 1 decimal
  doc["voltaje"] = round(VDC * 100) / 100.0;            // 2 decimales
  doc["corriente"] = round(IDC_promedio * 1000) / 1000.0; // 3 decimales
  doc["potencia"] = round(potencia * 100) / 100.0;      // 2 decimales
  
  // Agregar metadatos
  doc["sensor"] = "ESP32_Energy_Monitor";
  doc["version"] = "1.0";
  doc["unidades"] = "C|%|V|A|W";
  
  // Serializar JSON a string
  String jsonString;
  serializeJson(doc, jsonString);
  
  Serial.println("Enviando JSON a MQTT:");
  Serial.println(jsonString);
  
  // Publicar en MQTT
  if (mqttClient.publish(mqttTopic, jsonString.c_str())) {
    Serial.println("Datos enviados a EMQX via MQTT");
  } else {
    Serial.println("Error enviando a MQTT");
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  conectarWiFi();
  
  // Configurar MQTT
  mqttClient.setServer(mqttServer, mqttPort);
  mqttClient.setBufferSize(512); // Aumentar buffer para JSON
  
  dht4.begin();
  analogSetAttenuation(ADC_11db);

  // Calibrar Vref sin carga (promediando 200 lecturas)
  float suma = 0;
  const int calibracionLecturas = 200;
  for (int i = 0; i < calibracionLecturas; i++) {
      suma += analogRead(PIN_CURR);
      delay(1);
  }
  Vref = (suma / calibracionLecturas) * REF_VOLTAGE / ADC_RESOLUTION;
  Serial.printf("Vref calibrado: %.5f V\n", Vref);

  // Inicializar EMA con primera lectura
  int adc = analogRead(PIN_CURR);
  float voltageCurr = (adc * REF_VOLTAGE) / ADC_RESOLUTION;
  IDC_ema = fabs(((voltageCurr - Vref) / (mVperAmp / 1000.0)) * factorCalibracion);
  
  // Inicializar buffer de promedio
  for (int i = 0; i < bufferSize; i++) bufferEMA[i] = IDC_ema;
  
  Serial.println("Sistema inicializado - Listo para enviar a ThingSpeak y EMQX");
}

void loop() {
  static unsigned long ultimaLectura = 0;

  // Mantener conexión MQTT
  if (!mqttClient.connected()) {
    reconnectMQTT();
  }
  mqttClient.loop();

  if (millis() - ultimaLectura >= intervaloLectura) {
    ultimaLectura = millis();

    // --- LECTURA DEL DHT22 ---
    float temperatura = dht4.readTemperature();
    float humedad = dht4.readHumidity();

    if (isnan(temperatura) || isnan(humedad)) {
        Serial.println("Error leyendo DHT22");
        dhtErrorCount++;

        if (dhtErrorCount >= maxDhtErrors) {
            Serial.println("DHT colgado. Reiniciando micro...");
            delay(100);
            ESP.restart();
        }

        if (isnan(temperatura)) temperatura = -1;
        if (isnan(humedad)) humedad = -1;
    } else {
        dhtErrorCount = 0; // lectura exitosa
    }

    // --- LECTURA DE VOLTAJE ---
    int adcValue = analogRead(PIN_VOLT);
    float voltageADC = (adcValue * REF_VOLTAGE) / ADC_RESOLUTION;
    float VDC = k * voltageADC * (R1 + R2) / R2;

    // --- LECTURA DE CORRIENTE DC ---
    int adc = analogRead(PIN_CURR);
    float voltageCurr = (adc * REF_VOLTAGE) / ADC_RESOLUTION;

    float IDC_actual = fabs(((voltageCurr - Vref) / (mVperAmp / 1000.0)) * factorCalibracion);

    // EMA
    IDC_ema = alfa * IDC_actual + (1 - alfa) * IDC_ema;

    // Buffer promedio
    bufferEMA[bufferIndex] = IDC_ema;
    bufferIndex = (bufferIndex + 1) % bufferSize;
    if (bufferIndex == 0) bufferLleno = true;

    float IDC_promedio = 0;
    int n = bufferLleno ? bufferSize : bufferIndex;
    for (int i = 0; i < n; i++) IDC_promedio += bufferEMA[i];
    IDC_promedio /= n;

    if (IDC_promedio < 0.01) IDC_promedio = 0.0;

    float potencia = VDC * IDC_promedio;

    // --- PUBLICACIÓN cada 30s ---
    if (millis() - ultimaPublicacion >= intervaloPublicacion) {
        ultimaPublicacion = millis();

        // 1. ENVIAR A THINGSPEAK
        String url = String(server) + "?api_key=" + apiKey +
                     "&field1=" + String(temperatura, 1) +
                     "&field2=" + String(humedad, 1) +
                     "&field3=" + String(VDC, 2) +
                     "&field4=" + String(IDC_promedio, 3) +
                     "&field5=" + String(potencia, 2);

        Serial.println("\n=== ENVIANDO DATOS ===");
        Serial.println("Enviando a ThingSpeak...");
        Serial.println(url);

        HTTPClient http;
        http.begin(url);
        int httpCode = http.GET();

        if (httpCode > 0) {
          Serial.printf("ThingSpeak: OK (Código HTTP: %d)\n", httpCode);
        } else {
          Serial.printf("ThingSpeak Error: %s\n", http.errorToString(httpCode).c_str());
        }
        http.end();

        // 2. ENVIAR A EMQX MQTT
        Serial.println("Enviando a EMQX MQTT...");
        publicarMQTT(temperatura, humedad, VDC, IDC_promedio, potencia);
        
        Serial.println("=== DATOS ENVIADOS ===\n");
    }

    // Mostrar en serial cada 5s
    Serial.printf("Temp: %.1f°C, Hum: %.1f%%, V: %.2fV, I: %.3fA, P: %.2fW\n", 
                  temperatura, humedad, VDC, IDC_promedio, potencia);
  }
}
