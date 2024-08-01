#!/usr/bin/env python3

# from inky.auto import auto
from inky.inky_ac073tc1a import Inky as InkyAC073TC1A
from PIL import Image, ImageDraw, ImageFont

inky = InkyAC073TC1A(resolution=(800, 480))
display = Image.new(mode="RGB", size=(800,480), color=(255,255,255))

inky.set_image(display)
inky.show()