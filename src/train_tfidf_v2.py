import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline

N_TRAIN = 100_000     # domain populer yang ikut training
N_HOLDOUT = 20_000    # domain populer lain, hanya untuk evaluasi

# 1. Dataset asli
df = pd.read_csv("data/phishing_site_urls.csv").drop_duplicates(subset="URL").dropna()
y = (df["Label"].str.lower() == "bad").astype(int)
X = df["URL"].astype(str).str.lower()
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# 2. Daftar domain populer (Tranco)
tr = pd.read_csv("data/top-1m.csv", header=None, names=["rank", "domain"])
tr["domain"] = tr["domain"].astype(str).str.lower()
train_domains = tr["domain"].iloc[:N_TRAIN]
holdout = pd.Series(tr["domain"].iloc[N_TRAIN:N_TRAIN + N_HOLDOUT].tolist())

def make_samples(domains):
    # variasi format supaya model tidak belajar satu pola saja
    return [d if i % 2 == 0 else f"www.{d}/" for i, d in enumerate(domains)]

extra_X = pd.Series(make_samples(train_domains))
extra_y = pd.Series([0] * len(extra_X))

X_train2 = pd.concat([X_train.reset_index(drop=True), extra_X], ignore_index=True)
y_train2 = pd.concat([y_train.reset_index(drop=True), extra_y], ignore_index=True)

# 3. Training
model = make_pipeline(
    TfidfVectorizer(analyzer="char", ngram_range=(3, 5),
                    max_features=200000, sublinear_tf=True),
    LogisticRegression(C=5, solver="liblinear", class_weight="balanced"),
)
print("Training v2 (bisa beberapa menit)...")
model.fit(X_train2, y_train2)

# 4. Evaluasi pada test set asli
pred = model.predict(X_test)
print(classification_report(y_test, pred, target_names=["good", "bad"]))
print("Confusion matrix:\n", confusion_matrix(y_test, pred))

# 5. Perbandingan model lama vs baru
old = joblib.load("models/phishing_tfidf.joblib")

fp_old = old.predict(holdout).mean() * 100
fp_new = model.predict(holdout).mean() * 100
print(f"\nFalse positive pada {N_HOLDOUT} domain populer (tidak ikut training):")
print(f"  model lama: {fp_old:.1f}%   model baru: {fp_new:.1f}%")

# Pastikan phishing berbentuk domain polos tidak jadi lolos
mask = (~X_test.str.contains("/")) & (y_test == 1)
bare_bad = X_test[mask]
print(f"\nRecall phishing domain polos ({len(bare_bad)} sampel):")
print(f"  model lama: {old.predict(bare_bad).mean()*100:.1f}%   "
      f"model baru: {model.predict(bare_bad).mean()*100:.1f}%")

# 6. Uji manual
for u in ["nikke.gg/", "game8.co/games/arknights-endfield",
          "secure-update.paypa1-support.net/signin",
          "github.com.akun-verifikasi.xyz/login"]:
    print(f"{u:55s} -> {model.predict_proba([u])[0][1]*100:.1f}%")

joblib.dump(model, "models/phishing_tfidf_v2.joblib")
print("\nTersimpan di models/phishing_tfidf_v2.joblib")