#!/usr/bin/env python3
"""Download ML models from external storage (e.g., S3, GCS).

This script is run at startup to ensure models are available.
In production, store models in S3/GCS instead of Git.
"""

import os
import sys
from pathlib import Path


def setup_models_for_dev():
    """
    In development, models should be available locally.
    In production, implement download from S3/GCS.
    """
    model_dir = Path(__file__).parent.parent / 'backend' / 'model'
    model_dir.mkdir(parents=True, exist_ok=True)
    
    required_files = [
        'catboost_model.cbm',
        'target_encoder.pkl',
        'feature_names.txt',
    ]
    
    missing_files = [f for f in required_files if not (model_dir / f).exists()]
    
    if missing_files:
        print(f"⚠️  Missing model files: {missing_files}")
        print("Models should be stored in S3/GCS, not in Git.")
        print("To download models, implement download logic here or manually place files in backend/model/")
        
        if os.getenv('FLASK_ENV') == 'production':
            raise RuntimeError(
                f"CRITICAL: Model files not found in production: {missing_files}. "
                "Configure MODEL_S3_BUCKET or MODEL_GCS_BUCKET to download models."
            )
        else:
            print("Development mode: proceeding without models (predictions will fail if unavailable)")
            return False
    
    print("✓ All model files present")
    return True


if __name__ == '__main__':
    setup_models_for_dev()
