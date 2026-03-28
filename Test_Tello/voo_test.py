<<<<<<< HEAD
from djitellopy import tello
import time

# --- Configuração ---
# Tempo de espera no ar em segundos
TEMPO_VOO = 5

# --- Inicialização ---
drone = tello.Tello()

# Conecta ao drone (certifique-se de estar conectado ao Wi-Fi do Tello)
print("Conectando ao Tello...")
drone.connect()
print(f"Bateria: {drone.get_battery()}%")

# --- Sequência de Voo ---
try:
    print("Decolando...")
    # O comando decolar (takeoff) é não bloqueante, mas leva um tempo para ser concluído.
    drone.takeoff() 
    
    print(f"Mantendo no ar por {TEMPO_VOO} segundos...")
    # O comando sleep pausa o código, fazendo o drone pairar no ar.
    time.sleep(TEMPO_VOO) 
    
    print("Pousando...")
    drone.land()
    
    print("Voo concluído com sucesso!")

except Exception as e:
    print(f"Ocorreu um erro: {e}")
    # Boa prática: garantir que o drone pouse em caso de erro.
    drone.land() 
    
# --- Limpeza ---
print("Desligando...")
=======
from djitellopy import tello
import time

# --- Configuração ---
# Tempo de espera no ar em segundos
TEMPO_VOO = 5

# --- Inicialização ---
drone = tello.Tello()

# Conecta ao drone (certifique-se de estar conectado ao Wi-Fi do Tello)
print("Conectando ao Tello...")
drone.connect()
print(f"Bateria: {drone.get_battery()}%")

# --- Sequência de Voo ---
try:
    print("Decolando...")
    # O comando decolar (takeoff) é não bloqueante, mas leva um tempo para ser concluído.
    drone.takeoff() 
    
    print(f"Mantendo no ar por {TEMPO_VOO} segundos...")
    # O comando sleep pausa o código, fazendo o drone pairar no ar.
    time.sleep(TEMPO_VOO) 
    
    print("Pousando...")
    drone.land()
    
    print("Voo concluído com sucesso!")

except Exception as e:
    print(f"Ocorreu um erro: {e}")
    # Boa prática: garantir que o drone pouse em caso de erro.
    drone.land() 
    
# --- Limpeza ---
print("Desligando...")
>>>>>>> e947cbd31e2edc5b21f5cb7e239f399cbaa0df11
# Pode ser necessário desligar o stream se estivesse ligado, mas não é o caso aqui.