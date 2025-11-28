import time
import sys
import paho.mqtt.client as mqtt

# --- CONFIGURAÇÕES ---

MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
MQTT_CLIENT_ID = "UEA-MPEE-sic-contador"

# Tópicos
# Onde ESCUTAMOS o comando de paralisar/iniciar
TOPICO_FLAG_SUB = "UEA/MPEE/sic/gw/Flag"
TOPICO_CONTADOR_SUB = "UEA/MPEE/sic/gw/Contador1"
# Onde PUBLICAMOS o valor atual do contador (para o Gateway enviar ao OPC)
TOPICO_CONTADOR_PUB = "UEA/MPEE/sic/Contador1"
# Onde PUBLICAMOS para pedir atualização inicial
TOPICO_REQ_LEITURA = "UEA/MPEE/sic/gw/LerDados"

# Variáveis de Controle
flag_ativa = False
contador = 0
sincronizou_com_gateway = False

# --- CALLBACKS MQTT ---

def on_connect(client, userdata, flags, rc):
    """Executado quando a conexão com o Broker é estabelecida."""
    if rc == 0:
        print(f"[Sistema] Conectado ao Broker MQTT!")
        
        # 1. Assina o tópico da Flag para monitorar mudanças
        client.subscribe(TOPICO_FLAG_SUB)
        client.subscribe(TOPICO_CONTADOR_SUB)
        print(f"[Sistema] Monitorando tópicos: \nFLAG: {TOPICO_FLAG_SUB}\nCONTADOR: {TOPICO_CONTADOR_SUB}")
        
    else:
        print(f"[Erro] Falha ao conectar. Código: {rc}")

def on_disconnect(client, userdata, rc):
    """Executado se a conexão cair."""
    global sincronizou_com_gateway
    sincronizou_com_gateway = False
    if rc != 0:
        print("[Aviso] Desconexão inesperada. O cliente tentará reconectar automaticamente...")

def on_message(client, userdata, msg):
    """Executado quando chega uma mensagem (Neste caso, o valor da Flag)."""
    global flag_ativa
    global contador
    global sincronizou_com_gateway
    
    topic = msg.topic
    payload = msg.payload.decode()
    
    if topic == TOPICO_FLAG_SUB:
        sincronizou_com_gateway = True
        # Normaliza a mensagem para lidar com "True", "true", "1", etc.
        dado_limpo = payload.lower()
        
        if dado_limpo in ["true", "1", "on"]:
            if not flag_ativa:
                print(f"[Comando] Flag recebida: {payload} -> INICIANDO contagem.")
            flag_ativa = True
        else:
            if flag_ativa:
                print(f"[Comando] Flag recebida: {payload} -> PARANDO contagem.")
            flag_ativa = False
    
    if topic == TOPICO_CONTADOR_SUB:
        
        print(f"[Comando] Contador recebido: {payload}")
        contador = int(payload)
        

# --- PROGRAMA PRINCIPAL ---

def main():
    global contador
    global sincronizou_com_gateway
    is_disconnect = 0
    direction = 1
    
    # Configuração do Cliente
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=MQTT_CLIENT_ID)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    
    while(1):

        print("--- Cliente Contador MQTT ---")
        print("Objetivo: Contar 0-9 quando Flag for True.")
        
        # 1. Loop de Conexão Robusta (Tenta até conseguir)
        conectado = False
        while not conectado:
            try:
                print(f"[Conexão] Tentando conectar a {MQTT_BROKER}...")
                client.connect(MQTT_BROKER, MQTT_PORT, 60)
                conectado = True
            except Exception as e:
                print(f"[Erro] Não foi possível conectar: {e}")
                print("[Sistema] Tentando novamente em 5 segundos...")
                time.sleep(5)

        # Inicia a thread de rede do MQTT
        client.loop_start()
        
        while(1):
            if(sincronizou_com_gateway == True):
                break
            
            # 2. Requisita o estado atual (Sincronização Inicial)
            # Isso garante que não começamos com o valor errado se o Gateway já estiver rodando
            print("[Sistema] Solicitando estado atual ao Gateway...")
            client.publish(TOPICO_REQ_LEITURA, "CMD_INIT")
            
            time.sleep(10)
            
            

        try:
            # 2. Loop Lógico Principal
            while True:
                if flag_ativa:
                    # Incrementa e reseta se passar de 9
                    print(f"[Contador] Enviando valor: {contador}")
                    
                    # Publica o valor para o Gateway pegar e enviar ao OPC
                    client.publish(TOPICO_CONTADOR_PUB, str(contador))
                    
                    
                    contador += direction
                    if contador >= 9:
                        direction = -1
                    elif contador <= 0:
                        direction = 1
                    
                    # Velocidade da contagem (1 segundo)
                    time.sleep(1)
                else:
                    # Se a flag for False, apenas espera sem contar
                    # Print opcional para debug, comentado para não poluir o terminal
                    # print("[Standby] Aguardando Flag = True...")
                    time.sleep(1)

        except KeyboardInterrupt:
            print("\n[Sistema] Ctrl+C pressionado. Encerrando...")
            is_disconnect = 1

        finally:
            client.loop_stop()
            client.disconnect()
            print("[Sistema] Cliente desconectado.")
        
        if( is_disconnect == 1):
            print("Programa finalizado.")
            break
        else:
            time.sleep(2)

if __name__ == "__main__":
    main()
    