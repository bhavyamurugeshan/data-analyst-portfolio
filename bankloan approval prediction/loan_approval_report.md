# Bank loan approval prediction

## Problem

Practise predicting a fictional loan approval label from information available at application time. There are 1,200 generated applications, not real bank records. All results describe synthetic patterns only.

## Verified run

```text
BANK LOAN APPROVAL PREDICTION
Fictional practice data. Not a real lending decision tool.

Applications loaded: 1,200
Approved: 598 | Rejected: 602
Approval rate: 49.8%
Missing source numeric cells: 36
Training applications: 900 | Test applications: 300
Test actual approved: 150 | Test actual rejected: 150

Always-Rejected baseline: accuracy 50.0% | precision 0.0% | recall 0.0%
Logistic regression: accuracy 79.0% | precision 75.7% | recall 85.3%
Correct approvals: 128 | Wrong approvals: 41
Missed approvals: 22 | Correct rejections: 109

Top model inputs (test accuracy drop when shuffled):
  1. Credit history: +17.08 percentage points
  2. Estimated EMI / monthly income: +14.62 percentage points
  3. Total monthly income: +0.95 percentage points
  4. Loan term: -0.12 percentage points

Two NEW fictional applicants (not part of the test set):
Sample A: Approved | model approval score 89.9%
Sample B: Rejected | model approval score 0.1%
```

## Method

- Stratified 75% training / 25% test split, random_state=42.
- Median imputation and standard scaling are fitted ONLY on training data.
- Logistic regression with approval score threshold 0.50.
- Compare with a baseline that predicts the most common training label for everybody.
- applicant_id, loan_status and all demographic fields are excluded from model inputs.
- Amounts are INR, income is monthly, and loan_amount_inr is the total principal, not an EMI.
- Estimated EMI uses an illustrative fixed annual interest rate of 10% and an amortizing loan formula. This is not a quote or actual lender policy.

## Reading the results

- Accuracy: fraction of ALL test applications classified correctly.
- Precision: among predicted approvals, fraction labelled Approved.
- Recall: among actual Approved labels, fraction found by the model.
- A wrong approval is an actual Rejected label predicted Approved. A missed approval is the reverse.
- Approval is the positive class. These labels are NOT repayment/default outcomes.

## Feature importance

Each raw model input is shuffled 20 times in the test set. The mean fall in accuracy is reported in percentage points. Higher means the fitted model relied on that input more in this test. Small or negative values can be noise. This does NOT show the direction of an effect or prove a cause. Related inputs can share importance. The test set is used for final evaluation/interpretation, not model tuning.

## New applicant examples

- Sample A: monthly income INR 60,000 + co-income INR 20,000; loan INR 12,00,000; 180 months; credit_history=1.
- Sample B: monthly income INR 25,000 + co-income INR 0; loan INR 18,00,000; 60 months; credit_history=0.
- Scores are model estimates, not calibrated real-world approval probabilities or bank promises.

## Data notes and limits

credit_history is a made-up binary indicator: 1 means satisfactory history, 0 means adverse history. Blank cells are unknown, not automatically 0. Fictional labels were generated mainly from credit history and estimated EMI/income burden with random variation; there is no universal real-bank approval rule here. Gender, marital status, dependents, education, employment category and property area are included only as practice descriptive columns, not used to score people. Excluding them does not prove a model is fair. Do not enter real personal data or use this model for lending, eligibility advice or automated decisions. A real project needs permissioned data, representative validation, fairness review, calibrated scores and human/regulatory oversight. This kit does not estimate loan default risk.

## Portfolio wording

Built a Python classification project on synthetic loan applications using pandas and scikit-learn. Compared logistic regression with a majority-class baseline using a stratified holdout, reported accuracy/precision/recall, and interpreted model inputs with permutation importance. Documented leakage controls and limits of simulated lending data.

## Reproducibility

Python 3.14.2, pandas 3.1.1, scikit-learn 1.9.1. Random seed is 42. Library versions can slightly change scores or rankings.
