import re
import os
import path
import tess_ORC

#----------------------------------------------------------------------------
#------------------------------INVOICE---------------------------------------
#----------------------------------------------------------------------------

class Invoice:
    invoiceName = ""
    invoiceNumber = ""

    sellerNipNumber = ""
    sellerCity = ""
    sellerAddress =""
    sellerName = ""

    buyerNipNumber = ""
    buyerCity = ""
    buyerAddress =""
    buyerName = ""

def startColletion(path):
    invoiceList = []

    for val in os.listdir(path):
        if val.endswith(".png") or val.endswith(".jpg") or val.endswith(".pdf"):
            tmp = Invoice()
            tmp.invoiceName = val[:-4]
            invoiceList.append(tmp)

    return invoiceList

#----------------------------------------------------------------------------
#------------------------------PARSER----------------------------------------
#----------------------------------------------------------------------------


#dokończyć pattern na szukanie numeru faktury
#       .*((Numer:\s)|(Faktura\sVAT\snr\s))(\S*)
class Parser:
  def __init__(self):
        self.filePath = path.getPath()

  def setFilePath(self, newPath):
        self.filePath = newPath

  def parseInvoices(self, list):

      numberPattern = r".*((Faktura\s*VAT\s*numer)|(Faktura\s*VAT\s*nr)|(Faktura\s*VAT)|(Faktura\s*Numer)|(Faktura\s*nr)):?\s*(?P<invoiceNumber>\S*)"
      sellerWithoutHeaderPatternTmp = r"(?xs).+?(nabywca|odbiorca|sprzedawca)"         #dotall needed
      #sellerNipWithoutHeaderPattern = r".*NIP\s*(?P<sellerNIP>\d{10})"
      sellerWithoutHeaderPattern = r"\s*(?P<sellerName>[^\n]*)\s*(?P<sellerAddress>[^\n]*)\s*(?P<sellerCity>[^\n]*)\s*NIP:?\s*(?P<sellerNip>\d{10})"
      #buyerNipWhenSellerHasNoHeaderPattern = r"nabywca:?.*?NIP:?\s*(?P<buyerNip>\d{10})"
      sellerAndBuyerPattern = r"(?xs).+?sprzedawca:?.+?nabywca:?.+?NIP:?\s*(?P<sellerNip>\d{10}).+?(NIP:?\s*(?P<buyerNip>\d{10}))?"
      sellerPattern = r'sprzedawca:?\s*(?P<sellerName>[^\n]*)\s*(?P<sellerAddress>[^\n]*)\s*(?P<sellerCity>[^\n]*)\s*NIP:?\s*(?P<sellerNip>\d{10})'
      buyerPattern = r'nabywca:?\s*(?P<buyerName>[^\n]*)\s*(?P<buyerAddress>[^\n]*)\s*(?P<buyerCity>[^\n]*)\s*NIP:?\s*(?P<buyerNip>\d{10})?'

      sellerNipPattern = r"(?xs)NIP:?.s*(?P<sellerNIP>\d{10}).*(nabywca|odbiorca)"

      # ------------------GETTING INVOICE NUMBER----------------------------
      tess_ORC.ocrToGetNumber()

      for val in list:
          file = open(self.filePath+"/"+val.invoiceName+".txt", "r")
          if file.mode == 'r':
              content = file.read()
              result = re.search(numberPattern, content, re.IGNORECASE)
              if result != None:
                  val.invoiceNumber = result.group('invoiceNumber')
              else:
                  val.invoiceNumber.invoiceNumber = -1
          file.close()

      #------------------GETTING  NIP NUMBERS----------------------------------
      #tess_ORC.ocrToGetNIPs()

      for val in list:
          file = open(self.filePath+"/"+val.invoiceName+".txt", "r")
          if file.mode == 'r':
              content = file.read()

              sellerWithoutHeaderTmp = re.search(sellerWithoutHeaderPatternTmp, content, re.IGNORECASE | re.DOTALL)
              sellerWithoutHeader = re.search(sellerWithoutHeaderPattern, sellerWithoutHeaderTmp.group(0), re.IGNORECASE | re.DOTALL)
              buyerNipWhenSellerHasNoHeader = re.search(buyerPattern, content, re.IGNORECASE | re.DOTALL)

              sellerAndBuyer = re.search(sellerAndBuyerPattern, content, re.IGNORECASE | re.DOTALL)

              seller = re.search(sellerPattern, content, re.IGNORECASE | re.DOTALL)
              buyer = re.search(buyerPattern, content,  re.IGNORECASE | re.DOTALL)

              if sellerWithoutHeader != None:                        #regex na udaną segmentację bez nagłówka sprzedawcy
                  val.sellerNipNumber = sellerWithoutHeader.group('sellerNip')
                  val.sellerAddress = sellerWithoutHeader.group('sellerAddress')
                  val.sellerCity = sellerWithoutHeader.group('sellerCity')
                  val.sellerName = sellerWithoutHeader.group('sellerName')
                  '''if buyerNipWhenSellerHasNoHeader.group('buyerNip')  != None:
                      val.buyerNipNumber = buyerNipWhenSellerHasNoHeader.group('buyerNip')'''
                  if buyer != None:         #dane nabywcy
                      if buyer.group('buyerName') != None:
                          val.buyerName = buyer.group('buyerName')
                      if buyer.group('buyerAddress') != None:
                          val.buyerAddress = buyer.group('buyerAddress')
                      if buyer.group('buyerCity') != None:
                          val.buyerCity = buyer.group('buyerCity')
                      if buyer.group('buyerNip') != None:
                          val.buyerNipNumber = buyer.group('buyerNip')
                  else:
                      val.buyerNipNumber = -1
              elif sellerAndBuyer != None:                              #regex na nieudaną segmentację
                  val.sellerNipNumber = sellerAndBuyer.group('sellerNip')
                  if sellerAndBuyer.group('buyerNip') != None:
                      val.buyerNipNumber = sellerAndBuyer.group('buyerNip')
                  else:
                      val.buyerNipNumber = -1
              elif seller != None:                                      #regex na udaną segmentację
                  if seller.group('sellerName') != None:
                      val.sellerName = seller.group('sellerName')
                  if seller.group('sellerAddress') != None:
                      val.sellerAddress = seller.group('sellerAddress')
                  if seller.group('sellerCity') != None:
                      val.sellerCity = seller.group('sellerCity')
                  if seller.group('sellerNip') != None:
                      val.sellerNipNumber = seller.group('sellerNip')
                  if buyer != None:         #dane nabywcy
                      if buyer.group('buyerName') != None:
                          val.buyerName = buyer.group('buyerName')
                      if buyer.group('buyerAddress') != None:
                          val.buyerAddress = buyer.group('buyerAddress')
                      if buyer.group('buyerCity') != None:
                          val.buyerCity = buyer.group('buyerCity')
                      if buyer.group('buyerNip') != None:
                          val.buyerNipNumber = buyer.group('buyerNip')


              file.close()

      '''for val in os.listdir(path):
          if val.endswith(".txt"):
              file = open(path + "/" + val, "r")
              if file.mode == 'r':
                  content = file.read()
                  result = re.search(numberPattern, content, re.IGNORECASE)
                  temporaryInvoice = Invoice()
                  if result != None:
                      temporaryInvoice.invoiceNumber = result.group('invoiceNumber')    #jeśli istnieje dopasowanie zgodne z numberPattern (znaleziono numer) to dodaj go do listy obiektów z tym właśnie numerem
                      invoiceList.append(temporaryInvoice)
                  else:
                      temporaryInvoice.invoiceNumber = -1

                  if result != None:
                      print(result.group('invoiceNumber'))'''

#p1 = Parser(r"E:/ważne rzeczy/SEMESTR 10 FINALL BOSS/tesseract/przykladowa_faktura.txt")
#p1.parseFile()

#p1 = Parser()
#p1.parseInvoices()
