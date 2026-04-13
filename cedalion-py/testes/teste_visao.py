from djitellopy import Tello
import cv2
from visao import ProcessadorVisao

def teste_visao_drone():
    # 1. Inicializa o nosso processador de visão
    visao = ProcessadorVisao()

    # 2. Conecta ao Drone
    print("Conectando ao Tello...")
    tello = Tello()
    tello.connect()
    print(f"Bateria: {tello.get_battery()}%")

    # 3. Liga a transmissão de vídeo
    tello.streamoff() # Prevenção caso o stream tenha travado na última vez
    tello.streamon()
    print("Câmera ligada! Segure o drone com a mão e aponte para o chão.")
    print("Pressione 'q' na janela de vídeo para encerrar o teste.")

    # 4. Loop de captura e processamento
    while True:
        # Pega o frame atual cru da câmera do drone
        frame_tello = tello.get_frame_read().frame
        frame_bruto = cv2.cvtColor(frame_tello, cv2.COLOR_RGB2BGR)

        # Processa o frame (Deixei tem_espelho=True, assumindo que a peça 3D já está nele!)
        oque_vejo, erro_x, img_processada, img_mascara = visao.processar_frame(frame_bruto, tem_espelho=True)

        # Mostra as duas telas para você debugar (A visão final e o filtro de cor)
        cv2.imshow("Teste - Visao do Drone", img_processada)
        cv2.imshow("Teste - Mascara Amarela", img_mascara)

        # Imprime no terminal o que ele está achando (útil para ver o valor do Erro X variando)
        if oque_vejo != "PERDIDO":
            print(f"Estado: {oque_vejo} | Erro Lateral (X): {erro_x}")

        # Aperte 'q' para fechar as janelas e desligar a câmera
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Limpeza e encerramento
    tello.streamoff()
    cv2.destroyAllWindows()
    print("Teste finalizado.")

if __name__ == "__main__":
    teste_visao_drone()