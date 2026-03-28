<<<<<<< HEAD
import cv2
import numpy as np
import json
import time
import os
from djitellopy import Tello

# ================= CONFIGURAÇÕES =================
WIDTH, HEIGHT = 854, 480
CAM_W, CAM_H = 427, 480

HSV_FILE = "hsv.json"

FORWARD_SPEED = 8
DESCENT_CM = 35


KP = 0.4
KI = 0.0
KD = 0.25

LOSS_TIME_LIMIT = 2.0
END_MESSAGE_TIME = 3.0
# =================================================

STATE_CALIBRATION = 0
STATE_FOLLOW = 1
STATE_FINISHED = 2

last_error = 0
integral = 0


# ================= FUNÇÕES =================
def pid_control(error):
    global last_error, integral
    integral += error
    derivative = error - last_error
    last_error = error
    return int(np.clip(KP * error + KI * integral + KD * derivative, -20, 20))


def process_mask(img, lower, upper):
    blur = cv2.GaussianBlur(img, (5, 5), 0)
    hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower, upper)
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.erode(mask, kernel, 1)
    mask = cv2.dilate(mask, kernel, 2)
    return mask


def get_center(mask):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if contours:
        c = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(c)
        return x + w // 2
    return None


def emergency_stop(msg="Emergência acionada"):
    try:
        drone.send_rc_control(0, 0, 0, 0)
        drone.land()
    except:
        pass

    tela = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    cv2.putText(tela, "EMERGENCIA", (60, HEIGHT // 2 - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
    cv2.putText(tela, msg, (40, HEIGHT // 2 + 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    cv2.imshow("Sistema", tela)
    cv2.waitKey(2000)
    cv2.destroyAllWindows()
    exit()


def check_emergency_key(key):
    if key == 27:  # ESC
        emergency_stop("ESC pressionado")


# ================= INÍCIO =================
try:
    drone = Tello()
    drone.connect()
    print(f"Bateria: {drone.get_battery()}%")

    drone.streamon()
    time.sleep(2)
    frame_read = drone.get_frame_read()

    lower = upper = None
    last_seen_time = None
    state = STATE_CALIBRATION

    # ---------- HSV UI ----------
    def empty(a): pass

    cv2.namedWindow("HSV")
    cv2.resizeWindow("HSV", 240, 640)

    cv2.createTrackbar("H Min", "HSV", 0, 179, empty)
    cv2.createTrackbar("H Max", "HSV", 179, 179, empty)
    cv2.createTrackbar("S Min", "HSV", 0, 255, empty)
    cv2.createTrackbar("S Max", "HSV", 255, 255, empty)
    cv2.createTrackbar("V Min", "HSV", 0, 255, empty)
    cv2.createTrackbar("V Max", "HSV", 255, 255, empty)

    # ================= LOOP =================
    while True:
        frame = frame_read.frame
        if frame is None:
            continue

        frame = cv2.resize(frame, (CAM_W, CAM_H))
        frame = cv2.flip(frame, 0)

        # ---------- CALIBRAÇÃO ----------
        if state == STATE_CALIBRATION:
            hmin = cv2.getTrackbarPos("H Min", "HSV")
            hmax = cv2.getTrackbarPos("H Max", "HSV")
            smin = cv2.getTrackbarPos("S Min", "HSV")
            smax = cv2.getTrackbarPos("S Max", "HSV")
            vmin = cv2.getTrackbarPos("V Min", "HSV")
            vmax = cv2.getTrackbarPos("V Max", "HSV")

            temp_lower = np.array([hmin, smin, vmin])
            temp_upper = np.array([hmax, smax, vmax])

            mask = cv2.inRange(
                cv2.cvtColor(frame, cv2.COLOR_BGR2HSV),
                temp_lower, temp_upper
            )

            cv2.imshow("HSV", mask)
            cv2.imshow("Sistema", frame)

            key = cv2.waitKey(1) & 0xFF
            check_emergency_key(key)

            if key == ord("s"):
                with open(HSV_FILE, "w") as f:
                    json.dump(
                        {"lower": temp_lower.tolist(), "upper": temp_upper.tolist()},
                        f
                    )

                lower, upper = temp_lower, temp_upper
                cv2.destroyWindow("HSV")

                last_seen_time = time.time()

                drone.takeoff()
                time.sleep(2)
                drone.move_down(DESCENT_CM)
                time.sleep(1)

                state = STATE_FOLLOW

        # ---------- SEGUINDO LINHA ----------
        elif state == STATE_FOLLOW:
            mask = process_mask(frame, lower, upper)
            cx = get_center(mask)

            mask_bgr = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
            display = cv2.resize(
                np.hstack([frame, mask_bgr]),
                (WIDTH, HEIGHT)
            )

            if cx is not None:
                last_seen_time = time.time()
                error = cx - CAM_W // 2
                lr = pid_control(error)
                drone.send_rc_control(lr, FORWARD_SPEED, 0, 0)
            else:
                drone.send_rc_control(0, 0, 0, 0)
                if time.time() - last_seen_time > LOSS_TIME_LIMIT:
                    state = STATE_FINISHED

            cv2.imshow("Sistema", display)
            key = cv2.waitKey(1) & 0xFF
            check_emergency_key(key)

        # ---------- FIM ----------
        else:
            drone.send_rc_control(0, 0, 0, 0)

            tela = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
            cv2.putText(tela, "Fim de Percurso", (60, HEIGHT // 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.4, (255, 255, 255), 3)
            cv2.imshow("Sistema", tela)

            key = cv2.waitKey(int(END_MESSAGE_TIME * 1000)) & 0xFF
            check_emergency_key(key)

            drone.land()
            break

except Exception as e:
    emergency_stop(str(e))

finally:
    try:
        drone.streamoff()
    except:
        pass
    cv2.destroyAllWindows()
=======
import cv2
import numpy as np
import json
import time
import os
from djitellopy import Tello

# ================= CONFIGURAÇÕES =================
WIDTH, HEIGHT = 854, 480
CAM_W, CAM_H = 427, 480

HSV_FILE = "hsv.json"

FORWARD_SPEED = 8
DESCENT_CM = 35


KP = 0.4
KI = 0.0
KD = 0.25

LOSS_TIME_LIMIT = 2.0
END_MESSAGE_TIME = 3.0
# =================================================

STATE_CALIBRATION = 0
STATE_FOLLOW = 1
STATE_FINISHED = 2

last_error = 0
integral = 0


# ================= FUNÇÕES =================
def pid_control(error):
    global last_error, integral
    integral += error
    derivative = error - last_error
    last_error = error
    return int(np.clip(KP * error + KI * integral + KD * derivative, -20, 20))


def process_mask(img, lower, upper):
    blur = cv2.GaussianBlur(img, (5, 5), 0)
    hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower, upper)
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.erode(mask, kernel, 1)
    mask = cv2.dilate(mask, kernel, 2)
    return mask


def get_center(mask):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if contours:
        c = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(c)
        return x + w // 2
    return None


def emergency_stop(msg="Emergência acionada"):
    try:
        drone.send_rc_control(0, 0, 0, 0)
        drone.land()
    except:
        pass

    tela = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    cv2.putText(tela, "EMERGENCIA", (60, HEIGHT // 2 - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
    cv2.putText(tela, msg, (40, HEIGHT // 2 + 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    cv2.imshow("Sistema", tela)
    cv2.waitKey(2000)
    cv2.destroyAllWindows()
    exit()


def check_emergency_key(key):
    if key == 27:  # ESC
        emergency_stop("ESC pressionado")


# ================= INÍCIO =================
try:
    drone = Tello()
    drone.connect()
    print(f"Bateria: {drone.get_battery()}%")

    drone.streamon()
    time.sleep(2)
    frame_read = drone.get_frame_read()

    lower = upper = None
    last_seen_time = None
    state = STATE_CALIBRATION

    # ---------- HSV UI ----------
    def empty(a): pass

    cv2.namedWindow("HSV")
    cv2.resizeWindow("HSV", 240, 640)

    cv2.createTrackbar("H Min", "HSV", 0, 179, empty)
    cv2.createTrackbar("H Max", "HSV", 179, 179, empty)
    cv2.createTrackbar("S Min", "HSV", 0, 255, empty)
    cv2.createTrackbar("S Max", "HSV", 255, 255, empty)
    cv2.createTrackbar("V Min", "HSV", 0, 255, empty)
    cv2.createTrackbar("V Max", "HSV", 255, 255, empty)

    # ================= LOOP =================
    while True:
        frame = frame_read.frame
        if frame is None:
            continue

        frame = cv2.resize(frame, (CAM_W, CAM_H))
        frame = cv2.flip(frame, 0)

        # ---------- CALIBRAÇÃO ----------
        if state == STATE_CALIBRATION:
            hmin = cv2.getTrackbarPos("H Min", "HSV")
            hmax = cv2.getTrackbarPos("H Max", "HSV")
            smin = cv2.getTrackbarPos("S Min", "HSV")
            smax = cv2.getTrackbarPos("S Max", "HSV")
            vmin = cv2.getTrackbarPos("V Min", "HSV")
            vmax = cv2.getTrackbarPos("V Max", "HSV")

            temp_lower = np.array([hmin, smin, vmin])
            temp_upper = np.array([hmax, smax, vmax])

            mask = cv2.inRange(
                cv2.cvtColor(frame, cv2.COLOR_BGR2HSV),
                temp_lower, temp_upper
            )

            cv2.imshow("HSV", mask)
            cv2.imshow("Sistema", frame)

            key = cv2.waitKey(1) & 0xFF
            check_emergency_key(key)

            if key == ord("s"):
                with open(HSV_FILE, "w") as f:
                    json.dump(
                        {"lower": temp_lower.tolist(), "upper": temp_upper.tolist()},
                        f
                    )

                lower, upper = temp_lower, temp_upper
                cv2.destroyWindow("HSV")

                last_seen_time = time.time()

                drone.takeoff()
                time.sleep(2)
                drone.move_down(DESCENT_CM)
                time.sleep(1)

                state = STATE_FOLLOW

        # ---------- SEGUINDO LINHA ----------
        elif state == STATE_FOLLOW:
            mask = process_mask(frame, lower, upper)
            cx = get_center(mask)

            mask_bgr = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
            display = cv2.resize(
                np.hstack([frame, mask_bgr]),
                (WIDTH, HEIGHT)
            )

            if cx is not None:
                last_seen_time = time.time()
                error = cx - CAM_W // 2
                lr = pid_control(error)
                drone.send_rc_control(lr, FORWARD_SPEED, 0, 0)
            else:
                drone.send_rc_control(0, 0, 0, 0)
                if time.time() - last_seen_time > LOSS_TIME_LIMIT:
                    state = STATE_FINISHED

            cv2.imshow("Sistema", display)
            key = cv2.waitKey(1) & 0xFF
            check_emergency_key(key)

        # ---------- FIM ----------
        else:
            drone.send_rc_control(0, 0, 0, 0)

            tela = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
            cv2.putText(tela, "Fim de Percurso", (60, HEIGHT // 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.4, (255, 255, 255), 3)
            cv2.imshow("Sistema", tela)

            key = cv2.waitKey(int(END_MESSAGE_TIME * 1000)) & 0xFF
            check_emergency_key(key)

            drone.land()
            break

except Exception as e:
    emergency_stop(str(e))

finally:
    try:
        drone.streamoff()
    except:
        pass
    cv2.destroyAllWindows()
>>>>>>> e947cbd31e2edc5b21f5cb7e239f399cbaa0df11
