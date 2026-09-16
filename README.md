# TaskFlow — Gestionnaire de tâches & projets

Application web full-stack développée en Python/Flask dans le cadre d'un projet personnel.
Elle permet de gérer des projets et des tâches en style **Kanban** (Todo / En cours / Terminé).

---

## Stack technique

| Couche | Technologies |
|--------|-------------|
| **Back-end** | Python 3.11+, Flask 3.0, Flask-SQLAlchemy |
| **Base de données** | SQLite (dev) via SQLAlchemy ORM |
| **Authentification** | Session Flask + hachage via Werkzeug (algorithme par défaut : scrypt) |
| **API REST** | Blueprints Flask, JSON, status codes HTTP corrects |
| **Front-end** | HTML5, CSS3, JavaScript ES6+ (`fetch()`) |
| **Templates** | Jinja2 |
| **Tests** | pytest + pytest-flask |
| **Versioning** | Git / GitHub |

---

## Architecture

```
flask-fullstack-webapp/
├── app/
│   ├── __init__.py          # Application factory (create_app)
│   ├── extensions.py        # SQLAlchemy instance partagée
│   ├── models.py            # Modèles ORM : User, Project, Task
│   ├── helpers.py           # Utilitaires : api_response, login_required
│   └── routes/
│       ├── auth.py          # /register, /login, /logout
│       ├── views.py         # Pages HTML (dashboard, board)
│       ├── api_projects.py  # API REST /api/projects
│       └── api_tasks.py     # API REST /api/projects/<id>/tasks
├── static/
│   ├── css/style.css        # Interface moderne dark mode
│   └── js/
│       ├── dashboard.js     # Création/suppression de projets (fetch)
│       └── board.js         # Kanban : création, déplacement, suppression de tâches
├── templates/               # Jinja2 : base, index, login, register, dashboard, board
├── tests/                   # Tests pytest (auth + API projets + API tâches)
├── wsgi.py                  # Point d'entrée WSGI
├── requirements.txt
├── .env.example
└── .gitignore
```

### Modèles de données

```
User ──< Project ──< Task
```

- **User** : `id`, `username`, `email`, `password_hash`, `created_at`
- **Project** : `id`, `name`, `description`, `color`, `created_at`, `user_id`
- **Task** : `id`, `title`, `description`, `status` (todo/doing/done), `priority` (low/medium/high), `due_date`, `created_at`, `project_id`

---

## Lancer le projet

### 1. Cloner et installer

```bash
git clone <url-du-repo>
cd flask-fullstack-webapp

python -m venv venv
source venv/bin/activate   # Windows : venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Configuration

```bash
cp .env.example .env
# Modifier SECRET_KEY dans .env avant de déployer en production
```

### 3. Démarrer le serveur

```bash
flask --app wsgi.py run --debug
# ou : python wsgi.py
```

Ouvrir [http://localhost:5000](http://localhost:5000)

### 4. Lancer les tests

```bash
pytest tests/ -v
```

---

## Endpoints API REST

Tous les endpoints nécessitent une session active (authentification).
Format de réponse uniforme : `{ "success": bool, "data": ..., "error": str|null }`.

### Projets

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/api/projects` | Liste tous les projets de l'utilisateur |
| `POST` | `/api/projects` | Créer un projet (`name`, `description`, `color`) |
| `GET` | `/api/projects/<id>` | Détail d'un projet (avec ses tâches) |
| `PUT` | `/api/projects/<id>` | Mettre à jour un projet |
| `DELETE` | `/api/projects/<id>` | Supprimer un projet et ses tâches |

### Tâches

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/api/projects/<id>/tasks` | Liste les tâches (filtre `?status=todo\|doing\|done`) |
| `POST` | `/api/projects/<id>/tasks` | Créer une tâche (`title`, `status`, `priority`, `due_date`) |
| `GET` | `/api/projects/<id>/tasks/<tid>` | Détail d'une tâche |
| `PUT` | `/api/projects/<id>/tasks/<tid>` | Modifier une tâche (dont changer le statut) |
| `DELETE` | `/api/projects/<id>/tasks/<tid>` | Supprimer une tâche |

---

## Fonctionnalités

- Inscription / connexion avec mots de passe hashés
- Tableau de bord avec liste des projets
- Tableau Kanban par projet (3 colonnes : À faire, En cours, Terminé)
- Création et suppression de projets sans rechargement (fetch API)
- Création, édition, déplacement et suppression de tâches sans rechargement
- Priorité visuelle sur les tâches (faible / normale / haute)
- Date d'échéance par tâche
- Isolation stricte des données : chaque utilisateur ne voit que ses projets

---

## Sécurité

- Mots de passe hachés avec le défaut sécurisé de Werkzeug (`scrypt` pour la version déclarée)
- `SECRET_KEY` lue depuis l'environnement ; une valeur de développement est présente et doit impérativement être remplacée avant publication
- Vérification de propriété sur chaque ressource (anti IDOR)
- Validation des inputs côté serveur avec messages d'erreur clairs
- Cookies de session `httponly` et `samesite=Lax`

---

*Projet réalisé par Yacine Ouasti — étudiant BBA, dans le cadre d'une démarche d'apprentissage du développement web full-stack.*

## Contrats API et limites

Les créations/modifications exigent un **objet JSON**, des champs textuels typés et des longueurs bornées. Une date d'échéance accepte `YYYY-MM-DD`, `null` ou une chaîne vide ; `null` efface la date lors d'un PUT. Un filtre de statut inconnu retourne 400. Les données d'un autre utilisateur retournent 404. Une session pointant sur un utilisateur absent est invalidée (401 en API / redirection vers connexion en HTML).

Les tests utilisent SQLite en mémoire ; ils vérifient aussi qu'un PUT invalide ne modifie pas la ressource, et qu'un utilisateur ne peut lire, modifier ou supprimer les tâches d'un autre.

Ce dépôt reste un démonstrateur : pas de migrations versionnées, pagination, limite de tentatives de connexion, journal d'audit ou preuve de charge. La protection CSRF dédiée, la rotation des secrets et le cookie Secure/HTTPS restent à intégrer avant une exposition publique. Ne pas présenter la présence de `SameSite=Lax` comme une protection CSRF complète. La base locale existante n'est pas utilisée par les tests.
