from djitellopy import Tello
import cv2

def teste_camera_crua():
    print("Iniciando conexão com o Tello...")
    
    # 1. Cria o objeto do drone e conecta
    tello = Tello()
    tello.connect()
    
    # 2. Mostra a bateria atual
    print(f"Bateria do Tello: {tello.get_battery()}%")

    # 3. Prepara a transmissão de vídeo
    tello.streamoff() # Garante que qualquer stream anterior seja fechado
    tello.streamon()  # Liga a câmera
    
    print("Câmera ligada! Pressione a tecla 'q' na janela do vídeo para encerrar.")

    # 4. Loop para capturar e mostrar a imagem continuamente
    while True:
        # Pega a imagem da câmera
        frame = tello.get_frame_read().frame
        
        # O Tello manda a imagem em RGB, mas o OpenCV trabalha em BGR.
        # Precisamos converter para as cores ficarem corretas na tela.
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        # Mostra a imagem numa janela chamada "Camera do Tello"
        cv2.imshow("Camera do Tello", frame_bgr)
        
        # Espera 1 milissegundo e verifica se a tecla 'q' foi pressionada
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Encerrando o teste...")
            break

    # 5. Desliga a câmera e fecha a janela de forma segura
    tello.streamoff()
    cv2.destroyAllWindows()
    print("Teste finalizado com sucesso.")

if __name__ == "__main__":
    teste_camera_crua()