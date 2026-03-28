import threading
from djitellopy import Tello
from queue import Empty

class TelloController(threading.Thread):
    def __init__(self, command_queue):
        super().__init__()
        self.tello = Tello()
        self.command_queue = command_queue
        self.running = True

    def run(self):
        try:
            self.tello.connect()
            self.tello.takeoff()
            print("Tello conectado e decolado!")

            while self.running:
                battery_percentage = self.tello.get_battery()
                print("Bateria {}".format(battery_percentage))

                # Pousa e disconecta se a bateria estiver menor que 20%
                if battery_percentage < 20:
                    print("Bateria baixa. Iniciando pouso...")
                    break  # Sai do loop para a seção 'finally'

                # Pega o comando da fila, com um timeout de 1 segundo
                try:
                    command = self.command_queue.get(block=True, timeout=1)
                except Empty:
                    continue  # Continua o loop se a fila estiver vazia

                if command == 'stop':
                    self.running = False
                    continue

                print(f"Executando comando do drone: {command}")

                if command == 'down':
                    self.tello.move_back(25)
                elif command == 'up':
                    self.tello.move_forward(25)
                elif command == 'left':
                    self.tello.move_left(25)
                elif command == 'right':
                    self.tello.move_right(25)

        except Exception as e:
            print(f"Erro inesperado: {e}")
        finally:
            battery_percentage = self.tello.get_battery()
            print("Bateria {}".format(battery_percentage))
            self.land_and_disconnect()

    def land_and_disconnect(self):
        # Lógica para pousar e desconectar
        try:
            print("Pousando o Tello...")
            self.tello.land()
            print("Tello pousado e desconectado.")
        except Exception as e:
            print(f"Erro ao pousar o Tello: {e}")
