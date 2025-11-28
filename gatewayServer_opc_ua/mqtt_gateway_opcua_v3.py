import time
import sys
# Importamos a biblioteca do OPC-UA
from opcua import Client, ua
# Importamos a biblioteca do MQTT
import paho.mqtt.client as mqtt

# --- CONFIGURAÇÕES ---

# Configurações MQTT
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_CLIENT_ID = "UEA-MPEE-sic-gw"

# Tópicos de Publicação (Envio de dados)
TOPICO_FLAG_PUB = "UEA/MPEE/sic/gw/Flag"           # Publica estado da Flag
TOPICO_CONTADOR_PUB = "UEA/MPEE/sic/gw/Contador1"  # Publica valor do Contador

# Tópicos de Subscrição (Recebimento de comandos)
TOPICO_CONTADOR_SUB = "UEA/MPEE/sic/Contador1"     # Escuta para escrever no OPC
TOPICO_REQ_LEITURA = "UEA/MPEE/sic/gw/LerDados"    # NOVO: Escuta para pedir leitura forçada

# Configurações OPC-UA
OPC_URL = "opc.tcp://localhost:4840"
ID_NO_FLAG = "ns=1;i=1000"     # Nó para LER (Boolean)
ID_NO_CONTADOR = "ns=1;i=1001" # Nó para ESCREVER (Int)

# Variáveis Globais
# Precisamos que ambos os nós sejam acessíveis dentro do 'on_message'
node_contador = None 
node_flag = None     

is_disconnect = 0
contador = 0

# --- FUNÇÕES CALLBACK DO MQTT ---

def on_connect(client, userdata, flags, rc):
    """Executado quando conecta ao Broker MQTT."""
    if rc == 0:
        print(f"[MQTT] Conectado ao Broker com sucesso!")
        
        # Inscreve nos tópicos de comando
        client.subscribe(TOPICO_CONTADOR_SUB)
        client.subscribe(TOPICO_REQ_LEITURA) # Inscreve no novo tópico
        
        print(f"[MQTT] Inscrito em: {TOPICO_CONTADOR_SUB}")
        print(f"[MQTT] Inscrito em: {TOPICO_REQ_LEITURA}")
    else:
        print(f"[MQTT] Falha na conexão. Código: {rc}")

def on_message(client, userdata, msg):
    """
    Executado SEMPRE que chega uma mensagem nos tópicos assinados.
    Gerencia: Escrita no OPC (Contador) OU Leitura forçada (Flag/Contador)
    """
    global node_contador
    global node_flag
    
    topic = msg.topic
    
    # 1. CASO SEJA PARA ESCREVER NO CONTADOR (MQTT -> OPC)
    if topic == TOPICO_CONTADOR_SUB:
        try:
            valor_recebido = msg.payload.decode()
            valor_inteiro = int(valor_recebido)
            
            print(f"[Gateway] Comando recebido p/ Contador: {valor_inteiro}")
            
            if node_contador:
                dv = ua.DataValue(ua.Variant(valor_inteiro, ua.VariantType.Int32))
                node_contador.set_value(dv)
                print(f"[OPC-UA] Escrito {valor_inteiro} no nó Contador.")
            else:
                print("[Erro] Nó OPC Contador não inicializado.")

        except Exception as e:
            print(f"[Erro Escrita] {e}")

    # 2. CASO SEJA UMA SOLICITAÇÃO DE LEITURA (OPC -> MQTT)
    elif topic == TOPICO_REQ_LEITURA:
        print("[Gateway] Requisição de leitura recebida. Lendo OPC-UA...")
        
        if node_contador and node_flag:
            try:
                # Lê os valores atuais do OPC
                val_flag = node_flag.get_value()
                val_cont = node_contador.get_value()
                
                # Publica no MQTT
                client.publish(TOPICO_CONTADOR_PUB, str(val_cont))
                time.sleep(3)
                client.publish(TOPICO_FLAG_PUB, str(val_flag))
                
                print(f"[Gateway] Dados Atualizados Enviados: Flag={val_flag}, Cont={val_cont}")
                
            except Exception as e:
                print(f"[Erro Leitura] Falha ao ler nós OPC: {e}")
        else:
             print("[Erro] Nós OPC não estão prontos para leitura.")

# --- PROGRAMA PRINCIPAL ---

def main():
    global node_contador
    global node_flag
    global is_disconnect
    
    # 1. Configuração do Cliente OPC-UA
    client_opc = Client(OPC_URL)
    
    # 2. Configuração do Cliente MQTT
    client_mqtt = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=MQTT_CLIENT_ID)
    client_mqtt.on_connect = on_connect
    client_mqtt.on_message = on_message

    print("--- Iniciando Gateway MQTT <-> OPC-UA ---")
    print(f"Para pedir dados, publique algo em: {TOPICO_REQ_LEITURA}")
    print("Pressione Ctrl+C para encerrar.")

    try:
        # Conecta ao Broker MQTT
        print(f"[MQTT] Tentando conectar a {MQTT_BROKER}...")
        client_mqtt.connect(MQTT_BROKER, MQTT_PORT, 60)
        client_mqtt.loop_start()

        # Loop de reconexão OPC-UA
        while(1):
            print(f"[OPC-UA] Tentando conectar a {OPC_URL}...")

            try:
                with client_opc:
                    print(f"[OPC-UA] Conectado ao servidor {OPC_URL}")

                    # Inicializa as variáveis globais dos nós
                    node_flag = client_opc.get_node(ID_NO_FLAG)
                    node_contador = client_opc.get_node(ID_NO_CONTADOR)
                    
                    ultimo_valor_flag = False
                    primeira_atualizacao = True
                    
                    print("[Gateway] Ciclo de monitoramento iniciado...")

                    # --- LOOP PRINCIPAL (Monitora mudança na FLAG) ---
                    while True:
                        try:
                            # Lê apenas para verificar mudança de estado (monitoramento passivo)
                            valor_flag = node_flag.get_value()
                            
                            # Lógica: Só publica se o valor mudou OU se é a primeira vez
                            if (not primeira_atualizacao and valor_flag == ultimo_valor_flag):
                                time.sleep(1)
                                continue
                            
                            # Se mudou, atualiza e publica
                            ultimo_valor_flag = valor_flag
                            primeira_atualizacao = False

                            client_mqtt.publish(TOPICO_FLAG_PUB, str(valor_flag))
                            
                            # Opcional: Publicar também o contador quando a flag muda
                            val_cont_atual = node_contador.get_value()
                            client_mqtt.publish(TOPICO_CONTADOR_PUB, str(val_cont_atual))

                            print(f"[Gateway] Mudança detectada (Flag): {valor_flag} -> Publicado.")
                            
                            time.sleep(1)
                            
                        except Exception as e:
                            print(f"[Erro no Loop OPC] {e}")
                            time.sleep(2)
                            break # Quebra para tentar reconectar o 'with'

            except Exception as e:
                print(f"[Erro Conexão OPC] {e}")
                
            except KeyboardInterrupt:
                is_disconnect = 1
                print("\n[Sistema] Ctrl+C pressionado...")
                break # Sai do While de conexão

            finally:
                if is_disconnect != 1:
                    print("[OPC-UA] Conexão perdida ou fechada. Tentando reconectar em 2s...")
                    time.sleep(2)

            if is_disconnect == 1:
                break

    finally:
        print("[Sistema] Finalizando processos...")
        client_mqtt.loop_stop()
        client_mqtt.disconnect()
        print("[Sistema] Gateway encerrado.")

if __name__ == "__main__":
    main()
    