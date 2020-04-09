from PIL import Image
import pytesseract
import os

import pdftables

import path


def ocrInvoices():
    myPath = path.getPath()

    for val in os.listdir(myPath):
        if val.endswith(".png") or val.endswith(".jpg"):             #OCRowanie plików .png
            picPath = myPath + '/' + val
            txtPath = picPath[:-4] + ".txt"
            img = Image.open(picPath)
            text = pytesseract.image_to_string(img, lang='pol')
            faktura = open(txtPath, "w")
            faktura.write(text)
            faktura.close()
        elif val.endswith(".pdf"):                                  #OCRowanie plików .pdf
            pdfPath = myPath + '/' + val
            txtPath = pdfPath[:-4] + ".txt"
            imgPath = pdfPath[:-4] + ".jpg"
            xmlPath = pdfPath[:-4] + ".xml"

            c = pdftables.Client("baq0339zc5zj")
            c.xml(pdfPath, xmlPath)

            '''pdf2jpeg(pdfPath,imgPath)                               #Tworzenie grafiki z dokumentu pdf
            img = Image.open(imgPath)                               #OCRowanie stworzonej grafiki
            text = pytesseract.image_to_string(img, lang='pol')
            faktura = open(txtPath, "w")
            faktura.write(text)
            faktura.close()'''
        print("done")