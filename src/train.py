import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from features import extract_features

# 1. Load & bersihkan data
df = pd.read_csv("data/phishing_site_urls.csv")
df = df.drop_duplicates(subset="URL").dropna()
df["target"] = (df["Label"].str.lower() == "bad"). astype(int)
print("Distribusi label:")
print(df["Label"].value_counts(), "\n")

# 2. Ekstraksi fitur (bisa 1-2 menit)
print("Ekstraksi fitur...")
X = pd.DataFrame([extract_features(u) for u in df["URL"]])
X = X.loc[:, X.nunique() > 1]
y = df["target"].values
print("Fitur dipakai:", list(X.columns), "\n")

# 3. Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# 4. Dua model
models = {
    "Logistic Regression": make_pipeline(
        StandardScaler(),
        LogisticRegression(max_iter=1000, class_weight="balanced"),
    ),
    "Random Forest": RandomForestClassifier(
        n_estimators=100, class_weight="balanced", n_jobs=-1, random_state=42
    ),
}

best_name, best_model, best_f1 = None, None, 0
for name, model in models.items():
    print("=" * 50)
    print(name)
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    print(classification_report(y_test, pred, target_names=["good", "bad"]))
    print("Confusion matrix:\n", confusion_matrix(y_test, pred))
    report = classification_report(y_test, pred, output_dict=True)
    if report["1"]["f1-score"] > best_f1:
        best_name, best_model, best_f1 = name, model, report["1"]["f1-score"]

# 5. Simpan model terbaik
joblib.dump({"model": best_model, "columns": list(X.columns)},
            "models/phishing_model.joblib")
print(f"\nModel terbaik: {best_name} (F1 phishing = {best_f1:.3f})")
print("Tersimpan di models/phishing_model.joblib")