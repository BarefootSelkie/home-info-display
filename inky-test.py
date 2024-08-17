#!/usr/bin/env python3

# from inky.auto import auto
from inky.inky_ac073tc1a import Inky as InkyAC073TC1A
from PIL import Image, ImageDraw, ImageFont
import datetime
import yaml
import logging
import requests
import json
import objectpath

# Logging setup
logging.basicConfig(format="%(asctime)s : %(message)s", filename="log-hid.log", encoding='utf-8', level=logging.WARN)

# Load settings
try:
    with open("./config-hid.yaml", "r") as read_file:
        config = yaml.safe_load(read_file)
except:
    logging.critical("Settings file missing")
    exit()


# Constants
colour = {
    "black": 0,
    "white": 1,
    "green": 2,
    "blue": 3,
    "red": 4,
    "yellow": 5,
    "orange": 6
    }

fontGridSingle = ImageFont.truetype("./ttf/Fredoka-Medium.ttf", int(44))
fontGridDual = ImageFont.truetype("./ttf/Fredoka-Medium.ttf", int(24))
fontGridLabel = ImageFont.truetype("./ttf/Fredoka-Medium.ttf", int(18))

fontCalBg = ImageFont.truetype("./ttf/Fredoka-Medium.ttf", int(64))
fontCalSm = ImageFont.truetype("./ttf/Fredoka-Medium.ttf", int(32))



# Functions

def toCompassPoint(degrees):
    if degrees < 22.5:
        return "N"
    if degrees < 67.5:
        return "NE"
    if degrees < 112.5:
        return "E"
    if degrees < 157.5:
        return "SE"
    if degrees < 202.5:
        return "S"
    if degrees < 247.5:
        return "SW"
    if degrees < 292.5:
        return "W"
    if degrees < 337.5:
        return "NW"
    return "N"

def msToKmh(ms):
    kmh = ms * 3.6
    return kmh    

# given an input text string, return a list of strings that don't exceed a certain pixel width
def wrap(image, text, wrapWidth, font):
    output = []
    currentLine = ""
    currentWord = ""

    # For each charater in the text
    for character in text:
        if character == " ":
            currentLine = currentLine + currentWord + character
            currentWord = ""
        else:
            currentWord = currentWord + character

            # check if adding the character would exceed the wrap width
            newWidth = image.textlength(currentLine + currentWord, font)

            if newWidth > wrapWidth:
                # if so, add the current line to the output list and start a new line
                output.append(currentLine)
                currentLine = ""
        
    currentLine = currentLine + currentWord
    output.append(currentLine)

    return output


converters = {
    "windDirection": lambda degrees: toCompassPoint(float(degrees)),
    "time": lambda time: time[:5]
}


# Load trips
try:
    with open("./trips.yaml", "r") as read_file:
        trips = yaml.safe_load(read_file)
except:
    # logging.critical("Settings file missing")
    exit()

# Load weather data
weather = None
try:
    r = requests.get("https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/" + str(config["location"]["lat"]) + "%2C" + str(config["location"]["long"]) + "/today?unitGroup=metric&include=remote%2Cobs%2Cfcst%2Ccurrent%2Calerts%2Cevents&key=" + config["apikeys"]["weather"] + "&contentType=json")
    weather = json.loads(r.text)
except Exception as e:
    logging.warning(e)
    logging.warning(r.text)

# Initialise display
inky = InkyAC073TC1A(resolution=(800, 480))
display = Image.new(mode="P", size=(480,800), color=(colour["white"]))
image = ImageDraw.Draw(display)

# Draw the calendar square in top left of screen
dateNumber = datetime.date.today().strftime('%d')
dateDay = datetime.date.today().strftime('%a')
dateMonth = datetime.date.today().strftime('%b')

image.rounded_rectangle([(0,0),(157,157)], radius=12, fill=None, outline=colour["red"], width=4)
image.rounded_rectangle([(0,0),(157,41)], radius=12, fill=colour["red"], outline=colour["red"], width=4, corners=(True, True, False, False))
image.text((79,20), dateMonth, colour["white"], font=fontCalSm, anchor="mm")
image.text((79,79), dateNumber, colour["black"], font=fontCalBg, anchor="mm")
image.text((79,136), dateDay, colour["black"], font=fontCalSm, anchor="mm")

# Draw the next trip box next to the current date
image.rounded_rectangle([(161,0),(479,157)], radius=12, fill=None, outline=colour["black"], width=4)

# Get trips that haven't happened yet
upcomingTrips = []
for trip in trips["trips"]:
    if datetime.date.fromisoformat(str(trip["date"])) > datetime.date.today():
        upcomingTrips.append(trip)

