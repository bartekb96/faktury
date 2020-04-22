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



def getBuyerData(list):
    myPath = path.getPath()
    buyerPattern = r'nabywca( \[\d*\])?:?\s*(?P<buyerName>[^\n]*)\s*(?P<buyerAddress>[^\n,]*)(\s*|\s?,\s?)(?P<buyerCity>\d{2}-\d{3}\s\w+ ?\w* ?\w*)\s*(NIP:?)?\s*((?P<buyerNip1>\d{10})|(?P<buyerNip2>\d{3}-\d{2}-\d{2}-\d{3})|(?P<buyerNip3>\d{3}-\d{3}-\d{2}-\d{2}))?'
    buyerNamePattern = r'nabywca( \[\d*\])?:?\s*(?P<name>[^\n]*)'
    buyerAddressPattern = r'nabywca( \[\d*\])?:?.*?((\n|,\x20|\x20)(?P<address>(os\.?\x20?|ul\.?\x20?|al\.?\x20?)?[a-ząćęłńóśźż]{2,}[a-ząćęłńóśźż\x20]+\d+\x20?/?m?\.?\x20?\d*[a-z]?))'  #global multiline isensitive sinngle line
    buyerCityPattern = r'nabywca( \[\d*\])?:?.*?((\n|,\x20?)(?P<city>\d{2}-\d{3}\x20[a-ząćęłńóśźż]+\x20?[a-ząćęłńóśźż]*\x20?[a-ząćęłńóśźż]*))'        #flagi jak wyżej
    #buyerNipPattern = r'nabywca( \[\d*\])?:?\s*.*?((\n|,\x20)NIP:?\x20(?P<NIP>((\d{10})|(\d{3}-\d{2}-\d{2}-\d{3})|(\d{3}-\d{3}-\d{2}-\d{2}))))'         #flagi jak wyżej
    buyerNipPattern = r'NIP:?\x20(?P<NIP>((\d{10})|(\d{3}-\d{2}-\d{2}-\d{3})|(\d{3}-\d{3}-\d{2}-\d{2})))'         #flagi jak wyżej

    for val in os.listdir(myPath):
        if val.endswith(".png") or val.endswith(".jpg"):
            picPath = myPath + '/' + val
            image = cv2.imread(picPath)
            image = get_grayscale(image)
            w = image.shape[0]
            h = image.shape[1]

            boxes = pytesseract.image_to_data(image, lang='pol', output_type=Output.DICT, config=config2)
            #boxes2 = pytesseract.image_to_data(image, lang='pol', config=config2)
            #print(boxes2)

            for i in range(len(boxes['text'])):
                if str(boxes['text'][i]) == "Nabywca" or str(boxes['text'][i]) == "Nabywca:" or str(boxes['text'][i]) == "NABYWCA" or str(boxes['text'][i]) == "NABYWCA:":
                    top = boxes['top'][i]
                    left = boxes['left'][i]
                    crop_img = image[top-10:top + int(h/5), left-10:left + int(w/3)]

                    #cv2.imshow(val, crop_img)
                    #cv2.waitKey(0)

                    content = pytesseract.image_to_string(crop_img, lang='pol', config=config2, output_type=Output.STRING)

                    #---------------------tylko robi .txt-------------------
                    txtPath = picPath[:-4] + ".txt"
                    faktura = open(txtPath, "w")
                    faktura.write(content)
                    faktura.close()
                    #-------------------------------------------------------

                    try:
                        #buyer = re.search(buyerPattern, content, re.IGNORECASE | re.DOTALL)
                        buyerName = re.search(buyerNamePattern, content, re.IGNORECASE | re.DOTALL)
                        buyerAddress = re.search(buyerAddressPattern, content, re.IGNORECASE | re.DOTALL)
                        buyerCity = re.search(buyerCityPattern, content, re.IGNORECASE | re.DOTALL)
                        buyerNip = re.search(buyerNipPattern, content, re.IGNORECASE | re.DOTALL)

                        name = buyerName.group('name')
                        address = buyerAddress.group('address')
                        city = buyerCity.group('city')

                        if buyerNip is not None:
                            if buyerNip.group('NIP') is not None:
                                nip = buyerNip.group('NIP')

                        for l in list:
                            if l.invoiceName == val[:-4]:
                                l.buyerName = name
                                l.buyerAddress = address
                                l.buyerCity = city
                                l.buyerNipNumber = nip

                                name = None
                                address = None
                                city = None
                                nip = None

                    except AttributeError as err:
                        print("nie udało się przypisać danych nabywcy faktury {0}, ERROR: {1}".format(val, err))

                    break


def getInvoiceNumber(list):
    myPath = path.getPath()
    numberPattern = r".*((Faktura\s*VAT\s*numer)|(Faktura\s*VAT\s*nr)|(Faktura\s*VAT)|(Faktura\s*Numer)|(Faktura\s*nr)):?\s*(?P<invoiceNumber>\S*)"

    for val in os.listdir(myPath):
        if val.endswith(".png") or val.endswith(".jpg"):  # OCRowanie plików .jpg i .png
            picPath = myPath + '/' + val
            image = cv2.imread(picPath)
            image = get_grayscale(image)
            text = pytesseract.image_to_string(image, lang='pol', config=config1)

            invoiceNumber = -1
            try:
                result = re.search(numberPattern, text, re.IGNORECASE)
                invoiceNumber = result.group('invoiceNumber')

                for l in list:
                    if l.invoiceName == val[:-4]:
                        l.invoiceNumber = invoiceNumber
            except AttributeError as err:
                print("nie udało się przypisać numeru faktury: {0}".format(err))



