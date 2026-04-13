import pyttsx3
import pyaudio
import json
import unicodedata
from vosk import Model, KaldiRecognizer
from mapeamento import MapaTopologico

class InterfaceVoz:
    def __init__(self):
        # 1. Configurando o falante (Cedalión)
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 170)
        
        vozes = self.engine.getProperty('voices')
        for voz in vozes:
            if 'brazil' in voz.name.lower() or 'pt-br' in voz.id.lower() or 'portuguese' in voz.name.lower():
                self.engine.setProperty('voice', voz.id)
                break

        # 2. Configurando o ouvinte Offline (Vosk)
        print("\n[Sistema]: Carregando o modelo de voz offline (Vosk)...")
        try:
            # Ele vai procurar a pasta chamada "modelo" que você colou no projeto
            self.modelo = Model("modelo")
            self.reconhecedor = KaldiRecognizer(self.modelo, 16000)
        except Exception as e:
            print("\nERRO CRÍTICO: Pasta 'modelo' não encontrada!")
            print("Você precisa baixar o modelo vosk-model-small-pt-0.3 e extrair na pasta do projeto com o nome 'modelo'.")
            exit()
            
        self.p = pyaudio.PyAudio()
        print("[Sistema]: Modelo carregado com sucesso!\n")

    def falar(self, texto):
        print(f"\n[Cedalión]: {texto}")
        self.engine.say(texto)
        self.engine.runAndWait()

    def ouvir(self):
        """Abre o microfone e escuta a frase offline"""
        stream = self.p.open(format=pyaudio.paInt16, channels=1, 
                             rate=16000, input=True, frames_per_buffer=8000)
        stream.start_stream()
        
        print("[Microfone aberto... Pode falar!]")
        
        texto_reconhecido = ""
        try:
            while True:
                data = stream.read(4000, exception_on_overflow=False)
                # Se o Vosk detectar que o usuário terminou a frase:
                if self.reconhecedor.AcceptWaveform(data):
                    resultado = json.loads(self.reconhecedor.Result())
                    texto_reconhecido = resultado.get("text", "")
                    
                    if texto_reconhecido: # Se realmente ouviu palavras e não só ruído
                        break
        except KeyboardInterrupt:
            pass
        finally:
            stream.stop_stream()
            stream.close()
            
        print(f"[Usuário]: {texto_reconhecido}")
        return texto_reconhecido.lower()

    
    def formatar_local(self, texto_falado):
        """Remove acentos e espaços. Ex: 'Laboratório' -> 'laboratório'"""
        texto_sem_acento = unicodedata.normalize('NFKD', texto_falado).encode('ASCII', 'ignore').decode('utf-8')
        return texto_sem_acento.replace(" ", "_")

    def extrair_local(self, texto_falado, mapa):
        """
        Limpa os acentos do que foi dito e procura se o nome de algum nó 
        do mapa está 'escondido' no meio da frase do usuário.
        """
        # 1. Limpa a frase que o usuário falou (Tira acentos e deixa minúsculo)
        texto_limpo = unicodedata.normalize('NFKD', texto_falado).encode('ASCII', 'ignore').decode('utf-8').lower()
        
        for local_mapa in mapa.grafo.nodes:
            # 2. Limpa o nome que está gravado no mapa também!
            nome_mapa_limpo = unicodedata.normalize('NFKD', local_mapa).encode('ASCII', 'ignore').decode('utf-8').lower()
            nome_mapa_com_espaco = nome_mapa_limpo.replace("_", " ")
            
            # 3. Compara os dois lados sem acentos
            if nome_mapa_com_espaco in texto_limpo or nome_mapa_limpo in texto_limpo:
                return local_mapa # Retorna o nome exato e oficial do mapa
                
        return None

    def obter_rota_do_usuario(self, mapa):
        origem = None
        destino = None

        self.falar("Olá, vou perguntar onde você está e depois onde você quer ir")

        # 1. ORIGEM
        while not origem:
            self.falar("Onde você está?")
            resposta = self.ouvir()
            
            if resposta:
                local_encontrado = self.extrair_local(resposta, mapa)
                if local_encontrado:
                    origem = local_encontrado
                    # Para a fala ficar natural, removemos o underline do nome
                    nome_bonito = origem.replace("_", " ")
                    self.falar(f"Entendido. Você está no local: {nome_bonito}.")
                else:
                    self.falar("Este local não existe no meu mapa.")

        # 2. DESTINO
        while not destino:
            self.falar("E para onde você quer ir?")
            resposta = self.ouvir()
            
            if resposta:
                local_encontrado = self.extrair_local(resposta, mapa)
                if local_encontrado:
                    if local_encontrado == origem:
                        self.falar("Você já está nesse local!")
                    else:
                        destino = local_encontrado
                        nome_bonito = destino.replace("_", " ")
                        self.falar(f"Perfeito. Vou te guiar para o local: {nome_bonito}.")
                else:
                    self.falar("Este destino não existe no meu mapa.")

        return origem, destino


if __name__ == "__main__":
    meu_mapa = MapaTopologico()
    assistente = InterfaceVoz()
    origem_escolhida, destino_escolhido = assistente.obter_rota_do_usuario(meu_mapa)
    rota, comandos = meu_mapa.gerar_plano_de_voo(origem_escolhida, destino_escolhido)
    print(f"Ações: {comandos}")