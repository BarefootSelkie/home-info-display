#!/usr/bin/env python3

# from inky.auto import auto
from inky.inky_ac073tc1a import Inky as InkyAC073TC1A
from PIL import Image, ImageDraw, ImageFont

colour = {
    "black": (28,24,28),
    "white": (255,255,255),
    "red": (205,36,37),
    "blue": (30,29,174),
    "green": (29,173,35),
    "yellow": (231,222,35),
    "orange": (216,123,36)
    }

inky = InkyAC073TC1A(resolution=(800, 480))
display = Image.new(mode="RGB", size=(800,480), color=(colour["red"]))

inky.set_image(display)
inky.show()