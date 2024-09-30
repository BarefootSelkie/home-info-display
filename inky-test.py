#!/usr/bin/env python3

# from inky.auto import auto
from inky.inky_ac073tc1a import Inky as InkyAC073TC1A
from PIL import Image, ImageDraw, ImageFont, ImageOps
import datetime
import yaml
import logging
import requests
import json
import argparse
from jsonpath_ng.ext import parse

# Arguments, Logging, Settings
parser = argparse.ArgumentParser()
parser.add_argument("-d", "--debug", action="store_true", help="Enable debug level logging")
args = parser.parse_args()

if args.debug:
  # If arg -d or --debug passed in endale debug logging
  logging.basicConfig(format="%(asctime)s : %(message)s", filename="log-hid.log", encoding='utf-8', level=logging.DEBUG)
else:
  # Otherwise use warn logging
  logging.basicConfig(format="%(asctime)s : %(message)s", filename="log-hid.log", encoding='utf-8', level=logging.WARN)

# Load config file
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

# Fonts
fontGridSingle = ImageFont.truetype("./ttf/Fredoka-Medium.ttf", int(44))
fontGridDual = ImageFont.truetype("./ttf/Fredoka-Medium.ttf", int(24))
fontGridLabel = ImageFont.truetype("./ttf/Fredoka-Medium.ttf", int(18))

fontCalBg = ImageFont.truetype("./ttf/Fredoka-Medium.ttf", int(64))
fontCalSm = ImageFont.truetype("./ttf/Fredoka-Medium.ttf", int(32))

# Sizing Constants
cellSpacing = 3
padding = 10

# Sizing for calendar
anchorCalendar = (0,0)
widthCalendar = 158
heightCalendar = 158

# Sizing for next up
anchorNextUp = (anchorCalendar[0] + widthCalendar + cellSpacing,0)
widthNextUp = 318
heightNextUp = 158

# Sizing for WhoMe
anchorWhoMe = (0, anchorCalendar[1] + heightCalendar + cellSpacing)
widthWhoMe = 480
heightWhoMe = 118

# Sizing for data grid
anchorDataGrid = (0, anchorWhoMe[1] + heightWhoMe + cellSpacing)
rowWidth = 3
boxWidth = 158
boxHeight = 118

# Sizing for Moth
anchorMoth = (0,anchorDataGrid[1] + ((boxHeight + cellSpacing) * 4))
widthMoth = 480
heightMoth = 31

### State variables ###

dataSources = {}
dataWhoMe = {}
dataTrips = {}


### Converter functions ###

converters = {
  "windDirection": lambda degrees: toCompassPoint(float(degrees)),
  "time": lambda time: time[:5]
}

### Functions ###

# Data requests
 
# For each entry in sources make api request and put returned json in dataSources
def requestSources():
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

def requestWhoMe():
  try:
    r = requests.get(config["whome"]["server"])
    print(r.text)
    dataWhoMe = json.loads(r.text)
  except Exception as e:
    logging.warning(e)

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

