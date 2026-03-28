import speech_recognition as sr

def extrair_locais(texto):
    """
    Função responsável por interpretar o texto falado.
    Ela analisa a posição das palavras para descobrir onde o usuário está (origem)
    e para onde ele quer ir (destino).
    """
    
    # 1. TRATAMENTO DO TEXTO
    # Converte tudo para minúsculas e remove acentos básicos para facilitar a busca
    texto_limpo = texto.lower().replace("ó", "o")
    
    # Define valores padrão caso o sistema não encontre os locais na frase
    origem = "Não identificado"
    destino = "Não identificado"
    
    # 2. BUSCA DE PALAVRAS-CHAVE
    # O método .find() retorna o índice (posição) da palavra na frase.
    # Se a palavra não existir na frase, ele retorna -1.
    pos_lab = texto_limpo.find("laboratorio")
    pos_aud = texto_limpo.find("auditorio")
    
    # =========================================================================
    # CASO 1: O usuário mencionou TANTO o laboratório QUANTO o auditório
    # =========================================================================
    if pos_lab != -1 and pos_aud != -1:
        
        # Procura se o usuário usou a palavra indicativa de origem: "estou"
        pos_estou = texto_limpo.find("estou")
        
        # Cénario 1A: O usuário falou a palavra "estou"
        if pos_estou != -1:
            # LÓGICA DE DISTÂNCIA: A palavra falada logo APÓS "estou" será a origem.
            # Se a posição do local for maior que a posição de "estou" (ou seja, vem depois),
            # subtraímos as posições para ver qual está mais perto.
            # Se o local foi dito ANTES do "estou", damos um valor absurdo (9999) para ignorá-lo.
            dist_lab = pos_lab - pos_estou if pos_lab > pos_estou else 9999
            dist_aud = pos_aud - pos_estou if pos_aud > pos_estou else 9999
            
            # Compara as distâncias: o local mais próximo da palavra "estou" é a origem.
            if dist_lab < dist_aud:
                origem = "Laboratório"
                destino = "Auditório"
            else:
                origem = "Auditório"
                destino = "Laboratório"
                
        # Cenário 1B: O usuário falou os dois locais, mas NÃO usou a palavra "estou"
        # Exemplo: "Quero ir do laboratório para o auditório"
        else:
            # LÓGICA DE ORDEM NATURAL: Assume-se que o primeiro local falado é a origem.
            if pos_lab < pos_aud:
                origem = "Laboratório"
                destino = "Auditório"
            else:
                origem = "Auditório"
                destino = "Laboratório"
                
    # =========================================================================
    # CASO 2: O usuário mencionou APENAS UM local
    # =========================================================================
    # LÓGICA DE DESTINO ÚNICO: Se só falou um lugar (Ex: "Me leve ao laboratório"),
    # assumimos que ele quer ir para lá, e a origem fica "Não identificada".
    elif pos_lab != -1:
        destino = "Laboratório"
    elif pos_aud != -1:
        destino = "Auditório"

    # Retorna as duas variáveis processadas para quem chamou a função
    return origem, destino


def escutar_comando():
    """
    Função principal que ativa o microfone, captura o áudio, 
    envia para a API do Google transformar em texto e chama a função de análise.
    """
    
    # Cria a instância do "reconhecedor" de voz
    recognizer = sr.Recognizer()
    
    # Abre o microfone padrão do sistema para capturar o áudio
    with sr.Microphone() as source:
        print("\n[SISTEMA] Ajustando ruído de fundo... Aguarde 1 segundo.")
        
        # Ouve o ambiente por 1 segundo para calibrar e ignorar o ruído de fundo (chiados)
        recognizer.adjust_for_ambient_noise(source, duration=1)
        
        print("[SISTEMA] Microfone aberto! Pode falar.")
        print("          (Exemplo: 'Estou no laboratório e quero ir para o auditório')\n")
        
        try:
            # 3. CAPTURA DE ÁUDIO
            # Fica ouvindo o microfone. 
            # timeout=5: Desiste se a pessoa não falar nada em 5 segundos.
            # phrase_time_limit=10: Corta a gravação se a pessoa falar por mais de 10 segundos sem parar.
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            print("[SISTEMA] Processando o áudio...\n")
            
            # 4. TRADUÇÃO DE ÁUDIO PARA TEXTO (Requer Internet)
            # Envia o áudio para o servidor do Google (API gratuita) em português do Brasil
            texto_transcrito = recognizer.recognize_google(audio, language="pt-BR")
            
            # 5. ANÁLISE DO TEXTO
            # Passa o texto para a nossa função "extrair_locais" e guarda as respostas
            origem, destino = extrair_locais(texto_transcrito)
            
            # 6. EXIBIÇÃO DOS RESULTADOS
            # Mostra na tela o que foi entendido e para onde o usuário quer ir
            print("=" * 50)
            print(f"Fala transcrita: '{texto_transcrito}'")
            print("-" * 50)
            print(f"Local onde estou : {origem}")
            print(f"Local para ir    : {destino}")
            print("=" * 50)
            
        # 7. TRATAMENTO DE ERROS
        except sr.WaitTimeoutError:
            # Erro disparado se os 5 segundos passarem em total silêncio
            print("[ERRO] Tempo esgotado. Nenhuma voz foi detectada.")
        except sr.UnknownValueError:
            # Erro disparado se o Google ouvir som, mas não conseguir identificar palavras
            print("[ERRO] Não consegui entender o que foi dito. Fale mais alto.")
        except sr.RequestError as e:
            # Erro disparado se o computador estiver sem internet ou a API do Google cair
            print(f"[ERRO] Verifique sua conexão com a internet: {e}")

# Ponto de entrada do script: se este arquivo for executado diretamente, ele roda a função abaixo.
if __name__ == "__main__":
    escutar_comando()