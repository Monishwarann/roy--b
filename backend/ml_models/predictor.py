"""
ML Models for Drug Discovery Platform
--------------------------------------
Model 1: Drug Toxicity Classifier (Deep Neural Network simulation via sklearn)
Model 2: Drug Effectiveness Predictor (Random Forest)

Since installing TensorFlow/DeepChem in free environments can be heavy,
we use scikit-learn's MLPClassifier (neural network) and RandomForestClassifier
which give equivalent results for this use case and run without GPU requirements.

The models are trained on synthetic Tox21-inspired features on first run,
then saved as .pkl files for fast inference.
"""

import numpy as np
import joblib
import os
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

MODEL_DIR = os.path.dirname(__file__)
TOXICITY_MODEL_PATH = os.path.join(MODEL_DIR, "toxicity_model.pkl")
DRUG_MODEL_PATH = os.path.join(MODEL_DIR, "drug_model.pkl")


# ─── Training Data Generation ──────────────────────────────────────────────────

def generate_toxicity_training_data(n_samples: int = 2000):
    """
    Generate synthetic Tox21-inspired training data.
    Features: [MW, logP, HBD, HBA, RotBonds, AromaticRings]
    Label: 0 = Non-Toxic, 1 = Possibly-Toxic, 2 = Toxic
    """
    np.random.seed(42)
    X = np.column_stack([
        np.random.uniform(100, 900, n_samples),    # molecular_weight
        np.random.uniform(-3, 8, n_samples),        # logP
        np.random.randint(0, 10, n_samples),        # h_bond_donors
        np.random.randint(0, 15, n_samples),        # h_bond_acceptors
        np.random.randint(0, 15, n_samples),        # rotatable_bonds
        np.random.randint(0, 6, n_samples),         # aromatic_rings
    ])

    # Rule-based labels with noise (reflects Lipinski + Tox21 logic)
    y = []
    for row in X:
        mw, logp, hbd, hba, rot, aro = row
        score = 0
        if mw > 500: score += 1
        if logp > 5 or logp < -2: score += 1
        if hbd > 5: score += 1
        if hba > 10: score += 1
        if rot > 10: score += 1
        if aro > 3: score += 1
        # Add noise
        score += np.random.randint(-1, 2)
        score = max(0, min(score, 6))

        if score <= 2:
            y.append(0)   # Non-Toxic
        elif score <= 4:
            y.append(1)   # Possibly-Toxic
        else:
            y.append(2)   # Toxic

    return X, np.array(y)


def generate_drug_training_data(n_samples: int = 2000):
    """
    Generate synthetic drug effectiveness training data.
    Features: [MW, HBD, LogP]
    Output: binding_score (0–10), success_probability (0–1)
    """
    np.random.seed(99)
    X = np.column_stack([
        np.random.uniform(100, 700, n_samples),    # molecular_weight
        np.random.randint(0, 8, n_samples),         # h_bond_donors
        np.random.uniform(-2, 6, n_samples),        # logP
    ])

    # Optimal range: MW 200-500, HBD 1-3, LogP 1-3 (Lipinski rule of five)
    y = []
    for row in X:
        mw, hbd, logp = row
        base = 10
        # Penalize out-of-range values
        if mw < 200 or mw > 500: base -= 2
        if hbd > 5: base -= 2
        if logp < 0 or logp > 5: base -= 2
        base = max(0, base) + np.random.uniform(-2, 2)
        base = max(0, min(10, base))
        y.append(base)

    return X, np.array(y)


# ─── Model Training & Saving ──────────────────────────────────────────────────

def train_and_save_toxicity_model():
    print("🔬 Training Toxicity Model (MLP Classifier)...")
    X, y = generate_toxicity_training_data()

    model = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", MLPClassifier(
            hidden_layer_sizes=(128, 64, 32),
            activation="relu",
            max_iter=300,
            random_state=42,
            early_stopping=True,
            validation_fraction=0.1
        ))
    ])
    model.fit(X, y)
    joblib.dump(model, TOXICITY_MODEL_PATH)
    print(f"✅ Toxicity model saved to {TOXICITY_MODEL_PATH}")
    return model


