import os
import sys
from PIL import Image, ImageDraw, ImageFilter

def create_ecg():
    # Grid dimensions: 800 x 400
    img = Image.new("RGB", (800, 400), "#FFF3F3")
    draw = ImageDraw.Draw(img)
    
    # Draw ECG Grid (minor lines every 5px, major lines every 25px)
    for x in range(0, 800, 5):
        color = "#FFCCCC" if x % 25 == 0 else "#FFEAE8"
        width = 2 if x % 25 == 0 else 1
        draw.line([(x, 0), (x, 400)], fill=color, width=width)
    for y in range(0, 400, 5):
        color = "#FFCCCC" if y % 25 == 0 else "#FFEAE8"
        width = 2 if y % 25 == 0 else 1
        draw.line([(0, y), (800, y)], fill=color, width=width)
        
    # Draw ECG Rhythm line (Normal Sinus Rhythm)
    points = []
    # Heart rate cycle width ~ 100px
    # Baseline at y = 200
    base_y = 200
    for x in range(0, 800):
        cycle_x = x % 100
        y = base_y
        if cycle_x < 20:
            pass # Isoelectric
        elif cycle_x < 30:
            # P wave
            dx = (cycle_x - 20) / 10
            y = base_y - 15 * (4 * dx * (1 - dx)) # quadratic bump
        elif cycle_x < 40:
            pass # PR segment
        elif cycle_x < 42:
            # Q wave
            y = base_y + 10 * ((cycle_x - 40) / 2)
        elif cycle_x < 46:
            # R wave (sharp peak)
            dx = (cycle_x - 42) / 4
            y = base_y + 10 - 120 * dx
        elif cycle_x < 50:
            # S wave
            dx = (cycle_x - 46) / 4
            y = base_y - 110 + 130 * dx
        elif cycle_x < 60:
            pass # ST segment
        elif cycle_x < 75:
            # T wave
            dx = (cycle_x - 60) / 15
            y = base_y - 30 * (4 * dx * (1 - dx))
        else:
            pass # Isoelectric
        points.append((x, y))
        
    # Draw the line
    draw.line(points, fill="#0F172A", width=3)
    return img

def create_xray(has_pneumonia=False):
    # Grayscale image: 600 x 600
    img = Image.new("RGB", (600, 600), "#111111")
    draw = ImageDraw.Draw(img)
    
    # Draw chest silhouette (shoulders & thorax)
    # Lungs: two dark ellipses
    # Left Lung
    draw.ellipse([80, 150, 260, 500], fill="#080808", outline="#444444", width=2)
    # Right Lung
    draw.ellipse([340, 150, 520, 500], fill="#080808", outline="#444444", width=2)
    
    # Spine (center column)
    draw.rectangle([280, 100, 320, 550], fill="#333333")
    for y in range(120, 540, 20):
        draw.line([(280, y), (320, y)], fill="#222222", width=2)
        
    # Rib cage (horizontal curved lines across lungs)
    for y in range(170, 480, 30):
        # Left ribs
        draw.arc([60, y-10, 300, y+30], start=90, end=270, fill="#252525", width=6)
        # Right ribs
        draw.arc([300, y-10, 540, y+30], start=270, end=90, fill="#252525", width=6)
        
    # Heart shadow (white blur in the middle, slightly to the left)
    heart_points = [(300, 300), (220, 380), (300, 440), (340, 380)]
    draw.polygon(heart_points, fill="#3A3A3A")
    draw.ellipse([240, 320, 350, 420], fill="#3A3A3A")
    
    # Diaphragm (bottom curves)
    draw.chord([50, 450, 290, 550], start=0, end=180, fill="#1F1F1F")
    draw.chord([310, 450, 550, 550], start=0, end=180, fill="#1F1F1F")
    
    # Blur the image slightly to make it look like a real radiograph
    img = img.filter(ImageFilter.GaussianBlur(3))
    
    # If pneumonia, overlay white patchy opacity in left lung (right side of image)
    if has_pneumonia:
        pneumonia_overlay = Image.new("RGBA", (600, 600), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(pneumonia_overlay)
        # Draw soft white spots in left lung (which is on the right side of the screen)
        # Infiltrates in lower zone (x: 380-480, y: 350-450)
        overlay_draw.ellipse([380, 340, 480, 440], fill=(220, 220, 220, 100))
        overlay_draw.ellipse([360, 380, 440, 460], fill=(200, 200, 200, 80))
        overlay_draw.ellipse([410, 370, 490, 430], fill=(240, 240, 240, 120))
        
        # Blur the pneumonia patch
        pneumonia_overlay = pneumonia_overlay.filter(ImageFilter.GaussianBlur(15))
        img = Image.alpha_composite(img.convert("RGBA"), pneumonia_overlay).convert("RGB")
        
    # Add clinical labels
    draw_label = ImageDraw.Draw(img)
    label_text = "PNEUMONIA SUSPECTED" if has_pneumonia else "CHEST RADIOGRAPH NORMAL"
    draw_label.text((20, 20), "Hospital AI Monitor", fill="#888888")
    draw_label.text((20, 40), label_text, fill="#AAAAAA")
    return img

def main():
    dest_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "test_medical_data")
    os.makedirs(dest_dir, exist_ok=True)
    print(f"Generating realistic clinical images in: {dest_dir}")

    # Generate ECG
    ecg = create_ecg()
    ecg.save(os.path.join(dest_dir, "sample_ecg.png"))
    print("Generated: sample_ecg.png")

    # Generate Normal Chest X-Ray
    normal_xray = create_xray(has_pneumonia=False)
    normal_xray.save(os.path.join(dest_dir, "normal_chest_xray.jpg"))
    print("Generated: normal_chest_xray.jpg")

    # Generate Pneumonia Chest X-Ray
    pneumonia_xray = create_xray(has_pneumonia=True)
    pneumonia_xray.save(os.path.join(dest_dir, "pneumonia_chest_xray.jpg"))
    print("Generated: pneumonia_chest_xray.jpg")

    print("\nAll clinical test images successfully generated locally!")

if __name__ == "__main__":
    main()
