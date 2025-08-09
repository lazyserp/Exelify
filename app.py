from flask import Flask,render_template

app = Flask(__name__)

@app.get("/")
def index():
    return render_template("index.html.j2")


@app.get("/ping")
def ping():
    return render_template("_preview.html.j2",message="HTMX working !")




if __name__=="__main__":
    app.run(debug=True)
