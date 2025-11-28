from opcua import Client, ua
import time
import sys
import os

# URL do seu servidor OPC-UA
# (Altere para o URL correto do seu servidor)
SERVER_URL = "opc.tcp://localhost:4840"


# NodeIds (ajuste conforme o seu servidor)
FLAG_NODE_ID = "ns=1;i=1000"
CONTADOR_NODE_ID = "ns=1;i=1001"


    


# 1. Criação do Objeto Cliente
# Note que apenas criamos o objeto, não conectamos ainda.
client = Client(SERVER_URL)
is_disconnect = 0

while(1):
    print(f"Tentando conectar a {SERVER_URL}...")
    # 2. Implementação com Gerenciador de Contexto (with)
    try:
        # O 'with' vai gerir o connect() e o disconnect()
        with client:


            flag = False
            flag_node = 0
            while(True):
                os.system("cls") #limpa o terminal
                print("Conectado ao servidor OPC-UA com sucesso!")

                # lendo nó
                try:
                    flag_node = client.get_node(FLAG_NODE_ID) 
                    flag = flag_node.get_value()
                    print(f"\n")
                    print(f"Valor lido do nó: {flag}")
                    print(f"\n")

                except Exception as e_node:
                    print(f"Erro ao ler o nó: {e_node}")
                    break


                
                escolha = (int)(input(f"\n \t\t== Menu ==\n0) Sair\n1) Mudar estado de flag\n\nEscolha uma entre as opções: "))

                if(escolha == 0):
                    is_disconnect = 1
                    break
                if(escolha == 1):
                    
                    # setando valor do nó
                    if(flag == True):
                        flag = False
                    else:
                        flag = True

                    try:
                        flag_node.set_value(ua.Variant(flag, ua.VariantType.Boolean))
                        print(f"Mudando estado da flag para {flag} ...")
                        time.sleep(1)

                    except Exception as e_node:
                        
                        if(flag == True):
                            flag = False
                        else:
                            flag = True

                        print(f"Erro ao configurar valor do nó: {e_node}")
                        break
                        

    except Exception as e:
        print(f"Erro: Falha ao conectar ou erro crítico durante a execução: {e}")

    finally:
        print("A conexão foi fechada .")

    if( is_disconnect == 1):
        print("Programa finalizado.")
        break
    else:
        time.sleep(2)