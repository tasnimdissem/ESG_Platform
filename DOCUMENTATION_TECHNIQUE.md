# Documentation Technique — ESG Platform
## Dossier de Soutenance Technique

**Version :** 1.1  
**Date :** 1 juin 2026  
**Auteur :** Tasnim Dissem  
**Email :** elaafriaa@gmail.com  
**Branche Git active :** `develop`

---

## Table des matières

1. [Présentation du Projet](#1-présentation-du-projet)
2. [Architecture Générale](#2-architecture-générale)
3. [Stack Technologique](#3-stack-technologique)
4. [Modèle de Données — Base de Données](#4-modèle-de-données--base-de-données)
5. [Sécurité](#5-sécurité)
6. [Traçabilité et Audit](#6-traçabilité-et-audit)
7. [API REST — Documentation Complète](#7-api-rest--documentation-complète)
8. [Modules Intelligence Artificielle](#8-modules-intelligence-artificielle)
9. [Gestion des Erreurs](#9-gestion-des-erreurs)
10. [Déploiement et Infrastructure](#10-déploiement-et-infrastructure)
11. [Flux Utilisateur (User Journeys)](#11-flux-utilisateur-user-journeys)
12. [Configuration et Variables d'Environnement](#12-configuration-et-variables-denvironnement)
13. [Glossaire](#13-glossaire)

---

## 1. Présentation du Projet

### 1.1 Contexte

L'ESG Platform est une application web full-stack dédiée à l'**analyse et au pilotage des critères ESG** (Environnementaux, Sociaux et de Gouvernance) d'entreprises. Elle répond à une problématique croissante dans le monde financier et industriel : mesurer, comprendre et améliorer la performance extra-financière des organisations.

### 1.2 Objectifs fonctionnels

| Objectif | Description |
|---|---|
| Prédiction ESG | Calculer un score ESG à partir de 22+ indicateurs métier via un modèle Machine Learning (CatBoost) |
| Analyse & Tendances | Visualiser l'évolution des scores ESG dans le temps via des graphiques et KPIs |
| Recommandations IA | Générer des recommandations personnalisées basées sur les scores et l'analyse RAG |
| Chatbot RAG | Répondre aux questions ESG via un moteur de recherche documentaire augmenté (RAG) |
| Interface vocale | Permettre l'interaction par la voix (Whisper + reconnaissance vocale) |
| Gestion d'entreprises | Créer et suivre l'historique ESG de chaque entreprise |
| Tableau de bord Power BI | Intégrer des dashboards analytiques embarqués |
| Administration | Gérer les utilisateurs, rôles, approbations et accès |

### 1.3 Acteurs du système

| Rôle | Description | Permissions |
|---|---|---|
| `admin` | Administrateur système | Accès total : gestion utilisateurs, toutes les routes, toutes les entreprises |
| `decideur` | Décideur stratégique | Tableau de bord, recommandations, analytics (données de sa propre entreprise) |
| `metier` | Expert métier ESG | Prédictions, entreprise assignée, chatbot, historique prédictions |

> **Multi-tenancy** : chaque utilisateur `metier` et `decideur` est rattaché à **une seule entreprise** via le champ `company_id`. Il ne peut accéder qu'aux données de cette entreprise. Seul l'`admin` a une vue transverse sur toutes les entreprises.
>
> **Note** : le rôle `user` a été fusionné avec `decideur` et n'est plus proposé à l'inscription. Les anciens comptes `user` sont traités comme des `decideur` pour la consultation.

---

## 2. Architecture Générale

### 2.1 Vue d'ensemble — Architecture Microservices 3 couches

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT (Navigateur)                         │
│              React 18 + TypeScript + Vite + Tailwind CSS            │
│                           Port 5173 (dev) / 80 (prod)               │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ HTTPS / REST API  (/api/*)
                               │ Cookies HttpOnly (JWT)
┌──────────────────────────────▼──────────────────────────────────────┐
│                    BACKEND ORCHESTRATEUR (Flask)                     │
│         Auth · Prédiction ML · Chat · Analytics · Admin             │
│                           Port 5050                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │  SQLAlchemy  │  │  CatBoost    │  │  Services métier          │  │
│  │  PostgreSQL  │  │  ML Model    │  │  Email · S3 · News · Voice│  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ HTTP interne (/api/v1/query)
┌──────────────────────────────▼──────────────────────────────────────┐
│                     SERVICE RAG (Flask)                              │
│       Retrieval-Augmented Generation · Indexation documentaire      │
│                           Port 8000                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  Vector Store    │  │  LLM Integration │  │  Document Index  │  │
│  │  (embeddings)    │  │  OpenAI/Groq/    │  │  (corpus ESG)    │  │
│  └──────────────────┘  │            │  └──────────────────┘  │
│                         └──────────────────┘                        │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                     INFRASTRUCTURE                                   │
│   PostgreSQL 16 (port 5433) · AWS S3 (avatars) · SMTP (emails)     │
│                        Docker Compose                                │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Architecture Frontend — Organisation des modules

```
src/
├── main.tsx                     # Point d'entrée React
├── app/
│   ├── App.tsx                  # Wrapper Router + AuthProvider
│   ├── routes.tsx               # Définition des routes (public/protégées)
│   ├── contexts/
│   │   └── AuthContext.tsx      # État global authentification
│   ├── components/
│   │   ├── Layout.tsx           # Structure principale
│   │   ├── Header.tsx           # Barre de navigation
│   │   ├── Sidebar.tsx          # Navigation latérale
│   │   ├── ESGIndicatorForm.tsx # Formulaire indicateurs
│   │   ├── ESGScoreCard.tsx     # Affichage score
│   │   ├── VoiceRecorder.tsx    # Interface vocale
│   │   └── ui/                  # 40+ composants Radix UI
│   ├── pages/
│   │   ├── Dashboard.tsx        # Power BI embarqué
│   │   ├── Analytics.tsx        # Tendances et KPIs
│   │   ├── ChatbotRag.tsx       # Interface chatbot
│   │   ├── RecommendationsRag.tsx # Recommandations IA
│   │   ├── Prediction.tsx       # Formulaire prédiction ML
│   │   ├── Companies.tsx        # Gestion entreprises
│   │   ├── CompanyView.tsx      # Détail entreprise
│   │   ├── AdminDashboard.tsx   # Administration
│   │   ├── Profile.tsx          # Profil utilisateur
│   │   ├── Login.tsx            # Authentification
│   │   ├── Register.tsx         # Inscription
│   │   ├── ForgotPassword.tsx   # Mot de passe oublié
│   │   └── ResetPassword.tsx    # Réinitialisation
│   └── hooks/
│       └── useSpeechRecognition.ts
└── styles/
    └── index.css                # Tailwind + styles globaux
```

### 2.3 Architecture Backend — Organisation des modules

```
backend/
├── app.py               # Factory Flask : CORS, JWT, rate limiting, erreurs
├── config.py            # Configuration centralisée (env vars)
├── extensions.py        # Instances Flask (db, bcrypt, jwt, limiter)
├── schemas.py           # Validation Pydantic (requêtes entrantes)
├── models/
│   ├── user.py          # User, EmailVerificationToken, PasswordResetToken
│   ├── company.py       # Company (avec historique JSON)
│   ├── prediction.py    # PredictionHistory
│   └── chat.py          # ChatConversation, ChatMessage
├── routes/
│   ├── auth.py          # /api/auth/* — Authentification complète
│   ├── companies.py     # /api/companies/* — CRUD entreprises
│   ├── prediction.py    # /api/predict — Prédiction ML
│   ├── analytics.py     # /api/analytics/* — Statistiques
│   ├── chat.py          # /api/chat/* — Conversations persistantes
│   ├── admin.py         # /api/admin/* — Administration
│   ├── api.py           # /api/* — Intégration, news, Power BI
│   └── voice.py         # /api/v1/* — Interface vocale
├── services/
│   ├── ml_service.py            # Singleton CatBoost
│   ├── esg_service.py           # Calculs et scores ESG
│   ├── email_service.py         # SMTP
│   ├── avatar_service.py        # S3 / stockage local
│   ├── news_service.py          # Agrégation actualités ESG
│   ├── speech_service.py        # Transcription Whisper
│   ├── conversation_service.py  # Sessions en mémoire (thread-safe)
│   ├── integration_service.py   # Orchestration RAG
│   └── local_rag_service.py     # Fallback local
└── utils/
    └── decorators.py    # @require_role, @require_roles — RBAC
```

### 2.4 Flux de communication inter-services

```
[Navigateur] ──cookies JWT──▶ [Backend :5050]
                                    │
                         ┌──────────┴──────────┐
                         │                     │
                    [PostgreSQL]        [RAG Service :8000]
                    (données               (documents + LLM)
                    persistantes)
                         │
                    [AWS S3]
                    (avatars)
                         │
                    [SMTP Gmail]
                    (emails)
```

---

## 3. Stack Technologique

### 3.1 Frontend

| Catégorie | Technologie | Version | Usage |
|---|---|---|---|
| Framework UI | React | 18.3.1 | Rendu composants |
| Langage | TypeScript | 5.x | Typage statique |
| Build tool | Vite | 6.3.5 | Bundling, HMR, proxy |
| Styles | Tailwind CSS | 4.1.12 | Utility-first CSS |
| Composants | Radix UI | Latest | 26 bibliothèques accessibles |
| Routing | React Router | 7.13.0 | Navigation SPA |
| Icônes | Lucide React | 0.487.0 | Icons SVG |
| Graphiques | Recharts | 2.15.2 | Visualisations |
| Formulaires | React Hook Form | 7.55.0 | Gestion formulaires |
| Animations | Motion (Framer) | 12.23.24 | Animations fluides |
| Notifications | Sonner | 2.0.3 | Toast messages |
| Thèmes | Next-themes | 0.4.6 | Dark/light mode |
| PDF | jsPDF | 4.2.1 | Export rapports |
| Drag & Drop | React DnD | 16.0.1 | Interfaces interactives |

### 3.2 Backend

| Catégorie | Technologie | Version | Usage |
|---|---|---|---|
| Framework | Flask | 3.0.0+ | API REST |
| ORM | Flask-SQLAlchemy | Latest | Abstraction base de données |
| Migrations | Flask-Migrate (Alembic) | 4.0.0+ | Versionnement schéma BD |
| Auth | Flask-JWT-Extended | Latest | Tokens JWT |
| Hashing | Flask-Bcrypt | Latest | Mots de passe |
| Rate Limiting | Flask-Limiter | 3.5.0+ | Protection anti-abus |
| CORS | Flask-CORS | Latest | Cross-origin requests |
| Validation | Pydantic | 2.0.0+ | Validation données entrantes |
| Email | Python smtplib | Standard | Envoi emails |
| AWS | Boto3 | 1.34.0+ | Upload S3 |
| Web scraping | BeautifulSoup4 | 4.12.0+ | Actualités ESG |

### 3.3 Intelligence Artificielle / ML

| Catégorie | Technologie | Version | Usage |
|---|---|---|---|
| ML Model | CatBoost | 1.2.5+ | Prédiction score ESG |
| Data processing | Pandas | 2.0.0+ | Manipulation features |
| Preprocessing | scikit-learn | 1.2.0+ | Target encoding |
| Sérialisation | Joblib | 1.2.0+ | Sauvegarde/chargement modèle |
| Transcription | OpenAI Whisper | Via API | Voix → texte |
| LLM | OpenAI / Groq | Latest | Synthèse RAG |
| RAG | Service Flask dédié | Custom | Recherche documentaire |

### 3.4 Infrastructure

| Catégorie | Technologie | Version | Usage |
|---|---|---|---|
| Base de données | PostgreSQL | 16 | Production |
| Base de données | SQLite | 3.x | Développement (fallback) |
| Conteneurs | Docker | Latest | Isolation services |
| Orchestration | Docker Compose | Latest | Multi-conteneurs |
| Reverse proxy | Nginx | Alpine | Servir frontend, SSL |
| Email relay | Gmail SMTP | Required for activation/reset | Envoi des e-mails de la plateforme |
| Stockage fichiers | AWS S3 | Latest | Avatars utilisateurs |
| CI/CD | GitHub (branches) | N/A | Versionnement code |

---

## 4. Modèle de Données — Base de Données

### 4.1 Schéma relationnel

```
┌──────────────────────────────────────────────────────────────────────┐
│                           SCHÉMA BASE DE DONNÉES                     │
└──────────────────────────────────────────────────────────────────────┘

users
├── id                  INTEGER PK AUTO_INCREMENT
├── name                VARCHAR NOT NULL
├── email               VARCHAR UNIQUE NOT NULL
├── password            VARCHAR NOT NULL          ← bcrypt hash
├── role                VARCHAR DEFAULT 'user'    ← user|metier|decideur|admin
├── company_id          INTEGER FK → companies.id ← isolation multi-tenant (nullable)
├── avatar_url          VARCHAR NULLABLE
├── avatar_s3_key       VARCHAR NULLABLE
├── is_blocked          BOOLEAN DEFAULT FALSE
├── is_approved         BOOLEAN DEFAULT FALSE     ← workflow approbation admin
├── is_verified         BOOLEAN DEFAULT FALSE     ← vérification email
└── created_at          DATETIME DEFAULT NOW()

email_verification_tokens
├── id                  INTEGER PK AUTO_INCREMENT
├── user_id             INTEGER FK → users.id
├── token               VARCHAR UNIQUE NOT NULL   ← UUID token sécurisé
├── created_at          DATETIME DEFAULT NOW()
└── expires_at          DATETIME                  ← validité 24h

password_reset_tokens
├── id                  INTEGER PK AUTO_INCREMENT
├── user_id             INTEGER FK → users.id
├── token               VARCHAR UNIQUE NOT NULL   ← UUID token sécurisé
├── created_at          DATETIME DEFAULT NOW()
└── expires_at          DATETIME                  ← validité 15 min

companies
├── id                  INTEGER PK AUTO_INCREMENT
├── name                VARCHAR NOT NULL
├── sector              VARCHAR NULLABLE
├── country             VARCHAR NULLABLE
├── historique          JSON                      ← tableau d'entrées historiques
├── created_by_user_id  INTEGER FK → users.id
├── created_at          DATETIME DEFAULT NOW()
└── updated_at          DATETIME ON UPDATE NOW()

  Exemple structure JSON historique :
  [
    {
      "date": "2026-05-31",
      "score": 72.5,
      "details": { "env": 75, "social": 70, "gov": 68 },
      "indicators": { ... }
    }
  ]

prediction_history
├── id                  INTEGER PK AUTO_INCREMENT
├── user_id             INTEGER FK → users.id
├── company_name        VARCHAR NOT NULL
├── primary_industry    VARCHAR NOT NULL
├── score               FLOAT NOT NULL            ← score ESG prédit (0-100)
├── features_data       JSON                      ← 22+ indicateurs utilisés
└── created_at          DATETIME DEFAULT NOW()

chat_conversations
├── id                  INTEGER PK AUTO_INCREMENT
├── user_id             INTEGER FK → users.id
├── title               VARCHAR DEFAULT 'Nouvelle conversation'
├── session_id          VARCHAR UNIQUE             ← identifiant de session
└── created_at          DATETIME DEFAULT NOW()
    └── has many → chat_messages

chat_messages
├── id                  INTEGER PK AUTO_INCREMENT
├── conversation_id     INTEGER FK → chat_conversations.id
├── sender              VARCHAR                   ← 'user' | 'bot'
├── text                TEXT NOT NULL
├── sources             JSON NULLABLE              ← sources documentaires RAG
└── timestamp           DATETIME DEFAULT NOW()
```

### 4.2 Relations et cardinalités

```
users          1 ──────────── N  email_verification_tokens
users          1 ──────────── N  password_reset_tokens
users          1 ──────────── N  prediction_history
users          1 ──────────── N  chat_conversations
users          N ──────────── 1  companies   (company_id — entreprise d'appartenance)
companies      1 ──────────── N  users       (created_by_user_id — créateur)
chat_conversations 1 ──────── N  chat_messages
```

### 4.3 Index et contraintes

| Table | Colonne | Type de contrainte |
|---|---|---|
| users | email | UNIQUE NOT NULL |
| users | company_id | INDEX (FK → companies.id, ON DELETE SET NULL) |
| email_verification_tokens | token | UNIQUE NOT NULL |
| password_reset_tokens | token | UNIQUE NOT NULL |
| chat_conversations | session_id | UNIQUE |

### 4.4 Migrations de base de données

Le projet utilise **Alembic** (via Flask-Migrate) pour la gestion des migrations :

```bash
# Créer une migration
flask db migrate -m "description_changement"

# Appliquer les migrations
flask db upgrade

# Revenir en arrière
flask db downgrade
```

Dossier de migrations : `migrations/versions/`

De plus, chaque module de routes implémente une fonction `ensure_*_schema()` qui ajoute automatiquement les colonnes manquantes via `ALTER TABLE` — assurant la compatibilité avec les bases existantes lors des mises à jour. La colonne `company_id` sur la table `users` est ajoutée par `ensure_user_schema()` au démarrage si elle est absente.

### 4.5 Stratégie de persistance des données

| Type de données | Stockage | Justification |
|---|---|---|
| Données utilisateurs, prédictions, conversations | PostgreSQL | Relationnelle, ACID, requêtes complexes |
| Historique ESG par entreprise | JSON dans PostgreSQL | Flexibilité du schéma temporel |
| Avatars utilisateurs | AWS S3 (prod) / disque local (dev) | Stockage objet scalable |
| Sessions de conversation | Mémoire (thread-safe, max 20 turns) | Performance, pas de persistance requise |
| Modèle ML | Fichiers `.cbm`, `.pkl`, `.txt` | Chargement unique via Singleton |

---

## 5. Sécurité

### 5.1 Authentification — JWT + Cookies HttpOnly

#### Mécanisme

Le système utilise des **JSON Web Tokens (JWT)** stockés dans des **cookies HttpOnly**, une approche plus sécurisée que le `localStorage` car elle protège contre les attaques XSS.

```
[Login] ──POST /api/auth/login──▶ [Backend]
                                       │
                              Vérification bcrypt
                                       │
                              Génération JWT (24h)
                                       │
                    ◀── Set-Cookie: access_token_cookie; HttpOnly; SameSite=Lax
```

#### Configuration JWT (backend/config.py)

| Paramètre | Valeur | Description |
|---|---|---|
| Durée du token | 24 heures | Expiration automatique |
| Type de stockage | Cookie HttpOnly | Inaccessible depuis JavaScript |
| SameSite | Lax | Protection CSRF de base |
| Secure | True (production) | HTTPS uniquement en prod |
| CSRF protection | Activée (production) | Double protection |

#### Flux complet d'authentification

```
1. INSCRIPTION
   POST /api/auth/register
   → Vérification email unique + validation Pydantic
   → Hash bcrypt du mot de passe
   → Création User (is_approved=False, is_verified=False)
   → Attente approbation admin

2. APPROBATION ADMIN
   PUT /api/admin/users/<id>/approve
   → is_approved = True
   → Envoi email avec lien de vérification (token 24h)

3. VÉRIFICATION EMAIL
   POST /api/auth/verify-email { token }
   → Validation token non expiré
   → is_verified = True
   → Suppression du token

4. CONNEXION
   POST /api/auth/login { email, password }
   → Vérification is_approved + is_verified + not is_blocked
   → Comparaison bcrypt
   → Émission JWT dans cookie HttpOnly
   → Retour infos utilisateur

5. REQUÊTES AUTHENTIFIÉES
   [Cookie JWT envoyé automatiquement]
   → @jwt_required() vérifie le token
   → Extraction user_id du payload JWT
   → Vérification rôle si @require_role()

6. DÉCONNEXION
   POST /api/auth/logout
   → Suppression du cookie JWT côté serveur
```

### 5.2 Hachage des mots de passe — BCrypt

```python
# Création d'un hash (backend/models/user.py)
password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

# Vérification
bcrypt.check_password_hash(user.password, provided_password)
```

- Algorithme : **bcrypt** avec salt aléatoire
- Facteur de coût : par défaut (12 rounds)
- Le mot de passe brut n'est **jamais** stocké ni loggué

### 5.3 Contrôle d'accès basé sur les rôles (RBAC)

#### Décorateurs personnalisés

```python
# backend/utils/decorators.py

@require_role('admin')          # Un seul rôle exact
def admin_only_endpoint(): ...

@require_roles('admin', 'metier')  # Plusieurs rôles acceptés
def metier_or_admin_endpoint(): ...
```

#### Matrice des permissions backend

| Endpoint | user | metier | decideur | admin |
|---|---|---|---|---|
| GET /api/auth/me | ✓ | ✓ | ✓ | ✓ |
| PUT /api/auth/me (profil) | ✓ | ✓ | ✓ | ✓ |
| POST /api/predict | ✗ | ✓ | ✗ | ✓ |
| GET /api/history | ✗ | ✓ (entreprise) | ✗ | ✓ (tout) |
| GET /api/analytics/summary | ✗ | ✗ | ✓ (entreprise) | ✓ (tout) |
| GET /api/chat/conversations | ✗ | ✓ | ✗ | ✓ |
| POST /api/chat/conversations | ✗ | ✓ | ✗ | ✓ |
| GET /api/companies | ✗ | ✓ (sa propre) | ✗ | ✓ (toutes) |
| POST /api/companies | ✗ | ✗ | ✗ | ✓ |
| PUT/DELETE /api/companies/* | ✗ | ✗ | ✗ | ✓ |
| GET /api/admin/users | ✗ | ✗ | ✗ | ✓ |
| PUT /api/admin/users/*/approve | ✗ | ✗ | ✗ | ✓ |
| PUT /api/admin/users/*/company | ✗ | ✗ | ✗ | ✓ |
| DELETE /api/admin/users/* | ✗ | ✗ | ✗ | ✓ |

#### Matrice des permissions frontend (routes)

| Route | user | metier | decideur | admin |
|---|---|---|---|---|
| `/` Tableau de bord | ✓ | ✓ | ✓ | ✓ |
| `/profile` | ✓ | ✓ | ✓ | ✓ |
| `/analytics` | ✗ | ✗ | ✓ | ✓ |
| `/recommendations` | ✗ | ✗ | ✓ | ✓ |
| `/prediction` | ✗ | ✓ | ✗ | ✓ |
| `/chatbot` | ✗ | ✓ | ✗ | ✓ |
| `/companies` | ✗ | ✓ | ✗ | ✓ |
| `/admin` | ✗ | ✗ | ✗ | ✓ |

> Les routes non autorisées redirigent automatiquement vers `/` via le composant `RoleRoute` de React Router.

#### Isolation des données (multi-tenancy)

Un `metier` ou `decideur` avec un `company_id` ne voit que :
- L'entreprise correspondant à son `company_id`
- Son propre historique de prédictions (metier) ou celui de toute son entreprise (decideur pour analytics)

Un accès à une ressource hors périmètre retourne **HTTP 403 Forbidden**.

### 5.4 Rate Limiting — Protection anti-abus

Implémenté via **Flask-Limiter** avec stockage en mémoire :

| Endpoint | Limite | Fenêtre |
|---|---|---|
| Global (toutes routes) | 200 requêtes | par jour |
| Global (toutes routes) | 50 requêtes | par heure |
| POST /api/auth/register | 3 requêtes | par minute |
| POST /api/auth/login | 5 requêtes | par minute |
| POST /api/predict | 20 requêtes | par minute |

**Identification** : par adresse IP  
**Réponse en cas de dépassement** : `HTTP 429 Too Many Requests`

### 5.5 Validation des données entrantes — Pydantic v2

Tous les payloads entrants sont validés avec des schémas Pydantic stricts :

```python
# backend/schemas.py

class PredictRequest(BaseModel):
    primary_industry: str
    env_score: float = Field(ge=0, le=100)
    social_score: float = Field(ge=0, le=100)
    gov_score: float = Field(ge=0, le=100)
    # ... 22+ champs validés
    
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    
class RegisterRequest(BaseModel):
    name: str = Field(min_length=2)
    email: EmailStr
    password: str = Field(min_length=8)
    role: str
```

**Comportement** : si la validation échoue, une erreur `HTTP 422 Unprocessable Entity` est retournée avec les détails des champs invalides (en français).

### 5.6 CORS — Cross-Origin Resource Sharing

```python
# backend/app.py
CORS(app, 
     origins=["http://localhost:5173"],  # Origines autorisées
     supports_credentials=True,          # Autorise les cookies
     allow_headers=["Content-Type", "Authorization", "X-CSRF-TOKEN"]
)
```

En production, les origines sont configurées via les variables d'environnement pour pointer vers le domaine officiel.

### 5.7 Gestion des tokens de réinitialisation

```
Mot de passe oublié :
├── POST /api/auth/forgot-password { email }
│   → Génération UUID token sécurisé
│   → Stockage en base avec expires_at = NOW() + 15 min
│   → Envoi email avec lien tokenisé
│
├── POST /api/auth/reset-password { token, new_password }
│   → Récupération token en base
│   → Vérification expires_at > NOW()
│   → Hash bcrypt nouveau mot de passe
│   → Suppression du token (usage unique)
│   → Mise à jour user.password
```

### 5.8 Blocage et workflow d'approbation

- **is_blocked** : un administrateur peut bloquer un utilisateur immédiatement. Tout appel avec un compte bloqué retourne `HTTP 403 Forbidden`.
- **is_approved** : tout nouvel utilisateur est en attente d'approbation. Sans approbation, la connexion est refusée.
- **is_verified** : l'email doit être vérifié après approbation. Un compte non vérifié ne peut pas se connecter.

### 5.9 Sécurité de l'upload de fichiers (avatars)

```python
# backend/services/avatar_service.py
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

# En production : upload vers AWS S3 avec clé unique
# En développement : stockage local dans /static/avatars/
```

### 5.10 Récapitulatif des mesures de sécurité

| Menace | Contre-mesure |
|---|---|
| Vol de token (XSS) | Cookies HttpOnly (pas de localStorage) |
| CSRF | SameSite=Lax + CSRF token en production |
| Brute force (login) | Rate limiting 5/min + bcrypt lent |
| Injection SQL | ORM SQLAlchemy (requêtes préparées) |
| Données invalides | Validation Pydantic + EmailStr |
| Accès non autorisé | JWT @jwt_required() + @require_role() / @require_roles() |
| Fuite inter-entreprises | Filtrage company_id sur toutes les routes de données |
| Spam d'inscription | Rate limiting 3/min + approbation admin |
| Mots de passe faibles | Minimum 8 caractères + bcrypt |
| Accès CORS non autorisé | Liste blanche d'origines stricte |
| Fichiers malicieux | Validation extension + taille maximale |

---

## 6. Traçabilité et Audit

### 6.1 Historique des prédictions

Chaque appel à `/api/predict` est automatiquement enregistré dans la table `prediction_history` :

```python
# backend/routes/prediction.py
history = PredictionHistory(
    user_id=current_user_id,
    company_name=data.company_name,
    primary_industry=data.primary_industry,
    score=result['score'],
    features_data=data.dict()    # ← tous les 22+ indicateurs sauvegardés
)
db.session.add(history)
db.session.commit()
```

**Données tracées :**
- Identifiant de l'utilisateur ayant effectué la prédiction
- Nom de l'entreprise analysée
- Secteur d'activité
- Score ESG calculé
- Snapshot complet des 22+ features utilisées
- Timestamp de création

### 6.2 Historique ESG des entreprises

La table `companies` maintient un champ JSON `historique` qui stocke l'évolution temporelle des scores ESG :

```python
# backend/models/company.py
def add_history_entry(self, entry: dict):
    if self.historique is None:
        self.historique = []
    self.historique.append({
        "date": entry.get("date", datetime.utcnow().isoformat()),
        "score": entry.get("score"),
        "details": entry.get("details", {}),
        "indicators": entry.get("indicators", {})
    })
```

**Utilisation :** construction du graphique d'évolution dans `CompanyView.tsx` et alimentation du module Analytics.

### 6.3 Traçabilité des conversations

Chaque message du chatbot est persisté en base :

```
chat_conversations
└── session_id (unique)
    └── title (premier message comme titre)
    └── created_at

chat_messages
└── conversation_id → FK
    ├── sender: 'user' | 'bot'
    ├── text: contenu
    ├── sources: [] ← documents RAG utilisés (traçabilité des sources)
    └── timestamp
```

Les sources documentaires retournées par le RAG sont stockées avec chaque réponse, permettant l'**audit des références utilisées**.

### 6.4 Traçabilité des actions administratives

Le module admin logge les actions critiques :
- Approbation d'un utilisateur → email envoyé, statut changé, date enregistrée
- Blocage d'un utilisateur → flag `is_blocked = True`
- Changement de rôle → `PUT /api/admin/users/<id>/role`
- Assignation d'entreprise → `PUT /api/admin/users/<id>/company` (multi-tenancy)

### 6.5 Audit de la session en mémoire (conversation_service)

```python
# backend/services/conversation_service.py
class ConversationService:
    MAX_TURNS = 20           # Limite de l'historique en mémoire
    CONTEXT_WINDOW = 5       # Tours récents envoyés au LLM
    
    def add_turn(self, session_id, user_msg, bot_msg):
        # Stockage thread-safe avec verrou
        with self._lock:
            self._sessions[session_id].append({
                "user": user_msg,
                "bot": bot_msg,
                "timestamp": datetime.utcnow().isoformat()
            })
```

### 6.6 Traçabilité des emails

Le service email logge chaque envoi :
- Email de vérification (activation de compte)
- Email de réinitialisation de mot de passe
- Email d'approbation admin

### 6.7 Analytics — Exploitation des données tracées

Le module Analytics (`/api/analytics/summary`) exploite les données de traçabilité pour produire :

| Métrique | Source de données |
|---|---|
| Score ESG moyen | `prediction_history.score` |
| Score minimum / maximum | `prediction_history.score` |
| Évolution mensuelle | `prediction_history.created_at` groupé par mois |
| Importance des features | Corrélation `features_data` ↔ `score` |
| Répartition par secteur | `prediction_history.primary_industry` |

---

## 7. API REST — Documentation Complète

### 7.1 Conventions générales

| Aspect | Valeur |
|---|---|
| Base URL (dev) | `http://localhost:5050/api` |
| Format | JSON |
| Authentification | Cookie JWT (`access_token_cookie`) |
| Encoding | UTF-8 |
| Content-Type | `application/json` |

**Codes HTTP utilisés :**

| Code | Signification |
|---|---|
| 200 | Succès |
| 201 | Création réussie |
| 400 | Mauvaise requête (paramètres invalides) |
| 401 | Non authentifié (JWT manquant ou expiré) |
| 403 | Non autorisé (rôle insuffisant ou compte bloqué) |
| 404 | Ressource introuvable |
| 409 | Conflit (email déjà utilisé) |
| 422 | Erreur de validation Pydantic |
| 429 | Trop de requêtes (rate limiting) |
| 500 | Erreur serveur interne |

---

### 7.2 Module Authentification — `/api/auth`

#### POST /api/auth/register
**Description :** Inscription d'un nouvel utilisateur  
**Auth :** Non requise  
**Rate limit :** 3/minute

```json
// Request Body
{
  "name": "Jean Dupont",
  "email": "jean.dupont@example.com",
  "password": "motdepasse123",
  "role": "metier"
}

// Response 201 - Succès
{
  "message": "Compte créé. En attente d'approbation administrateur."
}

// Response 409 - Email déjà utilisé
{
  "error": "Cet email est déjà utilisé."
}
```

---

#### POST /api/auth/login
**Description :** Connexion et émission du JWT  
**Auth :** Non requise  
**Rate limit :** 5/minute

```json
// Request Body
{
  "email": "jean.dupont@example.com",
  "password": "motdepasse123"
}

// Response 200 - Succès
// Cookie: access_token_cookie=<JWT> HttpOnly
{
  "message": "Connecté avec succès",
  "user": {
    "id": 1,
    "name": "Jean Dupont",
    "email": "jean.dupont@example.com",
    "role": "metier",
    "avatar_url": null,
    "created_at": "2026-05-31T10:00:00"
  }
}

// Response 401 - Identifiants invalides
{ "error": "Email ou mot de passe incorrect." }

// Response 403 - Compte non approuvé / bloqué
{ "error": "Votre compte est en attente d'approbation." }
```

---

#### POST /api/auth/logout
**Description :** Déconnexion (suppression du cookie JWT)  
**Auth :** Requise

```json
// Response 200
{ "message": "Déconnecté avec succès" }
```

---

#### GET /api/auth/me
**Description :** Récupérer les informations de l'utilisateur connecté  
**Auth :** Requise

```json
// Response 200
{
  "id": 1,
  "name": "Jean Dupont",
  "email": "jean.dupont@example.com",
  "role": "metier",
  "avatar_url": "https://s3.amazonaws.com/...",
  "created_at": "2026-05-31T10:00:00"
}
```

---

#### POST /api/auth/verify-email
**Description :** Vérification de l'email via token  
**Auth :** Non requise

```json
// Request Body
{ "token": "uuid-token-reçu-par-email" }

// Response 200
{ "message": "Email vérifié avec succès." }

// Response 400 - Token expiré ou invalide
{ "error": "Token invalide ou expiré." }
```

---

#### POST /api/auth/forgot-password
**Description :** Demander un lien de réinitialisation de mot de passe  
**Auth :** Non requise

```json
// Request Body
{ "email": "jean.dupont@example.com" }

// Response 200 (toujours, même si email inexistant - sécurité)
{ "message": "Si cet email existe, un lien de réinitialisation a été envoyé." }
```

---

#### POST /api/auth/reset-password
**Description :** Réinitialiser le mot de passe avec le token reçu  
**Auth :** Non requise

```json
// Request Body
{
  "token": "uuid-reset-token",
  "new_password": "nouveauMotDePasse123"
}

// Response 200
{ "message": "Mot de passe réinitialisé avec succès." }
```

---

#### PUT /api/auth/profile
**Description :** Mettre à jour le profil utilisateur  
**Auth :** Requise

```json
// Request Body (champs optionnels)
{
  "name": "Jean-Paul Dupont",
  "email": "jp.dupont@example.com",
  "current_password": "ancien",
  "new_password": "nouveau123"
}

// Response 200
{ "message": "Profil mis à jour." }
```

---

#### POST /api/auth/avatar
**Description :** Uploader un avatar (multipart/form-data)  
**Auth :** Requise

```
// Request: multipart/form-data
// Champ: file = <image PNG/JPG/WebP, max 5MB>

// Response 200
{ "avatar_url": "https://..." }
```

---

### 7.3 Module Prédiction — `/api`

#### POST /api/predict
**Description :** Calculer un score ESG via le modèle CatBoost  
**Auth :** Requise (`metier` ou `admin`)  
**Rate limit :** 20/minute

```json
// Request Body (22+ features, toutes entre 0 et 100)
{
  "primary_industry": "Technology",
  "env_score": 72.5,
  "social_score": 68.0,
  "gov_score": 80.0,
  "carbon_emissions": 45.2,
  "water_usage": 60.1,
  "waste_management": 70.0,
  "renewable_energy": 85.0,
  "employee_satisfaction": 75.0,
  "diversity_score": 65.0,
  "safety_incidents": 30.0,
  "community_investment": 55.0,
  "board_independence": 90.0,
  "executive_pay_ratio": 40.0,
  "transparency_score": 78.0,
  "anti_corruption": 85.0,
  "data_privacy": 70.0,
  "supply_chain_ethics": 60.0,
  "innovation_index": 80.0,
  "customer_satisfaction": 75.0,
  "financial_stability": 85.0,
  "regulatory_compliance": 90.0
}

// Response 200
{
  "score": 74.3,
  "interpretation": "Score ESG Bon",
  "category": "B",
  "details": {
    "environmental": 75.0,
    "social": 68.5,
    "governance": 82.0
  },
  "recommendations": ["Améliorer la gestion des déchets", "..."]
}
```

---

### 7.4 Module Entreprises — `/api/companies`

#### GET /api/companies
**Auth :** Requise  
**Description :** Consulter les entreprises selon le rôle

| Rôle | Comportement |
|---|---|
| `admin` | Retourne toutes les entreprises |
| `metier` | Retourne uniquement l'entreprise assignée (`company_id`) en lecture seule |
| `decideur`, `user` | **403 Forbidden** |

```json
// Response 200 — admin (liste complète)
[
  {
    "entreprise_id": "1",
    "nom": "Acme Corp",
    "sector": "Technology",
    "country": "France",
    "historique": [...],
    "created_at": "2026-05-31T10:00:00"
  }
]

// Response 200 — metier (sa propre entreprise seulement)
[
  { "entreprise_id": "3", "nom": "Ma Société", ... }
]

// Response 403 — decideur / user
{ "error": "Accès refusé. Permissions insuffisantes." }

// Response 403 — metier sans company_id assigné
{ "error": "Aucune entreprise assignée à votre compte. Contactez un administrateur." }
```

---

#### GET /api/companies/:id
**Auth :** Requise  
**Description :** Détail d'une entreprise

| Rôle | Comportement |
|---|---|
| `admin` | Retourne n'importe quelle entreprise |
| `metier` | Retourne l'entreprise **seulement si** `id == user.company_id` |
| Autre | **403 Forbidden** |

```json
// Response 403 — metier tentant d'accéder à une autre entreprise
{ "error": "Accès refusé. Vous n'avez pas accès à cette entreprise." }
```

---

#### POST /api/companies
**Auth :** Requise (admin uniquement)  
**Description :** Créer ou mettre à jour une entreprise avec ses indicateurs (admin uniquement)

```json
// Request Body
{
  "name": "Acme Corp",
  "sector": "Technology",
  "country": "France",
  "indicators": { "env_score": 72, ... }
}

// Response 201
{ "message": "Entreprise créée.", "id": 1 }
```

---

---

### 7.5 Module Analytics — `/api/analytics`

#### GET /api/analytics/summary
**Auth :** Requise (`admin` ou `decideur`)  
**Description :** Statistiques agrégées sur les prédictions ESG

| Rôle | Périmètre des données |
|---|---|
| `admin` | Toutes les prédictions de toutes les entreprises |
| `decideur` | Prédictions des utilisateurs de sa propre entreprise (`company_id`) |
| Autre | **403 Forbidden** |

```json
// Response 200
{
  "total_predictions": 142,
  "avg_score": 71.2,
  "min_score": 32.1,
  "max_score": 95.8,
  "monthly_evolution": [
    { "month": "2026-01", "avg_score": 68.5, "count": 12 },
    { "month": "2026-05", "avg_score": 74.1, "count": 28 }
  ],
  "feature_importance": [
    { "feature": "gov_score", "importance": 0.18 },
    { "feature": "env_score", "importance": 0.15 }
  ],
  "industry_breakdown": {
    "Technology": { "avg": 75.2, "count": 45 },
    "Manufacturing": { "avg": 63.8, "count": 30 }
  }
}
```

---

### 7.6 Module Chat — `/api/chat`

> Tous les endpoints du chatbot sont réservés aux rôles `admin` et `metier`. Un `decideur` ou `user` reçoit une **403 Forbidden**.

#### GET /api/chat/conversations
**Auth :** Requise (`admin` ou `metier`)  
**Description :** Lister les conversations de l'utilisateur connecté

```json
// Response 200
[
  {
    "id": 1,
    "title": "Questions sur le reporting ESG",
    "session_id": "abc-123",
    "created_at": "2026-05-31T09:00:00"
  }
]
```

---

#### POST /api/chat/conversations/:id/messages
**Auth :** Requise  
**Description :** Envoyer un message dans une conversation (appel RAG)

```json
// Request Body
{ "text": "Quels sont les indicateurs clés pour le scope 3 ?" }

// Response 200
{
  "message": {
    "id": 15,
    "sender": "bot",
    "text": "Les indicateurs clés pour le scope 3 comprennent...",
    "sources": [
      { "document": "GRI_Standards_2023.pdf", "page": 42, "relevance": 0.92 }
    ],
    "timestamp": "2026-05-31T10:05:00"
  }
}
```

---

### 7.7 Module Administration — `/api/admin`

#### GET /api/admin/users
**Auth :** Requise (admin uniquement)  
**Description :** Lister tous les utilisateurs

```json
// Response 200
[
  {
    "id": 1,
    "name": "Jean Dupont",
    "email": "jean@example.com",
    "role": "metier",
    "is_approved": true,
    "is_verified": true,
    "is_blocked": false,
    "created_at": "2026-05-01T08:00:00"
  }
]
```

---

#### PUT /api/admin/users/:id/approve
**Auth :** Requise (admin)  
**Description :** Approuver un compte + envoi email de vérification

```json
// Response 200
{ "message": "Utilisateur approuvé. Email de vérification envoyé." }
```

---

#### PUT /api/admin/users/:id/block
**Auth :** Requise (admin)  
**Description :** Bloquer / débloquer un utilisateur

```json
// Request Body
{ "blocked": true }

// Response 200
{ "message": "Utilisateur bloqué." }
```

---

#### PUT /api/admin/users/:id/role
**Auth :** Requise (admin)  
**Description :** Modifier le rôle d'un utilisateur

```json
// Request Body
{ "role": "decideur" }   // Valeurs : user | metier | decideur | admin

// Response 200
{ "message": "Rôle mis à jour." }
```

---

#### PUT /api/admin/users/:id/company
**Auth :** Requise (admin)  
**Description :** Assigner ou retirer une entreprise à un utilisateur (multi-tenancy)

```json
// Request Body — assigner
{ "company_id": 5 }

// Request Body — retirer l'entreprise
{ "company_id": null }

// Response 200
{
  "message": "Entreprise mise à jour.",
  "user": {
    "id": 12,
    "name": "Marie Curie",
    "role": "metier",
    "company_id": 5,
    ...
  }
}

// Response 404 — entreprise inexistante
{ "error": "Entreprise introuvable." }
```

---

### 7.8 Module Vocal — `/api/v1`

#### POST /api/v1/transcribe
**Description :** Transcrire un fichier audio (multipart/form-data)  
**Auth :** Requise

```
// Request: multipart/form-data
// Champ: audio = <fichier WAV/MP3/WebM>

// Response 200
{
  "transcription": "Quels sont nos indicateurs ESG ce mois-ci ?",
  "language": "fr",
  "confidence": 0.97
}
```

---

#### POST /api/v1/voice-query
**Description :** Requête vocale complète (transcription + RAG)  
**Auth :** Requise

```json
// Response 200
{
  "transcription": "...",
  "answer": "...",
  "sources": [...]
}
```

---

### 7.9 Endpoint de santé

#### GET /api/health
**Description :** Vérification de l'état du service  
**Auth :** Non requise

```json
// Response 200
{
  "status": "healthy",
  "database": "connected",
  "rag_service": "available",
  "version": "1.0.0"
}
```

---

## 8. Modules Intelligence Artificielle

### 8.1 Modèle de prédiction ESG — CatBoost

#### Présentation du modèle

**CatBoost** (Categorical Boosting, Yandex) est un algorithme de Gradient Boosting particulièrement adapté aux données mixtes (numériques + catégorielles) sans prétraitement intensif.

#### Pipeline de prédiction

```
[Requête API] → Validation Pydantic → [Données brutes]
                                            │
                                    Target Encoding
                                    (primary_industry → numérique)
                                            │
                                    Alignement features
                                    (ordre exact du modèle)
                                            │
                                    Prédiction CatBoost
                                    catboost_model.cbm
                                            │
                                    Score ESG (0-100)
                                            │
                              ┌─────────────────────────┐
                              │  Stockage PredictionHistory │
                              └─────────────────────────┘
```

#### Fichiers du modèle

| Fichier | Description |
|---|---|
| `catboost_model.cbm` | Modèle CatBoost sérialisé |
| `target_encoder.pkl` | Encodeur pour `primary_industry` (joblib) |
| `feature_names.txt` | Ordre exact des 22+ features |

#### Classe MLService (Singleton)

```python
# backend/services/ml_service.py
class MLService:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
            cls._instance._load_model()
        return cls._instance
```

Le modèle est chargé une seule fois au démarrage du serveur (pattern Singleton) pour optimiser les performances.

#### Formule de calcul ESG (esg_service.py)

```python
score = (
    0.35 * env_score +     # Environnement : 35%
    0.25 * social_score +  # Social : 25%
    0.30 * gov_score +     # Gouvernance : 30%
    0.10 * co2_score       # CO2 : 10%
)
```

**Note :** Le modèle CatBoost peut affiner ce calcul avec les interactions entre variables.

#### Interprétation des scores

| Score | Catégorie | Interprétation |
|---|---|---|
| 85 - 100 | AAA | Excellence ESG |
| 70 - 84 | AA | Très bonne performance |
| 55 - 69 | A / B+ | Bonne performance |
| 40 - 54 | B | Performance moyenne |
| 25 - 39 | C | Performances insuffisantes |
| 0 - 24 | D | Performances très faibles |

---

### 8.2 Système RAG — Retrieval-Augmented Generation

#### Architecture du système RAG

```
[Question utilisateur]
        │
        ▼
[Encodage de la question]
(modèle d'embedding)
        │
        ▼
[Recherche vectorielle]      ← Corpus ESG indexé
(cosine similarity, top-k=5)   (normes GRI, CSRD, TCFD, etc.)
        │
        ▼
[Passages pertinents récupérés]
(avec métadonnées : document, page, score)
        │
        ▼
[Construction du prompt]
Système + contexte + question + historique
        │
        ▼
[LLM - Synthèse]
(OpenAI / Groq )
        │
        ▼
[Réponse + Sources]  ─────────────────────► [Stockage en BD]
```

#### Configuration RAG

| Paramètre | Variable env | Défaut |
|---|---|---|
| URL du service | `RAG_API_BASE_URL` | `http://127.0.0.1:8000` |
| Endpoint query | `RAG_INTEGRATION_PATH` | `/api/v1/query` |
| Nombre de documents | `RAG_TOP_K` | `5` |
| Timeout | `RAG_TIMEOUT_SECONDS` | `90` |
| Fallback local | `RAG_ALLOW_LOCAL_FALLBACK` | `false` |

#### Mécanisme de fallback

```python
# backend/services/integration_service.py
try:
    response = call_rag_api(query)
except (ConnectionError, Timeout):
    if RAG_ALLOW_LOCAL_FALLBACK:
        response = generate_local_chat_answer(query)
    else:
        raise ServiceUnavailableError()
```

#### Service local de fallback

Pour garantir la disponibilité sans le service RAG, `local_rag_service.py` fournit des réponses prédéfinies pour les questions ESG communes en français.

---

### 8.3 Interface Vocale — Whisper + Web Speech API

#### Pipeline vocal

```
[Microphone] → [MediaRecorder API] → [Blob audio WebM/WAV]
                                              │
                              POST /api/v1/transcribe
                                              │
                              [OpenAI Whisper]
                              (transcription multilingue)
                                              │
                              [Texte transcrit]
                                              │
                              → Envoyé comme message chat
                              → OU détection de commandes vocales
```

#### Commandes vocales reconnues

| Commande | Action |
|---|---|
| "nouvelle conversation" | Créer une nouvelle session chat |
| "effacer" | Effacer le dernier message |
| "analyser [entreprise]" | Lancer une analyse ESG |

---

## 9. Gestion des Erreurs

### 9.1 Handlers globaux Flask

```python
# backend/app.py

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Ressource introuvable"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Erreur serveur interne"}), 500

@app.errorhandler(429)
def rate_limit_exceeded(e):
    return jsonify({"error": "Trop de requêtes. Veuillez patienter."}), 429

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({"error": "Session expirée. Veuillez vous reconnecter."}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({"error": "Token invalide."}), 401
```

### 9.2 Erreurs de validation Pydantic

```json
// HTTP 422 - Exemple de réponse d'erreur Pydantic
{
  "error": "Données invalides",
  "details": [
    {
      "field": "env_score",
      "message": "La valeur doit être comprise entre 0 et 100"
    },
    {
      "field": "email",
      "message": "Format d'email invalide"
    }
  ]
}
```

### 9.3 Gestion des erreurs côté Frontend

```typescript
// Intercepteur API global (src/app/contexts/AuthContext.tsx)
// Si une requête retourne 401 → redirection automatique vers /login
// Si une requête retourne 403 → message d'erreur "Accès refusé"

// Notifications via Sonner Toast
toast.error("Erreur : " + error.message)
toast.success("Opération réussie")
```

---

## 10. Déploiement et Infrastructure

### 10.1 Architecture Docker

```yaml
# docker-compose.yml - Services

services:
  postgres:
    image: postgres:16
    ports: ["5433:5432"]
    environment:
      POSTGRES_USER: esg_user
      POSTGRES_PASSWORD: <secret>
      POSTGRES_DB: esg_db
    volumes:
      - postgres_data:/var/lib/postgresql/data

  rag:
    build: { context: ., dockerfile: Dockerfile.rag }
    ports: ["8000:8000"]
    depends_on: [postgres]

  backend:
    build: { context: ., dockerfile: Dockerfile.backend }
    ports: ["5050:5050"]
    depends_on: [postgres, rag]
    environment:
      DATABASE_URL: postgresql://esg_user:<secret>@postgres:5432/esg_db
      JWT_SECRET_KEY: <secret>

  frontend:
    build: { context: ., dockerfile: Dockerfile.frontend }
    ports: ["80:80"]
    depends_on: [backend]

  # SMTP Gmail utilisé directement par le backend via SMTP_HOST/SMTP_USERNAME/SMTP_PASSWORD
```

### 10.2 Processus de build

#### Frontend

```dockerfile
# Dockerfile.frontend
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build        # → /app/dist

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

#### Backend

```dockerfile
# Dockerfile.backend
FROM python:3.10-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5050
CMD ["python", "backend/app.py"]
```

### 10.3 Environnements

| Environnement | Base de données | Frontend | Backend | Notes |
|---|---|---|---|---|
| Développement | SQLite (fallback) | Vite :5173 | Flask :5050 | Hot reload |
| Production | PostgreSQL :5433 | Nginx :80 | Flask :5050 | Docker Compose |

### 10.4 Commandes de démarrage

```bash
# Développement
npm run dev          # Frontend seul (Vite :5173)
npm run dev:backend  # Backend seul (Flask :5050)
npm run dev:full     # Les deux en parallèle (concurrently)

# Production Docker
docker-compose up --build   # Premier démarrage
docker-compose up -d        # En arrière-plan
docker-compose down         # Arrêt

# Migrations base de données
flask db upgrade             # Appliquer migrations
flask db migrate -m "desc"   # Créer nouvelle migration
```

### 10.5 Proxy de développement (Vite)

```typescript
// vite.config.ts
server: {
  proxy: {
    '/api': {
      target: 'http://127.0.0.1:5050',
      changeOrigin: true
    }
  }
}
```

Toutes les requêtes `/api/*` depuis le frontend sont automatiquement proxifiées vers le backend Flask.

---

## 11. Flux Utilisateur (User Journeys)

### 11.1 Onboarding complet d'un nouvel utilisateur

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. L'utilisateur s'inscrit via /register                        │
│    → Compte créé (is_approved=false, is_verified=false)         │
│                                                                  │
│ 2. L'administrateur voit le compte dans /admin                  │
│    → Clique "Approuver"                                         │
│    → PUT /api/admin/users/<id>/approve                          │
│    → (is_approved=true)                                         │
│    → Email automatique envoyé avec lien de vérification         │
│                                                                  │
│ 3. L'admin assigne une entreprise à l'utilisateur               │
│    → PUT /api/admin/users/<id>/company { "company_id": 5 }      │
│    → (user.company_id = 5)                                      │
│    → L'utilisateur ne verra que les données de cette entreprise │
│                                                                  │
│ 4. L'utilisateur clique le lien dans l'email                    │
│    → POST /api/auth/verify-email { token }                      │
│    → (is_verified=true)                                         │
│                                                                  │
│ 5. L'utilisateur se connecte via /login                         │
│    → JWT cookie émis + company_id retourné dans user object     │
│    → Sidebar filtrée selon son rôle                             │
│    → Redirection vers le Dashboard                              │
└─────────────────────────────────────────────────────────────────┘
```

### 11.2 Réaliser une prédiction ESG

```
1. Navigation vers /prediction
2. Remplissage du formulaire (22+ indicateurs)
3. POST /api/predict → Score ESG retourné
4. Stockage automatique dans prediction_history
5. Visualisation du score et recommandations
6. Option : attacher à une entreprise (POST /api/companies)
```

### 11.3 Utiliser le chatbot RAG

```
1. Navigation vers /chatbot
2. Création automatique d'une conversation (POST /api/chat/conversations)
3. Saisie ou dictée vocale d'une question
4. POST /api/chat/conversations/<id>/messages
5. Backend → appel RAG service → synthèse LLM
6. Réponse avec sources documentaires affichées
7. Historique persisté en base de données
```

---

## 12. Configuration et Variables d'Environnement

### 12.1 Variables requises

| Variable | Description | Exemple |
|---|---|---|
| `DATABASE_URL` | Connexion PostgreSQL | `postgresql://user:pass@host:5433/db` |
| `JWT_SECRET_KEY` | Clé secrète pour signer les JWT (min. 32 chars) | `random-256-bits-string` |

### 12.2 Variables optionnelles

| Variable | Description | Défaut |
|---|---|---|
| `FLASK_ENV` | Environnement Flask | `development` |
| `FLASK_DEBUG` | Mode debug | `0` |
| `RAG_API_BASE_URL` | URL du service RAG | `http://127.0.0.1:8000` |
| `RAG_TOP_K` | Nombre de documents retournés | `5` |
| `RAG_TIMEOUT_SECONDS` | Timeout service RAG | `90` |
| `RAG_ALLOW_LOCAL_FALLBACK` | Activer le fallback local | `false` |
| `SMTP_HOST` | Serveur SMTP | `smtp.gmail.com` |
| `SMTP_PORT` | Port SMTP | `587` |
| `SMTP_USERNAME` | Adresse email d'envoi | — |
| `SMTP_PASSWORD` | Mot de passe app Gmail | — |
| `MAIL_USE_TLS` | Chiffrement TLS | `true` |
| `AWS_ACCESS_KEY_ID` | Accès AWS | — |
| `AWS_SECRET_ACCESS_KEY` | Clé secrète AWS | — |
| `AWS_S3_BUCKET` | Nom du bucket S3 | — |
| `INTEGRATION_AUTH_ENABLED` | Auth sur endpoint intégration | `false` |
| `INTEGRATION_BEARER_TOKEN` | Token bearer intégration | — |
| `NEWS_API_KEY` | Clé API actualités | — |
| `OPENAI_API_KEY` | Clé OpenAI (optionnel) | — |
| `GROQ_API_KEY` | Clé Groq (optionnel) | — |
| 

---

## 13. Glossaire

| Terme | Définition |
|---|---|
| **ESG** | Environmental, Social, and Governance — critères extra-financiers d'évaluation |
| **E** (Environnemental) | Empreinte carbone, gestion des déchets, énergie renouvelable, eau |
| **S** (Social) | Satisfaction employés, diversité, sécurité, investissement communautaire |
| **G** (Gouvernance) | Indépendance du CA, transparence, anti-corruption, conformité |
| **CSRD** | Corporate Sustainability Reporting Directive — directive UE sur le reporting |
| **GRI** | Global Reporting Initiative — standards de reporting ESG |
| **TCFD** | Task Force on Climate-related Financial Disclosures |
| **Scope 1, 2, 3** | Catégories d'émissions carbone (directes, énergie, valeur ajoutée) |
| **CatBoost** | Algorithme de Gradient Boosting de Yandex pour données catégorielles |
| **RAG** | Retrieval-Augmented Generation — IA générative enrichie par recherche documentaire |
| **JWT** | JSON Web Token — standard d'authentification sans état |
| **bcrypt** | Algorithme de hachage de mots de passe adaptatif |
| **RBAC** | Role-Based Access Control — contrôle d'accès par rôles |
| **CORS** | Cross-Origin Resource Sharing — mécanisme de sécurité des navigateurs |
| **ORM** | Object-Relational Mapping — abstraction de base de données |
| **Pydantic** | Bibliothèque Python de validation de données via annotations de type |
| **Whisper** | Modèle de reconnaissance vocale d'OpenAI |
| **Alembic** | Outil de migration de base de données pour SQLAlchemy |
| **Singleton** | Pattern de conception garantissant une instance unique d'une classe |
| **HMR** | Hot Module Replacement — rechargement à chaud en développement |
| **SPA** | Single Page Application — application web sans rechargement de page |

---

## Annexe A — Dépendances principales

### Backend (requirements.txt)

```
Flask>=3.0.0
Flask-SQLAlchemy
Flask-Migrate>=4.0.0
Flask-CORS
flask-jwt-extended
flask-bcrypt
flask-limiter>=3.5.0
pydantic>=2.0.0
email-validator>=1.3.0
psycopg2-binary
catboost>=1.2.5
scikit-learn>=1.2.0
pandas>=2.0.0
joblib>=1.2.0
requests>=2.31.0
openai>=1.30.0
boto3>=1.34.0
python-dotenv>=1.0.1
beautifulsoup4>=4.12.0
Pillow>=10.0.0
```

### Frontend (package.json — principales)

```json
{
  "react": "^18.3.1",
  "react-dom": "^18.3.1",
  "react-router": "^7.13.0",
  "typescript": "^5.x",
  "vite": "^6.3.5",
  "@tailwindcss/vite": "^4.1.12",
  "recharts": "^2.15.2",
  "react-hook-form": "^7.55.0",
  "lucide-react": "^0.487.0",
  "motion": "^12.23.24",
  "sonner": "^2.0.3",
  "jspdf": "^4.2.1"
}
```

---

## Annexe B — Structure des fichiers de configuration

```
ESG_Platform/
├── .env                         # Variables d'environnement (NON VERSIONNÉ)
├── .env.example                 # Template des variables
├── docker-compose.yml           # Orchestration multi-conteneurs
├── Dockerfile.backend           # Image backend Flask
├── Dockerfile.frontend          # Image frontend React + Nginx
├── Dockerfile.rag               # Image service RAG
├── vite.config.ts               # Configuration Vite + proxy
├── tailwind.config.mjs          # Configuration Tailwind CSS
├── tsconfig.json                # Configuration TypeScript
├── package.json                 # Dépendances frontend
├── alembic.ini                  # Configuration migrations
├── migrations/                  # Versions de migration Alembic
└── .postman/                    # Collections Postman pour tests API
```

---

*Documentation mise à jour le 1 juin 2026 — ESG Platform v1.1*  
*Pour toute question technique : elaafriaa@gmail.com*
