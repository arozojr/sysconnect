# Sistema de Integração MQTT/OPC-UA - Guia de Instalação e Execução

Este documento apresenta o passo a passo completo para configurar e executar o sistema de integração entre protocolos MQTT e OPC-UA, incluindo a instalação de todas as dependências necessárias.

## 📋 Pré-requisitos

- Python 3.7 ou superior
- Sistema operacional Windows ou Linux
- ESP32 (para execução do código em hardware)
- Arduino IDE ou PlatformIO (para compilar código do ESP32)
- Conexão com rede Wi-Fi (para o ESP32)

---

## 1. Instalação do Mosquitto (Broker MQTT)

O Mosquitto é o broker MQTT necessário para intermediar a comunicação entre os componentes do sistema.

### Windows

1. **Baixar o instalador:**
   - Acesse: https://mosquitto.org/download/
   - Baixe a versão mais recente para Windows (arquivo `.exe`)

2. **Instalar:**
   - Execute o instalador baixado
   - Siga as instruções do assistente de instalação
   - **Importante:** Durante a instalação, marque a opção para instalar o serviço do Windows

3. **Verificar instalação:**
   - Abra o Prompt de Comando ou PowerShell como Administrador
   - Execute:
     ```bash
     mosquitto -v
     ```
   - Se aparecer a versão do Mosquitto, a instalação foi bem-sucedida

### Linux (Ubuntu/Debian)

1. **Atualizar repositórios:**
   ```bash
   sudo apt update
   ```

2. **Instalar o Mosquitto:**
   ```bash
   sudo apt install mosquitto mosquitto-clients -y
   ```

3. **Verificar instalação:**
   ```bash
   mosquitto -v
   ```

---

## 2. Executando o Broker MQTT

### Windows

1. **Iniciar o serviço do Mosquitto:**
   - Abra o **Gerenciador de Serviços do Windows** (services.msc)
   - Procure por "Mosquitto Broker"
   - Clique com o botão direito e selecione **Iniciar**
   - Ou execute no PowerShell (como Administrador):
     ```powershell
     net start mosquitto
     ```

2. **Verificar se está rodando:**
   - O serviço deve aparecer como "Em execução"
   - Por padrão, o Mosquitto escuta na porta **1883**

### Linux

1. **Iniciar o serviço:**
   ```bash
   sudo systemctl start mosquitto
   ```

2. **Habilitar para iniciar automaticamente:**
   ```bash
   sudo systemctl enable mosquitto
   ```

3. **Verificar status:**
   ```bash
   sudo systemctl status mosquitto
   ```

---

## 3. Instalação das Dependências Python

Antes de executar os scripts Python, é necessário instalar as bibliotecas necessárias.

1. **Instalar dependências:**
   ```bash
   pip install opcua paho-mqtt
   ```

   Ou usando `pip3`:
   ```bash
   pip3 install opcua paho-mqtt
   ```

2. **Verificar instalação:**
   ```bash
   python -c "import opcua; import paho.mqtt.client as mqtt; print('Dependências instaladas com sucesso!')"
   ```

---

## 4. Executando o Servidor OPC-UA

O servidor OPC-UA é o componente central que expõe os nós `Flag` e `Contador` para leitura e escrita.

1. **Navegar até o diretório do projeto:**
   ```bash
   cd caminho/para/projeto_opc_ua
   ```

2. **Executar o servidor:**
   ```bash
   python opcua_server_monitor.py
   ```

3. **Verificar execução:**
   - Você deve ver a mensagem: `Servidor OPC UA iniciado em opc.tcp://0.0.0.0:4840`
   - O servidor começará a imprimir logs periódicos mostrando o estado da Flag e do Contador
   - **Mantenha este terminal aberto** - o servidor deve permanecer em execução

4. **Para encerrar:**
   - Pressione `Ctrl+C` no terminal

---

## 5. Executando o Gateway MQTT/OPC-UA

O Gateway faz a ponte entre os protocolos MQTT e OPC-UA, permitindo comunicação bidirecional.

1. **Abrir um novo terminal** (mantendo o servidor OPC-UA rodando)

2. **Navegar até o diretório do projeto:**
   ```bash
   cd caminho/para/projeto_opc_ua
   ```

3. **Executar o Gateway:**
   ```bash
   python mqtt_gateway_opcua_v3.py
   ```

