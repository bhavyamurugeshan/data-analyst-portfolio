"""
fraud_check.py - Fraud trend analysis for beginners
====================================================
What this script does, step by step:
  1. Loads fraud_transactions.csv
  2. Shows how IMBALANCED the data is (very few fraud rows)
  3. Shows the "naive baseline" trap: 98%+ accuracy while catching zero fraud
  4. Trains a simple model (logistic regression) and measures it properly
  5. Shows fraud trends by category and by hour
  6. Saves everything to fraud_report.md (screenshot it for GitHub)

Run it with:  python fraud_check.py
Needs: pandas and scikit-learn  (python -m pip install pandas scikit-learn)
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, precision_score, recall_score, accuracy_score
from sklearn.model_selection import train_test_split

report = []  # we collect lines here and write them to fraud_report.md at the end


def show(text=""):
    """Print a line on screen AND remember it for the report file."""
    print(text)
    report.append(text)


# ---------------------------------------------------------------
# STEP 1: Load the data
# ---------------------------------------------------------------
df = pd.read_csv("fraud_transactions.csv")
# Turn the timestamp text into a real date/time so we can pull out the hour.
df["timestamp"] = pd.to_datetime(df["timestamp"])
df["hour"] = df["timestamp"].dt.hour

show("# Fraud Trend Analysis Report")
show()
show(f"Loaded {len(df)} transactions, {df['timestamp'].min().date()} to {df['timestamp'].max().date()}")
show()

# ---------------------------------------------------------------
# STEP 2: Class imbalance
# ---------------------------------------------------------------
# is_fraud is our "label": 1 = fraud, 0 = legit.
# In real life fraud is rare (often well under 2%). That is called CLASS IMBALANCE.
# It matters because most simple metrics (like accuracy) get fooled by it.
counts = df["is_fraud"].value_counts().sort_index()
legit_n, fraud_n = int(counts[0]), int(counts[1])
show("## 1. Class imbalance")
show()
show(f"- Legit transactions: {legit_n} ({legit_n / len(df):.1%})")
show(f"- Fraud transactions: {fraud_n} ({fraud_n / len(df):.1%})")
show()

# ---------------------------------------------------------------
# STEP 3: The naive baseline (the accuracy trap)
# ---------------------------------------------------------------
# Imagine a "model" that is lazy and says "legit" for EVERY transaction.
# Since ~98.5% are legit, it is right ~98.5% of the time - and catches ZERO fraud.
# That is why a high accuracy number alone means nothing on imbalanced data.
naive_pred = np.zeros(len(df), dtype=int)  # predict 0 (legit) for everyone
naive_acc = accuracy_score(df["is_fraud"], naive_pred)
naive_recall = recall_score(df["is_fraud"], naive_pred, zero_division=0)
show("## 2. The naive baseline trap")
show()
show("Naive model: predict 'legit' for every single transaction.")
show(f"- Accuracy: {naive_acc:.1%}  <- looks amazing")
show(f"- Fraud caught (recall): {naive_recall:.0%}  <- useless, it catches nothing")
show()

# ---------------------------------------------------------------
# STEP 4: Train a simple model
# ---------------------------------------------------------------
# Features = the clues the model may use. Models need numbers, so:
#  - amount is very skewed, so we use log(amount) to tame huge values
#  - category text becomes 0/1 columns (get_dummies = "one-hot encoding")
#  - night = 1 if the purchase was between midnight and 5am
df["log_amount"] = np.log1p(df["amount"])
df["night"] = (df["hour"] <= 4).astype(int)
X = pd.get_dummies(df[["log_amount", "hour", "night", "cardholder_age", "category"]],
                   columns=["category"], dtype=int)
y = df["is_fraud"]

# Split: train on 70%, TEST on the 30% the model has never seen.
# Testing on training data would be like grading a student on questions they memorised.
# stratify=y keeps the same fraud % in both halves (important when fraud is rare!).
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y)

# class_weight="balanced" tells the model: "a missed fraud costs more than a false alarm".
# Without it, the model learns the lazy lesson "just say legit".
# We scale the numbers first so logistic regression trains smoothly.
mean, std = X_train.mean(), X_train.std().replace(0, 1)
model = LogisticRegression(class_weight="balanced", max_iter=1000)
model.fit((X_train - mean) / std, y_train)
pred = model.predict((X_test - mean) / std)

# ---------------------------------------------------------------
# STEP 5: Judge the model properly
# ---------------------------------------------------------------
tn, fp, fn, tp = confusion_matrix(y_test, pred).ravel()
precision = precision_score(y_test, pred, zero_division=0)
recall = recall_score(y_test, pred, zero_division=0)
acc = accuracy_score(y_test, pred)

show("## 3. Model results (on the 30% test set it never saw)")
show()
show("Confusion matrix:")
show()
show("| | Predicted legit | Predicted fraud |")
show("|---|---|---|")
show(f"| Actually legit | {tn} (true negative) | {fp} (false alarm) |")
show(f"| Actually fraud | {fn} (missed fraud) | {tp} (caught fraud) |")
show()
# PRECISION: of everything we flagged as fraud, how much really was fraud?
#   Low precision = lots of false alarms = annoyed customers with blocked cards.
# RECALL: of all the real fraud, how much did we catch?
#   Low recall = fraud slips through = the bank loses money.
# You almost always trade one for the other. Banks decide which matters more.
show(f"- Precision: {precision:.1%} -> of the transactions we flagged, this share really was fraud")
show(f"- Recall: {recall:.1%} -> of all real fraud, this share we caught (naive baseline: 0%)")
show(f"- Accuracy: {acc:.1%} -> shown only for comparison; do not rely on it alone")
show()

# ---------------------------------------------------------------
# STEP 6: Fraud trends (the "analysis" part)
# ---------------------------------------------------------------
# groupby + mean of a 0/1 column = the fraud RATE for each group.
show("## 4. Fraud trends")
show()
show("Fraud rate by category (highest first):")
show()
by_cat = df.groupby("category")["is_fraud"].agg(["count", "sum", "mean"])
by_cat = by_cat.sort_values("mean", ascending=False)
show("| Category | Transactions | Fraud | Fraud rate |")
show("|---|---|---|---|")
for cat, r in by_cat.iterrows():
    show(f"| {cat} | {int(r['count'])} | {int(r['sum'])} | {r['mean']:.1%} |")
show()

# Group hours into time-of-day blocks so the table stays small.
blocks = pd.cut(df["hour"], bins=[-1, 4, 8, 12, 17, 23],
                labels=["00-04 night", "05-08 early", "09-12 morning", "13-17 afternoon", "18-23 evening"])
by_hour = df.groupby(blocks, observed=True)["is_fraud"].agg(["count", "sum", "mean"])
show("Fraud rate by time of day:")
show()
show("| Time of day | Transactions | Fraud | Fraud rate |")
show("|---|---|---|---|")
for blk, r in by_hour.iterrows():
    show(f"| {blk} | {int(r['count'])} | {int(r['sum'])} | {r['mean']:.1%} |")
show()

avg = df.groupby("is_fraud")["amount"].mean()
show(f"Average amount: legit {avg[0]:,.0f} vs fraud {avg[1]:,.0f}")
show()
show("Takeaway: fraud is rare, so accuracy is misleading. Precision and recall tell the real story.")

with open("fraud_report.md", "w", encoding="utf-8") as f:
    f.write("\n".join(report) + "\n")
print("\nSaved fraud_report.md")
