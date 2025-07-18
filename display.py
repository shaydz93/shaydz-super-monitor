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
        try:
            self.epd.init()
            image = Image.new('1', (self.height, self.width), 255)
            draw = ImageDraw.Draw(image)
            y = 0
            for line in lines:
                if y + 14 > self.width:  # Prevent text from going off display
                    break
                draw.text((0, y), str(line), font=self.font, fill=0)
                y += 14
            self.epd.display(self.epd.getbuffer(image))
        except Exception as e:
            print(f"[EPD] Display error: {e}")

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
        bbox = draw.textbbox((0, 0), shaydz_text, font=font_large)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = (image.width - w) // 2
        draw.text((x, 15), shaydz_text, font=font_large, fill=0)
        sub = "Super Monitor"
        bbox2 = draw.textbbox((0, 0), sub, font=font_small)
        w2, h2 = bbox2[2] - bbox2[0], bbox2[3] - bbox2[1]
        draw.text(((image.width - w2) // 2, 55), sub, font=font_small, fill=0)
        self.epd.display(self.epd.getbuffer(image))

    def sleep(self):
        if self.epd:
            try:
                self.epd.sleep()
            except Exception as e:
                print(f"[EPD] Sleep error: {e}")

    def __del__(self):
        """Clean up display when object is destroyed"""
        try:
            self.sleep()
        except Exception:
            pass
