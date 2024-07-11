import generate_pddl
import threading
import paho.mqtt.client as mqtt
import random
import time
import requests
import config
from queue import Empty
from utils import DatabaseHandler
# MQTT settings
broker = '127.0.0.1'
port = 1883
client = mqtt.Client()

count = 0

sensorDict = config.sensorDict

db_handler = DatabaseHandler('mqtt_data.db', config.topics)
# Queue for inter-thread communication
value_queue = {"iot/sensor/temperature":None,
               "iot/sensor/airquality":None,
               "iot/sensor/presence":None,
               "iot/sensor/luminosity":None,
               "iot/actuator/heater":None,
               "iot/actuator/light":None,
               "iot/actuator/window":None}

message_buffer = {topic: None for topic in config.topics}
dict_lock = threading.Lock()
# MQTT Publisher
def publish(client,queue):
    global sensorDict
    while True:
        with dict_lock:
            for sensor in value_queue:
                try:
                    new_value = value_queue[sensor]
                    if new_value is not None:
                        sensorDict[sensor]["value"] = new_value
                except Empty:
                    pass
            
                result = client.publish(sensorDict[sensor]["topic"],
                                        sensorDict[sensor]["value"])
                time.sleep(2)

def on_message(client, userdata, msg):
    """
    Callback function to call when message is published in the MQTT broker
    
    """
    global message_buffer
    message_buffer[msg.topic] = msg.payload.decode('utf-8')
    if all(value is not None for value in message_buffer.values()):
        time.sleep(2)
        print("\nSubscribed value from all topics:\n",message_buffer,"\n")
        # write_buffer = {k: v for k, v in message_buffer.items() if k in config.db_topics}
        db_handler.write_to_db(message_buffer)
        check_sensor_state(sensorDict, message_buffer)
        message_buffer = {topic: None for topic in config.topics}


def on_connect(client, userdata, flags, rc):
    for topic in config.topics:
        client.subscribe(topic)

def implement_action(action:str, message_buffer:dict):
    """
    A function which simulates the actuator output based on plan generated.
    This update a global dict which updates sensor values and actuator status
    
    """
    global value_queue
    value_queue["iot/sensor/presence"] = random.randint(0, 1)
    if ("switch-off-heater") in action:
        value_queue["iot/sensor/temperature"] = int(message_buffer["iot/sensor/temperature"]) - 2
        value_queue["iot/actuator/heater"] = "heater-off"
    if ("switch-on-heater") in action:
        value_queue["iot/sensor/temperature"] = int(message_buffer["iot/sensor/temperature"]) + 2
        value_queue["iot/actuator/heater"] = "heater-on"
    if ("switch-on-light") in action:
        value_queue["iot/sensor/luminosity"] = int(message_buffer["iot/sensor/luminosity"]) + 500
        value_queue["iot/actuator/light"] = "light-on"

    if ("switch-off-light") in action:
        value_queue["iot/sensor/luminosity"] = int(message_buffer["iot/sensor/luminosity"]) - 500
        value_queue["iot/actuator/light"] = "light-off"
    if ("open-window") in action:
        value_queue["iot/sensor/airquality"] = int(message_buffer["iot/sensor/airquality"]) - 20
        value_queue["iot/actuator/window"] = "window-open"
    if ("close-window") in action:
        value_queue["iot/sensor/airquality"] = int(message_buffer["iot/sensor/airquality"]) + 20
        value_queue["iot/actuator/window"] = "window-close"
    

def check_sensor_state(sensorDict:dict,message_buffer:dict):
    """
    Checks the each sensor status, if the state is not optimal, then a problem is generated based 
    on sensor and sent to AI planning API
    
    """
    global value_queue, count
    notOptimalState=False
    for topic in config.topics:
        if 'sensor' in topic and message_buffer[topic] is not None:
                if not (sensorDict[topic]["lower_bound"] <= int(message_buffer[topic]) <= sensorDict[topic]["upper_bound"]):
                    print(topic +" is not in optimum level...")
                    notOptimalState=True
                
    if notOptimalState:
        problem_pddl, problem = generate_pddl.problemGeneration(sensorDict,message_buffer)
        action = call_aiplanning_api(generate_pddl.domain, problem_pddl)
        client.publish('iot/aiplanning/problem', problem)
        client.publish('iot/aiplanning/solution', action)
        if action != 'No plan found':
            print("\nComputed Plan:\n"+action+"\n")
        implement_action(action, message_buffer)
    else:
        count=count+1
        if count==10:
            value_queue["iot/sensor/airquality"] = 1000
        if count==20:
            value_queue["iot/sensor/temperature"] = 40
            count = 0


def call_aiplanning_api(domain:str, problem:str)->str:
    """
    sends POST request to AI planning API with configured domain and dynamically generated problem
    
    """
    req_body = {
        "domain": domain,
        "problem":problem
    }

    solve_request_url = requests.post(url="https://solver.planning.domains:5001/package/delfi/solve", json=req_body)

    result_url = solve_request_url.json()['result']
    celery_result = requests.post('https://solver.planning.domains:5001' + result_url)

    while celery_result.json().get("status") == 'PENDING':
        # Query the result every 0.5 seconds while the job is executing
        celery_result = requests.post('https://solver.planning.domains:5001' + result_url)
        time.sleep(0.5)

    result = celery_result.json()
    # Extract the plan
    if result['status'] == 'ok' and 'output' in result['result']:
        plan = result['result']['output'].get('plan', 'No plan found')
        return plan
    else:
        return plan

def get_light_intensity()->int:
    #light_intensity = grovepi.analogRead(light_sensor)
    light_intensity = random.randint(100,1000)
    return light_intensity

def main():
    global client
    client.connect(broker, port, 60)
    client.on_connect = on_connect
    client.on_message = on_message
    client.loop_start() 
    while True:
        t1 = threading.Thread(target=publish, args=(client, value_queue))
        # t2 = threading.Thread(target=subscribe, args=(client))
        t1.start()


if __name__ == '__main__':
    main()



