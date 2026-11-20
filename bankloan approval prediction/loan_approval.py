"""Loan approval prediction practice kit. All applications are fictional.
Run: python loan_approval_check.py
Needs: pandas and scikit-learn. No internet, account or personal data needed.
"""
from pathlib import Path
import sys

try:
    import pandas as pd
    import sklearn
    from sklearn.impute import SimpleImputer
    from sklearn.inspection import permutation_importance
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, confusion_matrix, precision_score, recall_score
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
except ImportError as exc:
    print('A required package is missing:', exc.name)
    print('Run: python -m pip install pandas scikit-learn')
    print('Then run: python loan_approval_check.py')
    sys.exit(1)

HERE = Path(__file__).resolve().parent
CSV_NAME = 'loan_applications.csv'
FEATURES = ['credit_history', 'emi_to_income_ratio',
            'total_monthly_income_inr', 'loan_term_months']
LABELS = {
    'credit_history': 'Credit history',
    'emi_to_income_ratio': 'Estimated EMI / monthly income',
    'total_monthly_income_inr': 'Total monthly income',
    'loan_term_months': 'Loan term',
}
REQUIRED = ['applicant_id', 'applicant_income_inr', 'coapplicant_income_inr',
            'loan_amount_inr', 'loan_term_months', 'credit_history', 'loan_status']
NUMERIC = REQUIRED[1:6]


def prepare_features(data):
    """Row-wise calculations only; learn imputation/scaling from training rows later."""
    clean = data.copy()
    for column in NUMERIC:
        clean[column] = pd.to_numeric(clean[column], errors='coerce')
    for column in ['applicant_income_inr', 'loan_amount_inr', 'loan_term_months']:
        clean.loc[clean[column] <= 0, column] = float('nan')
    clean.loc[clean.coapplicant_income_inr < 0, 'coapplicant_income_inr'] = float('nan')
    clean.loc[~clean.credit_history.isin([0, 1]), 'credit_history'] = float('nan')
    clean['total_monthly_income_inr'] = clean.applicant_income_inr + clean.coapplicant_income_inr
    # 10% annual interest is an illustrative assumption, NOT a bank's actual rate.
    rate = 0.10 / 12
    growth = (1 + rate) ** clean.loan_term_months
    estimated_emi = clean.loan_amount_inr * rate * growth / (growth - 1)
    clean['emi_to_income_ratio'] = estimated_emi / clean.total_monthly_income_inr
    return clean[FEATURES].replace([float('inf'), -float('inf')], float('nan'))


def metric_line(name, actual, predicted):
    return (f'{name}: accuracy {accuracy_score(actual, predicted):.1%} | '
            f'precision {precision_score(actual, predicted, zero_division=0):.1%} | '
            f'recall {recall_score(actual, predicted, zero_division=0):.1%}')


