"""Merge all heart disease datasets and train a strengthened cardiac risk model.

Data sources:
  - 29 local CSV files (Kaggle Heart Failure + UCI format, 1,219 unique rows)
  - 4 UCI processed datasets (Cleveland, Hungarian, Switzerland, VA — 920 rows)
Total: ~2,138 unique rows after dedup.

Strategy:
  Binary classifier (normal vs. heart disease) trained on all data.
  Risk levels derived from predicted probability:
    normal  (<20%), low (20-50%), moderate (50-75%), high (>75%)
Model: HistGradientBoostingClassifier (LightGBM-style, built into scikit-learn)
Tuning: GridSearchCV with 5-fold stratified cross-validation.
"""

import csv
import glob
import os
import logging
import urllib.request
import numpy as np
import joblib

from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, roc_auc_score

logger = logging.getLogger(__name__)

HERE = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(HERE, "..", "..", "dataset")
UCI_DIR = os.path.join(DATASET_DIR, "uci")
MODEL_DIR = os.path.join(HERE, "models")

UNIFIED_COLUMNS = [
    "age", "sex", "cp", "trestbps", "chol", "fbs",
    "restecg", "thalach", "exang", "oldpeak", "slope",
    "ca", "thal", "target",
]

FEATURE_ORDER = UNIFIED_COLUMNS[:-1]

FORMAT1_MAP = {
    "Age": "age", "Sex": "sex", "ChestPainType": "cp",
    "RestingBP": "trestbps", "Cholesterol": "chol", "FastingBS": "fbs",
    "RestingECG": "restecg", "MaxHR": "thalach", "ExerciseAngina": "exang",
    "Oldpeak": "oldpeak", "ST_Slope": "slope", "HeartDisease": "target",
}
FORMAT1_ENCODINGS = {
    "sex": {"M": 1, "F": 0},
    "cp": {"ATA": 1, "NAP": 2, "ASY": 3, "TA": 0},
    "restecg": {"Normal": 0, "ST": 1, "LVH": 2},
    "exang": {"N": 0, "Y": 1},
    "slope": {"Up": 2, "Flat": 1, "Down": 0},
}

RISK_LEVELS = {0: "normal", 1: "low", 2: "moderate", 3: "high"}
RISK_THRESHOLDS = [0.20, 0.50, 0.75]


def detect_format(header):
    if "Age" in header and "ChestPainType" in header:
        return 1
    if "age" in header and "cp" in header:
        return 2
    return None


def normalize_row_format1(row):
    out = {}
    for src, dst in FORMAT1_MAP.items():
        val = row.get(src, "")
        if dst in FORMAT1_ENCODINGS:
            val = FORMAT1_ENCODINGS[dst].get(val, val)
        out[dst] = val
    out["ca"] = 0
    out["thal"] = 0
    return out


def normalize_row_format2(row):
    return {col: row.get(col, "") for col in UNIFIED_COLUMNS}


def target_to_binary(val):
    try:
        v = int(float(val))
    except (ValueError, TypeError):
        return None
    return 1 if v > 0 else 0


def merge_local_datasets():
    files = sorted(glob.glob(os.path.join(DATASET_DIR, "*.csv")))
    all_rows = []
    seen = set()
    for fpath in files:
        with open(fpath, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            header = reader.fieldnames or []
            fmt = detect_format(header)
            if fmt is None:
                continue
            for row in reader:
                normalized = normalize_row_format1(row) if fmt == 1 else normalize_row_format2(row)
                key = tuple(normalized[c] for c in UNIFIED_COLUMNS)
                if key in seen:
                    continue
                seen.add(key)
                all_rows.append(normalized)
    logger.info("Local datasets: %d unique rows from %d files", len(all_rows), len(files))
    return all_rows


def load_uci_file(path):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, encoding="utf-8") as f:
        reader = csv.reader(f)
        for raw in reader:
            if not raw or not raw[0].strip():
                continue
            padded = (raw + [""] * 14)[:14]
            row = dict(zip(UNIFIED_COLUMNS, padded))
            rows.append(row)
    logger.info("Loaded %s: %d rows", os.path.basename(path), len(rows))
    return rows


def merge_uci_datasets():
    os.makedirs(UCI_DIR, exist_ok=True)
    base_url = "https://archive.ics.uci.edu/ml/machine-learning-databases/heart-disease"
    files_map = {
        "processed.cleveland.data": os.path.join(UCI_DIR, "processed.cleveland.data"),
        "processed.hungarian.data": os.path.join(UCI_DIR, "processed.hungarian.data"),
        "processed.switzerland.data": os.path.join(UCI_DIR, "processed.switzerland.data"),
        "processed.va.data": os.path.join(UCI_DIR, "processed.va.data"),
    }
    all_rows = []
    for fname, path in files_map.items():
        if not os.path.exists(path) or os.path.getsize(path) < 100:
            try:
                logger.info("Downloading %s ...", fname)
                data = urllib.request.urlopen(f"{base_url}/{fname}", timeout=30).read()
                with open(path, "wb") as f:
                    f.write(data)
            except Exception as e:
                logger.warning("Failed to download %s: %s", fname, e)
                continue
        all_rows.extend(load_uci_file(path))
    logger.info("UCI datasets: %d total rows", len(all_rows))
    return all_rows


