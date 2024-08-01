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

bigFont = ImageFont.truetype("./ttf/LeagueSpartan-Medium.ttf", int(44))
smallFont = ImageFont.truetype("./ttf/LeagueSpartan-Medium.ttf", int(24))

inky = InkyAC073TC1A(resolution=(800, 480))
display = Image.new(mode="P", size=(480,800), color=(colour["white"]))
image = ImageDraw.Draw(display)

image.rounded_rectangle([(0,0),(157,117)], radius=12, fill=None, outline=colour["black"], width=4)
image.rounded_rectangle([(161,0),(479,117)], radius=12, fill=None, outline=colour["black"], width=4)

width = 158
height = 118
padding = 3
offset = 121

for row in range(3):
    for col in range(2): 
        stx = (width + padding) * col
        sty = ((height + padding) * row) + offset
        spx = stx + width - 1
        spy = sty + height - 1 

        image.rounded_rectangle([(stx,sty),(spx,spy)], radius=12, fill=None, outline=colour["black"], width=4)
        image.text(((width / 2) +  stx, (height / 2) + sty), str(row) + "-" + str(col), colour["black"], font=bigFont, anchor="mm")

image.text((80, 60), "O", colour["black"], font=bigFont, anchor="mm")


inky.set_image(display.rotate(90, expand=True))
inky.show()
