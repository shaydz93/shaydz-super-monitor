# test_font.py
from PIL import Image, ImageDraw, ImageFont

img = Image.new('RGB', (400, 200), color='white')
d = ImageDraw.Draw(img)

# Make sure the font path is correct and points to an existing font
font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 60)
d.text((10, 10), "Hello ShaydZ", fill="black", font=font)

img.save("test.png")
