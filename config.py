sensorDict = {
    "iot/sensor/temperature":{
        "topic":"iot/sensor/temperature",
        "value":23,
        "lower_bound":22,
        "upper_bound":25
    },
    "iot/sensor/airquality":{
        "topic":"iot/sensor/airquality",
        "value":350,
        "lower_bound":300,
        "upper_bound":400
    },
    "iot/sensor/presence":{
        "topic":"iot/sensor/presence",
        "value":1,
        "lower_bound":0,
        "upper_bound":1
    },
    "iot/sensor/luminosity":{
        "topic":"iot/sensor/luminosity",
        "value":600,
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

topics = ['iot/sensor/temperature',
          'iot/sensor/airquality', 
          'iot/sensor/presence',
          "iot/sensor/luminosity",
          "iot/actuator/heater",
          "iot/actuator/light",
          "iot/actuator/window"]

sensor_topics = ['iot/sensor/temperature',
          'iot/sensor/airquality', 
          'iot/sensor/presence',
          "iot/sensor/luminosity"]

actuator_topics = ["iot/actuator/heater",
          "iot/actuator/light",
          "iot/actuator/window"]