def main():
    path = HERE / CSV_NAME
    if not path.exists():
        print(f'Cannot find {CSV_NAME}.')
        print('Save it in the SAME folder as loan_approval_check.py.')
        print('Run dir /b to check the exact filenames. Remove any extra suffix letters.')
        print('Do not rename an Excel workbook to .csv; use the supplied CSV file.')
        return 1
    try:
        data = pd.read_csv(path)
    except (OSError, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
        print('Could not read the CSV:', exc)
        return 1
    missing = sorted(set(REQUIRED) - set(data.columns))
    if missing:
        print('Required columns missing:', ', '.join(missing))
        print('Use the supplied loan_applications.csv without editing its header.')
        return 1
    if data.applicant_id.isna().any() or data.applicant_id.duplicated().any():
        print('Each applicant_id must be present and unique. Use the original CSV.')
        return 1
    target = data.loan_status.astype(str).str.strip().str.lower().map({'approved': 1, 'rejected': 0})
    if target.isna().any() or target.nunique() != 2 or target.value_counts().min() < 10:
        print('Need at least 10 Approved and 10 Rejected labels, with no missing/unknown labels.')
        return 1
    X = prepare_features(data)
    if X.isna().all().any():
        print('A model input has no valid values. Use the original CSV.')
        return 1
    y = target.astype(int)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y)
    model = Pipeline([
        ('fill_missing', SimpleImputer(strategy='median')),
        ('scale', StandardScaler()),
        ('classifier', LogisticRegression(max_iter=2000, random_state=42)),
    ])
    model.fit(X_train, y_train)
    # A score >= 0.50 is called Approved for this practice exercise.
    scores = model.predict_proba(X_test)[:, 1]
    predicted = (scores >= 0.50).astype(int)
    majority = int(y_train.mode().iloc[0])
    baseline = [majority] * len(y_test)
    baseline_name = 'Approved' if majority else 'Rejected'
    tn, fp, fn, tp = confusion_matrix(y_test, predicted, labels=[0, 1]).ravel()
    importance = permutation_importance(
        model, X_test, y_test, scoring='accuracy', n_repeats=20, random_state=42)
    ranked = sorted(zip(FEATURES, importance.importances_mean), key=lambda item: item[1], reverse=True)
    feature_lines = [f'  {i}. {LABELS[name]}: {value * 100:+.2f} percentage points'
                     for i, (name, value) in enumerate(ranked, 1)]
    model_metrics = metric_line('Logistic regression', y_test, predicted)
    baseline_metrics = metric_line(f'Always-{baseline_name} baseline', y_test, baseline)
    summary = [
        'BANK LOAN APPROVAL PREDICTION',
        'Fictional practice data. Not a real lending decision tool.',
        '',
        f'Applications loaded: {len(data):,}',
        f'Approved: {int(y.sum()):,} | Rejected: {int((1-y).sum()):,}',
        f'Approval rate: {y.mean():.1%}',
        f'Missing source numeric cells: {int(data[NUMERIC].isna().sum().sum())}',
        f'Training applications: {len(X_train):,} | Test applications: {len(X_test):,}',
        f'Test actual approved: {int(y_test.sum())} | Test actual rejected: {int((1-y_test).sum())}',
        '', baseline_metrics, model_metrics,
        f'Correct approvals: {tp} | Wrong approvals: {fp}',
        f'Missed approvals: {fn} | Correct rejections: {tn}',
        '', 'Top model inputs (test accuracy drop when shuffled):', *feature_lines,
    ]
    examples = pd.DataFrame([
        {'applicant_income_inr': 60000, 'coapplicant_income_inr': 20000,
         'loan_amount_inr': 1200000, 'loan_term_months': 180, 'credit_history': 1},
        {'applicant_income_inr': 25000, 'coapplicant_income_inr': 0,
         'loan_amount_inr': 1800000, 'loan_term_months': 60, 'credit_history': 0},
    ])
    example_scores = model.predict_proba(prepare_features(examples))[:, 1]
    example_lines = []
    for name, score in zip(['Sample A', 'Sample B'], example_scores):
        label = 'Approved' if score >= 0.50 else 'Rejected'
        example_lines.append(f'{name}: {label} | model approval score {score:.1%}')
    summary += ['', 'Two NEW fictional applicants (not part of the test set):', *example_lines]
    report = [
        '# Bank loan approval prediction',
        '## Problem',
        'Practise predicting a fictional loan approval label from information available at application time. '
        'There are 1,200 generated applications, not real bank records. All results describe synthetic patterns only.',
        '## Verified run', '```text\n' + '\n'.join(summary) + '\n```',
        '## Method',
        '- Stratified 75% training / 25% test split, random_state=42.\n'
        '- Median imputation and standard scaling are fitted ONLY on training data.\n'
        '- Logistic regression with approval score threshold 0.50.\n'
        '- Compare with a baseline that predicts the most common training label for everybody.\n'
        '- applicant_id, loan_status and all demographic fields are excluded from model inputs.\n'
        '- Amounts are INR, income is monthly, and loan_amount_inr is the total principal, not an EMI.\n'
        '- Estimated EMI uses an illustrative fixed annual interest rate of 10% and an amortizing loan formula. '
        'This is not a quote or actual lender policy.',
        '## Reading the results',
        '- Accuracy: fraction of ALL test applications classified correctly.\n'
        '- Precision: among predicted approvals, fraction labelled Approved.\n'
        '- Recall: among actual Approved labels, fraction found by the model.\n'
        '- A wrong approval is an actual Rejected label predicted Approved. A missed approval is the reverse.\n'
        '- Approval is the positive class. These labels are NOT repayment/default outcomes.',
        '## Feature importance',
        'Each raw model input is shuffled 20 times in the test set. The mean fall in accuracy is reported in '
        'percentage points. Higher means the fitted model relied on that input more in this test. '
        'Small or negative values can be noise. This does NOT show the direction of an effect or prove a cause. '
        'Related inputs can share importance. The test set is used for final evaluation/interpretation, not model tuning.',
        '## New applicant examples',
        '- Sample A: monthly income INR 60,000 + co-income INR 20,000; loan INR 12,00,000; 180 months; credit_history=1.\n'
        '- Sample B: monthly income INR 25,000 + co-income INR 0; loan INR 18,00,000; 60 months; credit_history=0.\n'
        '- Scores are model estimates, not calibrated real-world approval probabilities or bank promises.',
        '## Data notes and limits',
        'credit_history is a made-up binary indicator: 1 means satisfactory history, 0 means adverse history. '
        'Blank cells are unknown, not automatically 0. Fictional labels were generated mainly from credit history '
        'and estimated EMI/income burden with random variation; there is no universal real-bank approval rule here. '
        'Gender, marital status, dependents, education, employment category and property area are included only as '
        'practice descriptive columns, not used to score people. Excluding them does not prove a model is fair. '
        'Do not enter real personal data or use this model for lending, eligibility advice or automated decisions. '
        'A real project needs permissioned data, representative validation, fairness review, calibrated scores '
        'and human/regulatory oversight. This kit does not estimate loan default risk.',
        '## Portfolio wording',
        'Built a Python classification project on synthetic loan applications using pandas and scikit-learn. '
        'Compared logistic regression with a majority-class baseline using a stratified holdout, '
        'reported accuracy/precision/recall, and interpreted model inputs with permutation importance. '
        'Documented leakage controls and limits of simulated lending data.',
        '## Reproducibility',
        f'Python {sys.version.split()[0]}, pandas {pd.__version__}, scikit-learn {sklearn.__version__}. '
        'Random seed is 42. Library versions can slightly change scores or rankings.',
    ]
    output = HERE / 'loan_approval_report.md'
    try:
        output.write_text('\n\n'.join(report) + '\n', encoding='utf-8')
    except OSError as exc:
        print('\n'.join(summary))
        print('Could not save report:', exc)
        return 1
    print('\n'.join(summary))
    print('\nSaved report:', output)
    print('Done. No real applicant data was used.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
