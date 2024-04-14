import os
import json
from dotenv import load_dotenv

import paho.mqtt.client as paho
from paho import mqtt
import time

from InputTypes import NewPlayer
import random

validated = False
wait_next_variable = False
answer = 'UP'

# setting callbacks for different events to see if it works, print the message etc.
def on_connect(client, userdata, flags, rc, properties=None):
    """
        Prints the result of the connection with a reasoncode to stdout ( used as callback for connect )
        :param client: the client itself
        :param userdata: userdata is set when initiating the client, here it is userdata=None
        :param flags: these are response flags sent by the broker
        :param rc: stands for reasonCode, which is a code for the connection result
        :param properties: can be used in MQTTv5, but is optional
    """
    print("CONNACK received with code %s." % rc)


# with this callback you can see if your publish was successful
def on_publish(client, userdata, mid, properties=None):
    """
        Prints mid to stdout to reassure a successful publish ( used as callback for publish )
        :param client: the client itself
        :param userdata: userdata is set when initiating the client, here it is userdata=None
        :param mid: variable returned from the corresponding publish() call, to allow outgoing messages to be tracked
        :param properties: can be used in MQTTv5, but is optional
    """
    print("mid: " + str(mid))


# print which topic was subscribed to
def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    """
        Prints a reassurance for successfully subscribing
        :param client: the client itself
        :param userdata: userdata is set when initiating the client, here it is userdata=None
        :param mid: variable returned from the corresponding publish() call, to allow outgoing messages to be tracked
        :param granted_qos: this is the qos that you declare when subscribing, use the same one for publishing
        :param properties: can be used in MQTTv5, but is optional
    """
    print("Subscribed: " + str(mid) + " " + str(granted_qos))


# print message, useful for checking if it was successful
def on_message(client, userdata, msg):
    """
        Prints a mqtt message to stdout ( used as callback for subscribe )
        :param client: the client itself
        :param userdata: userdata is set when initiating the client, here it is userdata=None
        :param msg: the message with topic and payload
    """
    topic_list = msg.topic.split("/")

    # Validate it is input we can deal with
    if topic_list[-1] in dispatch.keys(): 
        dispatch[topic_list[-1]](client, topic_list, msg.payload)

    #player = NewPlayer(**json.loads(msg.payload))
    #print(player.player_name)

    if f'games/TestLobby/Player2/game_state' == msg.topic:
        global wait_next_variable
        wait_next_variable = True
        gamestate = json.loads(msg.payload)
        global answer
        answer = getnextcommand(gamestate)

    print("message: " + msg.topic + " " + str(msg.qos) + " " + str(msg.payload))

def validate_player(client, topic_list, msg_payload):
        player = NewPlayer(**json.loads(msg_payload))
        if player.player_name == "Player4":
            global validated
            validated = True


dispatch = {
    'new_game' : validate_player
}


def getnextcommand(game_state):
        moves = get_moves(game_state)
        if moves:
            return random.choice(moves)
        else:
            return None
        
def get_moves(game_state):
        current_position = game_state["currentPosition"]
        valid_moves = []
        # Check all adjacent positions
        for move in [[0, 1], [0, -1], [1, 0], [-1, 0]]:
            new_position = (current_position[0] + move[0], current_position[1] + move[1])
            print(new_position)
            if is_valid(new_position, game_state):
                if move == [0,1]:
                    valid_moves.append("RIGHT")
                elif move == [0,-1]:
                    valid_moves.append("LEFT")
                elif move == [1,0]:
                    valid_moves.append("DOWN")
                elif move == [-1,0]:
                    valid_moves.append("UP")    
        return valid_moves

def is_valid(position, game_state):
        x, y = position
        if 0 <= x < 10 and 0 <= y < 10:  # Check if within grid boundaries
            if list(position) not in game_state["walls"]:  # Check if not a wall
                print("true")
                print(game_state["walls"])
                return True
        return False

if __name__ == '__main__':
    load_dotenv(dotenv_path='./credentials.env')
    
    broker_address = os.environ.get('BROKER_ADDRESS')
    broker_port = int(os.environ.get('BROKER_PORT'))
    username = os.environ.get('USER_NAME')
    password = os.environ.get('PASSWORD')

    client = paho.Client(callback_api_version=paho.CallbackAPIVersion.VERSION1, client_id="Player2", userdata=None, protocol=paho.MQTTv5)
    
    # enable TLS for secure connection
    client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
    # set username and password
    client.username_pw_set(username, password)
    # connect to HiveMQ Cloud on port 8883 (default for MQTT)
    client.connect(broker_address, broker_port)

    # setting callbacks, use separate functions like above for better visibility
    client.on_subscribe = on_subscribe # Can comment out to not print when subscribing to new topics
    client.on_message = on_message
    client.on_publish = on_publish # Can comment out to not print when publishing to topics

    lobby_name = "TestLobby"
    player_1 = "Player1"
    player_2 = "Player2"
    player_3 = "Player3"

    client.subscribe(f"games/{lobby_name}/lobby")
    client.subscribe(f'games/{lobby_name}/+/game_state')
    client.subscribe(f'games/{lobby_name}/scores')

    client.publish("new_game", json.dumps({'lobby_name':lobby_name,
                                            'team_name':'ATeam',
                                            'player_name' : player_2}))

    time.sleep(1) # Wait a second to resolve game start
    """
    client.publish(f"games/{lobby_name}/start", "START")
    client.publish(f"games/{lobby_name}/{player_1}/move", "UP")
    client.publish(f"games/{lobby_name}/{player_2}/move", "DOWN")
    client.publish(f"games/{lobby_name}/{player_3}/move", "DOWN")
    client.publish(f"games/{lobby_name}/start", "STOP")

    """
    client.subscribe(f"new_game")


    #client.publish(f"games/{lobby_name}/start", "START")
    #client.loop_forever()
    
    client.loop_start()

    time.sleep(3)

    while(True):
        if validated == 1:
            val = answer
            client.publish(f"games/{lobby_name}/{player_2}/move", val)
            wait_next_variable = False
            while(wait_next_variable == False):
                #print(wait_next_variable)
                time.sleep(1)
        #client.publish(f"games/{lobby_name}/start", "STOP") 
        time.sleep(1)
    
    #client.loop_forever()
