import sys, os
import numpy as np
from kortex_api.autogen.messages import Base_pb2
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from modulos.robo_kinova import KinovaRobot, vetorCartesiano
import matriz_coordenadas  # seu FK base->tool (INT)

# --- rotação básica (convenção: R = Rz * Ry * Rx) ---
def rot_x(a): c,s=np.cos(a),np.sin(a); return np.array([[1,0,0],[0,c,-s],[0,s,c]])
def rot_y(a): c,s=np.cos(a),np.sin(a); return np.array([[c,0,s],[0,1,0],[-s,0,c]])
def rot_z(a): c,s=np.cos(a),np.sin(a); return np.array([[c,-s,0],[s,c,0],[0,0,1]])

def euler_xyz_deg_to_R(tx,ty,tz):
    ax,ay,az = np.deg2rad([tx,ty,tz])
    return rot_z(az) @ rot_y(ay) @ rot_x(ax)

def R_to_euler_xyz_deg(R):
    # assume R = Rz * Ry * Rx (intrínseca XYZ); troque se sua API usar outra ordem
    sy = -R[2,0]
    ay = np.arcsin(np.clip(sy, -1.0, 1.0))
    cy = np.cos(ay)
    if abs(cy) > 1e-6:
        ax = np.arctan2(R[2,1]/cy, R[2,2]/cy)
        az = np.arctan2(R[1,0]/cy, R[0,0]/cy)
    else:  # gimbal lock
        az = 0.0
        ax = np.arctan2(-R[0,1], R[1,1])
    return np.rad2deg([ax, ay, az])

def main():
    kinova = KinovaRobot()
    kinova.connect()
    kinova.subscribe_to_notifications()

    # T é a pose base->tool (INT) calculada do seu modelo (FK)
    T = matriz_coordenadas.T_BASE_INT_q(kinova)   # 4x4

    # queremos deslocar 30 cm ao longo do eixo Z do tool (sem girar no tool)
    T_delta = np.eye(4)
    T_delta[:3,3] = [0.0, 0.0, 0.20]       # deslocamento NO FRAME DO TOOL
    # se quisesse girar no tool, ligue esta linha:
    # T_delta[:3,:3] = euler_xyz_deg_to_R(dtx, dty, dtz)

    T_target = T @ T_delta

    # posição alvo em BASE:
    x,y,z = T_target[:3,3]
    # orientação alvo em BASE (a mesma de T se T_delta não girar):
    R_target = T_target[:3,:3]
    tx,ty,tz = R_to_euler_xyz_deg(R_target)   # -> graus

    print("pos base:", x,y,z, "ang base (deg):", tx,ty,tz)

    kinova.executa_acao_existente("Home")  # se quiser “Home” antes
    kinova.moveTo(
        vetorCartesiano(x, y, z),
        vetorCartesiano(tx, ty, tz),
        Base_pb2.CARTESIAN_REFERENCE_FRAME_BASE
    )

    kinova.unsubscribe_from_notifications()
    kinova.disconnect()

if __name__ == "__main__":
    main()
