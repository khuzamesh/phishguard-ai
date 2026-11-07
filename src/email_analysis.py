import json
import re

from predict import get_host, predict_url, risk_label

URGENCY_PHRASES = [
    "urgent", "immediately", "act now", "within 24 hours", "within 48 hours",
    "permanent suspension", "will be suspended", "will be closed",
    "account has been restricted", "account has been suspended",
    "final warning", "last chance", "verify immediately",
    "segera", "mendesak", "dalam 24 jam", "akan diblokir", "akan ditutup",
    "dibekukan", "diblokir", "peringatan terakhir", "batas waktu",
]

SENSITIVE_PHRASES = [
    "password", "kata sandi", "pin", "otp", "cvv", "card number",
    "credit card", "nomor kartu", "kartu kredit", "social security",
    "verify your identity", "confirm your identity", "verifikasi identitas",
    "login credentials", "bank account", "nomor rekening",
    "billing information", "kode verifikasi",
]

# Merek -> domain resmi miliknya (tambah sendiri sesuai kebutuhan)
BRANDS = {
    "paypal": ["paypal.com", "paypal.co.uk"],
    "google": ["google.com", "gmail.com"],
    "microsoft": ["microsoft.com", "outlook.com", "live.com"],
    "apple": ["apple.com", "icloud.com"],
    "amazon": ["amazon.com"],
    "netflix": ["netflix.com"],
    "facebook": ["facebook.com", "facebookmail.com"],
    "instagram": ["instagram.com"],
    "tokopedia": ["tokopedia.com"],
    "shopee": ["shopee.co.id", "shopee.com"],
    "bca": ["bca.co.id", "klikbca.com"],
    "bri": ["bri.co.id"],
    "mandiri": ["bankmandiri.co.id", "mandiri.co.id"],
}

URL_RE = re.compile(r"(?:https?://|www\.)[^\s<>\"')\]]+", re.IGNORECASE)


def _mentions(phrase: str, text: str) -> bool:
    return re.search(r"\b" + re.escape(phrase) + r"\b", text) is not None


def _domain_matches(host: str, legit_domains: list) -> bool:
    return any(host == d or host.endswith("." + d) for d in legit_domains)


def parse_sender(text: str):
    """Ambil nama tampilan dan domain pengirim dari baris 'From:'."""
    m = re.search(r"^from:\s*(.+)$", text, re.IGNORECASE | re.MULTILINE)
    if not m:
        return "", ""
    line = m.group(1)
    addr = re.search(r"([\w.+-]+)@([\w.-]+)", line)
    domain = addr.group(2).lower().rstrip(".") if addr else ""
    display = re.sub(r"<[^>]*>", "", line).replace('"', "").strip().lower()
    if "@" in display:
        display = ""
    return display, domain


def extract_links(text: str) -> list:
    links = []
    for raw in URL_RE.findall(text):
        url = raw.rstrip(".,;:!?")
        if url not in links:
            links.append(url)
    return links


def analyze_email(text: str) -> dict:
    lower = re.sub(r"\s+", " ", text.lower())
    display, sender_domain = parse_sender(text)

    urgent = [p for p in URGENCY_PHRASES if _mentions(p, lower)]
    sensitive = [p for p in SENSITIVE_PHRASES if _mentions(p, lower)]

    # Spoofing: pengirim
    spoofing = []
    if sender_domain:
        for brand, legit in BRANDS.items():
            if _domain_matches(sender_domain, legit):
                continue
            if _mentions(brand, display):
                spoofing.append(
                    f"Nama pengirim menyebut '{brand}' tetapi domain pengirim adalah {sender_domain}")
            elif _mentions(brand, sender_domain):
                spoofing.append(
                    f"Domain pengirim {sender_domain} meniru merek '{brand}'")

    # Link: dinilai model URL + dicek peniruan merek
    links = extract_links(text)
    link_results = [predict_url(u) for u in links]
    suspicious_links = [
        {"url": r["url"], "risk_score": r["risk_score"]}
        for r in link_results if r["risk_score"] >= 35
    ]
    for u in links:
        host = get_host(u)
        for brand, legit in BRANDS.items():
            if host and _mentions(brand, host) and not _domain_matches(host, legit):
                spoofing.append(f"Link meniru merek '{brand}': {host}")
    spoofing = list(dict.fromkeys(spoofing))  # buang duplikat

    # Skor: jumlah berbobot, maksimal 100
    score = (min(len(urgent), 4) * 8
             + min(len(sensitive), 3) * 10
             + min(len(spoofing), 2) * 15
             + min(len(suspicious_links), 2) * 15)
    score = float(min(score, 100))

    return {
        "risk_score": score,
        "label": risk_label(score),
        "sender_domain": sender_domain,
        "links_found": len(links),
        "suspicious_links": suspicious_links,
        "urgent_triggers": urgent,
        "sensitive_requests": sensitive,
        "spoofing_flags": spoofing,
        "indicator_counts": {
            "Urgency": len(urgent),
            "Sensitive Info": len(sensitive),
            "Spoofing": len(spoofing),
            "Suspicious Links": len(suspicious_links),
        },
    }


if __name__ == "__main__":
    phishing = """From: "PayPal Security" <security@paypal-verification.com>
Subject: URGENT: Your account has been restricted

Dear Valued Customer,

We noticed unusual activity on your PayPal account. To avoid permanent
suspension, you must verify your identity immediately.

Click here to confirm your account:
http://paypal-secure-login.verify-account-now.com/confirm
Please enter your password and card number to restore access.
"""

    legit = """From: "Tokopedia" <info@tokopedia.com>
Subject: Pesanan kamu sudah dikirim

Halo, pesanan #12345 kamu sudah dikirim.
Lacak paket kamu di https://www.tokopedia.com/order/12345
Terima kasih sudah berbelanja.
"""

    for name, mail in [("PHISHING", phishing), ("LEGIT", legit)]:
        print("=" * 50, name)
        print(json.dumps(analyze_email(mail), indent=2, ensure_ascii=False))