# Sort the list
upcomingTrips.sort(key=lambda trip: trip["date"], reverse=False)

if len(upcomingTrips) > 0:
    nextTrip = upcomingTrips[0]
    nextTripDate = datetime.date.fromisoformat(str(nextTrip["date"]))
    todayDate = datetime.date.today()
    daysRemaining = (nextTripDate - todayDate).days

    lines = wrap(image, nextTrip["destination"], 294, fontCalSm)

    image.text((170,28), lines[0], colour["black"], font=fontCalSm, anchor="lm")
    if len(lines) > 1:
        image.text((170,60), lines[1], colour["black"], font=fontCalSm, anchor="lm")
    image.text((320,108), str(daysRemaining) + " days", colour["black"], font=fontCalBg, anchor="mm")

width = 158
height = 118
cellSpacing = 3
offset = 161
padding = 10

# look at box design - get template - fill in data - place in image

def boxTitledBig(box, position):
    image.rounded_rectangle(position, radius=12, fill=None, outline=colour["black"], width=4)
    image.text((padding +  position[0][0], padding + position[0][1]), str(box['label']), colour["black"], font=fontGridLabel, anchor="la")
    image.text(((width / 2) +  position[0][0], (height / 2) + position[0][1]), box["text1"], colour["black"], font=fontGridSingle, anchor="mm")

def boxBig(box, position):
    image.rounded_rectangle(position, radius=12, fill=None, outline=colour["red"], width=4)
    image.text(((width / 2) +  position[0][0], (height / 2) + position[0][1]), str(box["text1"]), colour["black"], font=fontGridSingle, anchor="mm")

def boxIcon(box, position):
    fileIcon = "./png/" + box["text1"] + ".png"
    iconWeather = Image.open(fileIcon)
    image.rounded_rectangle(position, radius=12, fill=None, outline=colour["red"], width=4)
    image.paste(iconWeather, (((width / 2) - 64) + position[0][0], ((height / 2) - 64) + position[0][1]))

def boxTitledDual(box, position):
    image.rounded_rectangle(position, radius=12, fill=None, outline=colour["blue"], width=4)
    image.text((padding +  position[0][0], padding + position[0][1]), str(box['label']), colour["black"], font=fontGridLabel, anchor="la")
    image.text(((width / 2) +  position[0][0], (height / 2) + position[0][1]), box["text1"], colour["black"], font=fontGridDual, anchor="mm")
    image.text(((width / 2) +  position[0][0], (3*height / 4) + position[0][1]), box["text2"], colour["black"], font=fontGridDual, anchor="mm")

def boxDual(box, position):
    image.rounded_rectangle(position, radius=12, fill=None, outline=colour["green"], width=4)
    image.text(((width / 2) +  position[0][0], (height / 4) + position[0][1]), box["text1"], colour["black"], font=fontGridDual, anchor="mm")
    image.text(((width / 2) +  position[0][0], (3*height / 4) + position[0][1]), box["text2"], colour["black"], font=fontGridDual, anchor="mm")

index = 0
rowWidth = 3
for box in config["boxes"]:
    row = index // rowWidth
    col = index % rowWidth
    stx = (width + cellSpacing) * col
    sty = ((height + cellSpacing) * row) + offset
    spx = stx + width - 1
    spy = sty + height - 1 
    position = [(stx,sty),(spx,spy)]

    if "data1" in box and box["data1"] is not None:
        box["text1"] = str(objectpath.Tree(weather).execute(box["data1"]))
    if "data2" in box and box["data2"] is not None:
        box["text2"] = str(objectpath.Tree(weather).execute(box["data2"]))

    if "converter1" in box and box["converter1"] is not None:
        box["text1"] = converters[box["converter1"]](box["text1"])
    if "converter2" in box and box["converter2"] is not None:
        box["text2"] = converters[box["converter2"]](box["text2"])

    if "unit1" in box and box["unit1"] is not None:
        box["text1"] = box["text1"] + " " + box["unit1"]
    if "unit2" in box and box["unit2"] is not None:
        box["text2"] = box["text2"] + " " + box["unit2"]

    if "type" in box and box["type"] is "weathericon":
        boxIcon(box, position)
    elif box['label'] is not None:
        if "data2" in box and box["data2"] is not None:
            boxTitledDual(box, position)
        else:
            boxTitledBig(box, position)
    else:
        if "data2" in box and box["data2"] is not None:
            boxDual(box, position)
        else:
            boxBig(box, position)
    
    index = index + 1


inky.set_image(display.rotate(90, expand=True))
inky.show()
