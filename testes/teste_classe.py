import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from modulos.robo_kinova import KinovaRobot

from modulos.robo_kinova import KinovaRobot
from modulos.robo_kinova import vetorCartesiano
def main():
    kinova = KinovaRobot()

    kinova.connect()
    
    print(kinova.device.GetDeviceType())
    print(kinova.base.GetArmState())  

    kinova.subscribe_to_notifications()
    d1 =vetorCartesiano(0, 0, -0.98)
    o1 = vetorCartesiano(0, 0, 0)
    deslocamento = vetorCartesiano(0.43621766567230225,-0.38904669880867004, 0.094813691675663)
    orientacao = vetorCartesiano(176.3494110107422,0.2221204936504364,90.15164184570312)
    kinova.moveTo(deslocamento, orientacao)
    kinova.moveFrom(d1, o1)
    kinova.close_gripper(value=0.8, hold_time=1.0, finger_ids=(1,))
    
    d2 =vetorCartesiano(0, 0, 0.98)
    o2 = vetorCartesiano(0, 0, 0)
    kinova.moveFrom(d2, o2)
    
    kinova.executa_acao_existente("Retract")
    kinova.moveTo(deslocamento, orientacao)
    kinova.moveFrom(d1, o1)
    kinova.open_gripper(value=0.0, hold_time=1.0, finger_ids=(1,))
    kinova.moveFrom(d2, o2)
    kinova.executa_acao_existente("Retract")

    kinova.unsubscribe_from_notifications()
    kinova.disconnect()

if __name__ == "__main__":
    main()