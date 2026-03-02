from PIL import Image

try:
    img = Image.open("med.avif")
    img.show()
    print("✅ med.avif loaded successfully!")
except Exception as e:
    print("❌ med.avif failed:", e)

try:
    img = Image.open("med1.jpeg")
    img.show()
    print("✅ med1.jpeg loaded successfully!")
except Exception as e:
    print("❌ med1.jpeg failed:", e)
