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
import find_tabels
import parse_invoice

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

def getBuyerData(list, myPath):
    #myPath = path.getPath()
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
                    '''txtPath = picPath[:-4] + ".txt"
                    faktura = open(txtPath, "w")
                    faktura.write(content)
                    faktura.close()'''
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
                            else:
                                nip = "-"
                        else:
                            nip = "-"

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

def getInvoiceNumber(list, myPath):
    #myPath = path.getPath()
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

def getSellerData(list, myPath):
    #myPath = path.getPath()
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
            #print((len(boxes['text'])))

            for i in range(len(boxes['text'])):

                if i == len(boxes['text'])-1:           #jeśli nie wynaleziono w całej kolekcji słowa kluczowego
                    getSellerSDataWhenNoHeader(myPath, val, list)

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

def getSellerSDataWhenNoHeader(directory, invoiceImage, invoiceList):
    picPath = directory + '/' + invoiceImage
    image = cv2.imread(picPath)
    image = get_grayscale(image)
    w = image.shape[0]
    h = image.shape[1]

    namePattern = r'\s*(?P<name>[^\n,]*\.\n)'
    addressPattern = r'.*?((\n|,\x20|\x20)(?P<address>(os\.?\x20?|ul\.?\x20?|al\.?\x20?)?[a-ząćęłńóśźż]{2,}[a-ząćęłńóśźż\x20]+\d+\x20?/?m?\.?\x20?\d*[a-z]?))'
    cityPattern = r'.*?(?P<city>\d{2}-\d{3}\x20[a-ząćęłńóśźż]+\x20?[a-ząćęłńóśźż]*\x20?[a-ząćęłńóśźż]*)'
    nipPattern = r'NIP:?\x20(?P<NIP>((\d{10})|(\d{3}-\d{2}-\d{2}-\d{3})|(\d{3}-\d{3}-\d{2}-\d{2})))'

    crop_img = image[0:int(h / 5.5), 0:int(w / 3.5)]
    boxes = pytesseract.image_to_data(crop_img, lang='pol', output_type=Output.DICT, config=config2)

    for i in range(len(boxes['text'])):
        if str(boxes['text'][i]) == "NIP" or str(boxes['text'][i]) == "NIP:":
            top = boxes['top'][i]
            left = boxes['left'][i]
            height = boxes['height'][i]
            crop_img = crop_img[0:int(top) + int(height) + 10, left - 10:int(w / 3.5)]

    #cv2.imshow(directory, crop_img)
    #cv2.waitKey(0)

    content = pytesseract.image_to_string(crop_img, lang='pol', config=config1, output_type=Output.STRING)
    #print(content)

    try:
        sellerName = re.search(namePattern, content, re.IGNORECASE | re.DOTALL)
        sellerAddress = re.search(addressPattern, content, re.IGNORECASE | re.DOTALL)
        sellerCity = re.search(cityPattern, content, re.IGNORECASE | re.DOTALL)
        sellerNip = re.search(nipPattern, content, re.IGNORECASE | re.DOTALL)

        name = sellerName.group('name')
        address = sellerAddress.group('address')
        city = sellerCity.group('city')

        if sellerNip is not None:
            if sellerNip.group('NIP') is not None:
                nip = sellerNip.group('NIP')
                # print(nip)

        for l in invoiceList:
            if l.invoiceName == invoiceImage[:-4]:
                l.sellerName = name
                l.sellerAddress = address
                l.sellerCity = city
                l.sellerNipNumber = nip

                name = None
                address = None
                city = None
                nip = None

    except (AttributeError, UnboundLocalError) as err:
        print("nie udało się przypisać danych nabywcy faktury {0}, ERROR: {1}".format(invoiceImage, err))

