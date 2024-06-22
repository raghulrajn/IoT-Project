from utils import DatabaseHandler, MQTTClient, topics
import paho.mqtt.client as mqtt

if __name__ == "__main__":
    broker = '127.0.0.1'
    port = 1883
    
    db_handler = DatabaseHandler('mqtt_data.db', topics)
    mqtt_client = MQTTClient(broker, port, topics, db_handler)

    mqtt_client.connect()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Exiting...")
        mqtt_client.client.loop_stop()
