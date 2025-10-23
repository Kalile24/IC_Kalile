
import cv2
import sys

# --- CONFIGURAÇÃO ---
# O endereço IP padrão do robô Kinova Gen3 é frequentemente 192.168.1.10
# A URL RTSP exata pode variar. Consulte a documentação do seu robô ou a interface web.
# Exemplo de URL genérica:
# RTSP_URL = "rtsp://<USUARIO>:<SENHA>@<IP_DO_ROBÔ>/<CAMINHO_DO_STREAM>"
# Se o stream for aberto e não exigir autenticação, pode ser mais simples.

# **SUBSTITUA ESTA LINHA PELA URL RTSP REAL DO SEU ROBÔ**
RTSP_URL = "rtsp://192.168.1.10/color" 
# --------------------

def view_rtsp_stream(rtsp_url):
    """
    Tenta abrir e exibir o stream de vídeo RTSP usando o OpenCV.
    """
    print(f"Tentando conectar ao stream RTSP: {rtsp_url}")
    
    # Cria o objeto VideoCapture
    # cv2.CAP_FFMPEG é usado para garantir que o backend FFmpeg seja usado para RTSP
    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)

    if not cap.isOpened():
        print("\nERRO: Não foi possível abrir o stream RTSP.")
        print("Verifique:")
        print("1. Se o endereço IP e a URL RTSP estão corretos.")
        print("2. Se o robô está ligado e o serviço de streaming está ativo.")
        print("3. Se o OpenCV foi compilado com suporte a FFmpeg/RTSP (Geralmente é o caso em instalações padrão).")
        return

    try:
        print("\nConexão bem-sucedida. Pressione 'q' na janela de vídeo para sair.")
        while True:
            # Captura frame a frame
            ret, frame = cap.read()

            if not ret:
                print("Fim do stream ou erro de leitura do frame.")
                break

            # --- Processamento (Opcional: Adicionar texto para teste) ---
            # Esta é a seção onde você integrará sua lógica de detecção de objetos
            cv2.putText(frame, "Stream Kinova via RTSP (OpenCV)", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
            # Exibe o frame resultante
            cv2.imshow('Kinova Gen3 RTSP Stream', frame)

            # Para sair: Pressione 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    except KeyboardInterrupt:
        print("Interrompido pelo usuário.")
        
    finally:
        # Libera o objeto de captura e fecha as janelas
        cap.release()
        cv2.destroyAllWindows()
        print("Stream encerrado.")

if __name__ == "__main__":
    view_rtsp_stream(RTSP_URL)