def getInvoiceAmount(list, myPath):
    #myPath = path.getPath()
    amountPattern = r'(kwota\x20)?do\x20zapłaty:?[^\n,0-9]*(?P<amount>\d+,\d{2})(\x20(zł|PLN))?'

    for val in os.listdir(myPath):
        if val.endswith(".png") or val.endswith(".jpg"):
            picPath = myPath + '/' + val
            image = cv2.imread(picPath)
            #image = get_grayscale(image)

            content = pytesseract.image_to_string(image, lang='pol', config=config2, output_type=Output.STRING)

            # ---------------------tylko robi .txt-------------------
            '''txtPath = picPath[:-4] + ".txt"
            faktura = open(txtPath, "w")
            faktura.write(content)
            faktura.close()'''
            # -------------------------------------------------------

            try:
                invoiceAmount = re.findall(amountPattern, content, re.IGNORECASE | re.DOTALL)
                length = len(invoiceAmount)
                amount = invoiceAmount[length-1][1]

                for l in list:
                    if l.invoiceName == val[:-4]:
                        l.invoiceAmount = amount

            except (AttributeError, UnboundLocalError) as err:
                print("nie udało się przypisać kwoty faktury {0}, ERROR: {1}".format(val, err))

            continue

def getPositionsList(invoiceList, myPath):
    #myPath = path.getPath()

    for val in os.listdir(myPath):
        if val.endswith(".png") or val.endswith(".jpg"):
            picPath = myPath + '/' + val
            image = cv2.imread(picPath, 0)

            if image.shape[0] > 2340 or image.shape[1] > 1710:
                size = (int(image.shape[1] * 0.75), int(image.shape[0] * 0.75))
                image = cv2.resize(image, size)

            w = image.shape[1]
            h = image.shape[0]

            #serviceList.clear()
            serviceList = []

            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            #---------------------------------------------------Przycinanie obrazu do samej tabelki-----------------------------------------------------------------
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            boxes = pytesseract.image_to_data(image, lang='pol', output_type=Output.DICT, config=config2)
            boxes2 = pytesseract.image_to_data(image, lang='pol', output_type=Output.DICT, config=config1)
            try:
                croppedImage = searchInBoxes(val, image, boxes, h, w)
                if croppedImage is None:
                    croppedImage = searchInBoxes(val, image, boxes2, h, w)
                    if croppedImage is None:
                        print("nie udało się odnaleźć tabeli usług")
            except TypeError as err:
                print("nie udało się odnalezc pozycji pola kwoty brutto dla faktury {0}, ERROR: {1}".format(val, err))

            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            #-------------------------------------------------Odnajdowanie danych z przyciętej tabelki--------------------------------------------------------------
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            boxes = pytesseract.image_to_data(croppedImage, lang='pol', output_type=Output.DICT, config=config2)
            boxes2 = pytesseract.image_to_data(croppedImage, lang='pol', output_type=Output.DICT, config=config1)
            try:
                if croppedImage is not None:
                    serviceList = getDataFromTable(boxes2, croppedImage, w, val)
                    if len(serviceList) is 0:
                        serviceList = getDataFromTable(boxes, croppedImage, w, val)
                        if len(serviceList) is 0:
                            print("nie udało się odczytać listy pozycji faktury")
            except TypeError as err:
                print("nie udało się odnalezc kwoty brutto pozycji, dla faktury {0}, ERROR: {1}".format(val, err))

            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            #--------------------------------------------Przypisywanie otrzymanej listy do obiektu faktury----------------------------------------------------------
            # ------------------------------------------------------------------------------------------------------------------------------------------------------
            try:
                for l in invoiceList:
                    if l.invoiceName == val[:-4]:
                        l.positionsList = serviceList
            except TypeError as err:
                print("nie udało się przypisać listy pozycji, dla faktury {0}, ERROR: {1}".format(val, err))

