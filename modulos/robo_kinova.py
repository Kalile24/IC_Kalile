import sys
import os
import time
import threading

from kortex_api.TCPTransport import TCPTransport
from kortex_api.RouterClient import RouterClient
from kortex_api.SessionManager import SessionManager

from kortex_api.autogen.client_stubs.ControlConfigClientRpc import ControlConfigClient
from kortex_api.autogen.client_stubs.DeviceConfigClientRpc import DeviceConfigClient
from kortex_api.autogen.client_stubs.BaseClientRpc import BaseClient
from kortex_api.autogen.client_stubs.BaseCyclicClientRpc import BaseCyclicClient

from kortex_api.autogen.messages import DeviceConfig_pb2, Session_pb2, Base_pb2
from kortex_api.Exceptions.KException import KException
from google.protobuf import json_format

def error_print(ex):
    error_code = ex.get_error_code()
    sub_error_code = ex.get_error_sub_code()
    print("Error_code:{0} , Sub_error_code:{1} ".format(error_code, sub_error_code))
    print("Caught expected error: {0}".format(ex))

def notification_callback(data):
    print("****************************")
    print("* Callback function called *")
    print(json_format.MessageToJson(data))
    print("****************************")

class vetorCartesiano:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x
        self.y = y
        self.z = z
    def soma(self, v):
        return vetorCartesiano(self.x + v.x, self.y + v.y, self.z + v.z)
    @property
    def norma(self):
        return (self.x**2 + self.y**2 + self.z**2)**0.5
    @property
    def versor(self):
        n = self.norma
        if n == 0:
            return vetorCartesiano(0.0, 0.0, 0.0)
        return vetorCartesiano(self.x/n, self.y/n, self.z/n)

