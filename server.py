from flask import Flask, render_template, request, redirect
import os
import  path

app = Flask(__name__)
app.config["IMAGE_UPLOADS"] = path.getUploadFiles()
UPLOADS = os.path.join("static", "uploads")
app.config["UPLOAD_FOLDER"] = UPLOADS


@app.route("/")
def main():
    return render_template('index.html')

@app.route('/upload-invoice', methods = ['GET', 'POST'])
def getInvoice():
    if request.method == "POST":
        if request.files:
            invoice = request.files["invoice"]
            invoice.save(os.path.join(app.config["IMAGE_UPLOADS"], invoice.filename))
            #print(invoice)
            return render_template('index.html', invoiceName=invoice.filename)
            #return redirect(request.url)

    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug = True)