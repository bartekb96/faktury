from flask import Flask, render_template, request, redirect
import os

app = Flask(__name__)

@app.route("/")
def main():
    return render_template('index.html')

@app.route('/upload-invoice', methods = ['GET', 'POST'])
def getInvoice():
    if request.method == "POST":
        if request.files:
            invoice = request.files["invoice"]
            print(invoice)
            return redirect(request.url)

    return render_template('index.html')


if __name__ == "__main__":
    app.run(debug = True)