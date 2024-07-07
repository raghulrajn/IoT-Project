import generate_pddl
import threading
import paho.mqtt.client as mqtt
import random
import time
import requests
from queue import Empty
import grovepi
from utils import DatabaseHandler
# MQTT settings
broker = '127.0.0.1'
port = 1883

LED_PORT = 2
light_sensor = 1 # port A1

grovepi.pinMode(LED_PORT, "OUTPUT")
client = mqtt.Client()

sensorDict = {
    "iot/sensor/temperature":{
        "topic":"iot/sensor/temperature",
        "value":40,
        "lower_bound":22,
        "upper_bound":25
    },
    "iot/sensor/airquality":{
        "topic":"iot/sensor/airquality",
        "value":40,
        "lower_bound":10,
        "upper_bound":15
    },
    "iot/sensor/presence":{
        "topic":"iot/sensor/presence",
        "value":1,
        "lower_bound":0,
        "upper_bound":1
    },
    "iot/sensor/luminosity":{
        "topic":"iot/sensor/luminosity",
        "value":40,
        "lower_bound":500,
        "upper_bound":1000
    },
    "iot/actuator/heater":{
        "topic":"iot/actuator/heater",
        "value":"heater-off"
    },
    "iot/actuator/light":{
        "topic":"iot/actuator/light",
        "value":"light-off"
    },
    "iot/actuator/window":{
        "topic":"iot/actuator/window",
        "value":"open-window"
    }
}

db_topics = ['iot/sensor/temperature',
          'iot/sensor/airquality', 
          'iot/sensor/presence',
          "iot/sensor/luminosity"]

db_handler = DatabaseHandler('mqtt_data.db', db_topics)
# Queue for inter-thread communication
value_queue = {"iot/sensor/temperature":None,
               "iot/sensor/airquality":None,
               "iot/sensor/presence":None,
               "iot/sensor/luminosity":None,
               "iot/actuator/heater":None,
               "iot/actuator/light":None,
               "iot/actuator/window":None}

topics = ['iot/sensor/temperature',
          'iot/sensor/airquality', 
          'iot/sensor/presence',
          "iot/sensor/luminosity",
          "iot/actuator/heater",
          "iot/actuator/light",
          "iot/actuator/window"]


message_buffer = {topic: None for topic in topics}
dict_lock = threading.Lock()
# MQTT Publisher
def publish(client, queue):
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
                print("publishing " + str(sensorDict[sensor]["value"])+" to " +str(sensorDict[sensor]["topic"]))
                time.sleep(2)
        # time.sleep(1)  # Publish every 5 seconds

def on_message(client, userdata, msg):
    global message_buffer
    message_buffer[msg.topic] = msg.payload.decode('utf-8')
    if all(value is not None for value in message_buffer.values()):
        print("subscribed value from all topics ",message_buffer)
        write_buffer = {k: v for k, v in message_buffer.items() if k in db_topics}
        db_handler.write_to_db(write_buffer)
        check_value(sensorDict, message_buffer)
        message_buffer = {topic: None for topic in topics}


def on_connect(client, userdata, flags, rc):
    for topic in topics:
        client.subscribe(topic)

def implement_action(action, message_buffer):
    global value_queue
    if ("switch-off-heater") in action:
        value_queue["iot/sensor/temperature"] = int(message_buffer["iot/sensor/temperature"]) - 1
        value_queue["iot/actuator/heater"] = "heater-off"
    if ("switch-on-heater") in action:
        value_queue["iot/sensor/temperature"] = int(message_buffer["iot/sensor/temperature"]) + 1
        value_queue["iot/actuator/heater"] = "heater-on"
    if ("switch-on-light") in action:
        value_queue["iot/sensor/luminosity"] = get_light_intensity()
        value_queue["iot/actuator/light"] = "light-on"

    if ("switch-off-light") in action:
        value_queue["iot/sensor/luminosity"] = get_light_intensity()
        value_queue["iot/actuator/light"] = "light-off"
    if ("open-window") in action:
        value_queue["iot/sensor/airquality"] = int(message_buffer["iot/sensor/airquality"]) - 2
        value_queue["iot/actuator/window"] = "open-window"
    if ("close-window") in action:
        value_queue["iot/sensor/airquality"] = int(message_buffer["iot/sensor/airquality"]) + 2
        value_queue["iot/actuator/window"] = "close-window"
    

def check_value(sensorDict,message_buffer):
    global value_queue
    flag=False
    for topic in topics:
        if 'sensor' in topic:
            if message_buffer[topic] is not None:   
                if not (sensorDict[topic]["lower_bound"] <= int(message_buffer[topic]) <= sensorDict[topic]["upper_bound"]):
                    print(topic +" is not in optimum level...")
                    flag=True
    if flag:
        problem_pddl, problem = generate_pddl.problemGeneration(sensorDict,message_buffer)
        action = call_api(generate_pddl.domain, problem_pddl)
        client.publish('iot/aiplanning/problem', problem)
        client.publish('iot/aiplanning/solution', action)
        print(action)
        implement_action(action, message_buffer)

def call_api(domain, problem):
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
    # print(celery_result.json())
    # Extract the plan
    if result['status'] == 'ok' and 'output' in result['result']:
        plan = result['result']['output'].get('plan', 'No plan found')
        return plan
    else:
        return plan

def get_light_intensity():
    #light_intensity = grovepi.analogRead(light_sensor)
    light_intensity = random.randint(100,1000)
    print(light_intensity)
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



