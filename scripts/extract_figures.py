import os
import glob
from PIL import Image

out_dir = '/var/www/oge_physics/uploads/tasks'
os.makedirs(out_dir, exist_ok=True)

def get_page_img(p):
    matches = glob.glob(f'/tmp/page_{p}-*.png')
    if not matches:
        raise FileNotFoundError(f'No page image for {p}')
    return Image.open(matches[0])

# Page 23 -> Рис. 14: graph of s(t)
im23 = get_page_img(23)
w, h = im23.size
print(f"Page 23 size: {w}x{h}")
box_ris14 = (int(w * 0.04), int(h * 0.50), int(w * 0.45), int(h * 0.72))
crop14 = im23.crop(box_ris14)
crop14.save(os.path.join(out_dir, 'peryshkin_ris14.png'))

# Page 55 -> Рис. 56: U-tube with kerosene, mercury, water
im55 = get_page_img(55)
w55, h55 = im55.size
print(f"Page 55 size: {w55}x{h55}")
box_ris56 = (int(w55 * 0.70), int(h55 * 0.30), int(w55 * 0.95), int(h55 * 0.55))
crop56 = im55.crop(box_ris56)
crop56.save(os.path.join(out_dir, 'peryshkin_ris56.png'))

# Page 112 -> Рис. 104: I(U) graph
im112 = get_page_img(112)
w112, h112 = im112.size
print(f"Page 112 size: {w112}x{h112}")
box_ris104 = (int(w112 * 0.22), int(h112 * 0.17), int(w112 * 0.78), int(h112 * 0.42))
crop104 = im112.crop(box_ris104)
crop104.save(os.path.join(out_dir, 'peryshkin_ris104.png'))

# Page 117 -> Рис. 106: resistor circuit
im117 = get_page_img(117)
w117, h117 = im117.size
print(f"Page 117 size: {w117}x{h117}")
box_ris106 = (int(w117 * 0.08), int(h117 * 0.63), int(w117 * 0.40), int(h117 * 0.88))
crop106 = im117.crop(box_ris106)
crop106.save(os.path.join(out_dir, 'peryshkin_ris106.png'))

# Page 69 -> Рис. 71: lever with weights
im69 = get_page_img(69)
w69, h69 = im69.size
print(f"Page 69 size: {w69}x{h69}")
box_ris71 = (int(w69 * 0.05), int(h69 * 0.02), int(w69 * 0.45), int(h69 * 0.17))
crop71 = im69.crop(box_ris71)
crop71.save(os.path.join(out_dir, 'peryshkin_ris71.png'))

print("All figures cropped successfully!")
for f in os.listdir(out_dir):
    print(" ", f, os.path.getsize(os.path.join(out_dir, f)), "bytes")