def searchInBoxes(val, image, boxes, h, w):

    for i in range(len(boxes['text'])):

        if str(boxes['text'][i]) == "Usługa:" or str(boxes['text'][i]) == "Usługa" or str(boxes['text'][i]) == "Usługi:" or str(boxes['text'][i]) == "Usługi" or str(boxes['text'][i]) == "usługa:" or str(boxes['text'][i]) == "usługa" or str(boxes['text'][i]) == "usługi:" or str(boxes['text'][i]) == "usługi" or str(boxes['text'][i]) == "Opłaty:" or str(boxes['text'][i]) == "Opłaty" or str(boxes['text'][i]) == "opłaty:" or str(boxes['text'][i]) == "opłaty" or str(boxes['text'][i]) == "Usługa/Towar":
            top = boxes['top'][i]
            left = boxes['left'][i]

            bottom = h
            for i in range(len(boxes['text'])):
                if ((str(boxes['text'][i]) == "zapłaty" or str(boxes['text'][i]) == "zapłaty:") and (int(boxes['top'][i]) > top)):
                    bottom = boxes['top'][i] + boxes['height'][i]
                    break

            crop_img = image[top - 15:bottom + 5, 0:w]

            '''try:
                print("faktura " + str(val) + ": " + str(getBruttoColumnPosition(crop_img)))
                #y, x, h, w = getBruttoColumnPosition(crop_img)
                #cv2.rectangle(crop_img, (x, y), (x + w, y + h), (0, 0, 255), 1)
            except TypeError as err:
                print("nie udało się odnalezc pozycji kwoty brutto dla fakturys {0}, ERROR: {1}".format(val, err))

                #cv2.imshow(val, crop_img)
                #cv2.waitKey(0)'''

            return crop_img
            #break
    #return None

