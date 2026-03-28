import json
import queue
import sys
import sounddevice as sd 
from vosk import Model, KaldiRecognizer
import pyttsx3

# ===============================
# CONFIGURAÇÃO DA VOZ
# ===============================
# Inicializa o motor de conversão de texto em áudio
engine = pyttsx3.init()

# Define as propriedades da voz falada pelo sistema
engine.setProperty('rate', 170)   # Velocidade da fala
engine.setProperty('volume', 0.9) # Volume da voz

# listar e mudar a voz padrão do sistema:
# for voice in engine.getProperty('voices'):
#     print(voice.id)

# ===============================
# FILA DE ÁUDIO
# ===============================
q = queue.Queue()

def callback(indata, frames, time, status):
    """
    Função chamada automaticamente pela biblioteca sounddevice cada vez que um bloco 
    de áudio é capturado pelo microfone.
    """
    if status:
        print(status, file=sys.stderr) 
    q.put(bytes(indata))

# ===============================
# FUNÇÃO DE FALA
# ===============================
def falar(texto):
    """
    Recebe uma string de texto, faz o sistema "falar" em voz alta 
    e aguarda a fala terminar antes de prosseguir com o código.
    """
    engine.say(texto)
    engine.runAndWait()

# ===============================
# EXTRAÇÃO DE LOCAIS
# ===============================
def extrair_locais(texto):
    """
    Analisa o texto reconhecido para deduzir qual é a Origem e qual é o Destino.
    Baseia-se nas posições das palavras na frase.
    """
    # Padroniza o texto: tudo minúsculo e sem acento no 'ó' para facilitar a busca
    texto_limpo = texto.lower().replace("ó", "o")

    # Valores padrão caso o sistema não encontre as palavras
    origem = "Não identificado"
    destino = "Não identificado"
    
    # Busca em qual posição (índice) da frase aparecem as palavras-chave
    pos_lab = texto_limpo.find("laboratorio")
    pos_aud = texto_limpo.find("auditorio")
    
    # Se encontrou ambos (laboratório e auditório) na mesma frase
    if pos_lab != -1 and pos_aud != -1:
        # Tenta achar a palavra "estou" para usar como âncora de origem
        pos_estou = texto_limpo.find("estou")
        
        if pos_estou != -1:
            # Calcula qual local está mais próximo da palavra "estou" na frase.
            # O que estiver mais perto, será considerado a origem.
            dist_lab = pos_lab - pos_estou if pos_lab > pos_estou else 9999
            dist_aud = pos_aud - pos_estou if pos_aud > pos_estou else 9999
            
            if dist_lab < dist_aud:
                origem = "Laboratório"
                destino = "Auditório"
            else:
                origem = "Auditório"
                destino = "Laboratório"
        else:
            # Se não achou "estou", assume que o que foi dito primeiro é a origem
            if pos_lab < pos_aud:
                origem = "Laboratório"
                destino = "Auditório"
            else:
                origem = "Auditório"
                destino = "Laboratório"
                
    # Se encontrou apenas um dos locais, assume que o usuário quer ir PARA lá (Destino)
    elif pos_lab != -1:
        destino = "Laboratório"
    elif pos_aud != -1:
        destino = "Auditório"

    return origem, destino

# ===============================
# FUNÇÃO PRINCIPAL
# ===============================
def escutar_comando():
    """
    Função principal que gerencia o fluxo de ouvir, reconhecer e responder.
    """
    try:
        # 1. FALA INICIAL
        falar("Olá, onde estamos e para onde iremos?")

        # 2. CARREGA O MODELO VOSK
        model = Model("model")

        # 3. DEFINE A GRAMÁTICA
        palavras_permitidas = [
            "estou", "quero", "ir", "para", "o", "a", "no", "na", "do", "da", "e",
            "laboratorio", "auditorio",
            "[unk]" # [unk] representa palavras desconhecidas
        ]
        
        # Converte a lista do Python para um formato JSON que o Vosk entende
        gramatica = json.dumps(palavras_permitidas)

        # Configura o reconhecedor para taxa de amostragem de 16000Hz usando nossa gramática
        recognizer = KaldiRecognizer(model, 16000, gramatica)

        # 4. ABRE O MICROFONE
        with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                               channels=1, callback=callback):

            print("\n[SISTEMA] Pronto! Pode falar...\n")

            # Loop infinito (vai rodar até o sistema entender o comando e darmos um 'break')
            while True:
                # Pega um bloco de áudio da fila
                data = q.get()

                # Se o reconhecedor detectar que uma frase foi finalizada no áudio
                if recognizer.AcceptWaveform(data):
                    # Extrai o resultado em formato JSON e pega apenas o texto falado
                    resultado = json.loads(recognizer.Result())
                    fala = resultado.get("text", "")

                    if fala:
                        # Passa a frase falada pela lógica de extração
                        origem, destino = extrair_locais(fala)

                        # Exibe os resultados na tela para debug
                        print("=" * 50)
                        print(f"Fala detectada : '{fala}'")
                        print("-" * 50)
                        print(f"Local Origem   : {origem}")
                        print(f"Local Destino  : {destino}")
                        print("=" * 50)

                        # 5.
                        # Se o sistema conseguiu extrair pelo menos a origem ou o destino, ele responde
                        if origem != "Não identificado" or destino != "Não identificado":
                            resposta = f"Origem {origem}, destino {destino}"
                            falar(resposta)
                            print("[SISTEMA] Trajeto confirmado.")
                            break

    except Exception as e:
        print(f"[ERRO]: {e}")

# ===============================
# EXECUÇÃO DO SCRIPT
# ===============================
if __name__ == "__main__":
    escutar_comando()