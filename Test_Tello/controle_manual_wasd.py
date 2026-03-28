<<<<<<< HEAD
import pygame
import cv2
from djitellopy import Tello
import time
import threading
import queue
import numpy as np

SPEED = 60
SEND_HZ = 30
FRAME_QUEUE_MAXSIZE = 2

WINDOW_W, WINDOW_H = 640, 480  # resolução reduzida

class TelloController:
    def __init__(self):
        self.tello = Tello()
        self.is_flying = False
        self.battery = 0

        self.rc_command = [0, 0, 0, 0]
        self.rc_lock = threading.Lock()

        self.stop_event = threading.Event()
        self.frame_queue = queue.Queue(maxsize=FRAME_QUEUE_MAXSIZE)

        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        pygame.display.set_caption("Drone View")
        
        self.font = pygame.font.SysFont("Arial", 28)

    def _video_reader_task(self):
        try:
            frame_reader = self.tello.get_frame_read()
        except:
            return
        
        while not self.stop_event.is_set():
            frame = frame_reader.frame
            if frame is not None:
                if self.frame_queue.full():
                    try:
                        self.frame_queue.get_nowait()
                    except:
                        pass
                try:
                    self.frame_queue.put_nowait(frame)
                except:
                    pass
            time.sleep(0.01)

    def _control_sender_task(self):
        interval = 1 / SEND_HZ
        while not self.stop_event.is_set():
            with self.rc_lock:
                lr, fb, ud, yaw = self.rc_command.copy()

            if self.is_flying:
                try:
                    self.tello.send_rc_control(int(lr), int(fb), int(ud), int(yaw))
                except:
                    pass
            else:
                try:
                    self.tello.send_rc_control(0, 0, 0, 0)
                except:
                    pass

            time.sleep(interval)

    def _draw_overlay(self):
        w3 = WINDOW_W // 3
        h3 = WINDOW_H // 3

        pygame.draw.line(self.screen, (255, 255, 255), (w3, 0), (w3, WINDOW_H), 2)
        pygame.draw.line(self.screen, (255, 255, 255), (2 * w3, 0), (2 * w3, WINDOW_H), 2)
        pygame.draw.line(self.screen, (255, 255, 255), (0, h3), (WINDOW_W, h3), 2)
        pygame.draw.line(self.screen, (255, 255, 255), (0, 2 * h3), (WINDOW_W, 2 * h3), 2)

        positions = {
            "N": (2 * w3 - 30, 10),
            "O": (w3 - 30, h3 + 10),
            "L": (WINDOW_W - 30, h3 + 10),
            "S": (2 * w3 - 30, 2 * h3 + 10),
        }

        for letter, pos in positions.items():
            text = self.font.render(letter, True, (255, 255, 255))
            self.screen.blit(text, pos)

    def run(self):
        try:
            self.tello.connect()
            self.battery = self.tello.get_battery()

            self.tello.streamoff()
            time.sleep(1)
            self.tello.streamon()
            time.sleep(1)

            self.stop_event.clear()
            threading.Thread(target=self._video_reader_task, daemon=True).start()
            threading.Thread(target=self._control_sender_task, daemon=True).start()

            clock = pygame.time.Clock()
            battery_update_timer = time.time()

            while not self.stop_event.is_set():
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.stop_event.set()

                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_t and not self.is_flying:
                            try:
                                self.tello.takeoff()
                                self.is_flying = True
                            except:
                                pass

                        elif event.key == pygame.K_l and self.is_flying:
                            try:
                                self.tello.land()
                                self.is_flying = False
                            except:
                                pass

                keys = pygame.key.get_pressed()

                lr = fb = ud = yaw = 0
                if keys[pygame.K_a]: lr = -SPEED
                if keys[pygame.K_d]: lr = SPEED
                if keys[pygame.K_w]: fb = SPEED
                if keys[pygame.K_s]: fb = -SPEED
                if keys[pygame.K_UP]: ud = SPEED
                if keys[pygame.K_DOWN]: ud = -SPEED
                if keys[pygame.K_LEFT]: yaw = -SPEED
                if keys[pygame.K_RIGHT]: yaw = SPEED

                with self.rc_lock:
                    self.rc_command = [lr, fb, ud, yaw]

                try:
                    frame = self.frame_queue.get_nowait()
                except:
                    frame = None

                self.screen.fill((0, 0, 0))

                if frame is not None:
                    try:
                        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        rgb = np.rot90(rgb)
                        surf = pygame.surfarray.make_surface(rgb)
                        surf = pygame.transform.scale(surf, (WINDOW_W, WINDOW_H))
                        self.screen.blit(surf, (0, 0))
                    except:
                        pass

                self._draw_overlay()

                if time.time() - battery_update_timer > 5:
                    try:
                        self.battery = self.tello.get_battery()
                    except:
                        pass
                    battery_update_timer = time.time()

                pygame.display.flip()

                if keys[pygame.K_ESCAPE]:
                    self.stop_event.set()
                    break

                clock.tick(60)

        finally:
            self.cleanup()

    def cleanup(self):
        self.stop_event.set()

        if self.is_flying:
            try:
                self.tello.land()
            except:
                pass

        try:
            self.tello.streamoff()
        except:
            pass

        try:
            self.tello.end()
        except:
            pass

        pygame.quit()


if __name__ == "__main__":
    controller = TelloController()
    controller.run()
