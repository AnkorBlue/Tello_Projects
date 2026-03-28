#  SpectraLine

Este projeto utiliza o drone DJI Tello e a biblioteca OpenCV para realizar o seguimento de linha (path following) de forma autônoma. O sistema utiliza controle PID para suavizar os movimentos de correção e uma interface de calibração HSV em tempo real para se adaptar a diferentes cores de pista (fita preta ou folhas brancas).

---

##  Requisitos

Para rodar este sistema, você precisará instalar as seguintes bibliotecas Python:

```bash
pip install opencv-python
pip install numpy
pip install djitellopy
```
---

## Como Usar

Preparação Física Imprima em 3D o suporte para o clipe de espelho (mirror clip). Cole um pequeno espelho no clipe e encaixe-o na câmera frontal do Tello, apontando para baixo. Monte o percurso no chão: fita isolante preta sobre um fundo claro ou caminho com folhas de papel A4 brancas. Conexão: Ligue o drone Tello e conecte o seu computador à rede Wi-Fi emitida pelo drone. Calibração HSV: Execute o script main.py. Uma janela chamada HSV aparecerá com barras de ajuste (trackbars). Ajuste os valores de H, S e V até que a linha (pista) apareça totalmente branca e o restante do chão apareça preto. Decolagem e Execução: Com a calibração pronta, pressione a tecla s no teclado. O sistema irá salvar as configurações em hsv.json, decolar automaticamente, ajustar a altitude de cruzeiro e iniciar o seguimento da linha. Emergência: Pressione a tecla ESC a qualquer momento para forçar o pouso imediato e interromper o script.

# Test_Tello

Esta pasta contém scripts essenciais para validar o hardware e a conectividade do drone DJI Tello antes de realizar missões autônomas.

Ela funciona como uma **suíte de diagnóstico**, garantindo que:

- Motores estejam funcionando corretamente  
- Bateria esteja em bom estado  
- Streaming de vídeo esteja ativo  

Antes de executar missões autônomas.
