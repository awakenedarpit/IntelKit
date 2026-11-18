from app.services.ocr import extract_text
async def process(path, extractor):
    text=extract_text(path); return await extractor.analyze('Uploaded image. OCR text:\n'+(text or '[No readable text detected]'), [open(path,'rb').read()])
