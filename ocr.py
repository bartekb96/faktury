from PIL import Image
import pytesseract
import os
import path

def ocrInvoices():
    myPath = path.getPath()

    for val in os.listdir(myPath):
        if val.endswith(".png"):
            picPath = myPath + '/' + val
            txtPath = picPath[:-4] + ".txt"
            img = Image.open(picPath)
            text = pytesseract.image_to_string(img, lang='pol')
            faktura = open(txtPath, "w")
            faktura.write(text)
            faktura.close()

    print("done")