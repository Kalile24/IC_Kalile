import sys
import os

import numpy as np

from kortex_api.autogen.messages import DeviceConfig_pb2, Session_pb2, Base_pb2

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from modulos.robo_kinova import KinovaRobot
from modulos.robo_kinova import vetorCartesiano


##MATRIZES HOMOGÊNEAS PARA CADA FRAME##

#T_I_K -> TRANSFORMACAO DE K PARA I
T_BASE_1 = np.array([
    [1,0,0,0],
    [0,-1,0,0],
    [0,0,-1,0.15643],
    [0,0,0,1]
])

T_1_2 = np.array([
    [1,0,0,0],
    [0,0,-1,0.00538],
    [0,1,0,-0.12838],
    [0,0,0,1]
])

T_2_3 = np.array([
    [1,0,0,0],
    [0,0,1,-0.21038],
    [0,-1,0,-0.00638],
    [0,0,0,1]
])

T_3_4 = np.array([
    [1,0,0,0],
    [0,0,-1,0.00638],
    [0,1,0, -0.21038],
    [0,0,0,1]
])

T_4_5 = np.array([
    [1,0,0,0],
    [0,0,1, -0.20843],
    [0,-1,0,-0.00638],
    [0,0,0,1]
])

T_5_6 = np.array([
    [1,0,0,0],
    [0,0,-1,0],
    [0,1,0,-0.10593],
    [0,0,0,1]
])

T_6_7 = np.array([
    [1,0,0,0],
    [0,0,1,-0.10593],
    [0,-1,0,0],
    [0,0,0,1]
])

T_7_INT = np.array([
    [1,0,0,0],
    [0,-1,0,0],
    [0,0,-1,-0.06153],
    [0,0,0,1]
])

T_INT_COLOR = np.array([
    [1,0,0,0],
    [0,1,0,0.05639],
    [0,0,1,-0.00305],
    [0,0,0,1]
])

T_INT_DEPTH = np.array([
    [1,0,0,0.02750],
    [0,1,0,0.06600],
    [0,0,1,-0.00305],
    [0,0,0,1]
])

TRANSFORMATIONS = [T_BASE_1, T_1_2, T_2_3, T_3_4, T_4_5, T_5_6, T_6_7, T_7_INT]

def T_i_q(T_i: np.array, kinova: KinovaRobot, i: int):
    
    feedback = kinova.base_cyclic.RefreshFeedback()
    
    q_i_degrees = feedback.actuators[i-1].position
    q_i_rad = np.deg2rad(q_i_degrees)

    R_q = np.array([
        [np.cos(q_i_rad), -np.sin(q_i_rad),0,0],
        [np.sin(q_i_rad), np.cos(q_i_rad), 0, 0],
        [0,0,1,0],
        [0,0,0,1]
    ])

    return T_i @ R_q

def T_BASE_INT_q(kinova: KinovaRobot):
    i = 1
    t_base_int_q = np.identity(4)
    while i < 8:
        t_i = T_i_q(TRANSFORMATIONS[i-1],kinova,i)
        t_base_int_q = t_base_int_q @ t_i
        i = i + 1
    t_base_int_q =  t_base_int_q @ TRANSFORMATIONS[i-1]
    return t_base_int_q
