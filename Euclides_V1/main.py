import cv2 as cv
import mediapipe as mp
import numpy as np
import time
import os
from queue import Queue
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from tello_controller import TelloController

# --- CONFIGURAÇÕES DE TELA ---
SCREEN_WIDTH = 1366
SCREEN_HEIGHT = 768
WINDOW_NAME = "Euclides v2 - Control"

# Conexões manuais para o esqueleto (evita erro do solutions)
POSE_CONNECTIONS = [
    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16), (11, 23), (12, 24), (23, 24)
]


def clear_queue(queue):
    while not queue.empty():
        queue.get()


def resize_to_screen(frame, width, height):
    """Força o redimensionamento para preencher a tela."""
    return cv.resize(frame, (width, height), interpolation=cv.INTER_LINEAR)


def get_arm_direction(position_elbow, position_wrist):
    delta_x = position_wrist[0] - position_elbow[0]
    delta_y = position_wrist[1] - position_elbow[1]
    angle_rad = np.arctan2(delta_y, delta_x)
    angle_deg = np.degrees(angle_rad)

    if angle_deg < 0: angle_deg += 360

    if 45 < angle_deg < 135:
        return 'BAIXO'
    elif 225 < angle_deg < 315:
        return 'CIMA'
    elif angle_deg <= 45 or angle_deg >= 315:
        return 'ESQUERDA'
    else:
        return 'DIREITA'


def draw_skeleton_manually(frame, landmarks):
    h, w = frame.shape[:2]
    # Linhas
    for connection in POSE_CONNECTIONS:
        start_pt = landmarks[connection[0]]
        end_pt = landmarks[connection[1]]
        x1, y1 = int(start_pt.x * w), int(start_pt.y * h)
        x2, y2 = int(end_pt.x * w), int(end_pt.y * h)
        cv.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)

    # Pontos principais
    indices = [11, 12, 13, 14, 15, 16]
    for idx in indices:
        pt = landmarks[idx]
        cx, cy = int(pt.x * w), int(pt.y * h)
        cv.circle(frame, (cx, cy), 6, (255, 255, 255), -1)
    return frame


def process_gestures(landmarks, h, w):
    left_elbow, left_wrist = landmarks[13], landmarks[15]
    right_elbow, right_wrist = landmarks[14], landmarks[16]

    p_elbow_l = (int(left_elbow.x * w), int(left_elbow.y * h))
    p_wrist_l = (int(left_wrist.x * w), int(left_wrist.y * h))
    dir_left = get_arm_direction(p_elbow_l, p_wrist_l)

    p_elbow_r = (int(right_elbow.x * w), int(right_elbow.y * h))
    p_wrist_r = (int(right_wrist.x * w), int(right_wrist.y * h))
    dir_right = get_arm_direction(p_elbow_r, p_wrist_r)

    return dir_right, dir_left


