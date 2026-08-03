# FitMind AI — Architecture du Dashboard Premium

**Phase 2, Étape 1** · Document d'architecture · **v2 — ajustements validés**

---

## 0. Addendum v2 — ajustements intégrés

Suite à validation, 4 ajustements sont intégrés à l'architecture ci-dessous :

1. **Nouveau dossier `services/`** — toute la logique métier (recommandations, confiance, objectifs, agrégations d'historique) en sort de `dashboard/`. Les composants `dashboard/` ne font plus **que** de l'affichage : ils reçoivent des données déjà calculées.
2. **Gestion d'états explicite** (`dashboard/states.py`) — `EMPTY` / `LOADING` / `ERROR` / `READY`, avec un écran dédié pour chacun, réutilisable telle quelle par les futures pages Historique/Analytics.
3. **Dashboard orienté action** — ajout d'une **zone 0**, un bandeau "Statut & Action" en tête de page (avant même les KPI), qui condense en une lecture : état général, objectif, et la prochaine action recommandée avec un bouton CTA. Ce n'était auparavant qu'une carte parmi d'autres en colonne latérale — elle devient la porte d'entrée visuelle de la page.
4. **Réutilisabilité** — `services/` et les atomes de `dashboard/components.py`/`states.py` sont écrits sans dépendance au mot "Dashboard" : mêmes fonctions consommables telles quelles par Historique, Analytics, AI Coach et Settings quand ces phases arriveront.

Le reste du document (§1 à §8) est mis à jour en conséquence ci-dessous.

---

## 1. Périmètre de cette étape

Cette étape construit **uniquement** le Dashboard (point d'entrée principal). Elle ne construit pas Historique SQLite, Analytics, AI Coach complet, Model Evaluation (déjà existant côté admin) ni Settings — ces pages arrivent aux phases suivantes de la roadmap déjà validée.

**Conséquence directe sur la navigation cible :**

```
Accueil/Dashboard  ✅ CETTE ÉTAPE
Nouvelle prédiction ✅ existe déjà (prediction_form), simplement rattachée à la nav
Historique          ⏳ phase suivante (SQLite)
Analytics            ⏳ phase suivante
AI Coach             ⏳ phase suivante (texte généré complet)
Model Evaluation     ✅ existe déjà côté admin, sera exposé au client à sa phase
Settings              ⏳ dernière phase
```

Je n'ajoute donc **que deux entrées de navigation client** pour l'instant : `🏠 Dashboard` et `🔮 Nouvelle prédiction`. Les autres entrées seront ajoutées une par une, au moment où leur page existera réellement — pour ne jamais avoir de lien mort dans l'app.

### Fonctionnalités demandées section 4 : ce qui est possible maintenant vs. plus tard

| Composant demandé | Statut cette étape | Raison |
|---|---|---|
| KPI Cards | ✅ Réel, données de la dernière prédiction | — |
| Gauge Charts (BMI, zone cardiaque) | ✅ Réel | — |
| Radar Chart | ✅ Réel, basé sur `feature_distributions` déjà en metadata | — |
| Donut Chart | ✅ Réel si ≥1 prédiction en session ; état vide sinon | Pas de persistance encore |
| Trend Chart | ✅ Réel si ≥2 prédictions en session ; état vide sinon | Idem |
| Session Summary | ✅ Réel, recap de la dernière prédiction | — |
| Confidence Score | ✅ Réel — **réutilise** `compute_global_confidence()` déjà écrit (aucune duplication) | — |
| Recommendation Preview | ⚠️ Version allégée : **extraction** de la logique déjà présente dans `prediction_form` (le bloc "Analyse et recommandations") vers une fonction partagée. Pas encore le vrai AI Coach (phase #5) | Évite la duplication de code, prépare le terrain pour l'AI Coach complet sans tout reconstruire |
| Weekly Goal / Daily Progress / Calories Goal | ⚠️ Version **session-only** : un objectif saisi dans la session (non persistant), clairement étiqueté "objectif temporaire" | Un vrai objectif persistant appartient à User Profile (phase #4). Je ne construis pas un système d'objectifs à moitié maintenant pour le refaire ensuite. |

Cette approche respecte ta contrainte "ne jamais dupliquer de code" : la logique de recommandation et le score de confiance ne sont **pas réécrits**, seulement **extraits et réutilisés**.

---

## 2. Arborescence du module `dashboard/`

```
FitMind-AI/
├── app.py                      (MODIFIÉ)
├── model_utils.py               (inchangé — compute_global_confidence reste la source de calcul)
├── evaluation_utils.py          (inchangé)
├── services/                    (NOUVEAU) — logique métier, aucun rendu visuel
│   ├── __init__.py
│   ├── confidence_service.py    — enveloppe model_utils.compute_global_confidence pour une interface stable côté pages
│   ├── recommendation_service.py — logique de recommandation EXTRAITE de prediction_form (aucune duplication)
│   ├── goals_service.py          — objectifs session-only : lecture/écriture st.session_state, calcul de progression
│   └── history_service.py        — agrégations sur st.session_state.predictions (dernière séance, moyenne, tendance, meilleure séance)
├── dashboard/                   (NOUVEAU) — présentation uniquement, aucune logique métier
│   ├── __init__.py
│   ├── theme.py                 — tokens visuels (couleurs, rayons, ombres)
│   ├── states.py                 — écrans Empty / Loading / Error / Ready, réutilisables par les futures pages
│   ├── components.py            — atomes UI génériques réutilisables
│   ├── cards.py                 — cartes (statut/action, KPI, résumé, objectifs, coach, confiance)
│   ├── charts.py                — figures Plotly (gauges, radar, donut, trend)
│   ├── layout.py                — orchestration de la grille de page
│   └── dashboard_page.py        — point d'entrée : appelle services/, résout l'état via states.py, puis layout.py
```

### Règle de dépendance (respect de la séparation des responsabilités)

```
app.py  →  dashboard/dashboard_page.py  →  services/*  (données brutes → données calculées)
                                        →  dashboard/states.py  (quel écran afficher)
                                        →  dashboard/layout.py  →  cards.py + charts.py  (affichage pur)
```

`dashboard/cards.py` et `dashboard/charts.py` ne font **jamais** appel à `st.session_state` ni à `model_utils` directement — ils reçoivent uniquement des valeurs déjà calculées par `services/`. C'est ce qui rend chaque composant testable et réutilisable indépendamment de la page Dashboard.

### Responsabilité unique de chaque fichier

| Fichier | Responsabilité | Ne fait PAS |
|---|---|---|
| `services/confidence_service.py` | Interface stable `get_confidence(features) -> dict` au-dessus de `model_utils.compute_global_confidence` | Ne recalcule rien — délègue entièrement |
| `services/recommendation_service.py` | `get_recommendation(prediction) -> {text, action, priority}` — logique extraite de `prediction_form` | Ne fait aucun rendu HTML/Streamlit |
| `services/goals_service.py` | Lecture/écriture de l'objectif session (`st.session_state`), calcul `% de progression` | Ne persiste rien en base (pas encore de SQLite) |
| `services/history_service.py` | Agrégations sur `st.session_state.predictions` : dernière séance, moyenne, tendance, meilleure séance | Ne fait aucun graphique — retourne des nombres/listes |
| `theme.py` | Source unique des couleurs/rayons/ombres du Dashboard | Ne rend aucun HTML |
| `states.py` | Décide et rend l'écran actif : `render_empty()`, `render_loading()`, `render_error()`, ou laisse passer vers `layout.render_ready()` | Ne calcule aucune donnée métier |
| `components.py` | Atomes génériques : conteneur de carte, badge d'état, en-tête de section, grille responsive | Ne connaît aucune donnée métier |
| `cards.py` | Compose les atomes en cartes métier, y compris la nouvelle **carte Statut & Action** | Ne calcule aucune métrique — reçoit des valeurs déjà calculées par `services/` |
| `charts.py` | Construit les `go.Figure` Plotly | Ne fait pas de mise en page Streamlit |
| `layout.py` | Dispose les cartes/graphiques dans la grille, y compris la nouvelle zone 0 (Statut & Action) | Ne calcule rien, n'appelle jamais `services/` directement |
| `dashboard_page.py` | Point d'entrée : appelle `services/`, résout l'état via `states.py`, appelle `layout.render()` si `READY` | Ne contient pas de HTML/CSS brut |

Cette séparation permet d'ajouter une nouvelle carte, un nouveau graphique, ou une nouvelle règle de recommandation en ne touchant qu'un seul fichier — sans jamais modifier `layout.py` ni `dashboard_page.py`.

---

## 3. Flux de données

```
app.py (nav = "🏠 Dashboard")
   │
   ▼
dashboard_page.render(user, predictions, metadata)
   │
   ├─ état = states.resolve(predictions)             → EMPTY si aucune prédiction
   │                                                     READY sinon (ERROR si exception levée plus bas)
   │
   ├─ si EMPTY  → states.render_empty()  (invitation + CTA vers "🔮 Nouvelle prédiction") → FIN
   ├─ si ERROR  → states.render_error(message)                                            → FIN
   │
   ├─ si READY :
   │     latest      = history_service.get_latest(predictions)
   │     summary      = history_service.get_summary(predictions)      (moyenne, tendance, meilleure séance)
   │     confidence   = confidence_service.get_confidence(latest.features)   [délègue à model_utils]
   │     recommendation = recommendation_service.get_recommendation(latest, confidence)
   │     goal         = goals_service.get_progress(summary)            (session-only)
   │
   ▼
layout.render_ready(status_data, kpi_data, chart_data, coach_data, history_data, goal_data)
   │
   ├─ Zone 0 → cards.status_action_card()       (statut + objectif + action recommandée + CTA)
   ├─ Zone 1 → cards.kpi_card() × 6              (via components.responsive_grid)
   ├─ Zone 2 → charts.bmi_gauge(), charts.hr_zone_gauge(), charts.radar_profile(),
   │            charts.calories_trend() / charts.workout_donut()
   ├─ Colonne latérale → cards.recommendation_detail_card(), cards.confidence_score_card(), cards.goal_card()
   └─ Bas de page → cards.session_summary_card() + liste historique
                     (bandeau "Historique temporaire (session uniquement)")
```

**Point clé :** `dashboard_page.py` n'appelle jamais `model_utils` ni ne lit `st.session_state.predictions` directement pour en extraire une métrique — il passe systématiquement par `services/`. C'est ce qui garantit qu'Historique/Analytics pourront réutiliser les mêmes fonctions de service sans dupliquer le calcul.

---

## 4. Organisation visuelle (page orientée action)

| Zone | Répond à | Contenu |
|---|---|---|
| **Zone 0 — Bandeau Statut & Action** (nouveau, en tête de page) | *Où en est l'utilisateur, là, maintenant ?* + *Que dois-je faire ensuite ?* | Statut condensé (bon/attention), objectif en cours, **une** action recommandée avec bouton CTA — lisible en 3 secondes, avant tout graphique |
| **Ligne 1 — KPI Cards** | *Comment va l'utilisateur aujourd'hui ?* | Calories, IMC, Max_BPM (zone), Hydratation, Type d'entraînement, Score de confiance |
| **Ligne 2 — Graphiques principaux** | *Comment évoluent ses performances ?* + *Quelle a été sa dernière séance ?* | Jauge IMC, jauge zone cardiaque, radar profil, courbe de tendance (ou donut si historique trop court) |
| **Colonne latérale** | Détail derrière l'action recommandée en Zone 0 | Recommandation détaillée, Confidence Score détaillé, Objectif détaillé |
| **Bas de page** | Support des questions 2 et 3 | Résumé de séance, historique temporaire (liste), bandeau objectifs |

La Zone 0 est ce qui rend la page "orientée action" : l'utilisateur n'a pas besoin de lire les graphiques pour savoir quoi faire — la colonne latérale et les graphiques *justifient* la recommandation, ils ne la remplacent pas.

---

## 5. Fichiers impactés

### Modifiés
- **`app.py`** :
  - Ajout d'une navigation client (actuellement absente). Nouveau `st.radio` sidebar avec `["🏠 Dashboard", "🔮 Nouvelle prédiction"]`.
  - `show_client()` route désormais vers `dashboard_page.render(...)` ou `prediction_form(...)`.
  - Le bloc "Analyse et recommandations" actuellement en dur dans `prediction_form` est remplacé par un appel à `services/recommendation_service.get_recommendation(...)` — **la logique est déplacée, pas dupliquée**, et `prediction_form` continue d'afficher un résultat identique à aujourd'hui.
- Aucun autre fichier existant n'est modifié.

### Créés
- `services/__init__.py`, `confidence_service.py`, `recommendation_service.py`, `goals_service.py`, `history_service.py`
- `dashboard/__init__.py`, `theme.py`, `states.py`, `components.py`, `cards.py`, `charts.py`, `layout.py`, `dashboard_page.py`

### Inchangés
- `model_utils.py`, `evaluation_utils.py`, `train_save_models.py`, `requirements.txt`, toutes les pages admin existantes

---

## 6. Dépendances et impacts

- **Aucune nouvelle dépendance Python** : Plotly est déjà dans `requirements.txt`.
- **Impact sur le CSS global** : `dashboard/theme.py` introduit des tokens dédiés (cartes arrondies, ombres légères), en ajout — pas en remplacement du CSS existant.
- **Réutilisabilité par construction** : `services/*` et `dashboard/states.py`/`components.py` n'ont aucune dépendance au mot "dashboard" dans leur logique — ce sont des fonctions/composants génériques que `dashboard_page.py` assemble. Historique, Analytics, AI Coach et Settings pourront les importer directement.
- **Risque identifié** : l'historique étant en `st.session_state`, le Dashboard sera vide à chaque redémarrage — géré par l'état `EMPTY` de `states.py` et le bandeau "Historique temporaire (session uniquement)".
- **Aucune fonctionnalité existante retirée.**

---

## 7. Style visuel (réponse au §7)

- Cartes à coins arrondis (12–16px) avec ombre légère plutôt que les bordures nettes actuelles — appliqué uniquement aux nouveaux composants `dashboard/`, sans toucher au style des pages existantes.
- Palette conservée (bleu acier `#3A8FD4`, or `#D4A830`, fond `#08111E`) mais tokens centralisés dans `theme.py` pour cohérence et réutilisation future.
- Icônes cohérentes (même famille d'émoji/pictos que le reste de l'app).
- Animations discrètes : transitions CSS légères sur hover des cartes (déjà présentes ailleurs dans l'app, reprises ici).
- Responsive : grille en `auto-fit`/`minmax`, les cartes KPI passent de 6 par ligne à 2–3 par ligne sur écran étroit.

---

## 8. Ce qui reste hors périmètre (pour rester honnête sur ce qui sera livré)

- Pas de vraie persistance (→ phase Historique SQLite)
- Pas de vrai système d'objectifs (→ phase User Profile)
- Pas de génération de texte IA sophistiquée pour les recommandations (→ phase AI Coach) — seulement la réutilisation de règles déjà existantes
- Pas d'écran de bienvenue animé ni de transitions globales (→ phase UX finale #10), au-delà des états vides nécessaires au Dashboard lui-même
