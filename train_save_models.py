"""
Script autonome pour entraîner et sauvegarder les modèles.
À exécuter une fois si vous ne voulez pas que l'application les entraîne à chaque lancement.
"""

from model_utils import train_models

if __name__ == "__main__":
    print("Entraînement des modèles en cours...")
    model_reg, model_clf, scaler_reg, scaler_clf = train_models()
    print("Modèles entraînés et sauvegardés dans le dossier 'models/'.")