4. **Verificar execução:**
   - Você deve ver as mensagens:
     - `[MQTT] Conectado ao Broker com sucesso!`
     - `[OPC-UA] Conectado ao servidor opc.tcp://localhost:4840`
     - `[Gateway] Ciclo de monitoramento iniciado...`
   - **Mantenha este terminal aberto** - o Gateway deve permanecer em execução

5. **Para encerrar:**
   - Pressione `Ctrl+C` no terminal

**⚠️ Importante:** O Gateway deve ser executado **após** o servidor OPC-UA estar rodando, pois ele precisa se conectar ao servidor.

---

## 6. Configurando e Executando o Código no ESP32

### 6.1. Preparação do Ambiente

#### Opção A: Arduino IDE

1. **Instalar Arduino IDE:**
   - Baixe em: https://www.arduino.cc/en/software
   - Instale seguindo as instruções do instalador

2. **Instalar suporte para ESP32:**
   - Abra o Arduino IDE
   - Vá em **Arquivo → Preferências**
   - No campo "URLs Adicionais para Gerenciadores de Placas", adicione:
     ```
     https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
     ```
   - Vá em **Ferramentas → Placa → Gerenciador de Placas**
   - Procure por "ESP32" e instale "esp32 by Espressif Systems"

3. **Instalar bibliotecas necessárias:**
   - Vá em **Sketch → Incluir Biblioteca → Gerenciar Bibliotecas**
   - Instale as seguintes bibliotecas:
     - **PubSubClient** (por Nick O'Leary)
     - **WiFi** (já incluída com ESP32)

#### Opção B: PlatformIO

1. **Instalar PlatformIO:**
   - Instale a extensão PlatformIO no VS Code
   - Ou instale o PlatformIO IDE standalone

2. **Criar projeto:**
   - Crie um novo projeto para ESP32
   - Adicione as dependências no arquivo `platformio.ini`:
     ```ini
     [env:esp32dev]
     platform = espressif32
     board = esp32dev
     framework = arduino
     lib_deps = 
         knolleary/PubSubClient@^2.8
     ```

### 6.2. Configuração do Código

1. **Abrir o arquivo `esp32counter.cpp`**

2. **Configurar credenciais Wi-Fi:**
   - Edite as linhas 8-9:
     ```cpp
     const char* WIFI_SSID     = "SEU_WIFI_SSID";
     const char* WIFI_PASSWORD = "SUA_SENHA_WIFI";
     ```

3. **Configurar broker MQTT:**
   - Se estiver usando broker local (Mosquitto no PC):
     ```cpp
     const char* MQTT_BROKER   = "IP_DO_SEU_PC";  // Ex: "192.168.1.100"
     ```
   - Para descobrir o IP do PC:
     - **Windows:** Execute `ipconfig` no CMD e procure por "IPv4"
     - **Linux:** Execute `hostname -I` ou `ip addr`
   - Se estiver usando broker público (HiveMQ):
     ```cpp
     const char* MQTT_BROKER   = "broker.hivemq.com";
     ```

### 6.3. Compilação e Upload

#### Usando Arduino IDE:

1. **Selecionar a placa:**
   - Vá em **Ferramentas → Placa → ESP32 Arduino → ESP32 Dev Module**

2. **Selecionar a porta:**
   - Conecte o ESP32 ao PC via cabo USB
   - Vá em **Ferramentas → Porta** e selecione a porta COM correspondente

3. **Compilar:**
   - Clique no botão **Verificar** (✓) ou pressione `Ctrl+R`

4. **Fazer upload:**
   - Clique no botão **Carregar** (→) ou pressione `Ctrl+U`
   - Aguarde a compilação e upload completarem

5. **Abrir o Monitor Serial:**
   - Vá em **Ferramentas → Monitor Serial** ou pressione `Ctrl+Shift+M`
   - Configure a velocidade para **115200 baud**
   - Você verá as mensagens de conexão e operação do ESP32

#### Usando PlatformIO:

1. **Compilar:**
   ```bash
   pio run
   ```

2. **Fazer upload:**
   ```bash
   pio run --target upload
   ```

3. **Monitor serial:**
   ```bash
   pio device monitor
   ```

---

## 7. Ordem de Execução Recomendada

Para garantir que o sistema funcione corretamente, execute os componentes na seguinte ordem:

1. ✅ **Iniciar o Broker MQTT (Mosquitto)**
   - Verificar se o serviço está rodando

2. ✅ **Executar o Servidor OPC-UA**
   ```bash
   python opcua_server_monitor.py
   ```

3. ✅ **Executar o Gateway MQTT/OPC-UA**
   ```bash
   python mqtt_gateway_opcua_v3.py
   ```

4. ✅ **Conectar o ESP32**
   - Ligar o ESP32 e verificar conexão no Monitor Serial

5. ✅ **(Opcional) Executar o Cliente Chaveador**
   - Para controlar a Flag manualmente:
     ```bash
     python opcua_client_chaveador_v2.py
     ```

---

## 8. Testando o Sistema

### Teste Básico:

1. **Verificar conexões:**
   - Servidor OPC-UA deve mostrar logs periódicos
   - Gateway deve mostrar conexão bem-sucedida com MQTT e OPC-UA
   - ESP32 deve mostrar conexão Wi-Fi e MQTT no Monitor Serial

2. **Controlar a Flag:**
   - Execute o cliente chaveador (`opcua_client_chaveador_v2.py`)
   - Altere a Flag para `True`
   - O ESP32 deve começar a contar (0→9→0)
   - Os valores devem aparecer no servidor OPC-UA

3. **Pausar a contagem:**
   - Altere a Flag para `False` no cliente chaveador
   - O ESP32 deve pausar e manter o último valor

---

## 9. Solução de Problemas

### Problema: Mosquitto não inicia

**Windows:**
- Verifique se o serviço está instalado: `services.msc`
- Tente iniciar manualmente: `net start mosquitto`
- Verifique se a porta 1883 não está em uso

**Linux:**
- Verifique logs: `sudo journalctl -u mosquitto`
- Verifique se a porta está em uso: `sudo netstat -tulpn | grep 1883`

### Problema: Erro ao conectar ao OPC-UA

- Verifique se o servidor OPC-UA está rodando
- Verifique se a URL está correta: `opc.tcp://localhost:4840`
- Verifique se não há firewall bloqueando a porta 4840

### Problema: ESP32 não conecta ao Wi-Fi

- Verifique se o SSID e senha estão corretos
- Verifique se o ESP32 está dentro do alcance do roteador
- Verifique se a rede Wi-Fi está funcionando

### Problema: ESP32 não conecta ao MQTT

- Verifique se o broker MQTT está rodando
- Verifique se o IP do broker está correto
- Verifique se o ESP32 e o PC estão na mesma rede
- Se usar broker público, verifique conexão com internet

### Problema: Gateway não detecta mudanças na Flag

- Verifique se o Gateway está conectado ao servidor OPC-UA
- Verifique os logs do Gateway para erros
- Aguarde alguns segundos - o Gateway verifica mudanças a cada 1 segundo

---

## 10. Estrutura de Arquivos

```
projeto_opc_ua/
│
├── opcua_server_monitor.py      # Servidor OPC-UA
├── mqtt_gateway_opcua_v3.py     # Gateway MQTT/OPC-UA
├── mqtt_contador_client_v2.py   # Cliente contador (simulação Python)
├── opcua_client_chaveador_v2.py # Cliente chaveador (controle manual)
├── esp32counter.cpp              # Código para ESP32
└── README.md                     # Este arquivo
```

---

## 11. Informações Adicionais

### Portas Utilizadas:

- **1883:** MQTT (Mosquitto)
- **4840:** OPC-UA (Servidor)

### Tópicos MQTT:

- `UEA/MPEE/sic/Contador1` - Publicação do contador (ESP32 → Gateway)
- `UEA/MPEE/sic/gw/Flag` - Publicação da Flag (Gateway → ESP32)
- `UEA/MPEE/sic/gw/Contador1` - Sincronização do contador (Gateway → ESP32)
- `UEA/MPEE/sic/gw/LerDados` - Requisição de leitura (ESP32 → Gateway)

### Nós OPC-UA:

- `ns=1;i=1000` - Flag (Boolean)
- `ns=1;i=1001` - Contador (Int16)

---

## 📝 Notas Finais

- Todos os componentes devem estar na mesma rede local (exceto se usar broker público)
- O servidor OPC-UA e o Gateway devem estar rodando continuamente
- O ESP32 reconecta automaticamente em caso de perda de conexão
- Para encerrar qualquer componente Python, use `Ctrl+C`

---

## 📧 Suporte

Em caso de dúvidas ou problemas, verifique:
1. Os logs de cada componente
2. A ordem de execução dos componentes
3. As configurações de rede e IPs
4. As dependências instaladas

---

**Desenvolvido para a disciplina de Sistemas Inteligentes e Conectados - UEA**
