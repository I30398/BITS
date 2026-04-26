"""
Convert terminal output text files to PNG images
Requires: pip install Pillow
"""

from PIL import Image, ImageDraw, ImageFont
import os

# Configuration
BG_COLOR = (30, 30, 30)       # Dark background
TEXT_COLOR = (220, 220, 220)  # Light gray text
PADDING = 20
LINE_HEIGHT = 18
FONT_SIZE = 14

def text_to_image(text_file, output_png):
    """Convert a text file to a PNG image"""

    # Read text content
    with open(text_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Try to use a monospace font
    try:
        font = ImageFont.truetype("consola.ttf", FONT_SIZE)  # Windows
    except:
        try:
            font = ImageFont.truetype("DejaVuSansMono.ttf", FONT_SIZE)  # Linux
        except:
            font = ImageFont.load_default()

    # Calculate image size
    max_width = max(len(line) for line in lines) * 8 + PADDING * 2
    height = len(lines) * LINE_HEIGHT + PADDING * 2

    # Create image
    img = Image.new('RGB', (max_width, height), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Draw text
    y = PADDING
    for line in lines:
        line = line.rstrip('\n')

        # Color coding for different log types
        if '[SERVER]' in line:
            color = (100, 200, 100)  # Green for server
        elif '[DME]' in line:
            color = (100, 180, 255)  # Blue for DME
        elif '===' in line:
            color = (255, 200, 100)  # Yellow for section headers
        elif 'ERROR' in line:
            color = (255, 100, 100)  # Red for errors
        else:
            color = TEXT_COLOR

        draw.text((PADDING, y), line, font=font, fill=color)
        y += LINE_HEIGHT

    # Save image
    img.save(output_png)
    print(f"Created: {output_png}")

def main():
    # Get all text files in current directory
    script_dir = os.path.dirname(os.path.abspath(__file__))

    txt_files = [
        '1_file_server_started.txt',
        '2_node2_joel_started.txt',
        '3_node1_lucy_started.txt',
        '4_joel_posts_dme_in_action.txt',
        '5_both_users_posting.txt',
        '6_view_chat_history.txt'
    ]

    for txt_file in txt_files:
        txt_path = os.path.join(script_dir, txt_file)
        if os.path.exists(txt_path):
            png_file = txt_file.replace('.txt', '.png')
            png_path = os.path.join(script_dir, png_file)
            text_to_image(txt_path, png_path)
        else:
            print(f"Not found: {txt_file}")

if __name__ == "__main__":
    main()
