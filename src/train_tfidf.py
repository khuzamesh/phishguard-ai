import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline

df = pd.read_csv("data/phishing_site_urls.csv")
df = df.drop_duplicates(subset="URL").dropna()
y = (df["Label"].str.lower() == "bad").astype(int).values
X = df["URL"].astype(str).str.lower()

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

model = make_pipeline(
    TfidfVectorizer(analyzer="char", ngram_range=(3, 5),
                    max_features=200000, sublinear_tf=True),
    LogisticRegression(C=5, solver="liblinear", class_weight="balanced"),
)

print("Training (bisa beberapa menit)...")
model.fit(X_train, y_train)

pred = model.predict(X_test)
print(classification_report(y_test, pred, target_names=["good", "bad"]))
print("Confusion matrix:\n", confusion_matrix(y_test, pred))

joblib.dump(model, "models/phishing_tfidf.joblib")
print("Tersimpan di models/phishing_tfidf.joblib")