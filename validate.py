import parse_invoice
import path
import tess_ORC

myPath = path.getPath()

def validateInvoice(path):
 invoices = parse_invoice.startColletion(path)
 tess_ORC.getInvoiceNumber(invoices, path)
 tess_ORC.getBuyerData(invoices, path)
 tess_ORC.getSellerData(invoices, path)
 tess_ORC.getInvoiceAmount(invoices, path)
 tess_ORC.getPositionsList(invoices, path)

 return invoices

if __name__== "__main__":
 invoices = validateInvoice(myPath)

 print("done")


