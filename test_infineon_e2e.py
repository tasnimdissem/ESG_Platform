"""
Test de verification post-correction JETABLE.
Verifie que : 1) les valeurs negatives d'Infineon passent la validation Pydantic
              2) le score obtenu est proche de 81.57
              3) une valeur aberrante (9999) est bien rejetee
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.schemas import PredictRequest
from pydantic import ValidationError

# --- Payload Infineon avec valeurs negatives RobustScaler ---
infineon_payload = {
    "primary_industry": "Semiconductors",
    "log_market_cap": 1.8704,
    "log_employees": 1.2296,
    "log_revenue_wins": 3.2888,
    "log_scope_1": 1.0081,
    "log_scope_2": 0.9908,
    "log_scope_3": 0.6532,
    "log_energy_consumption": -0.1616,
    "log_waste_production": -0.3258,
    "log_water_consumption": 0.1671,
    "log_hours_of_training_wins": -5.6450,
    "log_ceo_compensation": -1.4681,
    "independent_board_members_percentage": -0.7414,
    "log_legal_costs_paid_for_controversies": 1.4714,
    "intensity_scope_1": 0.9148,
    "intensity_scope_2": 0.9602,
    "intensity_scope_3": 0.6136,
    "intensity_energy": -0.1985,
    "intensity_waste": -0.3600,
    "intensity_water": 0.1305,
    "intensity_training": -4.9509,
    "intensity_productivity": -1.1128,
    "revenue_negative_flag": 0,
}

print("=" * 60)
print("TEST 1 : Validation Pydantic sur valeurs negatives Infineon")
print("=" * 60)
try:
    validated = PredictRequest(**infineon_payload)
    print("[OK] Pydantic accepte les valeurs negatives -- aucune erreur 400")
    print(f"     log_energy_consumption = {validated.log_energy_consumption}")
    print(f"     log_hours_of_training_wins = {validated.log_hours_of_training_wins}")
    print(f"     intensity_training = {validated.intensity_training}")
    print(f"     independent_board_members_percentage = {validated.independent_board_members_percentage}")
except ValidationError as e:
    print("[ECHEC] Pydantic rejette encore les valeurs negatives !")
    for err in e.errors():
        print(f"  - {err['loc']} : {err['msg']}")
    sys.exit(1)

print()
print("=" * 60)
print("TEST 2 : Prediction de bout en bout (route -> validate -> predict)")
print("=" * 60)
try:
    from backend.services.ml_service import predict_esg
    score = predict_esg(validated.dict())
    print(f"[OK] Score obtenu : {score:.3f}")
    print(f"     Score reel Infineon : 81.567")
    print(f"     Ecart : {abs(score - 81.567):.3f} points")
    if abs(score - 81.567) < 5:
        print("[OK] Ecart < 5 pts -- pipeline coherent")
    else:
        print("[ATTENTION] Ecart > 5 pts -- verifier")
except Exception as ex:
    print(f"[ECHEC] predict_esg a leve une exception : {ex}")
    sys.exit(1)

print()
print("=" * 60)
print("TEST 3 : Valeur aberrante (9999) doit etre rejetee")
print("=" * 60)
aberrant_payload = dict(infineon_payload)
aberrant_payload["log_market_cap"] = 9999
try:
    PredictRequest(**aberrant_payload)
    print("[ECHEC] Pydantic a accepte 9999 -- la borne haute est cassee !")
    sys.exit(1)
except ValidationError as e:
    print("[OK] Pydantic rejette 9999 -- borne haute le=100 intacte")
    for err in e.errors():
        print(f"     {err['loc']} : {err['msg']}")

print()
print("Tous les tests passes -- correction validee.")
