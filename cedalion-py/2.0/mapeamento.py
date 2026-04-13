import networkx as nx

class MapaTopologico:
    def __init__(self):
        # Usamos DiGraph (Grafo Direcionado) porque ir de A para B 
        # pode exigir comandos diferentes de ir de B para A no futuro.
        self.grafo = nx.DiGraph()
        self._construir_mapa()

    def _construir_mapa(self):
        """
        Constrói o mapa do ambiente.
        Os NÓS (nodes) são os Pisos de Alerta (Checkpoints).
        As ARESTAS (edges) são os Pisos Direcionais (Linhas).
        """
        # Adicionando os locais (nós)
        self.grafo.add_node("laboratório")
        self.grafo.add_node("sala_de_aula")

        # Conectando os locais (arestas)
        # O atributo 'acao' diz ao drone o que ele deve fazer sobre a linha para chegar no destino
        self.grafo.add_edge("laboratório", "sala_de_aula", acao="SEGUIR_FRENTE")
        self.grafo.add_edge("sala_de_aula", "laboratório", acao="GIRAR_180_E_SEGUIR_FRENTE")

    def validar_local(self, local):
        """Verifica se o local dito pelo usuário existe no mapa"""
        return local.lower() in self.grafo.nodes

    def gerar_plano_de_voo(self, origem, destino):
        """
        Recebe a origem e destino, calcula a rota e traduz em comandos para a Máquina de Estados.
        """
        origem = origem.lower()
        destino = destino.lower()

        if not self.validar_local(origem) or not self.validar_local(destino):
            return None, "Erro: Origem ou destino não existem no mapa."

        if origem == destino:
            return None, "Erro: O drone já está no destino."

        try:
            # Calcula a rota mais curta passando pelos nós
            rota_nos = nx.shortest_path(self.grafo, source=origem, target=destino)
            
            # Monta a lista de ações que o Drone vai executar
            plano_acoes = ["DECOLAR"]
            
            for i in range(len(rota_nos) - 1):
                nodo_atual = rota_nos[i]
                proximo_nodo = rota_nos[i+1]
                
                # Pega a ação necessária para navegar nesta aresta
                acao = self.grafo[nodo_atual][proximo_nodo]['acao']
                
                plano_acoes.append(acao)
                plano_acoes.append(f"CHECKPOINT_ALERTA_{proximo_nodo.upper()}")
                
            plano_acoes.append("POUSAR")
            
            return rota_nos, plano_acoes

        except nx.NetworkXNoPath:
            return None, "Erro: Caminho bloqueado ou inexistente."

# ==========================================
# TESTE DO MÓDULO (Só roda se executar este arquivo diretamente)
# ==========================================
if __name__ == "__main__":
    mapa = MapaTopologico()
    
    print("--- Teste do Sistema de Mapeamento ---")
    origem = "laboratório"
    destino = "sala_de_aula"
    
    rota, plano = mapa.gerar_plano_de_voo(origem, destino)
    
    print(f"Trajeto: {origem} -> {destino}")
    print(f"Nós percorridos: {rota}")
    print(f"Comandos para a Máquina de Estados: {plano}")