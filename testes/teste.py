import sys
import os

from kortex_api.autogen.messages import DeviceConfig_pb2, Session_pb2, Base_pb2

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from modulos.robo_kinova import KinovaRobot
from modulos.robo_kinova import vetorCartesiano

def main():
    kinova = KinovaRobot()
    kinova.connect()
    kinova.subscribe_to_notifications()

    kinova.executa_acao_existente("Home")
    kinova.moveTo(vetorCartesiano(0, 0, 0.3), vetorCartesiano(0, 0, 0), Base_pb2.CARTESIAN_REFERENCE_FRAME_TOOL)

    kinova.unsubscribe_from_notifications()
    kinova.disconnect()

if __name__ == "__main__":
    main()