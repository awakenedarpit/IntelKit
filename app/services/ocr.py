from PIL import Image
import pytesseract
def extract_text(path):
    try: return pytesseract.image_to_string(Image.open(path)).strip()
    except Exception: return ''
