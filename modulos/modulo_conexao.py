import argparse

##Módulos de conexão da API Kortex
from kortex_api.TCPTransport import TCPTransport
from kortex_api.RouterClient import RouterClient   
from kortex_api.SessionManager import SessionManager
from kortex_api.autogen.messages import Session_pb2

#Função para ler os argumentos de conexão do terminal
#def parse_arguments_conexao(parser=argparse.ArgumentParser()):
#    parser.add_argument("--ip",type = str, default='192.168.1.10', help="Endereço IP do braço robótico")
#    parser.add_argument('-u',"--username", type = str, default='admin', help="Usuário de login do braço robótico")
#    parser.add_argument('-p', "--password",type = str, default='admin', help="Senha de login do braço robótico")
#    return parser.parse_args

#Classe de conexão com o braço robótico
class Conexao:
    IP = '192.168.1.10'
    TCP_PORT = 10000
    UDP_PORT = 10001
    username = 'admin'
    password = 'admin'

    def __init__(self, ip, port, credenciais):
        self.ip = ip
        self.port = port
        self.credenciais = credenciais

        self.transport = TCPTransport()
        self.router = RouterClient(self.transport, RouterClient.basicErrorCallback)
    
    def __enter__(self):

        #Conecta o transporte TCP
        self.transport.connect(self.ip, self.port)

        #Cria sessão de login 
        session_info = Session_pb2.CreateSessionInfo()
        session_info.username = self.credenciais[0]
        session_info.password = self.credenciais[1]
        session_info.session_inactivity_timeout = 60000
        session_info.connection_inactivity_timeout = 2000

        self.session_manager = SessionManager(self.router)
        print(f"Fazendo login como {self.credenciais[0]} e no IP {self.ip}...")
        self.session_manager.CreateSession(session_info)
        print("Login bem sucedido.")

        return self.router
    def __exit__(self, exc_type, exc_value, traceback):
        if self.session_manager:
            print("Fazendo logout...")
            self.session_manager.CloseSession()
        print("Desconectando...")
        self.transport.disconnect()
    @staticmethod
    def create_tcp_connection():
        return Conexao(Conexao.IP, Conexao.TCP_PORT, credenciais=(Conexao.username, Conexao.password))
        
              
