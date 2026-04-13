import cv2
import numpy as np

class ProcessadorVisao:
    def __init__(self):
        # ==========================================
        # CORES DOS PISOS TÁTEIS EM HSV (RANGES CALIBRADOS)
        # ==========================================
        # Limites da cor VERMELHA (Piso de Alerta). 
        # O vermelho fica nos dois extremos do espectro HSV no OpenCV
        self.lower_red1 = np.array([0, 120, 70])
        self.upper_red1 = np.array([10, 255, 255])
        self.lower_red2 = np.array([170, 120, 70])
        self.upper_red2 = np.array([180, 255, 255])
        
        # Limites da cor AZUL (Piso Direcional)
        self.lower_blue = np.array([100, 120, 50])
        self.upper_blue = np.array([130, 255, 255])
        
        # ==========================================
        # PARÂMETROS DE DIMENSÕES E ÁREAS
        # ==========================================
        self.area_minima_bolinha = 15   
        self.area_minima_linha = 400    
        self.qtd_bolinhas_alerta = 6    
        self.area_minima_piso_direcional = 3000  # Área total de azul para confirmar piso direcional

    def processar_frame(self, frame, tem_espelho=True):
        frame = cv2.resize(frame, (432, 320))

        if tem_espelho:
            frame = cv2.flip(frame, 0)

        altura, largura, _ = frame.shape
        centro_camera_x = largura // 2

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # 1. Cria as máscaras separadas para Vermelho e Azul
        mask_red1 = cv2.inRange(hsv, self.lower_red1, self.upper_red1)
        mask_red2 = cv2.inRange(hsv, self.lower_red2, self.upper_red2)
        mask_red = cv2.bitwise_or(mask_red1, mask_red2)  # Combina as duas faixas do vermelho
        
        mask_blue = cv2.inRange(hsv, self.lower_blue, self.upper_blue)

        # 2. Suaviza as máscaras para tirar ruídos
        mask_red = cv2.erode(mask_red, None, iterations=1)
        mask_red = cv2.dilate(mask_red, None, iterations=2)
        
        mask_blue = cv2.erode(mask_blue, None, iterations=1)
        mask_blue = cv2.dilate(mask_blue, None, iterations=2)

        # Cria uma máscara combinada (Vermelho + Azul) só para visualização de debug
        mascara_debug = cv2.bitwise_or(mask_red, mask_blue)

        # ==========================================
        # ANÁLISE 1: PISO DE ALERTA (VERMELHO)
        # ==========================================
        contornos_red, _ = cv2.findContours(mask_red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        bolinhas_detetadas = 0

        for c in contornos_red:
            area = cv2.contourArea(c)
            if self.area_minima_bolinha < area < 800: 
                x, y, w, h = cv2.boundingRect(c)
                proporcao = float(w) / float(h)
                
                # Se for gordinho (quadrado/círculo), é uma bolinha de alerta
                if 0.6 <= proporcao <= 1.6: 
                    bolinhas_detetadas += 1
                    # Desenha um retângulo vermelho em volta da bolinha detectada
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)

        if bolinhas_detetadas >= self.qtd_bolinhas_alerta:
            cv2.putText(frame, "PISO DE ALERTA DETECTADO!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            return "ALERTA", 0, frame, mascara_debug

        # ==========================================
        # ANÁLISE 2: PISO DIRECIONAL (AZUL)
        # ==========================================
        # Calcula a área total de azul na máscara para verificação de piso direcional puro
        area_total_azul = cv2.countNonZero(mask_blue)
        
        contornos_blue, _ = cv2.findContours(mask_blue, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(contornos_blue) > 0:
            maior_contorno_azul = max(contornos_blue, key=cv2.contourArea)
            area_maior_contorno = cv2.contourArea(maior_contorno_azul)

            if area_maior_contorno > self.area_minima_linha:
                x, y, w, h = cv2.boundingRect(maior_contorno_azul)
                proporcao_maior = float(w) / float(h)
                
                # Só aceita como linha se for esticado (proporção fora do 0.6~1.6)
                if proporcao_maior < 0.6 or proporcao_maior > 1.6:
                    M = cv2.moments(maior_contorno_azul)
                    if M["m00"] != 0:
                        centro_linha_x = int(M["m10"] / M["m00"])
                        centro_linha_y = int(M["m01"] / M["m00"])
                        
                        erro_x = centro_linha_x - centro_camera_x

                        # Desenha a linha central (Branca) e o centro da faixa direcional (Azul)
                        cv2.line(frame, (centro_camera_x, 0), (centro_camera_x, altura), (255, 255, 255), 2) 
                        cv2.circle(frame, (centro_linha_x, centro_linha_y), 10, (255, 0, 0), -1) 
                        cv2.putText(frame, f"Erro X: {erro_x}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                        
                        return "LINHA", erro_x, frame, mascara_debug

        # Verifica se há área azul suficiente para considerar como piso direcional mesmo sem linha definida
        if area_total_azul > self.area_minima_piso_direcional:
            cv2.putText(frame, "PISO DIRECIONAL DETECTADO", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            return "PISO_DIRECIONAL", 0, frame, mascara_debug

        # Se não achou nem vermelho nem azul
        return "PERDIDO", 0, frame, mascara_debug


# ==========================================
# TESTE DO MÓDULO DE VISÃO (Usando a webcam do PC)
# ==========================================
if __name__ == "__main__":
    visao = ProcessadorVisao()
    
    print("A abrir a webcam... Pressione 'q' para sair.")
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame_lido = cap.read()
        if not ret:
            break

        estado, erro, img_processada, img_mascara = visao.processar_frame(frame_lido, tem_espelho=False)

        cv2.imshow("Visao do Drone", img_processada)
        cv2.imshow("Filtro Cores (Mascara)", img_mascara)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()