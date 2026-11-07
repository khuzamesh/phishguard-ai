import os
import sys

from flask import Flask, jsonify, render_template, request

# Pastikan path relatif ke models/ benar, dan src/ bisa di-import
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))

from predict import predict_url  # noqa: E402
from email_analysis import analyze_email  # noqa: E402

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True) or {}
    url = str(data.get("url", "")).strip()
    if not url:
        return jsonify({"error": "URL kosong"}), 400
    return jsonify(predict_url(url))

@app.route("/analyze_email", methods=["POST"])
def analyze_email_api():
    data = request.get_json(silent=True) or {}
    text = str(data.get("text", "")).strip()
    if not text:
        return jsonify({"error": "Isi email kosong"}), 400
    return jsonify(analyze_email(text))

if __name__ == "__main__":
    app.run(debug=True)