def draw_hud(frame, dir_right, dir_left):
    frame = cv.flip(frame, 1)  # Espelha para ficar natural
    h, w = frame.shape[:2]

    gestures_map = {
        ("BAIXO", "BAIXO"): "BAIXO",
        ("CIMA", "CIMA"): "CIMA",
        ("ESQUERDA", "ESQUERDA"): "ESQUERDA",
        ("DIREITA", "DIREITA"): "DIREITA",
        ("BAIXO", "CIMA"): "ATERRISSAR",
        ("CIMA", "BAIXO"): "FLIP"
    }
    gesture_text = gestures_map.get((dir_left, dir_right), "PARADO")

    # Desenha HUD
    cv.putText(frame, f'Esq: {dir_left}', (30, 60), cv.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
    cv.putText(frame, f'Dir: {dir_right}', (30, 110), cv.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)

    # Texto de Comando centralizado em baixo
    color = (0, 0, 255) if gesture_text == "PARADO" else (0, 255, 255)
    cv.putText(frame, f'COMANDO: {gesture_text}', (30, h - 50), cv.FONT_HERSHEY_SIMPLEX, 2, color, 5)

    return frame, gesture_text


def control_drone_logic(command_queue, count, gesture):
    # REDUZI O LIMITE DE 50 PARA 20 (Resposta mais rápida)
    limit = 50

    if count > limit and gesture != "PARADO":
        commands = {
            "BAIXO": "down", "CIMA": "up",
            "ESQUERDA": "left", "DIREITA": "right",
            "ATERRISSAR": "land", "FLIP": "flip"
        }
        if gesture in commands:
            cmd = commands[gesture]
            print(f">>> COMANDO ENVIADO: {cmd}")
            command_queue.put(cmd)
            return 0  # Reseta contador

    # Se estiver parado, não incrementa para evitar disparo acidental ao transitar
    if gesture != "PARADO":
        return count + 1

    return 0  # Reseta se estiver parado


def show_welcome_screens(assets_dir):
    images = ["welcome1.png", "welcome2.png", "welcome3.png"]
    cv.namedWindow("Intro", cv.WINDOW_NORMAL)
    cv.setWindowProperty("Intro", cv.WND_PROP_FULLSCREEN, cv.WINDOW_FULLSCREEN)

    for img_name in images:
        path = os.path.join(assets_dir, img_name)
        if not os.path.exists(path): continue

        img = cv.imread(path)
        img = resize_to_screen(img, SCREEN_WIDTH, SCREEN_HEIGHT)

        while True:
            cv.imshow("Intro", img)
            if cv.waitKey(1) == 13:  # Enter
                break
    cv.destroyWindow("Intro")


def main():
    # 1. Caminhos
    script_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(script_dir, 'assets')
    model_path = os.path.join(assets_dir, 'pose_landmarker_full.task')

    if not os.path.exists(model_path):
        print(f"ERRO: Modelo não encontrado em {model_path}")
        return

    # 2. Intro
    try:
        show_welcome_screens(assets_dir)
    except Exception as e:
        print(f"Erro na intro: {e}")

    # 3. Setup MediaPipe
    BaseOptions = mp.tasks.BaseOptions
    PoseLandmarker = mp.tasks.vision.PoseLandmarker
    PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
    VisionRunningMode = mp.tasks.vision.RunningMode

    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=model_path),
        running_mode=VisionRunningMode.VIDEO,
        num_poses=1
    )

    # 4. Iniciar Hardware
    cap = cv.VideoCapture(0)  # Mude para 1 se necessárioq
    command_queue = Queue()
    tello = TelloController(command_queue)

    # --- CONFIGURAÇÃO DA JANELA PRINCIPAL (FULLSCREEN) ---
#    cv.namedWindow(WINDOW_NAME, cv.WINDOW_NORMAL)
#    cv.setWindowProperty(WINDOW_NAME, cv.WND_PROP_FULLSCREEN, cv.WINDOW_FULLSCREEN)

    try:
        print("Iniciando Tello...")
        tello.start()

        with PoseLandmarker.create_from_options(options) as landmarker:
            count = 0
            while True:
                success, frame = cap.read()
                if not success: break

                # Processamento MediaPipe
                timestamp = int(time.time() * 1000)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
                result = landmarker.detect_for_video(mp_image, timestamp)

                # Lógica
                current_gesture = "PARADO"
                dir_r, dir_l = "-", "-"

                if result.pose_landmarks:
                    landmarks = result.pose_landmarks[0]
                    h, w, _ = frame.shape

                    frame = draw_skeleton_manually(frame, landmarks)
                    dir_r, dir_l = process_gestures(landmarks, h, w)
                    frame, current_gesture = draw_hud(frame, dir_r, dir_l)
                    count = control_drone_logic(command_queue, count, current_gesture)

                # Redimensionar para Fullscreen e Mostrar
                final_frame = resize_to_screen(frame, SCREEN_WIDTH, SCREEN_HEIGHT)
                cv.imshow(WINDOW_NAME, final_frame)

                if cv.waitKey(1) & 0xFF == ord('q'):
                    print("Comando de saída recebido.")
                    break

    except Exception as e:
        print(f"Erro Fatal: {e}")

    finally:
        # --- ORDEM DE FECHAMENTO CORRIGIDA ---
        print("Fechando janelas...")
        cv.destroyAllWindows()  # 1. Fecha a janela visual IMEDIATAMENTE

        print("Pousando drone...")
        clear_queue(command_queue)
        command_queue.put('land')  # 2. Envia comando de pouso

        cap.release()  # 3. Solta a câmera

        print("Aguardando thread do drone finalizar...")
        tello.join()  # 4. Encerra o processo do drone
        print("Encerrado com sucesso.")


if __name__ == "__main__":
    main()