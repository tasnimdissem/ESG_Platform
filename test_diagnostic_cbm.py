"""
Script de test diagnostique JETABLE — NE PAS COMMITTER.
Objectif : déterminer dans quel espace de représentation le modèle .cbm
attend ses features (RobustScaler vs log brut).
Aucun fichier applicatif n'est modifié.
"""
import os
import sys
import joblib
import pandas as pd

# ---------------------------------------------------------------------------
# Chemins — calqués sur ml_service.py (BASE_DIR = dossier parent de backend/)
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR   = os.path.join(SCRIPT_DIR, 'backend', 'model')
MODEL_PATH   = os.path.join(MODEL_DIR, 'catboost_model.cbm')
ENCODER_PATH = os.path.join(MODEL_DIR, 'target_encoder.pkl')
FEATURES_PATH = os.path.join(MODEL_DIR, 'feature_names.txt')

# ---------------------------------------------------------------------------
# Chargement — identique à MLService.load_resources()
# ---------------------------------------------------------------------------
try:
    from catboost import CatBoostRegressor
except ImportError:
    sys.exit("ERREUR : catboost n'est pas installé dans cet environnement.")

model = CatBoostRegressor()
model.load_model(MODEL_PATH)
print(f"[OK] Modèle chargé : {MODEL_PATH}")

with open(ENCODER_PATH, 'rb') as f:
    target_encoder = joblib.load(f)
print(f"[OK] Encodeur chargé : {ENCODER_PATH}")

with open(FEATURES_PATH, 'r') as f:
    feature_names = [line.strip() for line in f if line.strip()]
print(f"[OK] {len(feature_names)} features chargées : {feature_names}\n")


# ---------------------------------------------------------------------------
# Fonction de prédiction — identique à MLService.predict()
# ---------------------------------------------------------------------------
def predict_raw(data: dict) -> float:
    """Appelle model.predict() exactement comme le backend, sans Pydantic."""
    d = dict(data)
    # Target encoding (ml_service.py l.66-73)
    primary_industry = d.get('primary_industry', 'Unknown')
    encoder_df = pd.DataFrame([{'primary_industry': primary_industry}])
    encoded_val = target_encoder.transform(encoder_df)[0][0]
    d['industry_target_enc'] = encoded_val

    # DataFrame (ml_service.py l.76)
    input_df = pd.DataFrame([d])

    # Ajouter les colonnes manquantes (ml_service.py l.92-94)
    for col in feature_names:
        if col not in input_df.columns:
            input_df[col] = None

    # Réordonner (ml_service.py l.97)
    input_df = input_df[feature_names]

    prediction = model.predict(input_df)
    score = prediction[0] if hasattr(prediction, '__len__') else prediction
    return float(score)


# ---------------------------------------------------------------------------
# CAS 1 — Infineon Technologies AG (Semiconductors, Germany, 2020)
# Valeurs RobustScaler extraites du dataset d'entraînement
# Score cible réel : 81.567
# ---------------------------------------------------------------------------
infineon_robustscaler = {
    'primary_industry': 'Semiconductors',
    'log_market_cap': 1.8703612992654584,
    'log_employees': 1.2295512353408995,
    'log_revenue_wins': 3.288764855188855,
    'log_scope_1': 1.008055048600736,
    'log_scope_2': 0.9908219787527395,
    'log_scope_3': 0.6532052769443398,
    'log_energy_consumption': -0.1616031177005487,
    'log_waste_production': -0.3258002010106843,
    'log_water_consumption': 0.16710270734636296,
    'log_hours_of_training_wins': -5.645013945360269,
    'log_ceo_compensation': -1.4681454776168084,
    'independent_board_members_percentage': -0.7413556844653537,
    'log_legal_costs_paid_for_controversies': 1.4713695249156618,
    'intensity_scope_1': 0.9148363498635473,
    'intensity_scope_2': 0.960213016566067,
    'intensity_scope_3': 0.6135614252271567,
    'intensity_energy': -0.19849861238307967,
    'intensity_waste': -0.35996713177630385,
    'intensity_water': 0.13051566458373007,
    'intensity_training': -4.950906938616705,
    'intensity_productivity': -1.1128054336269246,
    'revenue_negative_flag': 0,
}

# ---------------------------------------------------------------------------
# CAS 2 — XANO Industri AB (Industrial Machinery, Sweden, 2019)
# Score cible réel : 8.835
# ---------------------------------------------------------------------------
xano_robustscaler = {
    'primary_industry': 'Industrial Machinery',
    'log_market_cap': -0.39474953546371594,
    'log_employees': -0.46684723729797933,
    'log_revenue_wins': -0.21018264518657753,
    'log_scope_1': -1.2349214577528576,
    'log_scope_2': -0.752862923104855,
    'log_scope_3': -0.990210918071274,
    'log_energy_consumption': 0.6093870644502114,
    'log_waste_production': 0.39154946654070205,
    'log_water_consumption': 0.2863194504090316,
    'log_hours_of_training_wins': 0.0,
    'log_ceo_compensation': 0.2556283565244892,
    'independent_board_members_percentage': 0.056136664687343324,
    'log_legal_costs_paid_for_controversies': -0.031337969601376595,
    'intensity_scope_1': -1.1647572985612675,
    'intensity_scope_2': -0.7423822554474077,
    'intensity_scope_3': -0.9892297841629684,
    'intensity_energy': 0.6255842872830655,
    'intensity_waste': 0.42843588774440805,
    'intensity_water': 0.3371441930412059,
    'intensity_training': 0.24245098049461522,
    'intensity_productivity': 0.47962540053404457,
    'revenue_negative_flag': 0,
}

