import os
import joblib
import pandas as pd

# Safe relative paths based on the project structure (backend/services/ml_service.py -> backend/model)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, 'model')

MODEL_PATH = os.path.join(MODEL_DIR, 'catboost_model.cbm')
ENCODER_PATH = os.path.join(MODEL_DIR, 'target_encoder.pkl')
FEATURES_PATH = os.path.join(MODEL_DIR, 'feature_names.txt')

class MLService:
    """
    Singleton service to handle Machine Learning operations, ensuring models
    are loaded only once into memory.
    """
    def __init__(self):
        self.model = None
        self.target_encoder = None
        self.feature_names = []
        self.is_loaded = False

    def load_resources(self):
        """Loads the CatBoost model, target encoder, and feature names safely."""
        if self.is_loaded:
            return

        try:
            try:
                from catboost import CatBoostRegressor
            except ImportError as exc:
                raise RuntimeError(
                    "CatBoost is not installed in this environment. Install backend requirements before using prediction."
                ) from exc

            # 1. Load CatBoost Model
            self.model = CatBoostRegressor()
            self.model.load_model(MODEL_PATH)

            # 2. Load Target Encoder
            with open(ENCODER_PATH, 'rb') as f:
                self.target_encoder = joblib.load(f)

            # 3. Load Feature Names
            with open(FEATURES_PATH, 'r') as f:
                self.feature_names = [line.strip() for line in f if line.strip()]

            self.is_loaded = True
        except Exception as e:
            raise RuntimeError(f"Failed to load ML resources: {str(e)}")

    def predict(self, data: dict) -> float:
        """Processes the input data and returns the prediction score."""
        # Ensure resources are loaded before predicting
        self.load_resources()

        try:
            # 1. Handle Target Encoding for primary_industry
            if hasattr(self.target_encoder, 'transform'):
                # Extract primary_industry, default to 'Unknown' if not provided
                primary_industry = data.get('primary_industry', 'Unknown')
                encoder_df = pd.DataFrame([{'primary_industry': primary_industry}])
                
                # Transform and get the numerical value
                encoded_val = self.target_encoder.transform(encoder_df)[0][0]
                
                # Inject it back into the data dictionary under the expected feature name
                data['industry_target_enc'] = encoded_val

            # 2. Create a DataFrame from the input JSON
            input_df = pd.DataFrame([data])
            
            # Align columns: add missing columns as None/NaN
            for col in self.feature_names:
                if col not in input_df.columns:
                    input_df[col] = None
                    
            # 3. Reorder columns to exactly match what the CatBoost model expects
            input_df = input_df[self.feature_names]

            # Make prediction
            prediction = self.model.predict(input_df)
            
            # CatBoost predict() usually returns an array/list, grab the first element
            score = prediction[0] if isinstance(prediction, (list, tuple, pd.Series, type(pd.array([])))) or hasattr(prediction, '__len__') else prediction
            
            # Optional: ensure score matches typical JSON float format, round if needed
            return float(round(score, 2))
        except Exception as e:
            raise ValueError(f"Error during prediction logic: {str(e)}")

# Create a singleton instance to be used across the application
ml_service_instance = MLService()

def predict_esg(data: dict) -> float:
    """
    Public function exposed to the routes. 
    Receives JSON input (data dictionary) and returns the predicted ESG score.
    """
    return ml_service_instance.predict(data)
