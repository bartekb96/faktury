import re
import cv2
import numpy as np
import pytesseract
from pytesseract import Output
from matplotlib import pyplot as plt
import path
import os
import ghostscript
import locale

#-------------------------------TESSERACT CONFIGURATION----------------------------------
#config = r'--oem 3 --psm 6'
config1 = r'--oem 3 --psm 1'         #to jest spoko do szukania numeru faktury i troszke do nipów ale reszta słabo
config2 = r'--oem 3 --psm 6'

#-----------------------------------------------------------------------------------------
#--------------------------------IMAGE PREPROCESSING--------------------------------------
#-----------------------------------------------------------------------------------------
# get grayscale image
def get_grayscale(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# noise removal
def remove_noise(image):
    return cv2.medianBlur(image, 5)

# thresholding
def thresholding(image):
    return cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

# dilation
def dilate(image):
    kernel = np.ones((5, 5), np.uint8)
    return cv2.dilate(image, kernel, iterations=1)

# erosion
def erode(image):
    kernel = np.ones((5, 5), np.uint8)
    return cv2.erode(image, kernel, iterations=1)

# opening - erosion followed by dilation
def opening(image):
    kernel = np.ones((5, 5), np.uint8)
    return cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)

# canny edge detection
def canny(image):
    return cv2.Canny(image, 100, 200)

# skew correction
def deskew(image):
    coords = np.column_stack(np.where(image > 0))
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return rotated

# template matching
def match_template(image, template):
    return cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)


#-----------------------------------------------------------------------------------------
#-------------------------------PDF TO JPEG CONVERSION------------------------------------
#-----------------------------------------------------------------------------------------
def pdf2jpeg(pdf_input_path, jpeg_output_path):
    args = ["pef2jpeg", "-dNOPAUSE", "-sDEVICE=jpeg", "-r144", "-sOutputFile=" + jpeg_output_path, pdf_input_path]
    encoding = locale.getpreferredencoding()
    args = [a.encode(encoding) for a in args]
    ghostscript.Ghostscript(*args)


#-----------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------
def ocrToGetNumber():
    myPath = path.getPath()

    for val in os.listdir(myPath):
        if val.endswith(".png") or val.endswith(".jpg"):        # OCRowanie plików .jpg i .png
            picPath = myPath + '/' + val
            txtPath = picPath[:-4] + ".txt"
            image = cv2.imread(picPath)
            #----------image preprocessing-------------
            gray = get_grayscale(image)
            thresh = thresholding(gray)
            opening_ = opening(gray)        #na razie niepotrzebne
            canny1_ = canny(gray)           #na razie niepotrzebne
            #cv2.imshow('img1', image)
            #cv2.waitKey(0)
            #------------------------------------------
            text = pytesseract.image_to_string(image, lang='pol', config=config1)
            text = text.replace('-', '')
            faktura = open(txtPath, "w")
            faktura.write(text)
            faktura.close()
        elif val.endswith(".pdf"):                              # OCRowanie plików .pdf
            pdfPath = myPath + '/' + val
            txtPath = pdfPath[:-4] + ".txt"
            imgPath = pdfPath[:-4] + ".jpg"
            pdf2jpeg(pdfPath, imgPath)
            img = cv2.imread(imgPath)                           # OCRowanie stworzonej grafiki
            text = pytesseract.image_to_string(img, lang='pol', config=config1)
            text = text.replace('-', '')
            faktura = open(txtPath, "w")
            faktura.write(text)
            faktura.close()

def ocrToGetNIPs():
    myPath = path.getPath()

    for val in os.listdir(myPath):
        if val.endswith(".png") or val.endswith(".jpg"):
            picPath = myPath + '/' + val
            txtPath = picPath[:-4] + ".txt"
            image = cv2.imread(picPath)
            text = pytesseract.image_to_string(image, lang='pol', config=config1, output_type=Output.STRING)
            text = text.replace('-', '')
            faktura = open(txtPath, "w")
            faktura.write(text)
            faktura.close()

'''
Path = path.getPath() + '/f2.jpg'
image = cv2.imread(Path)

gray = get_grayscale(image)
thresh = thresholding(gray)

#-----------------------------
img = gray    #podmienić potem
#-----------------------------

boxes = pytesseract.image_to_data(img, lang='pol', output_type=Output.DICT, config=config)
#boxes = pytesseract.image_to_data(img, lang='pol')
print(boxes)
n_boxes = len(boxes['text'])

for i in range(n_boxes):
    if int(boxes['conf'][i]) > 0:
        (x, y, w, h) = (boxes['left'][i], boxes['top'][i], boxes['width'][i], boxes['height'][i])
        img1 = cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)

cv2.imshow('img1', img1)
cv2.waitKey(0)
'''

'''
b,g,r = cv2.split(image)
rgb_img = cv2.merge([r,g,b])
#plt.imshow(rgb_img)
#plt.show()

plt.imshow(thresh, cmap='gray')
plt.show()
'''

'''

images = {'gray': gray, 'thresh': thresh, 'opening': opening, 'canny': canny}


fig = plt.figure(figsize=(13,13))
ax = []

rows = 2
columns = 2
keys = list(images.keys())
for i in range(rows*columns):
    ax.append( fig.add_subplot(rows, columns, i+1) )
    ax[-1].set_title('AUREBESH - ' + keys[i])
    plt.imshow(images[keys[i]], cmap='gray')
'''