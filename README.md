# MQTT Subscriber and plotting

The Repo focuses on collecting data from MQTT publisher, store it a SqliteDB and create a plot to visualize the data

## Tools required
- Python 3.11.5
- Sqlite DB
- Mosquitto MQTT broker

## Installation of required libraries
````
cd IoT-Project
pip install -r requirements.txt
````
## Running the script

To get values published to broker and write it to Sqlite DB
````
python scenarios.py
````
To read values from Sqlite DB and plot it for visualisation
````
python plot.py
````
