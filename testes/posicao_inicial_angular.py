import sys
import os
import threading
import time


sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from kortex_api.TCPTransport import TCPTransport
from kortex_api.RouterClient import RouterClient
from kortex_api.SessionManager import SessionManager

from kortex_api.autogen.client_stubs.DeviceConfigClientRpc import DeviceConfigClient
from kortex_api.autogen.client_stubs.BaseClientRpc import BaseClient

from kortex_api.autogen.messages import DeviceConfig_pb2, Session_pb2, Base_pb2

TIMEOUT_DURATION = 20

##Criacao de evento após END ou ABORT
def check_for_end_or_abort(e):
    """Return a closure checking for END or ABORT notifications

    Arguments:
    e -- event to signal when the action is completed
        (will be set when an END or ABORT occurs)
    """
    def check(notification, event = e):
        print("EVENT : " + \
              Base_pb2.ActionEvent.Name(notification.action_event))
        if notification.action_event == Base_pb2.ACTION_END \
        or notification.action_event == Base_pb2.ACTION_ABORT:
            event.set()
    return check

def movimentacao_posicao_inicial(base):
    ##Usando angulos das juntas
    
    #Garante modo de funcionamento correto
    base_servo_mode = Base_pb2.ServoingModeInformation()
    base_servo_mode.servoing_mode = Base_pb2.SINGLE_LEVEL_SERVOING
    base.SetServoingMode(base_servo_mode)
    
    #Gera objeto que define angulos desejados
    constrained_joint_angles = Base_pb2.ConstrainedJointAngles()

    #Contagem juntas
    actuator_count = base.GetActuatorCount().count
    angles = [0.0] * actuator_count


    #Passagem angulos juntas
    for joint_id in range(len(angles)):
        joint_angle = constrained_joint_angles.joint_angles.joint_angles.add()
        joint_angle.joint_identifier = joint_id
        joint_angle.value = angles[joint_id]
    
    ##Criacao evento
    e = threading.Event()

    ##Inscrição na notificacao
    notification_handle = base.OnNotificationActionTopic(
        check_for_end_or_abort(e),
        Base_pb2.NotificationOptions()
    )

    print("Reaching joint angles...")
    base.PlayJointTrajectory(constrained_joint_angles)

    print("Waiting for movement to finish ...")
    finished = e.wait(TIMEOUT_DURATION)
    base.Unsubscribe(notification_handle)

    if finished:
        print("Joint angles reached")
    else:
        print("Timeout on action notification wait")
    return finished
def main():
    import modulos.modulo_conexao
        
    with modulos.modulo_conexao.Conexao.create_tcp_connection() as router:
        
        device_config = DeviceConfigClient(router)
        base = BaseClient(router)
        movimentacao_posicao_inicial(base)

if __name__ == "__main__":
    exit(main())
