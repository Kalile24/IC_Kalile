import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from modulos.robo_kinova import KinovaRobot
from modulos.robo_kinova import vetorCartesiano

def main():
    kinova = KinovaRobot()
    kinova.connect()
    kinova.subscribe_to_notifications()

    kinova.executa_acao_existente("Home")
    kinova.moveFrom(vetorCartesiano(0, 0, 0.1), vetorCartesiano(0, 0, 0))

    kinova.unsubscribe_from_notifications()
    kinova.disconnect()

if __name__ == "__main__":
    main()