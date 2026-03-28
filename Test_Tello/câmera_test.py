<<<<<<< HEAD
from djitellopy import Tello
import cv2, time, av

w, h = 640, 480
drone = Tello()
drone.connect()
print("Bateria:", drone.get_battery())

drone.streamon()

# tenta PyAV (get_frame_read), senão fallback para cv2.VideoCapture
try:
    frame_read = drone.get_frame_read()
    time.sleep(1)
    use_frame_read = True
except Exception as e:
    print("Erro PyAV:", e)
    print("Tentando fallback com cv2.VideoCapture")
    cap = cv2.VideoCapture('udp://@0.0.0.0:11111', cv2.CAP_FFMPEG)
    if not cap.isOpened():
        raise RuntimeError("Não foi possível abrir stream UDP (verifique FFmpeg/Firewall).")
    use_frame_read = False

while True:
    if use_frame_read:
        frame = frame_read.frame
    else:
        ret, frame = cap.read()
        if not ret:
            continue

    if frame is None:
        continue

    img = cv2.resize(frame, (w, h))
    cv2.imshow("Camera do Drone", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

if use_frame_read:
    drone.streamoff()
else:
    cap.release()
=======
from djitellopy import Tello
import cv2, time, av

w, h = 640, 480
drone = Tello()
drone.connect()
print("Bateria:", drone.get_battery())

drone.streamon()

# tenta PyAV (get_frame_read), senão fallback para cv2.VideoCapture
try:
    frame_read = drone.get_frame_read()
    time.sleep(1)
    use_frame_read = True
except Exception as e:
    print("Erro PyAV:", e)
    print("Tentando fallback com cv2.VideoCapture")
    cap = cv2.VideoCapture('udp://@0.0.0.0:11111', cv2.CAP_FFMPEG)
    if not cap.isOpened():
        raise RuntimeError("Não foi possível abrir stream UDP (verifique FFmpeg/Firewall).")
    use_frame_read = False

while True:
    if use_frame_read:
        frame = frame_read.frame
    else:
        ret, frame = cap.read()
        if not ret:
            continue

    if frame is None:
        continue

    img = cv2.resize(frame, (w, h))
    cv2.imshow("Camera do Drone", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

if use_frame_read:
    drone.streamoff()
else:
    cap.release()
>>>>>>> e947cbd31e2edc5b21f5cb7e239f399cbaa0df11
cv2.destroyAllWindows()