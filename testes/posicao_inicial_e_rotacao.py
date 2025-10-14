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

from kortex_api.autogen.messages import Base_pb2, DeviceConfig_pb2, DeviceManager_pb2

# Maximum allowed waiting time during actions (in seconds)
TIMEOUT_DURATION = 20

# Actuator speed (deg/s)
SPEED = 20

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

def example_move_to_home_position(base):
    # Make sure the arm is in Single Level Servoing mode
    base_servo_mode = Base_pb2.ServoingModeInformation()
    base_servo_mode.servoing_mode = Base_pb2.SINGLE_LEVEL_SERVOING
    base.SetServoingMode(base_servo_mode)
    
    # Move arm to ready position
    print("Moving the arm to a safe position")
    action_type = Base_pb2.RequestedActionType()
    action_type.action_type = Base_pb2.REACH_JOINT_ANGLES
    action_list = base.ReadAllActions(action_type)
    action_handle = None
    for action in action_list.action_list:
        if action.name == "Home":
            action_handle = action.handle

    if action_handle == None:
        print("Can't reach safe position. Exiting")
        return False

    e = threading.Event()
    notification_handle = base.OnNotificationActionTopic(
        check_for_end_or_abort(e),
        Base_pb2.NotificationOptions()
    )

    base.ExecuteActionFromReference(action_handle)
    finished = e.wait(TIMEOUT_DURATION)
    base.Unsubscribe(notification_handle)

    if finished:
        print("Safe position reached")
    else:
        print("Timeout on action notification wait")
    return finished
def example_send_joint_speeds(base):

    joint_speeds = Base_pb2.JointSpeeds()

    actuator_count = base.GetActuatorCount().count
    # The 7DOF robot will spin in the same direction for 10 seconds
    if actuator_count == 7:
        speeds = [SPEED, 0, 0, 0, 0 , 0, 0]
        i = 0
        for speed in speeds:
            joint_speed = joint_speeds.joint_speeds.add()
            joint_speed.joint_identifier = i 
            joint_speed.value = speed
            i = i + 1
        print ("Sending the joint speeds for 20 seconds...")
        base.SendJointSpeedsCommand(joint_speeds)
        time.sleep(20)
    # The 6 DOF robot will alternate between 4 spins, each for 2.5 seconds
    if actuator_count == 6:
        print ("Sending the joint speeds for 10 seconds...")
        for times in range(4):
            del joint_speeds.joint_speeds[:]
            if times % 2:
                speeds = [-SPEED, 0.0, 0.0, SPEED, 0.0, 0.0]
            else:
                speeds = [SPEED, 0.0, 0.0, -SPEED, 0.0, 0.0]
            i = 0
            for speed in speeds:
                joint_speed = joint_speeds.joint_speeds.add()
                joint_speed.joint_identifier = i 
                joint_speed.value = speed
                joint_speed.duration = 0
                i = i + 1
            
            base.SendJointSpeedsCommand(joint_speeds)
            time.sleep(2.5)

    print ("Stopping the robot")
    base.Stop()

    return True

def main():
    
    import modulos.modulo_conexao

    with modulos.modulo_conexao.Conexao.create_tcp_connection() as router:
        device_config = DeviceConfigClient(router)
        base = BaseClient(router)

        example_move_to_home_position(base)
        example_send_joint_speeds(base)

if __name__ == "__main__":
    exit(main())
