from PIL import Image, ImageDraw, ImageFont
import os

def make_shaydz_logo_pngs():
    font_path = os.path.join("C:/Windows/Fonts", "arial.ttf")
    shaydz_text = "S   h   a   y   d   Z"
    sub = "Super Monitor"
    colors = [
        ("black", "shaydz_logo.png"),
        ("#00c000", "shaydz_logo_green.png"),
        ("#c00000", "shaydz_logo_red.png")
    ]

    # Ensure the 'static' directory exists
    os.makedirs('static', exist_ok=True)

    for color, name in colors:
        img = Image.new('RGB', (600, 120), color='white')
        draw = ImageDraw.Draw(img)

        font = ImageFont.truetype(font_path, 60)
        font_small = ImageFont.truetype(font_path, 28)

        # Calculate text width using textbbox (new method)
        bbox_main = draw.textbbox((0, 0), shaydz_text, font=font)
        w_main = bbox_main[2] - bbox_main[0]

        draw.text(
            ((600 - w_main) // 2, 10),
            shaydz_text, fill=color, font=font
        )

        bbox_sub = draw.textbbox((0, 0), sub, font=font_small)
        w_sub = bbox_sub[2] - bbox_sub[0]

        draw.text(
            ((600 - w_sub) // 2, 80),
            sub, fill=color, font=font_small
        )

        img.save(f'static/{name}')
        print(f"Saved static/{name}")

if __name__ == "__main__":
    make_shaydz_logo_pngs()