# ---------------------------------------------------------------------------
# CAS 3 — Camping World Holdings (Automotive Retail, USA, 2020)
# Score cible réel : 77.984
# ---------------------------------------------------------------------------
camping_robustscaler = {
    'primary_industry': 'Automotive Retail',
    'log_market_cap': -0.04524039530541881,
    'log_employees': 0.5946534015960045,
    'log_revenue_wins': 1.9121876841605914,
    'log_scope_1': 0.3951104292496188,
    'log_scope_2': 0.36387608171452246,
    'log_scope_3': 0.10615242542579457,
    'log_energy_consumption': 0.2928290190190717,
    'log_waste_production': 0.20602371923542712,
    'log_water_consumption': -0.36246272619893516,
    'log_hours_of_training_wins': 1.2589602693930617,
    'log_ceo_compensation': -0.10713126984631566,
    'independent_board_members_percentage': -0.4875987758644309,
    'log_legal_costs_paid_for_controversies': -0.14167468562059737,
    'intensity_scope_1': 0.3608941714165124,
    'intensity_scope_2': 0.35233576860336285,
    'intensity_scope_3': 0.08643421809094629,
    'intensity_energy': 0.2714410604385108,
    'intensity_waste': 0.1981938159860144,
    'intensity_water': -0.342525103007468,
    'intensity_training': 0.26252162989612327,
    'intensity_productivity': -0.5211196066320634,
    'revenue_negative_flag': 0,
}

# ---------------------------------------------------------------------------
# TEST COMPLEMENTAIRE — valeurs par défaut "log brut" du frontend (esgIndicators.ts)
# Primary industry : "Technology" (valeur par défaut)
# ---------------------------------------------------------------------------
frontend_defaults_log_brut = {
    'primary_industry': 'Technology',
    'log_market_cap': 20.5,
    'log_employees': 8.1,
    'log_revenue_wins': 15.2,
    'log_scope_1': 4.5,
    'log_scope_2': 3.2,
    'log_scope_3': 5.1,
    'log_energy_consumption': 6.8,
    'log_waste_production': 3.4,
    'log_water_consumption': 7.2,
    'log_hours_of_training_wins': 5.0,
    'log_ceo_compensation': 14.5,
    'independent_board_members_percentage': 65.0,
    'log_legal_costs_paid_for_controversies': 0.0,
    'intensity_scope_1': 0.5,
    'intensity_scope_2': 0.3,
    'intensity_scope_3': 1.2,
    'intensity_energy': 0.8,
    'intensity_waste': 0.1,
    'intensity_water': 0.9,
    'intensity_training': 0.4,
    'intensity_productivity': 1.5,
    'revenue_negative_flag': 0,
}

# ---------------------------------------------------------------------------
# Exécution des prédictions
# ---------------------------------------------------------------------------
test_cases = [
    ("Infineon Technologies AG",     infineon_robustscaler, 81.567),
    ("XANO Industri AB",             xano_robustscaler,     8.835),
    ("Camping World Holdings",        camping_robustscaler,  77.984),
]

print("=" * 75)
print("RÉSULTATS — Espace RobustScaler (valeurs extraites du dataset)")
print("=" * 75)
print(f"{'Entreprise':<30} {'Prédit':>10} {'Réel':>10} {'Écart abs.':>12}")
print("-" * 75)

for name, features, real_score in test_cases:
    predicted = predict_raw(features)
    ecart = abs(predicted - real_score)
    print(f"{name:<30} {predicted:>10.3f} {real_score:>10.3f} {ecart:>12.3f}")

print("=" * 75)

# Test complémentaire — log brut
print()
print("=" * 75)
print("TEST COMPLÉMENTAIRE — Valeurs par défaut log brut (esgIndicators.ts)")
print("=" * 75)
score_log_brut = predict_raw(frontend_defaults_log_brut)
print(f"primary_industry : Technology")
print(f"log_market_cap   : 20.5  (vs ~1.87 RobustScaler pour Infineon)")
print(f"log_employees    : 8.1   (vs ~1.23 RobustScaler pour Infineon)")
print(f"Score obtenu     : {score_log_brut:.3f}")
print()
print("Interprétation attendue :")
print("  - Si scores RobustScaler proches des réels  → Hypothèse A (modèle entraîné sur RobustScaler)")
print("  - Si scores RobustScaler absurdes            → Hypothèse B (modèle entraîné sur autre espace)")
print("=" * 75)
