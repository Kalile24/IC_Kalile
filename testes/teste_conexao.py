import sys
import os

from kortex_api.TCPTransport import TCPTransport
from kortex_api.RouterClient import RouterClient
from kortex_api.SessionManager import SessionManager

from kortex_api.autogen.client_stubs.DeviceConfigClientRpc import DeviceConfigClient
from kortex_api.autogen.client_stubs.BaseClientRpc import BaseClient

from kortex_api.autogen.messages import DeviceConfig_pb2, Session_pb2, Base_pb2

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

def main():
    #Import o módulo de conexão
    
    import modulos.modulo_conexao

    with modulos.modulo_conexao.Conexao.create_tcp_connection() as router:
        
        device_config = DeviceConfigClient(router)
        base = BaseClient(router)

        print(device_config.GetDeviceType())
        print(base.GetArmState())   

if __name__ == "__main__":
    exit(main())