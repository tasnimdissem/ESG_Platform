#!/usr/bin/env python3
"""Download and cache the sentence-transformers model once."""

from sentence_transformers import SentenceTransformer

try:
    print("Téléchargement du modèle sentence-transformers/all-MiniLM-L6-v2...")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    print("✅ Modèle téléchargé et en cache localement.")
    print(f"Dimension: {model.get_sentence_embedding_dimension()}")
except Exception as e:
    print(f"❌ Erreur: {e}")
    print("\nSolutions:")
    print("1. Vérifiez votre connexion réseau")
    print("2. Essayez à nouveau dans 30 secondes")
    print("3. Utilisez un VPN si HuggingFace est bloqué")
    exit(1)