# Draw the calendar square in top left of screen
def drawCalendar(image):
  dateNumber = datetime.date.today().strftime('%d')
  dateDay = datetime.date.today().strftime('%a')
  dateMonth = datetime.date.today().strftime('%b')

  image.rounded_rectangle([anchorCalendar,(anchorCalendar[0] + widthCalendar, anchorCalendar[1] + heightCalendar)], radius=12, fill=None, outline=colour["red"], width=4)
  image.rounded_rectangle([anchorCalendar,(anchorCalendar[0] + widthCalendar, anchorCalendar[1] + 42)], radius=12, fill=colour["red"], outline=colour["red"], width=4, corners=(True, True, False, False))
  image.text(((anchorCalendar[0] + (widthCalendar // 2)), anchorCalendar[0] + 21), dateMonth, colour["white"], font=fontCalSm, anchor="mm")
  image.text(((anchorCalendar[0] + (widthCalendar // 2)), anchorCalendar[0] + 80), dateNumber, colour["black"], font=fontCalBg, anchor="mm")
  image.text(((anchorCalendar[0] + (widthCalendar // 2)),anchorCalendar[0] + 137), dateDay, colour["black"], font=fontCalSm, anchor="mm")

def drawNextUp(image):
  # Draw the next trip box next to the current date
  image.rounded_rectangle([anchorNextUp,(anchorNextUp[0] + widthNextUp,anchorNextUp[1] + heightNextUp)], radius=12, fill=None, outline=colour["black"], width=4)

  # Get trips that haven't happened yet
  upcomingTrips = []
  for trip in dataTrips["trips"]:
    if datetime.date.fromisoformat(str(trip["date"])) > datetime.date.today():
      upcomingTrips.append(trip)

  # Sort the list
  upcomingTrips.sort(key=lambda trip: trip["date"], reverse=False)

  if len(upcomingTrips) > 0:
    nextTrip = upcomingTrips[0]
    nextTripDate = datetime.date.fromisoformat(str(nextTrip["date"]))
    todayDate = datetime.date.today()
    daysRemaining = (nextTripDate - todayDate).days

    lines = wrap(image, nextTrip["destination"], (widthNextUp - (padding*2)), fontCalSm)

    image.text((anchorNextUp[0] + padding, anchorNextUp[1] + padding + 16), lines[0], colour["black"], font=fontCalSm, anchor="lm")
    if len(lines) > 1:
      image.text((anchorNextUp[0] + padding, anchorNextUp[1] + padding + 32 + 16), lines[1], colour["black"], font=fontCalSm, anchor="lm")
    image.text((anchorNextUp[0] + (widthNextUp // 2), anchorNextUp[1] + padding + 32 + 32 + (64/2)), str(daysRemaining) + " days", colour["black"], font=fontCalBg, anchor="mm")

def drawMoth(image):
  # Draw a text box below the date and next trip
  messageOfHour = "So long and thanks for all the fish"
  image.rounded_rectangle([anchorMoth,(anchorMoth[0]+widthMoth,anchorMoth[1]+heightMoth)], radius=12, fill=None, outline=colour["blue"], width=4)
  image.text((anchorMoth[0] + (widthMoth//2), anchorMoth[1] + (heightMoth//2)), messageOfHour, colour["blue"], font=fontGridLabel, anchor="mm")

# edge case boxes
def boxWeatherIcon(box, position, values):
  fileIcon = "./png/" + values[0] + ".png"
  iconWeather = Image.open(fileIcon)
  iconWeather = ImageOps.invert(iconWeather)
  image.rounded_rectangle(position, radius=12, fill=None, outline=colour["red"], width=4)
  image.bitmap((((boxWidth / 2) - 48) + position[0][0], ((boxHeight / 2) - 48) + position[0][1]), iconWeather)

# standard boxes
def boxTitledBig(box, position, values):
  image.rounded_rectangle(position, radius=12, fill=None, outline=colour["black"], width=4)
  image.text((padding +  position[0][0], padding + position[0][1]), str(box['title']), colour["black"], font=fontGridLabel, anchor="la")
  image.text(((boxWidth / 2) +  position[0][0], (boxHeight / 2) + position[0][1]), values[0], colour["black"], font=fontGridSingle, anchor="mm")

def boxBig(box, position, values):
  image.rounded_rectangle(position, radius=12, fill=None, outline=colour["red"], width=4)
  image.text(((boxWidth / 2) +  position[0][0], (boxHeight / 2) + position[0][1]), values[0], colour["black"], font=fontGridSingle, anchor="mm")

def boxTitledDual(box, position, values):
  image.rounded_rectangle(position, radius=12, fill=None, outline=colour["blue"], width=4)
  image.text((padding +  position[0][0], padding + position[0][1]), str(box['title']), colour["black"], font=fontGridLabel, anchor="la")
  image.text(((boxWidth / 2) +  position[0][0], (boxHeight / 2) + position[0][1]), values[0], colour["black"], font=fontGridDual, anchor="mm")
  image.text(((boxWidth / 2) +  position[0][0], (3*boxHeight / 4) + position[0][1]), values[1], colour["black"], font=fontGridDual, anchor="mm")

def boxDual(box, position, values):
  image.rounded_rectangle(position, radius=12, fill=None, outline=colour["green"], width=4)
  image.text(((boxWidth / 2) +  position[0][0], (boxHeight / 4) + position[0][1]), values[0], colour["black"], font=fontGridDual, anchor="mm")
  image.text(((boxWidth / 2) +  position[0][0], (3*boxHeight / 4) + position[0][1]), values[1], colour["black"], font=fontGridDual, anchor="mm")

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
  stx = ((boxWidth + cellSpacing) * col) + anchorDataGrid[0]
  sty = ((boxHeight + cellSpacing) * row) + anchorDataGrid[1]
  spx = stx + boxWidth - 1
  spy = sty + boxHeight - 1

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

def drawWhoMe(image):
  image.rounded_rectangle([anchorWhoMe,(anchorWhoMe[0] + widthWhoMe, anchorWhoMe[1] + heightWhoMe)], radius=12, fill=None, outline=colour["blue"], width=4)
  print(dataWhoMe)
  fronterName = dataWhoMe["members"][0]["name"]

  image.text((anchorWhoMe[0] + (widthWhoMe // 2), anchorWhoMe[1] + (heightWhoMe // 2)), fronterName, colour["blue"], font=fontCalBg, anchor="mm")

#### Initialisation

# Load trips
try:
  with open("./trips.yaml", "r") as read_file:
    dataTrips = yaml.safe_load(read_file)
except:
  logging.critical("Trips file missing")
  exit()

# Initialise display
inky = InkyAC073TC1A(resolution=(800, 480))
display = Image.new(mode="P", size=(480,800), color=(colour["white"]))
image = ImageDraw.Draw(display)


### Main code

requestSources()
requestWhoMe()
drawCalendar(image)
drawNextUp(image)
drawMoth(image)
drawWhoMe(image)
drawDataGrid(image)

inky.set_image(display.rotate(90, expand=True))
inky.show()
