from flask import Flask,render_template,request
from werkzeug.utils import secure_filename
from storage import new_doc_id, save_df
import pandas as pd


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


ALLOWED_EXTS = {".csv", ".xlsx"}  # we only accept CSV or Excel today

@app.route("/upload", methods=["POST"])
def upload():
    # 1) Get the uploaded file object from the form field named "file"
    file = request.files.get("file")
    if not file or file.filename.strip() == "":
        # If no file was chosen, return the preview partial with an error message
        return render_template("_preview.html.j2", message="No file selected ❌"), 400

    # 2) Clean the filename and check extension whitelisting (security)
    fname = secure_filename(file.filename)
    ext = ("." + fname.rsplit(".", 1)[1].lower()) if "." in fname else ""
    if ext not in ALLOWED_EXTS:
        return render_template("_preview.html.j2", message="Only .csv or .xlsx allowed ❌"), 400

    # 3) Create a new unique id (doc_id) for this uploaded dataset/session
    doc_id = new_doc_id()

    try:
        # 4) Read the FULL DataFrame (not just a preview)
        #    - For CSV we can read directly from file.stream
        #    - For Excel we rewind the stream and use read_excel
        #    - dtype_backend="pyarrow" gives better nullable dtypes (optional)
        if ext == ".csv":
            full_df = pd.read_csv(file.stream, dtype_backend="pyarrow")
        else:
            file.stream.seek(0)
            full_df = pd.read_excel(file.stream, dtype_backend="pyarrow")

        # 5) Persist the full DataFrame to disk for this doc_id
        save_df(doc_id, full_df)

        # 6) Build a lightweight preview (first 100 rows) to render in HTML
        preview_df = full_df.head(100)
        rows_html = preview_df.to_html(index=False, border=0, classes="preview")

        # 7) Build a small "schema" summary (column, dtype, % nulls)
        dtypes = preview_df.dtypes.astype(str)
        null_pct = (preview_df.isna().mean() * 100).round(2)
        lines = [
            f"{col:25} {dtypes[col]:12} nulls: {null_pct[col]:.2f}%"
            for col in preview_df.columns
        ]
        schema_text = "\n".join(lines)

        # 8) Return the preview partial with:
        #    - message text
        #    - HTML table for the first 100 rows
        #    - schema text
        #    - the doc_id so the page can carry it for future operations
        return render_template(
            "_preview.html.j2",
            message=f"Loaded {fname} ✅ (showing first 100 rows)",
            rows=rows_html,
            schema=schema_text,
            doc_id=doc_id,
        )

    except Exception as e:
        # If pandas throws (bad encoding, corrupt file, etc.), surface the error nicely
        return render_template("_preview.html.j2", message=f"Parse error ❌: {e}"), 400


    return render_template("_preview.html.j2", message=f"Received {fname} ✅")



@app.route("/info", methods=["POST"])
def info():
    # doc_id is carried by a hidden input in the preview partial
    doc_id = request.form.get("doc_id")
    if not doc_id:
        return render_template("_preview.html.j2", message="Missing doc_id ❌"), 400

    try:
        df = load_df(doc_id)  # load the full, persisted DataFrame
        msg = f"State OK ✅  rows={len(df)}  cols={len(df.columns)}"
        # We keep the preview minimal here; you can show table/schema again if you like
        return render_template("_preview.html.j2", message=msg, rows=None, schema=None, doc_id=doc_id)
    except Exception as e:
        return render_template("_preview.html.j2", message=f"Load error ❌: {e}"), 400


if __name__=="__main__":
    app.run(debug=True)
