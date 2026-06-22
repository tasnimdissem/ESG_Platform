import joblib, warnings
import pandas as pd
from catboost import CatBoostRegressor
warnings.filterwarnings('ignore')

model = CatBoostRegressor()
model.load_model('backend/model/catboost_model.cbm')
encoder = joblib.load('backend/model/target_encoder.pkl')

with open('backend/model/feature_names.txt') as f:
    feat = [l.strip() for l in f if l.strip()]

def predict(d, sector):
    enc_val = float(encoder.transform(pd.DataFrame([{'primary_industry': sector}]))[0][0])
    d2 = dict(d)
    d2['industry_target_enc'] = enc_val
    df = pd.DataFrame([d2])[feat]
    return float(model.predict(df)[0])

# Profils realistes de petites entreprises mal gouvernees
scenarios = {

    "PME Industrielle en difficulte": {
        'log_market_cap': 10.0,
        'log_employees': 4.5,
        'log_revenue_wins': 9.0,
        'log_scope_1': 5.5,
        'log_scope_2': 4.8,
        'log_scope_3': 6.0,
        'log_energy_consumption': 6.5,
        'log_waste_production': 5.2,
        'log_water_consumption': 5.8,
        'log_hours_of_training_wins': 0.5,
        'log_ceo_compensation': 12.0,
        'independent_board_members_percentage': 5.0,
        'log_legal_costs_paid_for_controversies': 6.5,
        'intensity_scope_1': 1.5,
        'intensity_scope_2': 1.4,
        'intensity_scope_3': 1.8,
        'intensity_energy': 1.6,
        'intensity_waste': 0.8,
        'intensity_water': 1.5,
        'intensity_training': 0.1,
        'intensity_productivity': 2.0,
        'revenue_negative_flag': 1,
    },

    "Entreprise coal/extraction": {
        'log_market_cap': 12.0,
        'log_employees': 6.0,
        'log_revenue_wins': 11.0,
        'log_scope_1': 7.5,
        'log_scope_2': 6.5,
        'log_scope_3': 7.8,
        'log_energy_consumption': 8.0,
        'log_waste_production': 7.2,
        'log_water_consumption': 7.5,
        'log_hours_of_training_wins': 1.0,
        'log_ceo_compensation': 14.0,
        'independent_board_members_percentage': 10.0,
        'log_legal_costs_paid_for_controversies': 8.0,
        'intensity_scope_1': 1.8,
        'intensity_scope_2': 1.6,
        'intensity_scope_3': 1.9,
        'intensity_energy': 1.8,
        'intensity_waste': 0.9,
        'intensity_water': 1.7,
        'intensity_training': 0.1,
        'intensity_productivity': 3.0,
        'revenue_negative_flag': 1,
    },

    "Startup en faillite": {
        'log_market_cap': 5.0,
        'log_employees': 2.5,
        'log_revenue_wins': 4.0,
        'log_scope_1': 2.0,
        'log_scope_2': 1.5,
        'log_scope_3': 2.5,
        'log_energy_consumption': 3.0,
        'log_waste_production': 1.8,
        'log_water_consumption': 2.0,
        'log_hours_of_training_wins': 0.3,
        'log_ceo_compensation': 13.0,
        'independent_board_members_percentage': 0.0,
        'log_legal_costs_paid_for_controversies': 5.0,
        'intensity_scope_1': 1.2,
        'intensity_scope_2': 1.0,
        'intensity_scope_3': 1.5,
        'intensity_energy': 1.3,
        'intensity_waste': 0.7,
        'intensity_water': 1.2,
        'intensity_training': 0.1,
        'intensity_productivity': 1.5,
        'revenue_negative_flag': 1,
    },

    "Entreprise familiale opaque": {
        'log_market_cap': 11.0,
        'log_employees': 5.5,
        'log_revenue_wins': 10.5,
        'log_scope_1': 6.0,
        'log_scope_2': 5.0,
        'log_scope_3': 6.5,
        'log_energy_consumption': 7.0,
        'log_waste_production': 6.0,
        'log_water_consumption': 6.5,
        'log_hours_of_training_wins': 0.8,
        'log_ceo_compensation': 15.0,
        'independent_board_members_percentage': 0.0,
        'log_legal_costs_paid_for_controversies': 7.0,
        'intensity_scope_1': 1.7,
        'intensity_scope_2': 1.5,
        'intensity_scope_3': 1.8,
        'intensity_energy': 1.7,
        'intensity_waste': 0.85,
        'intensity_water': 1.6,
        'intensity_training': 0.1,
        'intensity_productivity': 2.5,
        'revenue_negative_flag': 1,
    },
}

print("="*55)
print(f"{'Scenario':<35} {'Score':>8}")
print("="*55)

best = None
for name, vals in scenarios.items():
    score = predict(vals, 'Industrials')
    print(f"{name:<35} {score:>8.2f}")
    if best is None or score < best[1]:
        best = (name, score, vals)

print("="*55)
print(f"\nMeilleur scenario : {best[0]}")
print(f"Score             : {best[1]:.2f}")
print("\nValeurs exactes :")
for k, v in best[2].items():
    print(f"  {k}: {v}")
