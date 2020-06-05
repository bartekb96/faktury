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
    if request.method == "POST":
        if request.files:

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

                invoice = request.files["invoice"]
                invoice.save(os.path.join(app.config["IMAGE_UPLOADS"], invoice.filename))

                invoices = validate.validateInvoice(uploadDirectory)
                print(invoices[0].invoiceNumber)

                return render_template('index.html', invoiceName=invoice.filename,
                                       invoiceNumber=invoices[0].invoiceNumber, sellerNip=invoices[0].sellerNipNumber,
                                       sellerCity=invoices[0].sellerCity,
                                       sellerAddress=invoices[0].sellerAddress, sellerName=invoices[0].sellerName,
                                       buyerNip=invoices[0].buyerNipNumber, buyerCity=invoices[0].buyerCity,
                                       buyerAddress=invoices[0].buyerAddress, buyerName=invoices[0].buyerName,
                                       invoiceAmount=invoices[0].invoiceAmount)

            #return redirect(request.url)

    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug = True)