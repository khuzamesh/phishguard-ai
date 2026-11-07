import re
from urllib.parse import urlparse

SUSPICIOUS_WORDS = ["login", "verify", "secure", "account", "update",
                    "bank", "paypal", "confirm", "signin", "password"]

def extract_features(url:str) -> dict:
    url = str(url).strip()
    full = url if "://" in url else "http://" + url
    try:
        parsed = urlparse(full)
    except ValueError:
        # URL berformat aneh (mis. kurung siku tidak berpasangan): bersihkan lalu coba lagi
        parsed = urlparse(full.replace("[", "").replace("]", ""))
    host = parsed.netloc.lower()
    return {
        "url_length": len(url),
        "host_length": len(host),
        "num_dots": url.count("."),
        "num_hyphens": url.count("-"),
        "num_digits": sum(c.isdigit() for c in url),
        "num_subdomains": max(host.count(".") - 1, 0),
        "has_at": int("@" in url),
        "has_ip": int(bool(re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}(:\d+)?", host))),
        "is_https": int(parsed.scheme == "https"),
        "num_suspicious_words": sum(w in url.lower() for w in SUSPICIOUS_WORDS),
        "path_length": len(parsed.path),
        "num_params": parsed.query.count("&") + (1 if parsed.query else 0),
    }

if __name__ == "__main__":
    for u in ["https://www.google.com",
              "http://paypal-secure-login.verify-account.com/update?id=1&x=2"]:
        print(u)
        print(extract_features(u), "\n")