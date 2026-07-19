"""
Script autonome pour entrainer et sauvegarder les modeles.
A executer UNE SEULE FOIS en local avant de deployer sur Streamlit Cloud.

Usage :
    python train_save_models.py

Genere le dossier models/ avec :
    models/regression_model.keras
    models/classification_model.keras
    models/scaler_reg.pkl
    models/scaler_clf.pkl
"""

from model_utils import train_models

if __name__ == "__main__":
    print("Entrainement des modeles en cours...")
    model_reg, model_clf, scaler_reg, scaler_clf = train_models()
    print("Modeles entraines et sauvegardes dans le dossier 'models/'.")
