from flask import Flask,render_template,request
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 200*1024*1024

@app.get("/")
def index():
    return render_template("index.html.j2")

@app.get("/ping")
def ping():
    return render_template("_preview.html.j2",message="HTMX working !")

@app.route("/demo-post", methods=["POST"])
def demo_post():
    return render_template("_preview.html.j2", message=f"Route reached via POST ✅")



ALLOWED_EXTS = {".csv",".xlsx"}
@app.route("/upload",methods=["GET","POST"])
def upload():
    file = request.files.get("file")
    if not file or file.filename.strip() == "":
        return render_template("_preview.html.j2",mnessage="NO FILE SELECTED")

    fname = secure_filename(file.filename)
    ext = (("." + fname.rsplit(".",1)[1].lower()) if "." in fname else "")
    if ext not in ALLOWED_EXTS:
        return render_template("_preview.html.j2",message="only csv or .xlsx")

    return render_template("_preview.html.j2",messsage =f"Received {fname}")






if __name__=="__main__":
    app.run(debug=True)
