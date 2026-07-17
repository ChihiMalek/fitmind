# FitMind

Application web de prédiction des calories brûlées et de classification du niveau d'expérience en salle de sport.

## Accès en ligne

👉 [Lien vers l'application Streamlit Cloud] *(à ajouter après déploiement)*

## Fonctionnalités

- **Régression** : Estimation précise des calories brûlées (R² > 0.99)
- **Classification** : Détermination du niveau d'expérience (Débutant / Intermédiaire / Avancé)
- **Interface sportive** : Thème dynamique avec palette noir, orange, rouge
- **Visualisations interactives** : Barres de probabilités, métriques en temps réel
- **Entraînement automatique** : Les modèles sont entraînés à la volée si absents

## Modèles utilisés

- **Régression** : Réseau de neurones dense (64 → 32 → 16 → 1) avec Dropout et Early Stopping
- **Classification** : Réseau de neurones dense (64 → 32 → 16 → 3) avec Softmax

## Dataset

- 973 observations issues du dataset Gym
- 11 variables physiologiques (âge, poids, taille, BPM, durée, hydratation, fréquence, etc.)
- Cibles : `Calories_Burned` (continue) et `Experience_Level` (catégorielle 1-3)

## Installation locale

```bash
git clone https://github.com/votre-username/fitmind.git
cd fitmind
pip install -r requirements.txt
streamlit run app.py