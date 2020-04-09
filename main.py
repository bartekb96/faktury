import parse_invoice
import path
import tess_ORC

myPath = path.getPath()
p1 = parse_invoice.Parser()

if __name__== "__main__":
 invoices = parse_invoice.startColletion(myPath)
 p1.parseInvoices(invoices)    #parsowanie faktur

 print("done")