def getSellerData(list):
    myPath = path.getPath()
    sellerPattern = r'sprzedawca:?\s*(?P<sellerName>[^\n]*)\s*(?P<sellerAddress>[^\n]*)\s*(?P<sellerCity>[^\n]*)\s*NIP:?\s*(?P<sellerNip>\d{10})'
    sellerNamePattern = r'sprzedawca( \[\d*\])?:?\s*(?P<name>[^\n,]*(\n|\.\x20|,\x20))'
    sellerAddressPattern = r'sprzedawca( \[\d*\])?:?.*?((\n|,\x20|\x20)(?P<address>(os\.?\x20?|ul\.?\x20?|al\.?\x20?)?[a-ząćęłńóśźż]{2,}[a-ząćęłńóśźż\x20]+\d+\x20?/?m?\.?\x20?\d*[a-z]?))'  #global multiline isensitive sinngle line
    sellerCityPattern = r'sprzedawca( \[\d*\])?:?.*?((\n|,\x20?)(?P<city>\d{2}-\d{3}\x20[a-ząćęłńóśźż]+\x20?[a-ząćęłńóśźż]*\x20?[a-ząćęłńóśźż]*))'        #flagi jak wyżej
    #sellerNipPattern = r'sprzedawca( \[\d*\])?:?\s*.*?((\n|,\x20)NIP:?\x20(?P<NIP>((\d{10})|(\d{3}-\d{2}-\d{2}-\d{3})|(\d{3}-\d{3}-\d{2}-\d{2}))))'         #flagi jak wyżej
    sellerNipPattern = r'NIP:?\x20(?P<NIP>((\d{10})|(\d{3}-\d{2}-\d{2}-\d{3})|(\d{3}-\d{3}-\d{2}-\d{2})))'         #flagi jak wyżej

    for val in os.listdir(myPath):
        if val.endswith(".png") or val.endswith(".jpg"):
            picPath = myPath + '/' + val
            image = cv2.imread(picPath)
            image = get_grayscale(image)
            w = image.shape[0]
            h = image.shape[1]

            #cv2.imshow(val, image)
            #cv2.imshow("zmieniony", changeContrastAndBrightness(0.5, 10, image))
            #cv2.waitKey(0)

            boxes = pytesseract.image_to_data(image, lang='pol', output_type=Output.DICT, config=config2)

            for i in range(len(boxes['text'])):
                if str(boxes['text'][i]) == "Sprzedawca" or str(boxes['text'][i]) == "Sprzedawca:" or str(boxes['text'][i]) == "SPRZEDAWCA" or str(boxes['text'][i]) == "SPRZEDAWCA:":
                    top = boxes['top'][i]
                    left = boxes['left'][i]
                    crop_img = image[top-20:top + int(h/5.5), left-20:left + int(w/3.5)]

                    #cv2.imshow(val, crop_img)
                    #cv2.waitKey(0)

                    content = pytesseract.image_to_string(crop_img, lang='pol', config=config1, output_type=Output.STRING)      #tu było zmieniane na config1 z config2

                    #---------------------tylko robi .txt-------------------
                    '''txtPath = picPath[:-4] + ".txt"
                    faktura = open(txtPath, "w")
                    faktura.write(content)
                    faktura.close()'''
                    #-------------------------------------------------------

                    try:
                        # buyer = re.search(buyerPattern, content, re.IGNORECASE | re.DOTALL)
                        sellerName = re.search(sellerNamePattern, content, re.IGNORECASE | re.DOTALL)
                        sellerAddress = re.search(sellerAddressPattern, content, re.IGNORECASE | re.DOTALL)
                        sellerCity = re.search(sellerCityPattern, content, re.IGNORECASE | re.DOTALL)
                        sellerNip = re.search(sellerNipPattern, content, re.IGNORECASE | re.DOTALL)

                        name = sellerName.group('name')
                        address = sellerAddress.group('address')
                        city = sellerCity.group('city')

                        #print(city)

                        if sellerNip is not None:
                            if sellerNip.group('NIP') is not None:
                                nip = sellerNip.group('NIP')
                                #print(nip)

                        for l in list:
                            if l.invoiceName == val[:-4]:
                                l.sellerName = name
                                l.sellerAddress = address
                                l.sellerCity = city
                                l.sellerNipNumber = nip

                                name = None
                                address = None
                                city = None
                                nip = None

                    except (AttributeError, UnboundLocalError) as err:
                        print("nie udało się przypisać danych nabywcy faktury {0}, ERROR: {1}".format(val, err))

                    break


def changeContrastAndBrightness(contrast, brightness, image):   #contrast [0.0-3.0], brightness [0-100]

    new_image = np.zeros(image.shape, image.dtype)

    #print(image.shape[0])
    #print(image.shape[1])
    #print(image.shape[2])

    try:
        '''for y in range(image.shape[0]):
            for x in range(image.shape[1]):
                for c in range(image.shape[2]):
                    new_image[y, x, c] = np.clip(contrast * image[y, x, c] + brightness, 0, 255)'''

        for y in range(image.shape[0]):
            for x in range(image.shape[1]):
                    new_image[y, x] = np.clip(contrast * image[y, x] + brightness, 0, 255)

    except ValueError:
        print('Błąd edycji obrazu')

    return new_image


def removeTelNumberAndEmailAddress(text):
    phoneNumberPattern = r'tel:?\s(\+48/?\s?)?(?P<phonenNumber>(\d{2}\s?-?\s?\d{2}\s?-?\s?\d{2}\s?-?\s?\d{3})|(\d{9})|(\d{3}\s?-?\s?\d{2}\s?-?\s?\d{2}\s?-?\s?\d{2}))'
    emailAddressPattern = r' '




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