def train_and_save_drug_model():
    print("💊 Training Drug Effectiveness Model (Random Forest)...")
    X, y = generate_drug_training_data()

    # Binarize for classification: score >= 6 → effective
    y_class = (y >= 6).astype(int)

    model = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", GradientBoostingClassifier(
            n_estimators=100,
            max_depth=4,
            random_state=42
        ))
    ])
    model.fit(X, y_class)
    joblib.dump(model, DRUG_MODEL_PATH)
    print(f"✅ Drug model saved to {DRUG_MODEL_PATH}")
    return model


# ─── Load Models (train if not exists) ───────────────────────────────────────

def load_toxicity_model():
    if os.path.exists(TOXICITY_MODEL_PATH):
        return joblib.load(TOXICITY_MODEL_PATH)
    return train_and_save_toxicity_model()


def load_drug_model():
    if os.path.exists(DRUG_MODEL_PATH):
        return joblib.load(DRUG_MODEL_PATH)
    return train_and_save_drug_model()


# Initialize at import time
print("Loading ML models...")
_toxicity_model = load_toxicity_model()
_drug_model = load_drug_model()
print("✅ All ML models loaded!")


# ─── Prediction Functions ─────────────────────────────────────────────────────

def predict_toxicity(data) -> dict:
    features = np.array([[
        data.molecular_weight,
        data.logp,
        data.h_bond_donors,
        data.h_bond_acceptors,
        data.rotatable_bonds,
        data.aromatic_rings
    ]])

    pred_class = int(_toxicity_model.predict(features)[0])
    prob = _toxicity_model.predict_proba(features)[0].tolist()

    class_map = {
        0: ("Low Risk", "Non-Toxic"),
        1: ("Medium Risk", "Possibly Toxic"),
        2: ("High Risk", "Toxic")
    }

    toxicity_class, risk_level = class_map[pred_class]

    return {
        "toxicity_class": toxicity_class,
        "risk_level": risk_level,
        "confidence": round(max(prob) * 100, 2),
        "probability_scores": {
            "non_toxic": round(prob[0] * 100, 2),
            "possibly_toxic": round(prob[1] * 100, 2) if len(prob) > 1 else 0.0,
            "toxic": round(prob[2] * 100, 2) if len(prob) > 2 else 0.0
        },
        "molecular_features": {
            "molecular_weight": data.molecular_weight,
            "logp": data.logp,
            "h_bond_donors": data.h_bond_donors,
            "h_bond_acceptors": data.h_bond_acceptors
        }
    }


def predict_drug_effectiveness(data) -> dict:
    features = np.array([[
        data.molecular_weight,
        data.h_bond_donors,
        data.logp
    ]])

    pred_class = int(_drug_model.predict(features)[0])
    prob = _drug_model.predict_proba(features)[0]
    success_prob = round(float(prob[1]) * 100, 2)  # type: ignore[arg-type]

    # Binding score: scaled from features
    # Higher score = better binding
    mw_score = max(0, 10 - abs(data.molecular_weight - 350) / 60)
    logp_score = max(0, 5 - abs(data.logp - 2) * 0.8)
    hbd_score = max(0, 3 - max(0, data.h_bond_donors - 3))
    binding_score = round(float((mw_score + logp_score + hbd_score) / 1.8), 2)
    binding_score = min(10.0, max(0.0, binding_score))

    classification = "High Effectiveness" if pred_class == 1 else "Low Effectiveness"

    return {
        "compound_id": data.compound_id,
        "binding_score": binding_score,
        "success_probability": success_prob,
        "classification": classification,
        "drug_likeness": {
            "lipinski_compliant": (
                data.molecular_weight <= 500 and
                data.logp <= 5 and
                data.h_bond_donors <= 5
            ),
            "score_breakdown": {
                "molecular_weight_score": round(mw_score, 2),
                "logp_score": round(logp_score, 2),
                "hbd_score": round(hbd_score, 2)
            }
        }
    }
