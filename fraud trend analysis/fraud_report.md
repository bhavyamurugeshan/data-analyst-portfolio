# Fraud Trend Analysis Report

Loaded 5000 transactions, 2026-01-01 to 2026-06-29

## 1. Class imbalance

- Legit transactions: 4925 (98.5%)
- Fraud transactions: 75 (1.5%)

## 2. The naive baseline trap

Naive model: predict 'legit' for every single transaction.
- Accuracy: 98.5%  <- looks amazing
- Fraud caught (recall): 0%  <- useless, it catches nothing

## 3. Model results (on the 30% test set it never saw)

Confusion matrix:

| | Predicted legit | Predicted fraud |
|---|---|---|
| Actually legit | 1339 (true negative) | 139 (false alarm) |
| Actually fraud | 1 (missed fraud) | 21 (caught fraud) |

- Precision: 13.1% -> of the transactions we flagged, this share really was fraud
- Recall: 95.5% -> of all real fraud, this share we caught (naive baseline: 0%)
- Accuracy: 90.7% -> shown only for comparison; do not rely on it alone

## 4. Fraud trends

Fraud rate by category (highest first):

| Category | Transactions | Fraud | Fraud rate |
|---|---|---|---|
| jewelry | 168 | 21 | 12.5% |
| electronics | 402 | 19 | 4.7% |
| travel | 362 | 11 | 3.0% |
| online_shopping | 646 | 17 | 2.6% |
| groceries | 1248 | 7 | 0.6% |
| clothing | 598 | 0 | 0.0% |
| fuel | 739 | 0 | 0.0% |
| restaurants | 837 | 0 | 0.0% |

Fraud rate by time of day:

| Time of day | Transactions | Fraud | Fraud rate |
|---|---|---|---|
| 00-04 night | 295 | 51 | 17.3% |
| 05-08 early | 623 | 0 | 0.0% |
| 09-12 morning | 1236 | 6 | 0.5% |
| 13-17 afternoon | 1660 | 11 | 0.7% |
| 18-23 evening | 1186 | 7 | 0.6% |

Average amount: legit 231 vs fraud 819

Takeaway: fraud is rare, so accuracy is misleading. Precision and recall tell the real story.
