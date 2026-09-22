# 🧊 Smart Fridge & Nutrition Coach 
Concevoir et développer de zéro une application web fullstack complète de coaching nutritionnel intelligent.

## 📌 Présentation du Projet
**Smart Fridge & Nutrition Coach** est une application web moderne permettant à un utilisateur de :
- Créer un compte sécurisé **(JWT)**
- Renseigner son profil corporel : Poids, Taille, Âge, Sexe, Activité physique, Objectif
- Gérer les ingrédients disponibles dans son frigo
- Recevoir des suggestions de recettes basées sur **TheMealDB**
- Calculer les calories et macronutriments réels via l’**API USDA**
- Générer un plan alimentaire cohérent avec son métabolisme 

Ce projet est développé dans le cadre du Module **Python & FastAPI** (~35h).

## 📁 Arborescence du Projet 
```
Smart-Fridge
├── app
│   ├── core
│   ├── routers
│   ├── schemas
│   ├── services
│   ├── static
│   │   ├── css
│   │   └── js
│   ├── templates
│   ├── utils
│   └── __init__.py
├── tests
├── config.py
├── database.py
├── json_store.py
├── main.py
└── venv/
```

## 🧩 Description des dossiers
* `app/` Contient tout le code de l’application.
* `app/core/` Paramètres gloabaux : sécurité, gestion JWT, settings Pydantic
* `app/routers/` Tous les endpoints FastAPI : auth, profil, frigo, suggestions, recettes
* `app/schemas/` Modèles Pydantic : validation stricte, structures pour **TheMealDB**, structures pour **USDA**, profil utilisateur, moteur métabolique
* `app/services/` Logique métier : clients API, moteur de suggestions, mapping lexical, calculs nutritionnels, gestion d'erreurs
* `app/static/` Fichiers statiques
* `app/templates/` Templates Jinja2 
* `app/utils/` Fonctions utilitaires
* `config.py` Chargement des variables d’environnement
* `database.py` Connexion à Supabase
* `json_store.py` Stockage local des ingrédients
* `main.py` Point d’entrée FastAPI.

**venv/** Environnement virtuel Python.

## ⚙️ Fonctionnalités Principales 
### 🔐 1. Espace Utilisateur & Sécurité
- Inscription & connexion via JWT
- Hachage des mots de passe
- Protection des routes privées (Depends)
- CORS configuré proprement

### 🧮 2. Profil Métabolique & Calculs Nutritionnels
- Schémas Pydantic stricts
- Formule de Mifflin-St Jeor
- Calcul du TDEE selon l’activité
- Gestion des objectifs : perte, maintien, prise
- Répartition automatique des macronutriments

### 🧊 3. Frigo Intelligent
- Ajout / suppression d’ingrédients
- Normalisation des noms
- Synchronisation avec Supabase

### 🍽️ 4. Moteur de Suggestions
- Requêtes **TheMealDB** par ingrédients
- Requêtes **USDA** pour chaque ingrédient
- Extraction des macros via foodNutrients
- Scoring des recettes

## 🧪 Prérequis
- Python **3.10+**
- pip ou pipx
- Accès internet (APIs externes)
- Clés API
- Supabase

## 🐍 Utilisation d’un environnement virtuel (venv)
Nous avons fait le choix de se mettre en environnement virtuels pour plus facilement supprimer ou contrôler le téléchargement de dépendances lors du développement du projet 
Voici comment faire pour créer cet environnement : 
### Création 
```bash
python -m venv venv
```
### Activation 
Windows : 
```Windows PowerShell
venv\Scripts\Activate.ps1
```
Linux : 
```bash
source venv/bin/activate
```
### Installation des dépendances
```bash
pip install -r requirements.txt
```

## 🔧 Installation & Configuration
### 1. Cloner le projet 
```bash
git clone https://github.com/loschoe/Smart-Fridge.git
cd Smart-Fridge
```
### 2. Créer et activer le venv 
*(Voir la section précédente)*

### 3. Configurer le `.env`
```py
SECRET_KEY=...
USDA_API_KEY=...
SUPABASE_URL=...
SUPABASE_KEY=...
```

### 4. Lancer le serveur FastAPI 
```bash
uvicorn app.main:app --reload
```

Si aucune erreur n'apparait vous devriez avoir ce résultat en console : 
```uvicorn
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [11352] using WatchFiles
INFO:     Started server process [23152]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```
Vous pouvez alors vous connecter : http://127.0.0.1:8000

## 🧠 Architecture & Choix Techniques
Nous avons fait le choix d'une architecture simple et logique où chaque fichier à son rôle et sa fonctionnalité afin de s'y retrouver lors du dev et du debug.
Le choix des technologies était imposé par le cahier des charges du projet. 

## 🤖 Utilisation de l'Intelligence Artificielle
Dans le cadre de ce projet, nous avons adopté une approche dynamique et responsable de l'utilisation des IA génératives, en veillant scrupuleusement à éviter le « vibe coding ». 
<br>L'IA a servi d'outil d'apprentissage et d'assistance ciblée, chaque modèle ayant été sollicité pour des rôles spécifiques afin de maximiser notre productivité tout en conservant le contrôle total sur notre code :

- **GitHub Copilot** (Gestion de projet) : Utilisé comme chef de projet virtuel pour structurer notre rétroplanning et organiser la répartition quotidienne des fonctionnalités.
- **ChatGPT & Gemini** (Assistants Dev) : Mobilisés comme soutiens au développement pour nous débloquer face aux difficultés de logique, expliquer des concepts et accélérer notre apprentissage.
- **Claude** (CSS & Optimisation) : Sollicité pour l'intégration CSS — parce qu'en 2026, plus personne ne monte un design complexe entièrement à la main ! — ainsi que pour la relecture, l'amélioration et l'optimisation de nos fonctions algorithmiques les plus critiques.

## 🧩 Démo
[Ajouter le contenu de cette rubrique à la fin du projet]

## 👥 Licence & Collaborateurs
* **Libre d'accès et d'apprentissage :** Vous êtes libres de consulter le code, de le forker et de proposer des améliorations.
* **Contributions bienvenues :** Les *Pull Requests* sont les bienvenues pour corriger des bugs, optimiser le code ou proposer de nouvelles fonctionnalités. Tout ajout validé intégrera le projet original.
* **Pas d'appropriation :** Ce projet reste la propriété de ses auteurs originaux. Vous devez conserver la mention des auteurs initiaux dans toute copie ou modification.
* **Usage commercial strictement interdit :** Aucune réutilisation, revente ou exploitation commerciale (directe ou indirecte) du code et du projet n'est autorisée.

[Loschoe](https://github.com/loschoe) [Esqaaa](https://github.com/Esqaaa)


