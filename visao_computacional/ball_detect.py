import cv2
import numpy as np


PARAM_WINDOW = "Controles Hough"


def _noop(_: int) -> None:
    """Callback vazio exigido pela API de trackbars."""
    pass


def _make_odd(value: int) -> int:
    """Garante que o kernel de blur seja ímpar (necessário para medianBlur)."""
    if value <= 1:
        return 1
    return value if value % 2 else value + 1


def _init_trackbars() -> None:
    cv2.namedWindow(PARAM_WINDOW)
    cv2.resizeWindow(PARAM_WINDOW, 360, 280)
    cv2.createTrackbar("param1", PARAM_WINDOW, 60, 400, _noop)
    cv2.createTrackbar("param2", PARAM_WINDOW, 60, 200, _noop)
    cv2.createTrackbar("minDist", PARAM_WINDOW, 50, 400, _noop)
    cv2.createTrackbar("minR", PARAM_WINDOW, 80, 400, _noop)
    cv2.createTrackbar("maxR", PARAM_WINDOW, 200, 500, _noop)
    cv2.createTrackbar("Blur", PARAM_WINDOW, 5, 25, _noop)


def _read_params() -> dict:
    param1 = max(cv2.getTrackbarPos("param1", PARAM_WINDOW), 1)
    param2 = max(cv2.getTrackbarPos("param2", PARAM_WINDOW), 1)
    min_dist = max(cv2.getTrackbarPos("minDist", PARAM_WINDOW), 1)
    min_radius = max(cv2.getTrackbarPos("minR", PARAM_WINDOW), 1)
    max_radius = max(cv2.getTrackbarPos("maxR", PARAM_WINDOW), min_radius + 1)
    blur = _make_odd(cv2.getTrackbarPos("Blur", PARAM_WINDOW))
    if max_radius <= min_radius:
        max_radius = min_radius + 1
    return {
        "param1": param1,
        "param2": param2,
        "minDist": min_dist,
        "minRadius": min_radius,
        "maxRadius": max_radius,
        "blur": blur,
    }


_init_trackbars()


color = cv2.VideoCapture("rtsp://192.168.1.10/color")
if not color.isOpened():
    print("Não conseguiu abrir a câmera")
    exit()
try:
    print("\nConexão bem-sucedida. Pressione 'q' na janela de vídeo para sair.")
    while True:
        # Captura frame a frame
        ret, frame = color.read()

        if not ret:
            print("Fim do stream ou erro de leitura do frame.")
            break

        params = _read_params()

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.medianBlur(gray, params["blur"])

        circles = cv2.HoughCircles(
            gray,
            cv2.HOUGH_GRADIENT,
            dp = 1.2,
            minDist= params["minDist"],
            param1 = params["param1"],
            param2 = params["param2"],
            minRadius= params["minRadius"],
            maxRadius = params["maxRadius"]
        )

        out = frame.copy()

        if circles is not None:
            circles = np.uint16(np.around(circles[0]))
        # --- opcional: eliminar círculos muito próximos (duplicados) ---
            filtered = []
            for c in circles:
                if all(np.hypot(c[0]-f[0], c[1]-f[1]) > 40 for f in filtered):
                    filtered.append(c)
            print(f"Detectados: {len(filtered)} círculos")

            for (x, y, r) in filtered:
                cv2.circle(out, (x, y), r, (0, 255, 0), 3)
                cv2.circle(out, (x, y), 3, (0, 0, 255), -1)
                cv2.putText(out, f"r={r}", (x-20, y-10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)
        else:
            print("Nenhum círculo detectado")

        cv2.imshow("Original", frame)
        cv2.imshow("Deteccao - HoughCircles", out)      


        # Para sair: Pressione 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
except KeyboardInterrupt:
    print("Interrompido pelo usuário.")
        
finally:
    # Libera o objeto de captura e fecha as janelas
    color.release()
    cv2.destroyAllWindows()
    print("Stream encerrado.")
