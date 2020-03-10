import re
import os
import path

#----------------------------------------------------------------------------
#------------------------------INVOICE---------------------------------------
#----------------------------------------------------------------------------

class Invoice:
    invoiceNumber = ""

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

  def parseInvoices(self, path = None):
      path = self.filePath

      invoiceList = []

      for val in os.listdir(path):
          if val.endswith(".txt"):
              file = open(path + "/" + val, "r")
              if file.mode == 'r':
                  content = file.read()
                  result = re.search('.*Faktura VAT .*', content)
                  temporaryInvoice = Invoice()
                  temporaryInvoice.invoiceNumber = 1    #zamienić na wynik parsowania
                  invoiceList.append(temporaryInvoice)
                  if result != None:
                    print(result.group(0))

#p1 = Parser(r"E:/ważne rzeczy/SEMESTR 10 FINALL BOSS/tesseract/przykladowa_faktura.txt")
#p1.parseFile()

p1 = Parser()
p1.parseInvoices()
