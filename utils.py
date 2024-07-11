import sqlite3
import threading
import paho.mqtt.client as mqtt
from typing import Dict, Any
import pandas as pd
import config

class MQTTClient:
    """
    MQTT Client class to handle connections, subscriptions, and message processing.
    
    Attributes:
        broker (str): MQTT broker address.
        port (int): MQTT broker port.
        topics (list): List of topics to subscribe to.
        messages (Dict[str, Any]): Dictionary to store received messages.
        lock (threading.Lock): Lock for thread-safe operations on messages dictionary.
        db_handler (DatabaseHandler): Instance of DatabaseHandler to handle database operations.
    """

    def __init__(self, broker: str, port: int, topics: list, db_handler):
        self.broker = broker
        self.port = port
        self.topics = topics
        self.message_buffer = {topic: None for topic in topics}
        self.lock = threading.Lock()
        self.db_handler = db_handler
        self.client = mqtt.Client()

        # Assign the callbacks
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def connect(self):
        """Connects to the MQTT broker and starts the loop."""
        self.client.connect(self.broker, self.port, 60)
        self.client.loop_forever()

    def on_connect(self, client, userdata, flags, rc):
        """Callback for when the client receives a CONNECT response from the server."""
        print(f"Connected with result code {rc}")
        for topic in self.topics:
            self.client.subscribe(topic)

    def on_message(self, client, userdata, msg):
        """Callback for when a PUBLISH message is received from the server."""
        self.message_buffer[msg.topic] = msg.payload.decode('utf-8')
        if all(value is not None for value in self.message_buffer.values()):
            self.db_handler.write_to_db(self.message_buffer)
            self.message_buffer = {topic: None for topic in self.topics}
        # try:
        #     message_str = msg.payload.decode('utf-8')
        #     with self.lock:
        #         self.messages[msg.topic] = message_str
            
        #     self.db_handler.write_to_db(self.messages)
        #     self.messages.clear()
        # except json.JSONDecodeError as e:
        #     print("Failed to decode JSON:", e)


class DatabaseHandler:
    """
    Database Handler class to manage SQLite database operations.
    
    Attributes:
        db_name (str): Name of the SQLite database file.
    """

    def __init__(self, db_name: str, topics:list):
        self.db_name = db_name
        self.topics = topics
        self.init_db()

    def init_db(self):
        """Initializes the SQLite database and creates the table if it doesn't exist."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        columns = ', '.join([f"{topic.split('/')[2]} FLOAT" for topic in self.topics if topic in config.sensor_topics])
        columns = ', '.join([f"{topic.split('/')[2]} TEXT" for topic in self.topics if topic in config.actuator_topics])
        cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            {columns},
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        conn.commit()
        conn.close()

    def read_from_db(self) -> pd.DataFrame:
        """
        Reads all rows from the messages table in the SQLite database.
        
        Returns:
            pd.DataFrame: DataFrame representing the rows in the table.
        """
        conn = sqlite3.connect(self.db_name)
        query = f'SELECT * FROM messages'
        df = pd.read_sql_query(query, conn)
        for col in df.columns:
            df[col] = df[col].dropna().reset_index(drop=True)
        conn.close()
        return df

    def write_to_db(self, messages: Dict[str, Any]):
        """
        Writes messages to the SQLite database.
        
        Args:
            messages (Dict[str, Any]): Dictionary of messages to write to the database.
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        columns = ', '.join([f"'{topic.split('/')[2]}'" for topic in messages.keys()])
        placeholders = ', '.join(['?' for _ in messages.keys()])
        values = [messages[topic] for topic in messages.keys()]

        cursor.execute(f'''
        INSERT INTO messages ({columns}) VALUES ({placeholders})
        ''', values)

        conn.commit()
        conn.close()