=======
import pygame
import cv2
from djitellopy import Tello
import time
import threading
import queue
import numpy as np

SPEED = 60
SEND_HZ = 30
FRAME_QUEUE_MAXSIZE = 2

WINDOW_W, WINDOW_H = 640, 480  # resolução reduzida

class TelloController:
    def __init__(self):
        self.tello = Tello()
        self.is_flying = False
        self.battery = 0

        self.rc_command = [0, 0, 0, 0]
        self.rc_lock = threading.Lock()

        self.stop_event = threading.Event()
        self.frame_queue = queue.Queue(maxsize=FRAME_QUEUE_MAXSIZE)

        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        pygame.display.set_caption("Drone View")
        
        self.font = pygame.font.SysFont("Arial", 28)

    def _video_reader_task(self):
        try:
            frame_reader = self.tello.get_frame_read()
        except:
            return
        
        while not self.stop_event.is_set():
            frame = frame_reader.frame
            if frame is not None:
                if self.frame_queue.full():
                    try:
                        self.frame_queue.get_nowait()
                    except:
                        pass
                try:
                    self.frame_queue.put_nowait(frame)
                except:
                    pass
            time.sleep(0.01)

    def _control_sender_task(self):
        interval = 1 / SEND_HZ
        while not self.stop_event.is_set():
            with self.rc_lock:
                lr, fb, ud, yaw = self.rc_command.copy()

            if self.is_flying:
                try:
                    self.tello.send_rc_control(int(lr), int(fb), int(ud), int(yaw))
                except:
                    pass
            else:
                try:
                    self.tello.send_rc_control(0, 0, 0, 0)
                except:
                    pass

            time.sleep(interval)

    def _draw_overlay(self):
        w3 = WINDOW_W // 3
        h3 = WINDOW_H // 3

        pygame.draw.line(self.screen, (255, 255, 255), (w3, 0), (w3, WINDOW_H), 2)
        pygame.draw.line(self.screen, (255, 255, 255), (2 * w3, 0), (2 * w3, WINDOW_H), 2)
        pygame.draw.line(self.screen, (255, 255, 255), (0, h3), (WINDOW_W, h3), 2)
        pygame.draw.line(self.screen, (255, 255, 255), (0, 2 * h3), (WINDOW_W, 2 * h3), 2)

        positions = {
            "N": (2 * w3 - 30, 10),
            "O": (w3 - 30, h3 + 10),
            "L": (WINDOW_W - 30, h3 + 10),
            "S": (2 * w3 - 30, 2 * h3 + 10),
        }

        for letter, pos in positions.items():
            text = self.font.render(letter, True, (255, 255, 255))
            self.screen.blit(text, pos)

    def run(self):
        try:
            self.tello.connect()
            self.battery = self.tello.get_battery()

            self.tello.streamoff()
            time.sleep(1)
            self.tello.streamon()
            time.sleep(1)

            self.stop_event.clear()
            threading.Thread(target=self._video_reader_task, daemon=True).start()
            threading.Thread(target=self._control_sender_task, daemon=True).start()

            clock = pygame.time.Clock()
            battery_update_timer = time.time()

            while not self.stop_event.is_set():
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.stop_event.set()

                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_t and not self.is_flying:
                            try:
                                self.tello.takeoff()
                                self.is_flying = True
                            except:
                                pass

                        elif event.key == pygame.K_l and self.is_flying:
                            try:
                                self.tello.land()
                                self.is_flying = False
                            except:
                                pass

                keys = pygame.key.get_pressed()

                lr = fb = ud = yaw = 0
                if keys[pygame.K_a]: lr = -SPEED
                if keys[pygame.K_d]: lr = SPEED
                if keys[pygame.K_w]: fb = SPEED
                if keys[pygame.K_s]: fb = -SPEED
                if keys[pygame.K_UP]: ud = SPEED
                if keys[pygame.K_DOWN]: ud = -SPEED
                if keys[pygame.K_LEFT]: yaw = -SPEED
                if keys[pygame.K_RIGHT]: yaw = SPEED

                with self.rc_lock:
                    self.rc_command = [lr, fb, ud, yaw]

                try:
                    frame = self.frame_queue.get_nowait()
                except:
                    frame = None

                self.screen.fill((0, 0, 0))

                if frame is not None:
                    try:
                        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        rgb = np.rot90(rgb)
                        surf = pygame.surfarray.make_surface(rgb)
                        surf = pygame.transform.scale(surf, (WINDOW_W, WINDOW_H))
                        self.screen.blit(surf, (0, 0))
                    except:
                        pass

                self._draw_overlay()

                if time.time() - battery_update_timer > 5:
                    try:
                        self.battery = self.tello.get_battery()
                    except:
                        pass
                    battery_update_timer = time.time()

                pygame.display.flip()

                if keys[pygame.K_ESCAPE]:
                    self.stop_event.set()
                    break

                clock.tick(60)

        finally:
            self.cleanup()

    def cleanup(self):
        self.stop_event.set()

        if self.is_flying:
            try:
                self.tello.land()
            except:
                pass

        try:
            self.tello.streamoff()
        except:
            pass

        try:
            self.tello.end()
        except:
            pass

        pygame.quit()


if __name__ == "__main__":
    controller = TelloController()
    controller.run()
>>>>>>> e947cbd31e2edc5b21f5cb7e239f399cbaa0df11
