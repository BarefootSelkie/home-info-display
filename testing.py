import logging
import requests
import os
import json
import yaml

# Logging setup
logging.basicConfig(format="%(asctime)s : %(message)s", filename="log-hid.log", encoding='utf-8', level=logging.WARN)

# Load settings
try:
    with open("./config-hid.yaml", "r") as read_file:
        config = yaml.safe_load(read_file)
except:
    logging.critical("Settings file missing")
    exit()

weather = "blank"

try:
    r = requests.get("https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/" + str(config["location"]["lat"]) + "%2C" + str(config["location"]["long"]) + "?unitGroup=metric&include=remote%2Cobs%2Cfcst%2Ccurrent%2Calerts%2Cevents&key=" + config["apikeys"]["weather"] + "&contentType=json")
    weather = json.loads(r.text)
except Exception as e:
    logging.warning(e)

with open("./weather.json", "w") as weatherFile:
    weatherFile.write(json.dumps(weather))
