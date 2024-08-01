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

inky = InkyAC073TC1A(resolution=(800, 480))
display = Image.new(mode="P", size=(800,480), color=(colour["orange"]))

inky.set_image(display)
inky.show()