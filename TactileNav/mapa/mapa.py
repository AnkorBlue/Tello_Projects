import networkx as nx

# Grafo representando o mapa tátil: locais de interesse, pisos de alerta e cruzamentos
mapa_ifs = nx.Graph()
mapa_ifs.add_edge("Laboratório", "Alerta_Lab", weight=1)
mapa_ifs.add_edge("Alerta_Lab", "Cruzamento", weight=10)
mapa_ifs.add_edge("Cruzamento", "Alerta_Aud", weight=10)
mapa_ifs.add_edge("Alerta_Aud", "Auditório", weight=1)

def iniciar_guia(origem, destino):
    # Validação inicial dos nós de origem e destino
    if origem not in mapa_ifs.nodes or destino not in mapa_ifs.nodes:
        print("\n[ERRO] Local não reconhecido. Certifique-se de digitar 'Laboratório' ou 'Auditório'.")
        return

    if origem == destino:
        print(f"\n>> Você já está no {destino}.")
        return

    # Calcula a menor rota considerando a distância (peso) entre os pontos
    rota = nx.shortest_path(mapa_ifs, source=origem, target=destino, weight='weight')
    
    print("\n" + "="*60)
    print(">> Drone iniciando voo...")
    print(f">> Saia do {origem}.")
    
    # Gera as instruções de navegação iterando apenas pelos pontos intermediários da rota
    for i in range(1, len(rota) - 1):
        passo = rota[i]
        
        # Ponto de alerta de SAÍDA (primeiro passo após a origem)
        if i == 1:
            print(f">> Siga o piso de alerta do {origem}.")
            
        # Ponto estrutural fixo no meio do trajeto
        elif passo == "Cruzamento":
            print(">> Siga em frente pelo piso direcional.")
            print(">> Piso de alerta: cruzamento do corredor do Laboratório e Auditório.")
            
        # Ponto de alerta de CHEGADA (último passo antes do destino)
        elif i == len(rota) - 2:
            print(">> Siga em frente pelo piso direcional.")
            print(f">> Piso de alerta do {destino}.")

    print(f">> Chegou ao seu destino: {destino}.")
    print("="*60 + "\n")

# Interface do terminal
print("=== SISTEMA DE NAVEGAÇÃO DO DRONE GUIA ===")
print("Locais disponíveis no mapa: Laboratório, Auditório")
print("------------------------------------------")

while True:
    local_atual = input("Onde você está? (ou digite 'sair' para encerrar): ").strip()
    
    if local_atual.lower() == 'sair':
        print("Encerrando o sistema...")
        break
        
    local_destino = input("Para onde você quer ir?: ").strip()
    
    # Normalização básica de texto para mitigar erros comuns de digitação de acentos
    local_atual = local_atual.capitalize().replace("torio", "tório").replace("toria", "tória")
    local_destino = local_destino.capitalize().replace("torio", "tório").replace("toria", "tória")

    iniciar_guia(local_atual, local_destino)