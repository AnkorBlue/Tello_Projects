import cv2
import numpy as np

# Caminho do arquivo de vídeo que será analisado
VIDEO_PATH = "2.mp4"

# Inicializa a captura de vídeo
cap = cv2.VideoCapture(VIDEO_PATH)

# Verifica se o vídeo foi aberto corretamente antes de continuar
if not cap.isOpened():
    print("Erro ao abrir o vídeo")
    exit()

# =====================================================================
# CONFIGURAÇÃO DO DETECTOR DE BLOBS (Para encontrar as "bolinhas" do piso de alerta)
# =====================================================================
params = cv2.SimpleBlobDetector_Params()

# Filtrar por Área: Busca formas que tenham um tamanho específico
params.filterByArea = True
params.minArea = 50     # Ignora manchas muito pequenas (ruídos)
params.maxArea = 5000   # Ignora manchas muito grandes

# Desativamos outros filtros (Circularidade, Convexidade, Inércia) 
# para tornar a detecção mais tolerante a distorções da perspectiva da câmera
params.filterByCircularity = False 
params.filterByConvexity = False
params.filterByInertia = False

# Cria o detector com as configurações acima
blob_detector = cv2.SimpleBlobDetector_create(params)


def detectar_linhas(edges):
    """
    Detecta segmentos de reta em uma imagem com bordas destacadas.
    Ideal para encontrar os frisos do Piso Tátil Direcional.
    """
    # cv2.HoughLinesP encontra segmentos de linhas na imagem de bordas
    lines = cv2.HoughLinesP(
        edges,
        1,              
        np.pi / 180,    
        threshold=80,   
        minLineLength=50, 
        maxLineGap=10   
    )

    # Se não encontrar nenhuma linha, retorna 0
    if lines is None:
        return 0, []

    # Retorna a quantidade de linhas e as coordenadas delas
    return len(lines), lines


def detectar_blobs(gray):
    """
    Detecta 'blobs' (manchas/pontos) em uma imagem em tons de cinza.
    Ideal para encontrar as bolinhas do Piso Tátil de Alerta.
    """
    # Detecta os pontos-chave (keypoints) usando o detector configurado no início
    keypoints = blob_detector.detect(gray)
    
    # Retorna a quantidade de blobs encontrados e as informações deles
    return len(keypoints), keypoints


# =====================================================================
# LOOP PRINCIPAL DE PROCESSAMENTO DO VÍDEO
# =====================================================================
while True:
    # Lê o próximo quadro (frame) do vídeo
    ret, frame = cap.read()
    
    # Se 'ret' for False, o vídeo acabou ou houve erro na leitura
    if not ret:
        break

    # Redimensiona o frame para um tamanho padrão, ajudando na performance 
    # e padronizando os parâmetros de detecção
    frame = cv2.resize(frame, (800, 500))

    # Converte a imagem colorida (BGR) para tons de cinza (mais fácil e rápido de processar)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Aplica um desfoque (Blur) para suavizar a imagem e remover ruídos finos
    blur = cv2.GaussianBlur(gray, (5,5), 0)

    # Aplica o algoritmo de Canny para detectar os contornos/bordas da imagem
    # Pixels entre 50 e 150 de intensidade de variação serão considerados bordas
    edges = cv2.Canny(blur, 50, 150)

    # 1. Detectar as linhas (usando a imagem com bordas destacadas)
    num_linhas, linhas = detectar_linhas(edges)

    # 2. Detectar as bolinhas (usando a imagem em tons de cinza)
    num_blobs, blobs = detectar_blobs(gray)

    # Estado inicial da classificação
    classificacao = "Indefinido"

    # =====================================================================
    # LÓGICA DE CLASSIFICAÇÃO
    # =====================================================================
    # Se houver muitas linhas (mais de 8) E houver mais linhas do que bolinhas:
    if num_linhas > 8 and num_linhas > num_blobs:
        classificacao = "PISO TATIL DIRECIONAL"

    # Caso contrário, se detectar muitas bolinhas (mais de 15):
    elif num_blobs > 15:
        classificacao = "PISO TATIL DE ALERTA"


    # =====================================================================
    # DESENHO NA TELA (FEEDBACK VISUAL)
    # =====================================================================
    
    # Desenha as linhas detectadas na cor VERDE
    if linhas is not None:
        for line in linhas:
            x1, y1, x2, y2 = line[0] 
            cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

    # Desenha os círculos dos blobs detectados na cor AZUL
    for kp in blobs:
        x = int(kp.pt[0])      
        y = int(kp.pt[1])     
        r = int(kp.size / 2)   
        cv2.circle(frame, (x, y), r, (255, 0, 0), 2)

    # Escreve a classificação final no canto superior esquerdo da tela (em VERMELHO)
    cv2.putText(
        frame,
        classificacao,
        (20, 40),                     
        cv2.FONT_HERSHEY_SIMPLEX,     
        1,                            
        (0, 0, 255),                  
        3                             
    )

    # Exibe a janela com a imagem processada e as marcações
    cv2.imshow("Reconhecimento de Piso Tactil", frame)

    # Aguarda 1 milissegundo. Se a tecla 'ESC' (código 27) for pressionada, sai do loop
    if cv2.waitKey(1) & 0xFF == 27:
        break

# Libera o arquivo de vídeo da memória
cap.release()
# Fecha todas as janelas abertas pelo OpenCV
cv2.destroyAllWindows()