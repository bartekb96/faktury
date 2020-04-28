import parse_invoice
import path
import tess_ORC

myPath = path.getPath()
p1 = parse_invoice.Parser()

if __name__== "__main__":
 invoices = parse_invoice.startColletion(myPath)
 #p1.parseInvoices(invoices)    #parsowanie faktur

 tess_ORC.getInvoiceNumber(invoices)       #odzyskiwanie numeru faktury -> działa
 tess_ORC.getBuyerData(invoices)           #odzyskiwanie danych nabywcy -> działą
 tess_ORC.getSellerData(invoices)          #odzyskiwanie danych sprzedawcy -> działą
 tess_ORC.getInvoiceAmount(invoices)       #odzyskiwanie kwoty faktury -> działą

 print("done")


