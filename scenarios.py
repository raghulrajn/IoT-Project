import generate_pddl
import threading
import paho.mqtt.client as mqtt
import random
import time
import requests
from queue import Empty

# MQTT settings
broker = '127.0.0.1'
port = 1883
topic = "your/topic"
client_id = f'python-mqtt-{random.randint(0, 1000)}'

sensorDict = {
    "iot/temperature":{
        "topic":"iot/temperature",
        "value":40,
        "lower_bound":22,
        "upper_bound":25
    },
    "iot/airquality":{
        "topic":"iot/airquality",
        "value":40,
        "lower_bound":10,
        "upper_bound":15
    },
    "iot/presence":{
        "topic":"iot/presence",
        "value":1,
        "lower_bound":0,
        "upper_bound":1
    },
    "iot/luminosity":{
        "topic":"iot/luminosity",
        "value":25,
        "lower_bound":20,
        "upper_bound":50
    }
}

# Queue for inter-thread communication
value_queue = {"iot/temperature":None,
               "iot/airquality":None,
               "iot/presence":None,
               "iot/luminosity":None}

topics = ['iot/temperature','iot/airquality', 'iot/presence',"iot/luminosity"]
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
        check_value(sensorDict, message_buffer)
        message_buffer = {topic: None for topic in topics}


def on_connect(client, userdata, flags, rc):
    for topic in topics:
        client.subscribe(topic)

def implement_action(action, message_buffer):
    global value_queue
    if ("switch-off-heater") in action:
        value_queue["iot/temperature"] = int(message_buffer["iot/temperature"]) - 1
    if ("switch-on-heater") in action:
        value_queue["iot/temperature"] = int(message_buffer["iot/temperature"]) + 1
    if ("switch-on-light") in action:
        value_queue["iot/luminosity"] = int(message_buffer["iot/luminosity"]) + 1
    if ("switch-off-light") in action:
        value_queue["iot/luminosity"] = int(message_buffer["iot/luminosity"]) - 1
    if ("open-window") in action:
        value_queue["iot/airquality"] = int(message_buffer["iot/airquality"]) - 2
    if ("close-window") in action:
        value_queue["iot/airquality"] = int(message_buffer["iot/airquality"]) + 2
    

def check_value(sensorDict,message_buffer):
    global value_queue
    flag=False
    for topic in topics:
        if message_buffer[topic] is not None:
            if not (sensorDict[topic]["lower_bound"] <= int(message_buffer[topic]) <= sensorDict[topic]["upper_bound"]):
                print(topic +" is not in optimum level...")
                flag=True
    if flag:
        problem = generate_pddl.problemGeneration(sensorDict,message_buffer)
        action = call_api(generate_pddl.domain, problem)
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

# MQTT Client
# def connect_mqtt():
#     client = mqtt_client.Client(client_id)
#     client.connect(broker, port)
#     return client

def main():
    client = mqtt.Client()
    client.connect(broker, port, 60)
    client.on_connect = on_connect
    client.on_message = on_message
    client.loop_start() 
    while True:
        # publish(client, value_queue)
        # subscribe(client, value_queue)
        t1 = threading.Thread(target=publish, args=(client, value_queue))
        # t2 = threading.Thread(target=subscribe, args=(client))
        t1.start()
        # t2.start()


if __name__ == '__main__':
    main()



