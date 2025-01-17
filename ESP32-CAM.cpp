#include "secrets.h"
#include <WiFiClientSecure.h>
#include <MQTTClient.h>
#include "WiFi.h"
#include "esp_camera.h"
#include <driver/ledc.h>
#include <esp32cam.h>

#define TRIG_PIN 12
#define ECHO_PIN 13
#define FLASH_GPIO_NUM 4

#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

//schimba numarul la cam_X in functie de camera pentru identificarea lor in MQTT
#define ESP32CAM_PUBLISH_TOPIC   "esp32/cam_0"


const int bufferSize = 1024 * 23; // 23552 bytes
const long CAMERA_ON_DURATION = 30000; // 30 de secunde
const int DISTANCE_THRESHOLD = 15; // Interval de distanță în cm

WiFiClientSecure net = WiFiClientSecure();
MQTTClient client = MQTTClient(bufferSize);

unsigned long camTimerStart = 0;
bool cameraOn = false;

void connectAWS()
{
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  Serial.println("\n\n=====================");
  Serial.println("Connecting to Wi-Fi");
  Serial.println("=====================\n\n");

  while (WiFi.status() != WL_CONNECTED){
    delay(500);
    Serial.print(".");
  }

  // Configurează WiFiClientSecure pentru a folosi credențialele în AWS IoT
  net.setCACert(AWS_CERT_CA);
  net.setCertificate(AWS_CERT_CRT);
  net.setPrivateKey(AWS_CERT_PRIVATE);

  // Conectare la MQTT broker în punctul AWS definit mai sus
  client.begin(AWS_IOT_ENDPOINT, 8883, net);
  client.setCleanSession(true);

  Serial.println("\n\n=====================");
  Serial.println("Connecting to AWS IOT");
  Serial.println("=====================\n\n");

  while (!client.connect(THINGNAME)) {
    Serial.print(".");
    delay(100);
  }

  if(!client.connected()){
    Serial.println("AWS IoT Timeout!");
    ESP.restart();
    return;
  }

  Serial.println("\n\n=====================");
  Serial.println("AWS IoT Connected!");
  Serial.println("=====================\n\n");
}

void cameraInit(){
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_VGA; // 640x480
  config.jpeg_quality = 10;
  config.fb_count = 2;

  // initializare camera
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    ESP.restart();
    return;
  }
}

void grabImage(){
  camera_fb_t * fb = esp_camera_fb_get();
  if(fb != NULL && fb->format == PIXFORMAT_JPEG && fb->len < bufferSize){
    Serial.print("Image Length: ");
    Serial.print(fb->len);
    Serial.print("\t Publish Image: ");
    bool result = client.publish(ESP32CAM_PUBLISH_TOPIC, (const char*)fb->buf, fb->len);
    Serial.println(result);

    if(!result){
      ESP.restart();
    }
  }
  esp_camera_fb_return(fb);
  delay(1);
}

long measureDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  long duration = pulseIn(ECHO_PIN, HIGH);
  long distance = duration * 0.034 / 2; // Calculează distanța în cm
  return distance;
}

void turnOnCamera() {
  digitalWrite(PWDN_GPIO_NUM, LOW); // Pornește camera
  delay(100);
  cameraInit();
  cameraOn = true;
  digitalWrite(FLASH_GPIO_NUM, HIGH);
  Serial.println("Camera turned on.");
}

void turnOffCamera() {
  esp_camera_deinit(); // Deinitialize the camera to save power
  digitalWrite(PWDN_GPIO_NUM, HIGH); // Power off the camera
  cameraOn = false;
  digitalWrite(FLASH_GPIO_NUM, LOW);
  Serial.println("Camera turned off.");
}

void setup() {
  Serial.begin(115200);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(PWDN_GPIO_NUM, OUTPUT);
  pinMode(FLASH_GPIO_NUM, OUTPUT);
  digitalWrite(PWDN_GPIO_NUM, HIGH);

  connectAWS();
}

void loop() {
  client.loop();

  long distance = measureDistance();

  if (client.connected()) {
    if (!cameraOn && distance < DISTANCE_THRESHOLD) {
        turnOnCamera();           
        camTimerStart = millis();
    }

    if (cameraOn) {
        grabImage();

        if (millis() - camTimerStart > CAMERA_ON_DURATION) {
            turnOffCamera();
        }
    }
  } else {
      if (cameraOn) {
          turnOffCamera();
      }
  }
}
