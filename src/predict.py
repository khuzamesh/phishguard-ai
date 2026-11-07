import re
from urllib.parse import urlparse

import joblib

model = joblib.load("models/phishing_tfidf_v2.joblib")

# Domain tepercaya: tambah sendiri sesuai kebutuhan
TRUSTED_DOMAINS = {
    "google.com", "github.com", "tokopedia.com", "youtube.com",
    "microsoft.com", "apple.com", "wikipedia.org", "paypal.com",
    "shopee.co.id", "bca.co.id", "kompas.com", "detik.com",
}

def normalize(url: str) -> str:
    # Dataset latih umumnya tanpa skema (http/https), jadi samakan formatnya
    return re.sub(r"^https?://", "", url.strip().lower())

def get_host(url: str) -> str:
    full = url.strip().lower()
    if "://" not in full:
        full = "http://" + full
    try:
        return urlparse(full).hostname or ""
    except ValueError:
        return ""

def is_trusted(url: str) -> bool:
    host = get_host(url)
    return any(host == d or host.endswith("." + d) for d in TRUSTED_DOMAINS)

def risk_label(score: float) -> str:
    if score >= 65:
        return "FAKE / FRAUDULENT"
    if score >= 35:
        return "SUSPICIOUS"
    return "LEGIT"

def predict_url(url: str) -> dict:
    if is_trusted(url):
        return {"url": url, "risk_score": 0.0, "label": "LEGIT",
                "reason": "Domain ada di daftar tepercaya"}
    score = round(float(model.predict_proba([normalize(url)])[0][1]) * 100, 1)
    return {"url": url, "risk_score": score, "label": risk_label(score),
            "reason": "Hasil model ML"}

if __name__ == "__main__":
    tests = [
        "https://www.google.com",
        "https://github.com/login",
        "https://www.tokopedia.com",
        "https://nikke.gg/",
        "http://paypal-secure-login.verify-account.com/update?id=1",
        "http://192.168.10.5/bank-bca/login.php?cmd=verify",
        "http://secure-update.paypa1-support.net/signin",
        "http://github.com.akun-verifikasi.xyz/login",
    ]
    for u in tests:
        print(predict_url(u))