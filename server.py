from flask import Flask, render_template, request, redirect
import os
import path
import shutil
import validate

uploadDirectory = path.getUploadFiles()

app = Flask(__name__)
app.config["IMAGE_UPLOADS"] = uploadDirectory
UPLOADS = os.path.join("static", "uploads")
app.config["UPLOAD_FOLDER"] = UPLOADS


@app.route("/")
def main():
    return render_template('index.html')

@app.route('/upload-invoice', methods = ['GET', 'POST'])
def getInvoice():
    
    for filename in os.listdir(uploadDirectory):
        file_path = os.path.join(uploadDirectory, filename)
        try:
            if filename.endswith(".png") or filename.endswith(".jpg") or filename.endswith(".pdf"):
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
        except Exception as ex:
            print('Failed to delete %s. Reason: %s' % (file_path, ex))

    if request.method == "POST":
        if request.files:

                invoice = request.files["invoice"]
                invoice.save(os.path.join(app.config["IMAGE_UPLOADS"], invoice.filename))

                # -------------------------------------------------------------------------------------------------
                #------------------------------------SETtING VALUES------------------------------------------------
                #--------------------------------------------------------------------------------------------------
                invoices = validate.validateInvoice(uploadDirectory)
                print(invoices[0].invoiceNumber)

                if invoices[0].invoiceNumber and invoices[0].invoiceNumber is not "":
                    invoiceNumber = invoices[0].invoiceNumber
                else:
                    invoiceNumber = "-"

                if invoices[0].sellerNipNumber and invoices[0].sellerNipNumber is not "":
                    sellerNip = invoices[0].sellerNipNumber
                else:
                    sellerNip = "-"

                if invoices[0].sellerCity and invoices[0].sellerCity is not "":
                    sellerCity = invoices[0].sellerCity
                else:
                    sellerCity = "-"

                if invoices[0].sellerAddress and invoices[0].sellerAddress is not "":
                    sellerAddress = invoices[0].sellerAddress
                else:
                    sellerAddress = "-"

                if invoices[0].sellerName and invoices[0].sellerName is not "":
                    sellerName = invoices[0].sellerName
                else:
                    sellerName = "-"

                if invoices[0].buyerNipNumber and invoices[0].buyerNipNumber is not "":
                    buyerNip = invoices[0].buyerNipNumber
                else:
                    buyerNip = "-"

                if invoices[0].buyerCity and invoices[0].buyerCity is not "":
                    buyerCity = invoices[0].buyerCity
                else:
                    buyerCity = "-"

                if invoices[0].buyerAddress and invoices[0].buyerAddress is not "":
                    buyerAddress = invoices[0].buyerAddress
                else:
                    buyerAddress = "-"

                if invoices[0].buyerName and invoices[0].buyerName is not "":
                    buyerName = invoices[0].buyerName
                else:
                    buyerName = "-"

                if invoices[0].invoiceAmount and invoices[0].invoiceAmount is not "":
                    invoiceAmount = invoices[0].invoiceAmount
                else:
                    invoiceAmount = "-"
                # --------------------------------------------------------------------------------------------------
                # --------------------------------------------------------------------------------------------------
                # --------------------------------------------------------------------------------------------------

                return render_template('index.html', invoiceName=invoice.filename,
                                       invoiceNumber=invoiceNumber, sellerNip=sellerNip,
                                       sellerCity=sellerCity,
                                       sellerAddress=sellerAddress, sellerName=sellerName,
                                       buyerNip=buyerNip, buyerCity=buyerCity,
                                       buyerAddress=buyerAddress, buyerName=buyerName,
                                       invoiceAmount=invoiceAmount)

            #return redirect(request.url)

    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug = True)