# save_initial_pose.py
import sys
import os

import json
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from modulos.robo_kinova import KinovaRobot, Base_pb2

POSE_FILE = "pose_inicial.json"

def main():
    bot = KinovaRobot()
    try:
        if not bot.connect():
            print("Falha na conexão.")
            return

        # Garantir modo servo ativo
        if not bot.set_servoing_mode():
            print("Não foi possível colocar em SINGLE_LEVEL_SERVOING.")
            return

        # Ler pose atual via BaseCyclic (pose absoluta da ferramenta)
        fb = bot.base_cyclic.RefreshFeedback()
        pose = {
            "x": fb.base.tool_pose_x,
            "y": fb.base.tool_pose_y,
            "z": fb.base.tool_pose_z,
            "theta_x": fb.base.tool_pose_theta_x,
            "theta_y": fb.base.tool_pose_theta_y,
            "theta_z": fb.base.tool_pose_theta_z,
        }

        with open(POSE_FILE, "w") as f:
            json.dump(pose, f, indent=2)
        print(f"Pose inicial salva em {POSE_FILE}: {pose}")

    finally:
        bot.disconnect()

if __name__ == "__main__":
    main()