def getDataFromTable(boxes, croppedImage, w, val):
    #boxes = pytesseract.image_to_data(croppedImage, lang='pol', output_type=Output.DICT, config=config2)
    #boxes_2 = pytesseract.image_to_data(croppedImage, lang='pol', output_type=Output.STRING, config=config2)
    #print(boxes_2)

    positionList = []

    try:
        serviceColumnPosition = getServiceColumnPosition(boxes)
        #croppedImage = cv2.rectangle(croppedImage, (serviceColumnPosition[1], serviceColumnPosition[0]), (serviceColumnPosition[1] + serviceColumnPosition[3], serviceColumnPosition[0] + serviceColumnPosition[2]),(0, 0, 255), 1)

        # print("service column position: " + str(serviceColumnPosition))
        #cv2.imshow("1", croppedImage)
        #cv2.waitKey(0)

        BruttoColumnPosition = getBruttoColumnPosition(croppedImage, boxes)
        #croppedImage = cv2.rectangle(croppedImage, (BruttoColumnPosition[1], BruttoColumnPosition[0]), (BruttoColumnPosition[1] + BruttoColumnPosition[3], BruttoColumnPosition[0] + BruttoColumnPosition[2]), (0, 0, 255), 1)

        # print("brutto column position: " + str(BruttoColumnPosition))
        # cv2.imshow(val, croppedImage)
        # cv2.waitKey(0)

        currentBruttoPosition = getNextBruttoPosition(BruttoColumnPosition[0], BruttoColumnPosition[1],BruttoColumnPosition[2], int(w * 0.03), int(w * 0.03), boxes)
        #croppedImage = cv2.rectangle(croppedImage, (currentBruttoPosition[1], currentBruttoPosition[0]), (currentBruttoPosition[1] + currentBruttoPosition[3], currentBruttoPosition[0] + currentBruttoPosition[2]),(0, 0, 255), 1)

        # print("current brutto position: " + str(currentBruttoPosition))
        # cv2.imshow(val, croppedImage)
        # cv2.waitKey(0)

        currentServicePosition = getNextServicePosition(serviceColumnPosition[0], serviceColumnPosition[1],serviceColumnPosition[2], int(w * 0.15), int(w * 0.1), boxes)
        if currentServicePosition is not None:
            currentServicePosition = findNeighbours(currentServicePosition[4], boxes)
            #croppedImage = cv2.rectangle(croppedImage, (currentServicePosition[1], currentServicePosition[0]), (currentServicePosition[1] + currentServicePosition[3], currentServicePosition[0] + currentServicePosition[2]),(0, 0, 255), 1)

        if currentBruttoPosition[0] - 15 < currentServicePosition[0] < currentBruttoPosition[0] + 15:
            newPosition = parse_invoice.POSITION()
            nameImage = croppedImage[currentServicePosition[0] - 5 : currentServicePosition[0] + currentServicePosition[2] + 10, currentServicePosition[1] : currentServicePosition[1] + currentServicePosition[3]]
            amountImage = croppedImage[currentBruttoPosition[0] - 5:currentBruttoPosition[0] + currentBruttoPosition[2] + 5,currentBruttoPosition[1]:currentBruttoPosition[1] + currentBruttoPosition[3]]

            name = pytesseract.image_to_string(nameImage, lang='pol', config=config2, output_type=Output.STRING)
            amount = pytesseract.image_to_string(amountImage, lang='pol', config=config2, output_type=Output.STRING)
            newPosition.positionAmount = amount
            newPosition.positionName = name
            positionList.append(newPosition)

        # print("current service position: " + str(currentServicePosition))
        # cv2.imshow(val, croppedImage)
        # cv2.waitKey(0)

        deltaTop = currentBruttoPosition[0] - BruttoColumnPosition[0] + 10

        # print(deltaTop)

        nextBruttoPosition = getNextBruttoPosition(currentBruttoPosition[0], currentBruttoPosition[1],currentBruttoPosition[2], int(w * 0.03), int(w * 0.03), boxes)
        nextServicePosition = getNextPosition(currentServicePosition[0], currentServicePosition[1],currentServicePosition[2], 5, 5, boxes)
        if nextServicePosition is not None:
            nextServicePosition = findNeighbours(nextServicePosition[4], boxes)

        # print("next brutto position: " + str(nextBruttoPosition))
        # print("next service position: " + str(nextServicePosition))

        # croppedImage = cv2.rectangle(croppedImage, (nextBruttoPosition[1], nextBruttoPosition[0]), (nextBruttoPosition[1] + nextBruttoPosition[3], nextBruttoPosition[0] + nextBruttoPosition[2]),(0, 0, 255), 1)
        # croppedImage = cv2.rectangle(croppedImage, (nextServicePosition[1], nextServicePosition[0]), (nextServicePosition[1] + nextServicePosition[3], nextServicePosition[0] + nextServicePosition[2]),(0, 0, 255), 1)

        # cv2.imshow(val, croppedImage)
        # cv2.waitKey(0)

        while ((nextBruttoPosition is not None) and (nextServicePosition is not None) and (nextBruttoPosition[0] - currentBruttoPosition[0] < deltaTop) and (nextServicePosition[0] - currentServicePosition[0] < deltaTop)):
            #croppedImage = cv2.rectangle(croppedImage, (nextBruttoPosition[1], nextBruttoPosition[0]), (nextBruttoPosition[1] + nextBruttoPosition[3], nextBruttoPosition[0] + nextBruttoPosition[2]), (0, 0, 255), 1)
            #croppedImage = cv2.rectangle(croppedImage, (nextServicePosition[1], nextServicePosition[0]), (nextServicePosition[1] + nextServicePosition[3], nextServicePosition[0] + nextServicePosition[2]), (0, 0, 255),1)

            currentBruttoPosition = nextBruttoPosition
            currentServicePosition = nextServicePosition
            nextBruttoPosition = getNextBruttoPosition(nextBruttoPosition[0], nextBruttoPosition[1], nextBruttoPosition[2],int(w * 0.03), int(w * 0.03), boxes)
            nextServicePosition = getNextPosition(nextServicePosition[0], nextServicePosition[1], nextServicePosition[2], 5,5, boxes)
            if nextServicePosition is not None:
                nextServicePosition = findNeighbours(nextServicePosition[4], boxes)

            if currentBruttoPosition[0] - 15 < currentServicePosition[0] < currentBruttoPosition[0] + 15:
                newPosition = parse_invoice.POSITION()
                nameImage = croppedImage[currentServicePosition[0] - 5:currentServicePosition[0] + currentServicePosition[2] + 5,currentServicePosition[1]:currentServicePosition[1] + currentServicePosition[3]]
                amountImage = croppedImage[currentBruttoPosition[0] - 5:currentBruttoPosition[0] + currentBruttoPosition[2] + 5,currentBruttoPosition[1]:currentBruttoPosition[1] + currentBruttoPosition[3]]
                name = pytesseract.image_to_string(nameImage, lang='pol', config=config2, output_type=Output.STRING)
                amount = pytesseract.image_to_string(amountImage, lang='pol', config=config2, output_type=Output.STRING)
                newPosition.positionAmount = amount
                newPosition.positionName = name
                positionList.append(newPosition)
    except TypeError as err:
        print("nie udało się odnaleźć pól tabeli pozycji, dla faktury {0}, ERROR: {1}".format(val, err))

    return positionList

