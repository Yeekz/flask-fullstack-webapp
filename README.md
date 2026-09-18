# TaskFlow — Gestionnaire de tâches & projets

Application web full-stack développée en Python/Flask dans un cadre d'apprentissage.
Elle permet de gérer des projets et des tâches en style **Kanban** (Todo / En cours / Terminé).

## Essayer en ligne

**[▶ Essayer la démonstration TaskFlow](https://taskflow.62-171-168-208.nip.io)**

Cliquez sur **Essayer la démo**, puis sur **Avancer** pour déplacer une tâche.
Vous pouvez aussi créer, modifier et supprimer des tâches et des projets.
Aucun compte, mot de passe ou e-mail personnel n'est demandé.

Chaque visiteur reçoit son propre espace, avec trois tâches fictives. Les modifications
restent disponibles après un rechargement dans le même navigateur, pendant **2 heures
à partir de la création**. « Quitter la démo » supprime cet espace immédiatement.
Limites : **3 projets par invité, 20 tâches par projet et 40 invités simultanés**.
Les espaces expirés sont supprimés lors de la prochaine ouverture d'un nouvel espace.
À capacité maximale, la page invite à réessayer plus tard. Ne saisir que des exemples
fictifs : ce démonstrateur n'est pas un service de stockage de données personnelles.

Le mode normal d'inscription/connexion reste disponible en local avec `DEMO_MODE=0`.
La démonstration publique désactive ces deux routes et n'expose aucun compte réel.

---

## Stack technique

| Couche | Technologies |
|--------|-------------|
| **Back-end** | Python 3.11+, Flask 3.1, Flask-SQLAlchemy, Gunicorn |
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
flask --app wsgi.py run
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
Les méthodes POST, PUT et DELETE demandent aussi le jeton CSRF de la page
(`meta[name="csrf-token"]`) dans l'en-tête `X-CSRF-Token`. Les formulaires
utilisent un champ caché `csrf_token`. La déconnexion est un **POST**.
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
- `SECRET_KEY` lue depuis l'environnement ; en développement seulement, une clé éphémère est générée si elle manque. Une clé d'au moins 32 caractères est obligatoire en production ou en mode démo
- Vérification de propriété sur chaque ressource (anti IDOR)
- Validation des inputs côté serveur avec messages d'erreur clairs
- Cookies de session `HttpOnly`, `SameSite=Lax`, et `Secure` en production/démo
- Jeton CSRF sur toute mutation, contrôle d'Origin/Referer lorsqu'il est transmis, refus des requêtes navigateur cross-site
- CSP sans scripts inline, pages personnelles non mises en cache, refus de l'intégration dans une iframe
- Mode démo : expiration serveur, nonce de session et quotas contrôlés dans une transaction SQLite `BEGIN IMMEDIATE`
- Corps des requêtes limité à 24 Kio ; les champs et les choix de statut/couleur sont validés côté serveur

---

*Projet réalisé par Yacine Ouasti — étudiant BBA, dans le cadre d'une démarche d'apprentissage du développement web full-stack.*

## Contrats API et limites

Les créations/modifications exigent un **objet JSON**, des champs textuels typés et des longueurs bornées. Une date d'échéance accepte `YYYY-MM-DD`, `null` ou une chaîne vide ; `null` efface la date lors d'un PUT. Un filtre de statut inconnu retourne 400. Les données d'un autre utilisateur retournent 404. Une session pointant sur un utilisateur absent est invalidée (401 en API / redirection vers connexion en HTML).

Les tests utilisent SQLite en mémoire ; ils vérifient aussi qu'un PUT invalide ne modifie pas la ressource, et qu'un utilisateur ne peut lire, modifier ou supprimer les tâches d'un autre.

Ce dépôt reste un démonstrateur : pas de migrations versionnées, de collaboration
entre comptes, de synchronisation temps réel entre onglets, de rotation automatique
des secrets, de journal d'audit ou de qualification de charge. Les déplacements se
font avec des boutons, sans glisser-déposer. Le mode normal d'authentification ne
possède pas de limite de tentatives de connexion : les routes correspondantes sont
donc désactivées sur cette démonstration publique. Les quotas bornent le stockage de
la démo, sans constituer une protection complète contre le déni de service.
La base locale existante n'est pas utilisée par les tests.

## Héberger la démonstration derrière HTTPS

Utiliser une base SQLite **distincte de toute base personnelle**, un utilisateur
système dédié et un proxy HTTPS. Le mode démo exige `PUBLIC_ORIGIN`, valide le nom
d'hôte et impose les cookies Secure. Aucune confiance aveugle dans les en-têtes proxy
n'est activée par l'application.

```dotenv
APP_ENV=production
DEMO_MODE=1
PUBLIC_ORIGIN=https://taskflow.62-171-168-208.nip.io
DATABASE_URL=sqlite:////var/lib/yacine-taskflow/tasks.db
# SECRET_KEY : injecter une valeur aléatoire privée, jamais versionnée
```

```bash
gunicorn -c gunicorn.conf.py wsgi:app
```

Le serveur écoute par défaut sur `127.0.0.1:4593`, avec un seul worker/thread,
un délai de 30 secondes et le débogueur désactivé. Le proxy conserve l'en-tête Host
public. `GET /healthz` vérifie la base et renvoie `{"status":"ok"}` ; un contrôle
local direct doit donc transmettre le bon Host. Les écritures de la démo restent
sérialisées par SQLite, y compris si plusieurs processus sont utilisés plus tard.

Tests : parcours CRUD, déplacement de tâches, isolation entre invités, expiration,
nettoyage en cascade, quotas dont créations simultanées, CSRF, Origin, échappement
HTML et fonctionnement de l'authentification normale. Les tests HTTP locaux ne
constituent pas une mesure de charge ni une vérification de la publication.