class KinovaRobot:
    IP = '192.168.1.10'
    PORT = 10000
    user = 'admin'
    password = 'admin'

    def __init__(self, ip_address=IP, port=PORT, user=user, password=password):
        self.ip_address = ip_address
        self.port = port
        self.user = user
        self.password = password


        self.transport = None
        self.router = None
        self.session_manager = None
        self.device_config = None
        self.base = None
        self.base_cyclic = None
        self.notification_handles = []
        self.control_config_client = None
        self.action = Base_pb2.Action()

        self.is_connected = False
        self.is_busy = False

        self.number_of_joints = 0


    def connect(self):
        self.transport = TCPTransport()
        self.router = RouterClient(self.transport, RouterClient.basicErrorCallback)
        self.base = BaseClient(self.router)
        self.device = DeviceConfigClient(self.router)
        self.control_config_client = ControlConfigClient(self.router)   


        try:
            self.transport.connect(self.ip_address, self.port)

            session_info = Session_pb2.CreateSessionInfo()
            session_info.username = self.user
            session_info.password = self.password
            session_info.session_inactivity_timeout = 60000
            session_info.connection_inactivity_timeout = 2000

            self.session_manager = SessionManager(self.router)
            print(f"Fazendo login como {self.user} e no IP {self.ip_address}...")
            self.session_manager.CreateSession(session_info)
            print("Login bem sucedido.")
            
            self.is_connected = True

            self.device_config = DeviceConfigClient(self.router)
            self.base = BaseClient(self.router)
            self.base_cyclic = BaseCyclicClient(self.router)
        except KException as ex:
            print("Login falhou.")
            error_print(ex)
            return False
        
        self.number_of_joints = self.base.GetActuatorCount().count
        
        return True
    
    def disconnect(self):
        if not self.is_connected:
            return True
        if self.session_manager:
            self.session_manager.CloseSession()
            print("Sessão fechada.")
        
        self.transport.disconnect()
        print("Desconectado do robô.")
        self.is_connected = False
        return True
        

    ###CALLBACK UTILIZADO PARA INSCRIÇÃO NAS NOTIFICAÇÕES
    ###ALTERA O is_busy PARA COMUNICAR SE O ROBÔ ESTÁ SENDO UTILIZADO
    
    def action_notification_callback(self, data):
        if data.action_event == Base_pb2.ActionEvent.ACTION_START:
            print("Ação iniciada.")
            self.is_busy = True
        elif data.action_event == Base_pb2.ActionEvent.ACTION_END:
            print("Ação finalizada.")
            self.is_busy = False
        elif data.action_event == Base_pb2.ActionEvent.ACTION_ABORT:
            print("Ação abortada.")
            self.is_busy = False
        elif data.action_event == Base_pb2.ActionEvent.ACTION_PAUSE:
            print("Ação pausada")
            self.is_busy = False 
    
    ###INSCRIÇÃO NAS NOTIFICACOES DE ACAO E MUDANCAS DE CONFIGURACAO
    def subscribe_to_notifications(self):
        if not self.is_connected:
            print("Não conectado ao robô.")
            return None
        try:
            notification_options = Base_pb2.NotificationOptions()
            notif_handle1 = self.base.OnNotificationActionTopic(self.action_notification_callback, notification_options)
            notif_handle2 = self.base.OnNotificationConfigurationChangeTopic(notification_callback, notification_options)
            self.notification_handles.append(notif_handle1)
            self.notification_handles.append(notif_handle2)
        except KException as k_ex:
            print("Error occured: {}".format(k_ex))
        except Exception:
            print("Error occured")

    ###DESINSCRIAÇÃO DAS NOTIFICACOES 
    def unsubscribe_from_notifications(self):
        if not self.is_connected:
            print("Não há inscrição ativa para cancelar.")
            return
        try:
            for notif_handle in list(self.notification_handles):
                self.base.Unsubscribe(notif_handle)
                self.notification_handles.remove(notif_handle)
            print("Inscrições canceladas.")
        except KException as k_ex:
            print(f"Ocorreu um erro KException ao cancelar a inscrição: {k_ex}")
        except Exception as ex:
            print(f"Ocorreu um erro inesperado ao cancelar a inscrição: {ex}")

    ###DEFINE O MODO DE FUNCIONAMENTO DO ROBO PARA SINGLE_LEVEL_SERVOING
    def set_servoing_mode(self):

        if not self.is_connected:
            print("Não é possível definir o modo de controle: robô não conectado.")
            return False
    
        try:
            servoing_mode_info = Base_pb2.ServoingModeInformation()
            servoing_mode_info.servoing_mode = Base_pb2.SINGLE_LEVEL_SERVOING
            self.base.SetServoingMode(servoing_mode_info)
        
            time.sleep(1.0)
            return True
        except KException as ex:
            print(f"Falha ao definir o modo de controle. Erro: {ex}")
        return False

    ###EXECUTA UMA AÇÃO JÁ PREDEFINIDA SALVA NO ROBO A PATIR DO NOME DA AÇÃO E SEU TIPO

    def executa_acao_existente(self, action_name: str, action_type = Base_pb2.REACH_JOINT_ANGLES):
        if not self.is_connected or self.is_busy:
            return False
        if not self.set_servoing_mode(): 
            return False
        try:
            req_action_type = Base_pb2.RequestedActionType()
            req_action_type.action_type = action_type
            
            action_handle = None

            action_list = self.base.ReadAllActions(req_action_type)
            for action in action_list.action_list:
                if action.name == action_name:
                    action_handle = action.handle 
                    break  

            if action_handle is None:
                print(f"Ação '{action_name}' não encontrada no robô.")
                return False
        
            print(f"Ação '{action_name}' encontrada. ")

            self.base.ExecuteActionFromReference(action_handle)
            time.sleep(0.5)  
            while self.is_busy:
                time.sleep(1)
        except KException as ex:
            error_print(ex)
            return False
        return True

     ###EXECUTA UM MOVIMENTO PARA AS COORDENADAS PASSADAS

    def moveTo(self, posicao: vetorCartesiano, orientacao: vetorCartesiano, reference_frame = Base_pb2.CARTESIAN_REFERENCE_FRAME_BASE):
        if not self.is_connected or self.is_busy:
            return False
        if not self.set_servoing_mode(): 
            return False
        try: 
            waypoint = Base_pb2.CartesianWaypoint()
            waypoint.reference_frame = reference_frame
            waypoint.pose.x = posicao.x        # (meters)
            waypoint.pose.y = posicao.y   # (meters)
            waypoint.pose.z = posicao.z    # (meters)
            waypoint.pose.theta_x = orientacao.x # (degrees)
            waypoint.pose.theta_y = orientacao.y # (degrees)
            waypoint.pose.theta_z = orientacao.z # (degrees)

            waypoint_list = Base_pb2.WaypointList()
            waypoint_list.duration = 0.0
            waypoint_list.use_optimal_blending = False
            
            w = waypoint_list.waypoints.add()
            w.name = "MoveTo"
            w.cartesian_waypoint.CopyFrom(waypoint)

            report = self.base.ValidateWaypointList(waypoint_list)
            print("Validation report:", report)
            print("Executando movimento cartesiano...")
            self.base.ExecuteWaypointTrajectory(waypoint_list)
            time.sleep(0.5)
            while self.is_busy:
                time.sleep(0.5)
            err = self.base.GetTrajectoryErrorReport()
            print("Trajectory error report:", err)
        except KException as ex:
            error_print(ex)
            return False
        return True
     ###EXECUTA UM MOVIMENTO PARA ASSUMIR ANGULOS DE JUNTAS PREDEFINIDOS
    def moveTo_joint_angles(self,angulos: list[float]):
        if not self.is_connected or self.is_busy:
            return False
        if not self.set_servoing_mode(): 
            return False
        if len(angulos) != self.number_of_joints:
            print("Quantidade errada de angulos passados")
            return False
        try: 
           self.action.Clear()
           acao_angulos = self.action.reach_joint_angles 
           for i in range(self.number_of_joints):
               j = acao_angulos.joint_angles.joint_angles.add()
               j.joint_identifier = i 
               j.value = angulos[i]

               self.base.ExecuteAction(self.action)  
               time.sleep(0.5)
               while self.is_busy:
                   time.sleep(0.5)          
        except KException as ex: 
            error_print(ex)
            return False
        return True
    
    ###EXECUTA MOVIMENTO DE VELOCIDADE DAS JUNTAS
    def send_joint_speeds(self, velocidades: list[float], tempo: float):
        if not self.is_connected or self.is_busy:
            return False
        if not self.set_servoing_mode(): 
            return False
        if len(velocidades) != self.number_of_joints:
            print("Quantidade errada de angulos passados")
            return False
        try:
            
            joint_speeds = Base_pb2.JointSpeeds()
    
            for i in range(self.number_of_joints):
               j = joint_speeds.joint_speeds.add()
               j.joint_identifier = i 
               j.value = velocidades[i]
            
            self.base.SendJointSpeedsCommand(joint_speeds)
            time.sleep(tempo) 
            self.base.Stop()       
        except KException as ex: 
            error_print(ex)
            return False
        return True
    
    ###FUNCAO DE TWIST COMMAND (VELOCIDADE CARTESIANA)
    def send_twist_command(self, v1: vetorCartesiano, v2: vetorCartesiano, tempo: float, reference_frame = Base_pb2.CARTESIAN_REFERENCE_FRAME_TOOL ):
        if not self.is_connected or self.is_busy:
            return False
        if not self.set_servoing_mode(): 
            return False
        try: 
            twist = Base_pb2.TwistCommand()
            twist.reference_frame = reference_frame
            twist.twist.linear_x = v1.x
            twist.twist.linear_y = v1.y
            twist.twist.linear_z = v1.z

            twist.twist.angular_x = v2.x
            twist.twist.angular_y = v2.y
            twist.twist.angular_z = v2.z

            self.base.SendTwistCommand(twist)
            time.sleep(tempo)
            self.base.Stop()

        except KException as ex:
            error_print()
            return False
    
    ###FUNCOES DE FECHAMENTO E ABERTURA DA GARRA

    def _send_gripper_position(self, value: float = 1.0, finger_ids=(1,), hold_time: float = 0.8) -> bool:
        """
        Envia um comando de posição para a garra.
        value: 0.0 (aberta) ... 1.0 (fechada)
        finger_ids: tupla/lista com os IDs dos dedos existentes (1,2,3...) - ajuste se sua garra tiver + de 1 dedo
        hold_time: pequeno tempo para permitir o movimento mecânico (segundos)
        """
        if not self.is_connected:
            print("Não conectado ao robô.")
            return False

        # Sanitiza faixa [0,1]
        v = max(0.0, min(1.0, float(value)))

        try:
            cmd = Base_pb2.GripperCommand()
            cmd.mode = Base_pb2.GRIPPER_POSITION
            for fid in finger_ids:
                f = cmd.gripper.finger.add()
                f.finger_identifier = int(fid)
                f.value = v  # 0.0 aberto, 1.0 fechado

            self.base.SendGripperCommand(cmd)

            # Pequena espera para o atuador completar o movimento (não há callback de ação para garra)
            time.sleep(max(0.0, float(hold_time)))
            return True
        except KException as ex:
            error_print(ex)
            return False
        except Exception as ex:
            print(f"Erro inesperado ao mover a garra: {ex}")
            return False

    def open_gripper(self, value: float = 0.0, hold_time: float = 0.7, finger_ids=(1,)) -> bool:
        """
        Abre a garra. Por padrão abre totalmente (value=0.0).
        Ajuste 'value' se quiser abertura parcial, e 'finger_ids' se houver múltiplos dedos.
        """
        return self._send_gripper_position(value=value, finger_ids=finger_ids, hold_time=hold_time)

    def close_gripper(self, value: float = 0.8, hold_time: float = 1.0, finger_ids=(1,)) -> bool:
        """
        Fecha a garra. Por padrão fecha totalmente (value=1.0).
        Ajuste 'value' se quiser fechamento parcial, e 'finger_ids' se houver múltiplos dedos.
        """
        return self._send_gripper_position(value=value, finger_ids=finger_ids, hold_time=hold_time)




        
    