def test(path):
    #image = cv2.imread(path, 0)
    image = cv2.imread(path)

    boxes = pytesseract.image_to_data(image, lang='pol', output_type=Output.DICT, config=config2)
    w = image.shape[1]
    h = image.shape[0]
    image = searchInBoxes("test", image, boxes, h, w)
    #find_tabels.find_Tabels(image)

    pre = find_tabels.pre_process_image(image)
    text_boxes = find_tabels.find_text_boxes(pre)
    cells = find_tabels.find_table_in_boxes(text_boxes)
    hor_lines, ver_lines = find_tabels.build_lines(cells)

    # Visualize the result
    vis = image.copy()

    # for box in text_boxes:
    #     (x, y, w, h) = box
    #     cv2.rectangle(vis, (x, y), (x + w - 2, y + h - 2), (0, 255, 0), 1)

    for line in hor_lines:
        [x1, y1, x2, y2] = line
        cv2.line(vis, (x1, y1), (x2, y2), (0, 0, 255), 1)

    for line in ver_lines:
        [x1, y1, x2, y2] = line
        cv2.line(vis, (x1, y1), (x2, y2), (0, 0, 255), 1)

    cv2.imshow(path, vis)
    cv2.waitKey(0)

def getBruttoColumnPosition(image, boxes):

    h = image.shape[1]
    #w = image.shape[0]

    for i in range(len(boxes['text'])):
        if (boxes['text'][i] == "brutto" or boxes['text'][i] == "brutto[zł]" or boxes['text'][i] == "brutto(zł)") and boxes['height'][i] < int(h/2):
            #return boxes['top'][i] - 5, boxes['left'][i] - 15, boxes['height'][i] + 10, boxes['width'][i] + 60
            #print("_____brutto")
            #print(boxes['text'][i], boxes['top'][i], boxes['left'][i], boxes['height'][i], boxes['width'][i])
            return boxes['top'][i], boxes['left'][i], boxes['height'][i], boxes['width'][i]

    for i in range(len(boxes['text'])):
        if (boxes['text'][i] == "Wartość" or boxes['text'][i] == "wartość") and boxes['height'][i] < int(h/2):
            #return boxes['top'][i] - 5, boxes['left'][i] - 15, boxes['height'][i] + 10, boxes['width'][i] + 60
            #print("____wartosc:")
            #print(boxes['text'][i], boxes['top'][i], boxes['left'][i], boxes['height'][i], boxes['width'][i])
            return boxes['top'][i], boxes['left'][i], boxes['height'][i], boxes['width'][i]

    return 0

def getServiceColumnPosition(boxes):

    for i in range(len(boxes['text'])):
        if str(boxes['text'][i]) == "Usługa:" or str(boxes['text'][i]) == "Usługa" or str(boxes['text'][i]) == "Usługi:" or str(boxes['text'][i]) == "Usługi" or str(boxes['text'][i]) == "usługa:" or str(boxes['text'][i]) == "usługa" or str(boxes['text'][i]) == "usługi:" or str(boxes['text'][i]) == "usługi" or str(boxes['text'][i]) == "Opłaty:" or str(boxes['text'][i]) == "Opłaty" or str(boxes['text'][i]) == "opłaty:" or str(boxes['text'][i]) == "opłaty" or str(boxes['text'][i]) == "Usługa/Towar":
            return boxes['top'][i], boxes['left'][i], boxes['height'][i], boxes['width'][i]

    return 0