def clean_rows(rows):
    cleaned = []
    for r in rows:
        try:
            row_data = {}
            skip = False
            for col in UNIFIED_COLUMNS:
                val = str(r.get(col, "")).strip()
                if val in ("", "?", "None", "null", "NA"):
                    if col in ("ca", "thal"):
                        val = "0"
                    elif col == "target":
                        skip = True
                        break
                    else:
                        val = "0"
                row_data[col] = float(val)
            if skip:
                continue
            target_bin = target_to_binary(row_data["target"])
            if target_bin is None:
                continue
            row_data["target"] = target_bin
            cleaned.append(row_data)
        except (ValueError, TypeError):
            continue
    logger.info("Cleaned to %d valid rows", len(cleaned))
    return cleaned


def prepare_data(rows):
    X = np.array([[r[c] for c in FEATURE_ORDER] for r in rows])
    y = np.array([r["target"] for r in rows])
    return X, y


def print_distribution(y, label=""):
    unique, counts = np.unique(y, return_counts=True)
    logger.info("Class distribution %s:", label)
    for u, c in zip(unique, counts):
        pct = 100 * c / len(y)
        logger.info("  Class %d: %d samples (%.1f%%)", u, c, pct)


def risk_level_from_proba(proba_positive):
    if proba_positive < RISK_THRESHOLDS[0]:
        return 0, "normal"
    if proba_positive < RISK_THRESHOLDS[1]:
        return 1, "low"
    if proba_positive < RISK_THRESHOLDS[2]:
        return 2, "moderate"
    return 3, "high"


def train():
    os.makedirs(MODEL_DIR, exist_ok=True)

    local_rows = merge_local_datasets()
    uci_rows = merge_uci_datasets()

    combined = local_rows + uci_rows
    logger.info("Combined (before dedup): %d rows", len(combined))

    seen = set()
    deduped = []
    for r in combined:
        key = tuple(r.get(c, "") for c in UNIFIED_COLUMNS)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(r)
    logger.info("After dedup: %d unique rows", len(deduped))

    rows = clean_rows(deduped)
    X, y = prepare_data(rows)
    print_distribution(y, "(full dataset)")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)
    X_all_s = scaler.transform(X)

    logger.info("Training: X_train=%s, X_test=%s", X_train.shape, X_test.shape)

    param_grid = {
        "max_iter": [200, 300, 500],
        "max_depth": [4, 6, 8],
        "learning_rate": [0.05, 0.1, 0.15],
        "min_samples_leaf": [5, 10, 20],
    }

    base = HistGradientBoostingClassifier(
        random_state=42,
        early_stopping=True,
        validation_fraction=0.15,
        n_iter_no_change=15,
    )

    logger.info("Running GridSearchCV (this may take a minute)...")
    grid = GridSearchCV(
        base, param_grid, cv=5, scoring="accuracy",
        n_jobs=1, verbose=0, refit=True,
    )
    grid.fit(X_train_s, y_train)

    best = grid.best_estimator_
    logger.info("Best params: %s", grid.best_params_)
    logger.info("Best CV score: %.4f", grid.best_score_)

    # Calibrate probabilities for better risk scores
    logger.info("Calibrating probabilities...")
    calibrated = CalibratedClassifierCV(best, method="isotonic", cv=3)
    calibrated.fit(X_train_s, y_train)

    y_pred = calibrated.predict(X_test_s)
    y_proba = calibrated.predict_proba(X_test_s)[:, 1]
    acc = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_proba)
    logger.info("Test accuracy: %.4f", acc)
    logger.info("Test AUC: %.4f", auc)
    logger.info("Classification report:\n%s", classification_report(y_test, y_pred, target_names=["normal", "heart_disease"]))

    cm = confusion_matrix(y_test, y_pred)
    logger.info("Confusion matrix:\n%s", cm)

    # Verify risk-level distribution on test set
    logger.info("Risk-level distribution on test set:")
    for thr_label, lo, hi in [("normal", 0, 0.20), ("low", 0.20, 0.50), ("moderate", 0.50, 0.75), ("high", 0.75, 1.01)]:
        mask = (y_proba >= lo) & (y_proba < hi)
        actual_pos = y_test[mask].sum() if mask.sum() > 0 else 0
        logger.info("  %s: %d predictions, %d actually diseased (%.0f%% precision)", thr_label, mask.sum(), actual_pos, 100 * actual_pos / max(mask.sum(), 1))

    cv_scores = cross_val_score(calibrated, X_all_s, y, cv=5, scoring="accuracy")
    logger.info("Full CV: mean=%.4f, std=%.4f", cv_scores.mean(), cv_scores.std())

    model_path = os.path.join(MODEL_DIR, "heart_model.joblib")
    scaler_path = os.path.join(MODEL_DIR, "heart_scaler.joblib")
    joblib.dump(calibrated, model_path)
    joblib.dump(scaler, scaler_path)
    logger.info("Saved model to %s", model_path)
    logger.info("Saved scaler to %s", scaler_path)

    logger.info("Feature order: %s", FEATURE_ORDER)
    logger.info("Risk thresholds: %s", RISK_THRESHOLDS)
    return acc, auc, cv_scores.mean(), grid.best_params_


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    acc, auc, cv, params = train()
    print(f"\nDone! Test accuracy={acc:.4f}, AUC={auc:.4f}, CV mean={cv:.4f}")
    print(f"Best params: {params}")
