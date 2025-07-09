import sys
import time
import os

try:
    sys.path.append('/opt/e-Paper/RaspberryPi_JetsonNano/python/lib')
    from waveshare_epd import epd2in13_V3
    EPD_AVAILABLE = True
except Exception as e:
    print("E-paper library not found or failed to load:", e)
    EPD_AVAILABLE = False

from PIL import Image, ImageDraw, ImageFont

class EPDDisplay:
    def __init__(self):
        if EPD_AVAILABLE:
            self.epd = epd2in13_V3.EPD()
            self.width = self.epd.height  # 122
            self.height = self.epd.width  # 250
        else:
            self.epd = None
            self.width = 122
            self.height = 250
        try:
            self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 14)
        except Exception:
            self.font = ImageFont.load_default()
        self.clear()

    def clear(self):
        if self.epd:
            self.epd.init()
            self.epd.Clear(0xFF)

    def display_text(self, lines):
        if not self.epd:
            print("[EPD] Simulated Display:", lines)
            return
        self.epd.init()
        image = Image.new('1', (self.height, self.width), 255)
        draw = ImageDraw.Draw(image)
        y = 0
        for line in lines:
            draw.text((0, y), line, font=self.font, fill=0)
            y += 14
        self.epd.display(self.epd.getbuffer(image))

    def show_shaydz_welcome(self):
        if not self.epd:
            print("[EPD] Simulated Welcome Screen: S h a y d Z")
            return
        image = Image.new('1', (self.height, self.width), 255)
        draw = ImageDraw.Draw(image)
        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 22)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 14)
        except Exception:
            font_large = font_small = ImageFont.load_default()
        shaydz_text = "S h a y d Z"
        w, h = draw.textsize(shaydz_text, font=font_large)
        x = (image.width - w) // 2
        draw.text((x, 15), shaydz_text, font=font_large, fill=0)
        sub = "Super Monitor"
        w2, h2 = draw.textsize(sub, font=font_small)
        draw.text(((image.width - w2) // 2, 55), sub, font=font_small, fill=0)
        self.epd.display(self.epd.getbuffer(image))

    def sleep(self):
        if self.epd:
            self.epd.sleep()
