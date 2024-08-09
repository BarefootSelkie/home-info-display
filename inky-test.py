#!/usr/bin/env python3

# from inky.auto import auto
from inky.inky_ac073tc1a import Inky as InkyAC073TC1A
from PIL import Image, ImageDraw, ImageFont
import datetime
import yaml

# Load trips
try:
    with open("./trips.yaml", "r") as read_file:
        trips = yaml.safe_load(read_file)
except:
    # logging.critical("Settings file missing")
    exit()

colour = {
    "black": 0,
    "white": 1,
    "green": 2,
    "blue": 3,
    "red": 4,
    "yellow": 5,
    "orange": 6
    }

bigFont = ImageFont.truetype("./ttf/Fredoka-Medium.ttf", int(44))
smallFont = ImageFont.truetype("./ttf/Fredoka-Medium.ttf", int(24))

fontCalBg = ImageFont.truetype("./ttf/Fredoka-Medium.ttf", int(64))
fontCalSm = ImageFont.truetype("./ttf/Fredoka-Medium.ttf", int(32))

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
    if datetime.date.fromisoformat(str(trip["date"])) < datetime.date.today():
        upcomingTrips.append(trip)

# Sort the list
upcomingTrips.sort(key=lambda trip: trip["date"], reverse=True)

if len(upcomingTrips) > 0:
    nextTrip = upcomingTrips[0]
    image.text((79,79), dateNumber, colour["black"], font=fontCalBg, anchor="mm")
    image.text((79,136), dateDay, colour["black"], font=fontCalSm, anchor="mm")





width = 158
height = 118
padding = 3
offset = 161

for row in range(4):
    for col in range(3): 
        stx = (width + padding) * col
        sty = ((height + padding) * row) + offset
        spx = stx + width - 1
        spy = sty + height - 1 

        image.rounded_rectangle([(stx,sty),(spx,spy)], radius=12, fill=None, outline=colour["black"], width=4)
        image.text(((width / 2) +  stx, (height / 2) + sty), str(row) + "-" + str(col), colour["black"], font=bigFont, anchor="mm")
 
inky.set_image(display.rotate(90, expand=True))
inky.show()
