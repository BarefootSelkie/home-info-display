#!/usr/bin/env python3

# from inky.auto import auto
from inky.inky_ac073tc1a import Inky as InkyAC073TC1A
from PIL import Image, ImageDraw, ImageFont, ImageOps
import datetime
import yaml
import logging
import requests
import json
from jsonpath_ng.ext import parse

# Logging setup
logging.basicConfig(format="%(asctime)s : %(message)s", filename="log-hid.log", encoding='utf-8', level=logging.WARN)

# Load settings
try:
  with open("./config-hid.yaml", "r") as read_file:
    config = yaml.safe_load(read_file)
except:
  logging.critical("Settings file missing")
  exit()


### Constants ###
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

# Sizing for data grid
rowWidth = 3
width = 158
height = 118
cellSpacing = 3
offset = 198
padding = 10


### State variables ###

dataSources = {}
trips = {}


### Converter functions ###

converters = {
  "windDirection": lambda degrees: toCompassPoint(float(degrees)),
  "time": lambda time: time[:5]
}

### Functions ###

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

def drawCalendar(image):
  # Draw the calendar square in top left of screen
  dateNumber = datetime.date.today().strftime('%d')
  dateDay = datetime.date.today().strftime('%a')
  dateMonth = datetime.date.today().strftime('%b')

  image.rounded_rectangle([(0,0),(157,157)], radius=12, fill=None, outline=colour["red"], width=4)
  image.rounded_rectangle([(0,0),(157,41)], radius=12, fill=colour["red"], outline=colour["red"], width=4, corners=(True, True, False, False))
  image.text((79,20), dateMonth, colour["white"], font=fontCalSm, anchor="mm")
  image.text((79,79), dateNumber, colour["black"], font=fontCalBg, anchor="mm")
  image.text((79,136), dateDay, colour["black"], font=fontCalSm, anchor="mm")

def drawTrips(image):
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

def drawMoth(image):
  # Draw a text box below the date and next trip
  messageOfHour = "So long and thanks for all the fish"
  image.rounded_rectangle([(0,161),(479,195)], radius=12, fill=None, outline=colour["blue"], width=4)
  image.text((239, 161+17), messageOfHour, colour["blue"], font=fontGridLabel, anchor="mm")


# edge case boxes
def boxWeatherIcon(box, position, values):
  fileIcon = "./png/" + values[0] + ".png"
  iconWeather = Image.open(fileIcon)
  iconWeather = ImageOps.invert(iconWeather)
  image.rounded_rectangle(position, radius=12, fill=None, outline=colour["red"], width=4)
  image.bitmap((((width / 2) - 48) + position[0][0], ((height / 2) - 48) + position[0][1]), iconWeather)

# standard boxes
def boxTitledBig(box, position, values):
  image.rounded_rectangle(position, radius=12, fill=None, outline=colour["black"], width=4)
  image.text((padding +  position[0][0], padding + position[0][1]), str(box['title']), colour["black"], font=fontGridLabel, anchor="la")
  image.text(((width / 2) +  position[0][0], (height / 2) + position[0][1]), values[0], colour["black"], font=fontGridSingle, anchor="mm")

def boxBig(box, position, values):
  image.rounded_rectangle(position, radius=12, fill=None, outline=colour["red"], width=4)
  image.text(((width / 2) +  position[0][0], (height / 2) + position[0][1]), values[0], colour["black"], font=fontGridSingle, anchor="mm")

def boxTitledDual(box, position, values):
  image.rounded_rectangle(position, radius=12, fill=None, outline=colour["blue"], width=4)
  image.text((padding +  position[0][0], padding + position[0][1]), str(box['title']), colour["black"], font=fontGridLabel, anchor="la")
  image.text(((width / 2) +  position[0][0], (height / 2) + position[0][1]), values[0], colour["black"], font=fontGridDual, anchor="mm")
  image.text(((width / 2) +  position[0][0], (3*height / 4) + position[0][1]), values[1], colour["black"], font=fontGridDual, anchor="mm")

def boxDual(box, position, values):
  image.rounded_rectangle(position, radius=12, fill=None, outline=colour["green"], width=4)
  image.text(((width / 2) +  position[0][0], (height / 4) + position[0][1]), values[0], colour["black"], font=fontGridDual, anchor="mm")
  image.text(((width / 2) +  position[0][0], (3*height / 4) + position[0][1]), values[1], colour["black"], font=fontGridDual, anchor="mm")

def getValue(value):
  jsonpath_expr = parse(value["path"])
  output = jsonpath_expr.find(dataSources[value["source"]])[0].value
  output = str(output)

  if "converter" in value and value["converter"] is not None:
    output = converters[value["converter"]](output)

  if "round" in value:
    if value["round"] == 0:
      output = str(int(float(output)))
    else:
      output = str(round(float(output), value["round"]))

  if "prefix" in value and value["prefix"] is not None:
    output = value["prefix"] + output

  if "suffix" in value and value["suffix"] is not None:
    output = output + value["suffix"]

  return output

def getBoxPosition(index):
  row = index // rowWidth
  col = index % rowWidth
  stx = (width + cellSpacing) * col
  sty = ((height + cellSpacing) * row) + offset
  spx = stx + width - 1
  spy = sty + height - 1

  return [(stx,sty),(spx,spy)]

def drawDataGrid(image):
  index = 0
  for box in config["boxes"]:
    position = getBoxPosition(index)

    values = []
    if "values" in box:
      for value in box["values"]:
        values.append(getValue(value))

    if "type" in box and box["type"] == "weathericon":
      boxWeatherIcon(box, position, values)
    elif box['title'] is not None:
      if len(values) > 1:
        boxTitledDual(box, position, values)
      else:
        boxTitledBig(box, position, values)
    else:
      if len(values) > 1:
        boxDual(box, position, values)
      else:
        boxBig(box, position, values)

    index = index + 1

#### Initialisation

# Load trips
try:
  with open("./trips.yaml", "r") as read_file:
    trips = yaml.safe_load(read_file)
except:
  # logging.critical("Settings file missing")
  exit()

# Load in data

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
    dataSources[source["name"]] = json.loads(r.text)
  except Exception as e:
    logging.warning(e)

# Initialise display
inky = InkyAC073TC1A(resolution=(800, 480))
display = Image.new(mode="P", size=(480,800), color=(colour["white"]))
image = ImageDraw.Draw(display)


### Main code

drawCalendar(image)
drawTrips(image)
drawMoth(image)
drawDataGrid(image)

inky.set_image(display.rotate(90, expand=True))
inky.show()