def getNextBruttoPosition(currentTop, currentLeft, currentHeight,  leftTolerance, rightTolerance, boxes):

    for i in range(len(boxes['text'])):
        if (boxes['top'][i] > currentTop + currentHeight) and (currentLeft - leftTolerance < boxes['left'][i] < currentLeft + rightTolerance) and isFloat(boxes['text'][i]):
            #print("_____Następny")
            #print(boxes['text'][i], boxes['top'][i], boxes['left'][i], boxes['height'][i], boxes['width'][i])
            return boxes['top'][i], boxes['left'][i], boxes['height'][i], boxes['width'][i], i

    return None

def getNextServicePosition(currentTop, currentLeft, currentHeight,  leftTolerance, rightTolerance, boxes):

    for i in range(len(boxes['text'])):
        #if (boxes['top'][i] > currentTop + currentHeight) and (currentLeft - leftTolerance < boxes['left'][i] < currentLeft + rightTolerance) and boxes['text'][i].isalpha():
        if (boxes['top'][i] > currentTop + currentHeight) and (currentLeft - leftTolerance < boxes['left'][i] < currentLeft + rightTolerance) and isAlpha(boxes['text'][i]):
            return boxes['top'][i], boxes['left'][i], boxes['height'][i], boxes['width'][i], i

    return None

def getNextPosition(currentTop, currentLeft, currentHeight,  leftTolerance, rightTolerance, boxes):

    for i in range(len(boxes['text'])):
        if (boxes['top'][i] > currentTop + currentHeight) and (currentLeft - leftTolerance < boxes['left'][i] < currentLeft + rightTolerance) and boxes['text'][i] is not "":
            #print("_____Następny")
            #print(boxes['text'][i], boxes['top'][i], boxes['left'][i], boxes['height'][i], boxes['width'][i])
            return boxes['top'][i], boxes['left'][i], boxes['height'][i], boxes['width'][i], i

    return None

def isFloat(string):
    '''hasDottOccured = False
    for c in string:
        if c.isdigit() or ((c is "." or c is ",") and hasDottOccured is False):
            if c is "." or c is ",":
                hasDottOccured = True
                continue
            elif c.isdigit():
                continue
        else:
            return False
    return True'''

    for c in string:
        if c.isdigit() or (c is "." or c is ","):
            continue
        else:
            return False
    return True

def findNeighbours(i, boxes):
    top, left = findLeftNeighbour(i, boxes)
    bottom, right = findRightNeighbour(i, boxes)
    height = bottom - top
    width = right - left

    return top, left, height, width

def findLeftNeighbour(i, boxes):

    j = 0
    #while boxes['top'][i-j]-5 < boxes['top'][i-j-1] < boxes['top'][i-j]+5 and boxes['left'][i-j-1] + boxes['width'][i-j-1] + 10 > boxes['left'][i-j] and isAlpha(boxes['text'][i-j-1]):
    while boxes['top'][i-j]-5 < boxes['top'][i-j-1] < boxes['top'][i-j]+5 and boxes['left'][i-j-1] + boxes['width'][i-j-1] + 11 > boxes['left'][i-j]:
        j = j + 1
    return boxes['top'][i-j], boxes['left'][i-j]

def findRightNeighbour(i, boxes):

    j = 0
    #while boxes['top'][i+j] - 5 < boxes['top'][i + j + 1] < boxes['top'][i+j] + 5 and boxes['left'][i+j+1] < boxes['left'][i+j] + boxes['width'][i+j] + 10 and isAlpha(boxes['text'][i+j+1]):
    while boxes['top'][i+j] - 5 < boxes['top'][i + j + 1] < boxes['top'][i+j] + 5 and boxes['left'][i+j+1] < boxes['left'][i+j] + boxes['width'][i+j] + 11:
        j = j + 1
    return boxes['top'][i+j] + boxes['height'][i+j], boxes['left'][i+j] + boxes['width'][i+j]

def isAlpha(string):
    regex = re.compile('[@_!#$%^&*()<>?/\|}{~:]')

    if (regex.search(string) == None):
        if len(string) > 1:
            return True
        else:
            return False
    else:
        return False

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
