#!/usr/bin/env python3

# from inky.auto import auto
from inky.inky_ac073tc1a import Inky as InkyAC073TC1A
from PIL import Image, ImageDraw, ImageFont

colour = {
    "black": 0,
    "white": 1,
    "green": 2,
    "blue": 3,
    "red": 4,
    "yellow": 5,
    "orange": 6
    }

bigFont = ImageFont.truetype("./LeagueSpartan-Medium.ttf", int(44))
smallFont = ImageFont.truetype("./LeagueSpartan-Medium.ttf", int(24))

inky = InkyAC073TC1A(resolution=(800, 480))
display = Image.new(mode="P", size=(480,800), color=(colour["white"]))
image = ImageDraw.Draw(display)

image.rounded_rectangle([(0,0),(159,119)], radius=6, fill=colour["red"], outline=None, width=1)
image.rounded_rectangle([(160,0),(319,119)], radius=6, fill=colour["green"], outline=None, width=1)
image.rounded_rectangle([(320,0),(479,119)], radius=6, fill=colour["blue"], outline=None, width=1)

image.text((80, 60), "Text", colour["black"], font=bigFont, anchor="mm")


inky.set_image(display.rotate(90, expand=True))
inky.show()
