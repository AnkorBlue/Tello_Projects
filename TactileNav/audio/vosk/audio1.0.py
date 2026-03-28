import json
import queue
import sys
import sounddevice as sd
from vosk import Model, KaldiRecognizer

# Fila para armazenar os dados de áudio capturados
q = queue.Queue()

def callback(indata, frames, time, status):
    """Esta função é chamada para cada bloco de áudio capturado pelo microfone."""
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

def extrair_locais(texto):
    """
    Função responsável por interpretar o texto falado.
    Analisa a posição das palavras para descobrir a origem e o destino.
    """
    # Tratamento para facilitar a busca, removendo acentos básicos
    texto_limpo = texto.lower().replace("ó", "o")
    origem = "Não identificado"
    destino = "Não identificado"
    
    pos_lab = texto_limpo.find("laboratorio")
    pos_aud = texto_limpo.find("auditorio")
    
    # Caso o utilizador mencione ambos os locais
    if pos_lab != -1 and pos_aud != -1:
        pos_estou = texto_limpo.find("estou")
        if pos_estou != -1:
            dist_lab = pos_lab - pos_estou if pos_lab > pos_estou else 9999
            dist_aud = pos_aud - pos_estou if pos_aud > pos_estou else 9999
            
            if dist_lab < dist_aud:
                origem = "Laboratório"
                destino = "Auditório"
            else:
                origem = "Auditório"
                destino = "Laboratório"
        else:
            if pos_lab < pos_aud:
                origem = "Laboratório"
                destino = "Auditório"
            else:
                origem = "Auditório"
                destino = "Laboratório"
                
    elif pos_lab != -1:
        destino = "Laboratório"
    elif pos_aud != -1:
        destino = "Auditório"

    return origem, destino

def escutar_comando():
    """
    Função principal que ativa o microfone e usa o Vosk offline.
    """
    try:
        # 1. CARREGAR O MODELO
        model = Model("model")
        
        # 2. VOCABULÁRIO HÍBRIDO
        palavras_permitidas = [
            "estou", "quero", "ir", "para", "o", "a", "no", "na", "do", "da", "e", "com",
            "laboratorio", "auditorio",
            "[unk]"
        ]
        
        # Transforma a lista de palavras para o formato JSON exigido pelo Vosk
        gramatica = json.dumps(palavras_permitidas)
        
        # Inicia o reconhecedor passando o modelo, a taxa de amostragem e a gramática restrita
        recognizer = KaldiRecognizer(model, 16000, gramatica)
        
        # 3. CONFIGURAR O MICROFONE E INICIAR A ESCUTA
        with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                               channels=1, callback=callback):
            
            print("\n[SISTEMA] Vosk (Vocabulário Restrito) pronto! Pode falar.")
            print("          (Exemplo: 'Estou no laboratório e quero ir para o auditório')\n")
            
            while True:
                data = q.get()
                if recognizer.AcceptWaveform(data):
                    # O Vosk retorna os dados em formato JSON
                    resultado = json.loads(recognizer.Result())
                    fala = resultado.get("text", "")
                    
                    if fala:
                        # Passa a transcrição limpa para a sua lógica de extração
                        origem, destino = extrair_locais(fala)
                        
                        # Mostra os resultados no ecrã
                        print("=" * 50)
                        print(f"Fala detetada  : '{fala}'")
                        print("-" * 50)
                        print(f"Local Origem   : {origem}")
                        print(f"Local Destino  : {destino}")
                        print("=" * 50)
                        
                        # Para o loop se encontrar um trajeto válido
                        if origem != "Não identificado" or destino != "Não identificado":
                            print("[SISTEMA] Trajeto confirmado. A preparar comando para o drone...")
                            break

    except Exception as e:
        print(f"[ERRO]: {e}")

if __name__ == "__main__":
    escutar_comando()