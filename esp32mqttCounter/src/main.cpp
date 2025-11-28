#include <Arduino.h>

#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>

/* ====== CONFIGURAÇÕES WI-FI ====== */
const char* WIFI_SSID     = "Cyber_Workspace";
const char* WIFI_PASSWORD = "HubLS3s2";

/* ====== CONFIGURAÇÕES MQTT ====== */
// IP do broker: IP do PC onde está o Mosquitto
const char* MQTT_BROKER   = "broker.hivemq.com";
const int   MQTT_PORT     = 1883;
const char* MQTT_CLIENT_ID = "UEA-MPEE-sic-contador-ESP32";

/* ====== TÓPICOS MQTT (mesmos do Python) ====== */
const char* TOPICO_FLAG_SUB       = "UEA/MPEE/sic/gw/Flag";
const char* TOPICO_CONTADOR_SUB   = "UEA/MPEE/sic/gw/Contador1";
const char* TOPICO_CONTADOR_PUB   = "UEA/MPEE/sic/Contador1";
const char* TOPICO_REQ_LEITURA    = "UEA/MPEE/sic/gw/LerDados";

/* ====== VARIÁVEIS DE CONTROLE ====== */
WiFiClient espClient;
PubSubClient mqttClient(espClient);

bool flagAtiva = false;
int contador = 0;
int direction = 1;  // 1 = sobe, -1 = desce
bool sincronizadoComGateway = false;

unsigned long ultimoEnvioContador = 0;
unsigned long ultimoPedidoSync = 0;

/* ====== CONECTA WI-FI ====== */
void conectaWiFi() {
  Serial.print("Conectando ao WiFi: ");
  Serial.println(WIFI_SSID);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi conectado!");
  Serial.print("IP do ESP32: ");
  Serial.println(WiFi.localIP());
}

/* ====== CALLBACK DO MQTT ====== */
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  char msg[100];
  if (length >= sizeof(msg)) length = sizeof(msg) - 1;
  memcpy(msg, payload, length);
  msg[length] = '\0';
  String mensagem = String(msg);

  Serial.print("[MQTT] Mensagem recebida em ");
  Serial.print(topic);
  Serial.print(" -> ");
  Serial.println(mensagem);

  if (strcmp(topic, TOPICO_FLAG_SUB) == 0) {
    sincronizadoComGateway = true;
    String dado = mensagem;
    dado.toLowerCase();

    bool novoEstado = false;
    if (dado == "true" || dado == "1" || dado == "on") {
      novoEstado = true;
    }

    if (novoEstado && !flagAtiva) {
      Serial.println("[Comando] Flag -> INICIANDO contagem.");
    } else if (!novoEstado && flagAtiva) {
      Serial.println("[Comando] Flag -> PARANDO contagem.");
    }

    flagAtiva = novoEstado;
  }

  if (strcmp(topic, TOPICO_CONTADOR_SUB) == 0) {
    sincronizadoComGateway = true;
    int valorRecebido = mensagem.toInt();
    Serial.print("[Comando] Contador recebido: ");
    Serial.println(valorRecebido);
    contador = valorRecebido;
  }
}

/* ====== CONECTA AO BROKER MQTT ====== */
void conectaMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("Conectando ao MQTT em ");
    Serial.print(MQTT_BROKER);
    Serial.print(":");
    Serial.println(MQTT_PORT);

    if (mqttClient.connect(MQTT_CLIENT_ID)) {
      Serial.println("[MQTT] Conectado!");

      mqttClient.subscribe(TOPICO_FLAG_SUB);
      mqttClient.subscribe(TOPICO_CONTADOR_SUB);

      Serial.print("[MQTT] Assinando: ");
      Serial.println(TOPICO_FLAG_SUB);
      Serial.print("[MQTT] Assinando: ");
      Serial.println(TOPICO_CONTADOR_SUB);

      // pede sincronização inicial
      mqttClient.publish(TOPICO_REQ_LEITURA, "CMD_INIT");
      ultimoPedidoSync = millis();
    } else {
      Serial.print("Falha na conexão, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" tentando novamente em 5s...");
      delay(5000);
    }
  }
}

/* ====== SETUP ====== */
void setup() {
  Serial.begin(115200);
  delay(1000);

  conectaWiFi();

  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);
}

/* ====== LOOP PRINCIPAL ====== */
void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    conectaWiFi();
  }

  if (!mqttClient.connected()) {
    conectaMQTT();
  }
  mqttClient.loop();  // processa MQTT

  unsigned long agora = millis();

  // se ainda não sincronizou, pede estado a cada 10 s
  if (!sincronizadoComGateway && agora - ultimoPedidoSync > 10000) {
    Serial.println("[Sistema] Solicitando estado atual ao Gateway...");
    mqttClient.publish(TOPICO_REQ_LEITURA, "CMD_INIT");
    ultimoPedidoSync = agora;
  }

  // lógica do contador a cada 1 s
  if (flagAtiva && sincronizadoComGateway && (agora - ultimoEnvioContador > 1000)) {
    ultimoEnvioContador = agora;

    char buf[10];
    sprintf(buf, "%d", contador);
    Serial.print("[Contador] Enviando valor: ");
    Serial.println(buf);
    mqttClient.publish(TOPICO_CONTADOR_PUB, buf);

    contador += direction;
    if (contador >= 9) {
      direction = -1;
    } else if (contador <= 0) {
      direction = 1;
    }
  }
}