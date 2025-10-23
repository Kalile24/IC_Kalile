import sys, os
import numpy as np
from kortex_api.autogen.messages import Base_pb2
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from modulos.robo_kinova import KinovaRobot, vetorCartesiano
import modulos.matriz_coordenadas as matriz_coordenadas 

def main():
    kinova = KinovaRobot()
    kinova.connect()
    kinova.subscribe_to_notifications()
    T_tool_target = np.identity(4)
    T_tool_target[0:3, 3] = [0,0,0.2] ##COORDENADA DO ALVO EM RELAÇÃO À FERRAMENTA DO ROBÔ
    T_tool_target[0:3, 0:3] = matriz_coordenadas.euler_xyz_deg_to_R(0,30,0) ##ROTAÇÃO DO ALVO EM RELAÇÃO À FERRAMENTA DO ROBÔ
    T_base_tool = matriz_coordenadas.T_BASE_INT_q(kinova)
    
    T_target_base = T_base_tool @ T_tool_target
    pos_target = T_target_base[0:3, 3]
    rot_target = matriz_coordenadas.R_to_euler_xyz_deg(T_target_base[0:3, 0:3])
    kinova.moveTo(vetorCartesiano(pos_target[0], pos_target[1], pos_target[2]),
                    vetorCartesiano(rot_target[0], rot_target[1], rot_target[2]),
                                  Base_pb2.CARTESIAN_REFERENCE_FRAME_BASE)
    kinova.unsubscribe_from_notifications()
    kinova.disconnect()

if __name__ == "__main__":
    exit(main())