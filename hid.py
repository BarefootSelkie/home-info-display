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
import time
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

fontWhoMeName = ImageFont.truetype("./ttf/Fredoka-Medium.ttf", int(28))
fontWhoMeTime = ImageFont.truetype("./ttf/Fredoka-Medium.ttf", int(32))
fontWhoMeSymbol = ImageFont.truetype("./ttf/NotoSansSymbols.ttf", int(28))
fontWhoMeSymbol2 = ImageFont.truetype("./ttf/NotoSansSymbols2.ttf", int(28))


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

# Sizing for data grid
anchorDataGrid = (0, anchorCalendar[1] + heightCalendar + cellSpacing)
rowsDataGrid = 5
rowWidth = 3
boxWidth = 158
boxHeight = 118

# Sizing for Moth
anchorMoth = (0, anchorDataGrid[1] + ((boxHeight + cellSpacing) * rowsDataGrid))
widthMoth = 480
heightMoth = 31

### State variables ###

dataSources = {}
dataNextUp = {}
dataWhoMe = {}


### Converter functions ###

converters = {
  "windDirection": lambda degrees: toCompassPoint(float(degrees)),
  "time": lambda time: time[:5],
  "hhmm": lambda date: datetime.datetime.fromisoformat(date).astimezone().strftime("%H:%M")
}

### Functions ###

# Data requests
 
# For each entry in sources make api request and put returned json in dataSources
def requestAllSources():
  for source in config["sources"]:
    dataSources[source["name"]] = requestSource(source)

def requestSource(source):
  logging.debug("Requesting data source " + source["name"])

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
    sourceData = json.loads(r.text)
  except Exception as e:
    logging.warning(e)
    return None

  return sourceData

def requestNextUp():
  global dataNextUp
  start = datetime.datetime.now(tz = datetime.timezone.utc) - datetime.timedelta(weeks=4)
  end = datetime.datetime.now(tz = datetime.timezone.utc) + datetime.timedelta(weeks=52)
  queryurl = config["nextup"]["url"] + "?start=" + start.strftime("%Y-%m-%dT%H:%M:%S.000Z") + "&end=" + end.strftime("%Y-%m-%dT%H:%M:%S.000Z")

  try:
    r = requests.get(queryurl, headers={"authorization": "Bearer " + config["nextup"]["apikey"], "content-type": "application/json" })
    dataNextUp = json.loads(r.text)
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
  nextUp = []
  for event in dataNextUp:
    if datetime.date.fromisoformat(str(event["start"]["date"])) > datetime.date.today():
      nextUp.append(event)

  # Sort the list
  nextUp.sort(key=lambda event: event["start"]["date"], reverse=False)

  if len(nextUp) > 0:
    # If there are events in the list get the first one
    nextEvent = nextUp[0]

    # extract data into indivdual varibles
    nextEventDate = datetime.date.fromisoformat(str(nextEvent["start"]["date"]))
    nextEventName = nextEvent["summary"]
    todayDate = datetime.date.today()

    # work out how many days until the next event
    daysRemaining = (nextEventDate - todayDate).days

    # wordwarp the event name gives back a list
    lines = wrap(image, nextEventName, (widthNextUp - (padding*2)), fontCalSm)

    # draw the first line onto the display
    image.text((anchorNextUp[0] + padding, anchorNextUp[1] + padding + 16), lines[0], colour["black"], font=fontCalSm, anchor="lm")
    
    # if there is more than one line draw the second, but end there as only 2 lines available
    if len(lines) > 1:
      image.text((anchorNextUp[0] + padding, anchorNextUp[1] + padding + 32 + 16), lines[1], colour["black"], font=fontCalSm, anchor="lm")
    
    # draw the days remaining below the text
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

def boxWhoMe(box, position, values):
  image.rounded_rectangle(position, radius=12, fill=None, outline=colour["blue"], width=4)

  if len(dataSources["whome"]["members"]) > 0:
    member = dataSources["whome"]["members"][0]
    image.text(((boxWidth / 2) +  position[0][0], padding + position[0][1]), str(member["name"]), colour["black"], font=fontWhoMeName, anchor="ma")

    image.text(((boxWidth / 2) +  position[0][0], (boxHeight / 2) + position[0][1]), converters["hhmm"](member["lastIn"]), colour["black"], font=fontWhoMeTime, anchor="mm")

    if member["cardSuit"]:
      image.text(((boxWidth / 4) +  position[0][0], (3*boxHeight / 4) + position[0][1]), member["cardSuit"][0], colour["black"], font=fontWhoMeSymbol2, anchor="mm")
    
    if member["elementName"]:
      image.text(((3*boxWidth / 4) +  position[0][0], (3*boxHeight / 4) + position[0][1]), member["elementName"], colour["black"], font=fontWhoMeSymbol, anchor="mm")

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

  # Check if the data was retreived correctly
  if dataSources[value["source"]] is None:
    return "Error"

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

    if "type" in box:
      match box["type"]:
        case "weathericon":
            boxWeatherIcon(box, position, values)
        case "whome":
            boxWhoMe(None, position, None)
        case _:
          if box['title'] is not None:
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

# Get data
requestAllSources()
requestNextUp()

# Initialise display
inky = InkyAC073TC1A(resolution=(800, 480))
display = Image.new(mode="P", size=(480,800), color=(colour["white"]))
image = ImageDraw.Draw(display)

refreshDisplay = True
minutePast = 0

### Main code
while True:
  if minutePast != time.localtime()[4]:
    minutePast = time.localtime()[4]

    # iterate though srouces to see which need update
    for source in config["sources"]:
      # only update ones that need update
      if "updateInterval" not in source:
        continue

      if type(source["updateInterval"]) is int and ( time.localtime()[4] % source["updateInterval"] ) == 0:
        # update this source every N minutes
        newData = requestSource(source)
        if newData != dataSources[source["name"]]:
          logging.debug("Data source " + source["name"] + " changed, triggering redraw")
          dataSources[source["name"]] = newData
          refreshDisplay = True

      elif type(source["updateInterval"]) is list and time.localtime()[4] in source["updateInterval"]:
        newData = requestSource(source)
        if newData != dataSources[source["name"]]:
          logging.debug("Data source " + source["name"] + " changed, triggering redraw")
          dataSources[source["name"]] = newData
          refreshDisplay = True

      else:
        continue
    
    # update display if needed
    if refreshDisplay:
      display = Image.new(mode="P", size=(480,800), color=(colour["white"]))
      image = ImageDraw.Draw(display)

      drawCalendar(image)
      drawNextUp(image)
      drawMoth(image)
      drawDataGrid(image)

      inky.set_image(display.rotate(90, expand=True))
      inky.show()

      refreshDisplay = False

    # Wait for a while
    time.sleep(6)
