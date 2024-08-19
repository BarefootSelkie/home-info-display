#!/usr/bin/env python3

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
river = "blank"
homeass = "blank"

for source in config["sources"]:
    url = source["url"].format(
        apikey = source["apikey"], 
        lat=str(config["location"]["lat"]), 
        long=str(config["location"]["long"]) 
    )

    headers = {}
    if "headers" in source:
        for key in source["headers"].keys():
            headers[key] = source["headers"][key].format(
                apikey = source["apikey"], 
                lat=str(config["location"]["lat"]), 
                long=str(config["location"]["long"]) 
            )

    try:
        r = requests.get(url, headers=headers)
        data = json.loads(r.text)
        with open("./requests/" + source["name"] + ".json", "w") as outputFile:
            outputFile.write(json.dumps(data))
    except Exception as e:
        logging.warning(e)


"""     r = requests.get(url, headers=headers)
    
try:
    source = {}
    for item in config["sources"]:
        if item["name"] == "visualcrossing":
            source = item
    print("fred")
    
    print(url)
    print(url)
    r = requests.get(url)
    weather = json.loads(r.text)
except Exception as e:
    logging.warning(e)

with open("./requests/weather.json", "w") as weatherFile:
    weatherFile.write(json.dumps(weather))

try:
    r = requests.get(config["riverLevel"])
    river = json.loads(r.text)
except Exception as e:
    logging.warning(e)

with open("./requests/river.json", "w") as riverFile:
    riverFile.write(json.dumps(river))

try:
    headers = {
        "authorization": "Bearer " + config["apikeys"]["homeassistant"],
        "content-type": "application/json" 
    }
    r = requests.get("http://192.168.1.189:8123/api/states", headers = headers)
    homeass = json.loads(r.text)
except Exception as e:
    logging.warning(e)

with open("./requests/homeass.json", "w") as homeassFile:
    homeassFile.write(json.dumps(homeass)) """