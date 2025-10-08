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
    def __init__(self, x=0.0, y=0.0, z=0.0, theta_x=0.0, theta_y=0.0, theta_z=0.0):
        self.x = x
        self.y = y
        self.z = z
        self.theta_x = theta_x
        self.theta_y = theta_y
        self.theta_z = theta_z
    def soma(self, v):
        return vetorCartesiano(self.x + v.x, self.y + v.y, self.z + v.z, self.theta_x + v.theta_x, self.theta_y + v.theta_y, self.theta_z + v.theta_z)
    @property
    def norma(self):
        return (self.x**2 + self.y**2 + self.z**2 + self.theta_x**2 + self.theta_y**2 + self.theta_z**2)**0.5
    @property
    def versor(self):
        n = self.norma
        if n == 0:
            return vetorCartesiano(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        return vetorCartesiano(self.x/n, self.y/n, self.z/n, self.theta_x/n, self.theta_y/n, self.theta_z/n)
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
        return True
        
        self.is_connected = False
        return True
    
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

    def set_servoing_mode(self):

        if not self.is_connected:
            print("Não é possível definir o modo de controle: robô não conectado.")
            return False
    
        try:
            print("Definindo o modo de controle para SINGLE_LEVEL_SERVOING...")
            servoing_mode_info = Base_pb2.ServoingModeInformation()
            servoing_mode_info.servoing_mode = Base_pb2.SINGLE_LEVEL_SERVOING
            self.base.SetServoingMode(servoing_mode_info)
        
            # Os exemplos oficiais frequentemente adicionam um pequeno sleep após
            # mudanças de estado para garantir que o controlador do robô tenha tempo de processar.
            time.sleep(1.0)
        
            print("Modo de controle definido com sucesso.")
            return True
        except KException as ex:
            print(f"Falha ao definir o modo de controle. Erro: {ex}")
        return False

    
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
                    action_handle = action.handle  # Encontrou! Salva o handle.
                    break  # Otimização: pode parar de procurar assim que encontrar.

            if action_handle is None:
                print(f"Ação '{action_name}' não encontrada no robô.")
                return False
        
            print(f"Ação '{action_name}' encontrada. ")

            self.base.ExecuteActionFromReference(action_handle)
            time.sleep(0.5)  # Pequeno atraso para garantir que a ação comece.
            while self.is_busy:
                time.sleep(1)
        except KException as ex:
            error_print(ex)
            return False
        return True
    def moveTo(self, posicao: vetorCartesiano, orientacao: vetorCartesiano):
        if not self.is_connected or self.is_busy:
            return False
        if not self.set_servoing_mode(): 
            return False
        try:
            feedback = self.base_cyclic.RefreshFeedback()  
            
            cartesian_pose = self.action.reach_pose.target_pose
            
            cartesian_pose.x = feedback.base.tool_pose_x  +posicao.x        # (meters)
            cartesian_pose.y = feedback.base.tool_pose_y +posicao.y   # (meters)
            cartesian_pose.z = feedback.base.tool_pose_z +posicao.z    # (meters)
            cartesian_pose.theta_x = feedback.base.tool_pose_theta_x + orientacao.x # (degrees)
            cartesian_pose.theta_y = feedback.base.tool_pose_theta_y +orientacao.y # (degrees)
            cartesian_pose.theta_z = feedback.base.tool_pose_theta_z +orientacao.z # (degrees)

            print("Executando movimento cartesiano...")
            self.base.ExecuteAction(self.action)
            time.sleep(0.5)  # Pequeno atraso para garantir que a ação come
            while self.is_busy:
                time.sleep(1)
        except KException as ex:
            error_print(ex)
            return False
        return True




        
    