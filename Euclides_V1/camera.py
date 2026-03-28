import cv2

# Usamos o índice 0, que é o padrão para a primeira webcam encontrada
cap = cv2.VideoCapture(0)

# Tente adicionar estas configurações
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not cap.isOpened():
    print("❌ Erro: Não consegui acessar /dev/video0.")
    print("Verifique se você rodou o 'usbipd attach' no Windows e o 'sudo chmod' no WSL.")
else:
    print("✅ Câmera conectada com sucesso!")
    print("Pressione 'q' para fechar a janela de vídeo.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Erro ao receber o frame.")
            break

        # Mostra o vídeo em uma janela
        cv2.imshow("Teste Webcam WSL", frame)

        # Sai do loop ao apertar a tecla 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()