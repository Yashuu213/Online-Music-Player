from PIL import Image

# Open the PNG icon
img = Image.open(r"C:\Users\SVI\.gemini\antigravity\brain\21228013-49fd-4aec-9eda-dd32b1d3620c\pikachu_app_icon_1765385374603.png")

# Convert to ICO with multiple sizes
img.save("pikachu_icon.ico", format='ICO', sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)])
print("Icon converted successfully!")
