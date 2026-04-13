from djitellopy import Tello
import cv2
import time

# Módulos do projeto
from mapeamento import MapaTopologico
from voz import InterfaceVoz
from visao import ProcessadorVisao

class ControladorDrone:
    def __init__(self):
        self.mapa = MapaTopologico()
        self.voz = InterfaceVoz()
        self.visao = ProcessadorVisao()
        
        self.tello = Tello()
        self.tello.connect()
        print(f"Bateria: {self.tello.get_battery()}%")
        
        self.tello.streamoff() # Limpa stream antigo
        self.tello.streamon()

        # Estados: 0:Voz/Planos, 1:Decolagem, 1.5:Estabilização, 1.7:Confirmação de piso, 2:Navegação(Visão), 3:Ação, 4:Pouso
        self.estado_atual = 0  
        self.plano_acoes = []
        self.acao_index = 0
        
        # Parâmetros de controle (NÃO ALTERAR)
        self.velocidade_frente = 15 # Velocidade baixa por segurança
        self.kp = 0.2               # Ganho do ajuste lateral

    def iniciar_missao(self):
        while True:
            # 1. Obter o frame bruto da câmera
            frame_tello = self.tello.get_frame_read().frame
            frame_bruto = cv2.cvtColor(frame_tello, cv2.COLOR_RGB2BGR)
            
            # --- LÓGICA DE TRANSIÇÃO DE ESTADOS ---

            # ESTADO 0: Configuração via Voz
            if self.estado_atual == 0:
                origem, destino = self.voz.obter_rota_do_usuario(self.mapa)
                _, self.plano_acoes = self.mapa.gerar_plano_de_voo(origem, destino)
                self.voz.falar("Plano confirmado. Decolando agora.")
                self.estado_atual = 1

            # ESTADO 1: Decolagem Física
            elif self.estado_atual == 1:
                # Verificação de bateria antes do takeoff (segurança)
                bateria = self.tello.get_battery()
                print(f"[Segurança]: Bateria atual: {bateria}%")
                if bateria < 25:
                    self.voz.falar("Bateria fraca. Encerrando sistema por segurança.")
                    self.tello.land()          # Precaução se por algum motivo estiver no ar
                    cv2.destroyAllWindows()
                    raise SystemExit("Bateria insuficiente para o voo.")
                # Bateria OK, prossegue com decolagem
                self.tello.takeoff()
                # Após o comando de decolar, mudamos para o estado de estabilização
                self.estado_atual = 1.5

            # ESTADO 1.5: Estabilização (O drone já subiu, agora espera o balanço parar)
            elif self.estado_atual == 1.5:
                print("[Sistema]: Estabilizando altitude e sensores...")
                time.sleep(3) # Aguarda 3 segundos para o drone ficar imóvel no ar
                
                # Reduz altitude para metade da altura padrão (segurança e melhor visão do piso)
                print("[Segurança]: Reduzindo altitude para ~50 cm...")
                self.tello.move_down(30)
                time.sleep(1)  # Aguarda o movimento de descida estabilizar
                
                self.acao_index += 1 # Avança o índice (já saiu do 'DECOLAR')
                self.voz.falar("Drone estabilizado. Aguardando identificação do piso direcional.")
                self.estado_atual = 1.7   # Vai para o novo estado de confirmação

            # ESTADO 1.7: Confirmação do piso direcional azul (NOVO)
            elif self.estado_atual == 1.7:
                # Processa o frame para ver o que está embaixo
                oque_vejo, erro_x, frame_debug, mascara_debug = self.visao.processar_frame(frame_bruto, tem_espelho=True)
                
                # Exibe as janelas de vídeo (visão e máscara)
                cv2.imshow("Cedalión - Visão Ativa", frame_debug)
                cv2.imshow("Cedalión - Mascara de Cores", mascara_debug)
                
                print("[Estado 1.7]: Aguardando piso direcional azul...")
                
                # Se detectar linha ou piso direcional (grande área azul), confirma e avança
                if oque_vejo == "LINHA" or oque_vejo == "PISO_DIRECIONAL":
                    self.voz.falar("Piso direcional identificado. Iniciando navegação.")
                    time.sleep(1)  # Pequena pausa para a fala terminar
                    self.estado_atual = 2
                else:
                    # Continua parado (nenhum comando RC é enviado)
                    pass

            # --- PROCESSAMENTO DE VISÃO (Só ocorre nos estados de voo ativo) ---
            if self.estado_atual >= 2:
                # Aqui o processador de visão começa a trabalhar de fato
                oque_vejo, erro_x, frame_debug, mascara_debug = self.visao.processar_frame(frame_bruto, tem_espelho=True)
                
                # Mostramos o que o drone vê, mais a máscara de cores no fundo
                cv2.imshow("Cedalión - Visão Ativa", frame_debug)
                cv2.imshow("Cedalión - Mascara de Cores", mascara_debug)
                
                # LÓGICA DE NAVEGAÇÃO
                if self.estado_atual == 2: # Seguindo a Linha Azul
                    if oque_vejo == "LINHA":
                        v_lateral = int(erro_x * self.kp)
                        self.tello.send_rc_control(v_lateral, self.velocidade_frente, 0, 0)
                    elif oque_vejo == "ALERTA": # Chegou no piso vermelho
                        self.tello.send_rc_control(0, 0, 0, 0)
                        self.estado_atual = 3

                elif self.estado_atual == 3: # Ações em Checkpoints (Piso Vermelho)
                    acao = self.plano_acoes[self.acao_index]
                    if acao == "SEGUIR_FRENTE":
                        self.tello.move_forward(40)
                        self.acao_index += 2
                        self.estado_atual = 2
                    elif "POUSAR" in self.plano_acoes[self.acao_index:]:
                        self.estado_atual = 4

                elif self.estado_atual == 4: # Pouso
                    self.tello.land()
                    break
            else:
                # Enquanto não está navegando (estados 0, 1, 1.5, 1.7), mostra o vídeo cru se ainda não foi mostrado
                # Obs: O estado 1.7 já exibe as janelas acima; para os demais mostramos um preview simples.
                if self.estado_atual != 1.7:
                    img_preview = cv2.resize(frame_bruto, (432, 320))
                    cv2.imshow("Cedalión - Visão Ativa", img_preview)

            # Verificação de teclas de emergência: 'q' ou ESC (código 27)
            tecla = cv2.waitKey(1) & 0xFF
            if tecla == ord('q') or tecla == 27:
                print("[EMERGÊNCIA]: Botão de emergência acionado! Pousando imediatamente.")
                self.voz.falar("Emergência. Pousando agora.")
                self.tello.land()
                self.tello.streamoff()
                cv2.destroyAllWindows()
                break

        self.tello.streamoff()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    sistema = ControladorDrone()
    sistema.iniciar_missao()