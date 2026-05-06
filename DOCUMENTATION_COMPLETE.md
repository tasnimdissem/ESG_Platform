# 📊 ESG Platform - Documentation Technique Complète

**Version:** 1.0.0  
**Date:** May 2026  
**Stack:** React 18 + TypeScript + Vite | Flask + Python | CatBoost ML | RAG (FAISS) | SQLite/PostgreSQL

---

## 📑 Table des Matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture Globale](#architecture-globale)
3. [Installation & Setup](#installation--setup)
4. [Fonctionnalités Détaillées](#fonctionnalités-détaillées)
5. [Modèle Machine Learning - CatBoost](#modèle-machine-learning---catboost)
6. [Système RAG (Retrieval-Augmented Generation)](#système-rag-retrieval-augmented-generation)
7. [Base de Données](#base-de-données)
8. [Docker & Déploiement](#docker--déploiement)
9. [API Reference](#api-reference)
10. [Troubleshooting](#troubleshooting)

---

## 1. Vue d'ensemble

### Qu'est-ce que l'ESG Platform?

**ESG Platform** est une **plateforme intelligente de prédiction et d'analyse ESG (Environmental, Social, Governance)** conçue pour:

- **Prédire automatiquement** les scores ESG des entreprises basés sur leurs indicateurs financiers
- **Recommander** des actions concrètes pour améliorer les scores
- **Analyser** les tendances ESG avec dashboards interactives
- **Assister** via chatbot alimenté par RAG (Retrieval-Augmented Generation)
- **Authentifier** les utilisateurs et gérer les sessions JWT

### Cas d'Usage

✅ **Analystes ESG:** Prédire scores pour portfolio companies  
✅ **Investisseurs:** Évaluer durabilité avant investissement  
✅ **Consultants:** Recommander améliorations ESG  
✅ **Chercheurs:** Analyser corrélations ESG/finances  

---

## 2. Architecture Globale

### 2.1 Diagramme d'Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND (React 18)                      │
│  Port: 5173                                                  │
│  ┌──────────┐ ┌───────────┐ ┌──────────┐ ┌──────────────┐  │
│  │Dashboard │ │Prediction │ │Analytics │ │Recommendations│  │
│  └──────────┘ └───────────┘ └──────────┘ └──────────────┘  │
│  ┌──────────┐ ┌───────────┐ ┌──────────────────────────┐   │
│  │Chatbot   │ │Auth Pages │ │Vite Proxy (/api → 5050) │   │
│  └──────────┘ └───────────┘ └──────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              ↕ HTTP
                          Vite Proxy
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                   BACKEND (Flask)                            │
│  Port: 5050                                                  │
│  ┌──────────────┐ ┌──────────┐ ┌─────────────────────┐     │
│  │Auth Routes   │ │Prediction│ │Integration/RAG      │     │
│  │/api/auth/*   │ │/api/predict   │/api/v1/integration │   │
│  └──────────────┘ └──────────┘ └─────────────────────┘     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         ML Service (CatBoost Singleton)              │   │
│  │  - Load model once                                   │   │
│  │  - Target encode features                            │   │
│  │  - Return ESG score                                  │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │        Database Layer (SQLAlchemy ORM)               │   │
│  │  - User model (SQLite/PostgreSQL)                    │   │
│  │  - PasswordResetToken model                          │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
         ↕ (HTTP/REST)        ↕ (Query RAG API)
    Chatbot Integration    RAG System
         ↕                      ↕
┌─────────────────────────┐  ┌─────────────────────────┐
│   RAG System            │  │  Database (SQLite)      │
│   Port: 8000            │  │  esg_pfe.db             │
│ ┌─────────────────────┐ │  │ ┌───────────────────┐   │
│ │ FAISS Index         │ │  │ │ users table       │   │
│ │ - Vector DB         │ │  │ │ - id, email, pwd  │   │
│ │ - Semantic search   │ │  │ └───────────────────┘   │
│ └─────────────────────┘ │  │ ┌───────────────────┐   │
│ ┌─────────────────────┐ │  │ │ reset_tokens tbl  │   │
│ │ LLM (OpenAI)        │ │  │ │ - For pwd reset   │   │
│ │ - Generate answers  │ │  │ └───────────────────┘   │
│ └─────────────────────┘ │  │                         │
│ ┌─────────────────────┐ │  │                         │
│ │ Embedder (SBERT)    │ │  │                         │
│ │ - Semantic embed    │ │  │                         │
│ └─────────────────────┘ │  │                         │
└─────────────────────────┘  └─────────────────────────┘
```

### 2.2 Flow de Communication

**Exemple: Prédiction ESG**
```
1. User clique "Prédire le Score ESG"
2. Frontend (Prediction.tsx):
   - Collecte formulaire
   - POST /api/predict
3. Vite Proxy:
   - Intercepte /api/predict
   - Reroute vers http://127.0.0.1:5050
4. Backend (Flask prediction.py):
   - Reçoit JSON
   - Appelle predict_esg() (ML Service)
5. ML Service (ml_service.py):
   - Charge CatBoost (1ère fois)
   - Target encode 'primary_industry'
   - Aligne features
   - Prédit score
6. Retour Frontend:
   - {"score": 92.34}
   - Affiche inline recommendations
7. Appelle /api/v1/integration:
   - RAG génère 3 recommendations top
   - Affiche suggestions
8. "Voir tout" → Navigate /recommendations
```

### 2.3 Diagrammes UML (Pour Rapport)

#### 2.3.1 Diagramme de Cas d'Utilisation

```mermaid
graph TB
    subgraph Acteurs
        A1["👤 Analyste ESG"]
        A2["💰 Investisseur"]
        A3["📊 Consultant"]
        A4["🔐 Admin"]
    end
    
    subgraph "Système ESG Platform"
        UC1["Authentification<br/>(Login/Register)"]
        UC2["Prédire Score ESG"]
        UC3["Voir Recommendations"]
        UC4["Analyser Tendances"]
        UC5["Chat Assistance"]
        UC6["Gérer Utilisateurs"]
        UC7["Reset Mot de Passe"]
    end
    
    subgraph Services_Externes
        SE1["🤖 CatBoost ML"]
        SE2["🧠 RAG/FAISS"]
        SE3["📰 News API"]
        SE4["💬 OpenAI LLM"]
    end
    
    A1 -->|Utilise| UC1
    A1 -->|Utilise| UC2
    A1 -->|Utilise| UC3
    A1 -->|Utilise| UC4
    A1 -->|Utilise| UC5
    
    A2 -->|Utilise| UC1
    A2 -->|Utilise| UC2
    A2 -->|Utilise| UC4
    
    A3 -->|Utilise| UC1
    A3 -->|Utilise| UC3
    A3 -->|Utilise| UC5
    
    A4 -->|Utilise| UC6
    
    UC1 -->|Include| UC7
    UC2 -->|Utilise| SE1
    UC3 -->|Utilise| SE2
    UC5 -->|Utilise| SE2
    UC5 -->|Utilise| SE4
    UC4 -->|Utilise| SE3
```

#### 2.3.2 Diagramme de Séquence - Flux de Prédiction ESG

```mermaid
sequenceDiagram
    participant User as 👤 User
    participant Frontend as ⚛️ React Frontend
    participant ViteProxy as 🔄 Vite Proxy
    participant Backend as 🐍 Flask Backend
    participant MLService as 🤖 ML Service
    participant DB as 💾 SQLite/PostgreSQL
    participant RAG as 🧠 RAG System

    User->>Frontend: 1. Entre données (18 features)
    Frontend->>Frontend: 2. Valide formulaire
    Frontend->>ViteProxy: 3. POST /api/predict
    
    ViteProxy->>Backend: 4. Reroute vers 5050
    Backend->>MLService: 5. predict_esg(data)
    
    MLService->>MLService: 6. Load CatBoost (1ère fois)
    MLService->>MLService: 7. Target encode 'industry'
    MLService->>MLService: 8. Aligne features (18)
    MLService->>MLService: 9. Prédiction CatBoost
    
    MLService-->>Backend: 10. Retourne score
    Backend-->>Frontend: 11. {"score": 92.34}
    
    Frontend->>Frontend: 12. Affiche score
    Frontend->>Backend: 13. GET /api/v1/integration
    
    Backend->>RAG: 14. Query RAG API
    RAG->>RAG: 15. FAISS search + LLM gen
    RAG-->>Backend: 16. 3 recommendations
    
    Backend-->>Frontend: 17. Retourne suggestions
    Frontend->>User: 18. Affiche recommendations

    Frontend->>DB: 19. (Optionnel) Log score
    DB-->>Frontend: 20. ✓
```

#### 2.3.3 Diagramme d'Activité - Processus de Prédiction ESG

```mermaid
graph TD
    A["📥 Utilisateur soumet données<br/>18 features"] --> B{"✓ Données<br/>valides?"}
    
    B -->|Non| C["❌ Afficher erreur<br/>de validation"]
    C --> A
    
    B -->|Oui| D["🔐 Vérifier JWT<br/>token valide"]
    
    D -->|Invalide| E["❌ Rediriger login"]
    E --> A
    
    D -->|Valide| F["📤 POST /api/predict<br/>au backend"]
    
    F --> G["⚙️ Backend reçoit<br/>la requête"]
    
    G --> H{"🤖 CatBoost<br/>déjà chargé?"}
    
    H -->|Non| I["📦 Load model<br/>+ features"]
    H -->|Oui| J["⚡ Utilise cache"]
    
    I --> K["🔄 Target encode<br/>primary_industry"]
    J --> K
    
    K --> L["📊 Aligner features<br/>avec model"]
    
    L --> M["🎯 Prédire score<br/>CatBoost"]
    
    M --> N["✅ Retourner<br/>score au frontend"]
    
    N --> O["🎨 Afficher score<br/>à l'écran"]
    
    O --> P["🧠 Requête RAG<br/>pour recommendations"]
    
    P --> Q["💾 FAISS search<br/>+ LLM generate"]
    
    Q --> R["📋 Retourner<br/>3 suggestions"]
    
    R --> S["✨ Afficher<br/>recommendations"]
    
    S --> T["🎯 User voit:<br/>- Score ESG<br/>- Suggestions<br/>- Bouton 'Voir tout'"]
```

#### 2.3.4 Diagramme de Classes - Architecture Backend

```mermaid
classDiagram
    class User {
        +id: Integer
        +email: String
        +password_hash: String
        +created_at: DateTime
        +updated_at: DateTime
        +__init__()
        +set_password()
        +check_password()
    }

    class PasswordResetToken {
        +id: Integer
        +user_id: Integer
        +token: String
        +expires_at: DateTime
        +is_used: Boolean
        +__init__()
        +is_valid()
    }

    class MLService {
        -model: CatBoost
        -encoder: TargetEncoder
        -feature_names: List
        +load_resources()
        +predict(data) -> float
        +_align_features()
    }

    class PredictionBlueprint {
        +predict() -> dict
        +validate_input(data)
    }

    class AuthBlueprint {
        +login(email, password) -> dict
        +register(email, password) -> dict
        +get_me() -> dict
        +forgot_password(email)
        +reset_password(token, password)
    }

    class RAGService {
        +query(question) -> dict
        +generate_recommendations()
        +search_faiss()
    }

    class FlaskApp {
        +db: SQLAlchemy
        +jwt: JWTManager
        +create_app()
        +init_db()
        +register_blueprints()
    }

    class AuthContext {
        +isAuthenticated: Boolean
        +user: User
        +token: String
        +login(email, password)
        +logout()
        +restoreSession()
    }

    User "1" -- "*" PasswordResetToken : has
    PredictionBlueprint "1" -- "1" MLService : uses
    AuthBlueprint "1" -- "*" User : manages
    FlaskApp "1" -- "1" AuthBlueprint : registers
    FlaskApp "1" -- "1" PredictionBlueprint : registers
    AuthBlueprint "1" -- "1" RAGService : integrates
    AuthContext "1" -- "1" User : represents
    FlaskApp "1" -- "1" AuthContext : communicates
```

#### 2.3.5 Diagramme de Déploiement

```mermaid
graph TB
    subgraph Local["🖥️ Développement Local"]
        LFE["⚛️ Vite Frontend<br/>:5173"]
        LBE["🐍 Flask Backend<br/>:5050"]
        LRAG["🧠 RAG System<br/>:8000"]
        LSQLITE["💾 SQLite<br/>esg_pfe.db"]
    end

    subgraph Cloud["☁️ Production"]
        WEB["🌐 Web Server<br/>Nginx"]
        DOCKER["🐳 Docker Services"]
        PG["📊 PostgreSQL<br/>Cloud DB"]
        STORAGE["📦 Cloud Storage<br/>Models/Embeddings"]
        LLM["🤖 OpenAI API"]
    end

    LFE <-->|HTTP| LBE
    LBE <-->|HTTP| LRAG
    LBE <-->|SQL| LSQLITE
    LRAG <-->|SQL| LSQLITE

    WEB -->|reverse proxy| DOCKER
    DOCKER -->|container 1| BEContainer["🐍 Backend"]
    DOCKER -->|container 2| FEContainer["⚛️ Frontend"]
    DOCKER -->|container 3| RAGContainer["🧠 RAG"]
    
    BEContainer <-->|SQL| PG
    RAGContainer <-->|Read| STORAGE
    RAGContainer <-->|API| LLM

    style Local fill:#e1f5ff
    style Cloud fill:#f3e5f5
```

---

## 3. Installation & Setup

### 3.1 Prérequis

- **Node.js** ≥ 18.0
- **Python** ≥ 3.10
- **pip** (gestion packages Python)
- **Windows/macOS/Linux**

### 3.2 Installation Locale (Développement)

```bash
# 1. Clone le repo
git clone <repo-url>
cd ESG_Platform

# 2. Setup Python venv
python -m venv .venv

# Windows:
.\.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 3. Install Python dependencies
pip install -r backend/requirements.txt

# 4. Install Node dependencies
npm install

# 5. Vérifier env vars
# Crée .env à la racine (voir section 7.1)

# 6. Lance dev complet
npm run dev:full

# Services disponibles après ~30-60s:
# - Frontend: http://localhost:5173
# - Backend: http://127.0.0.1:5050
# - RAG: http://127.0.0.1:8000
```

### 3.3 Configuration Environnement (.env)

```bash
# .env à la racine du projet

# ===== DATABASE =====
DATABASE_URL=sqlite:///esg_pfe.db
# Pour PostgreSQL: DATABASE_URL=postgresql://user:password@localhost:5432/esg_platform

# ===== AUTHENTICATION =====
JWT_SECRET_KEY=your-secret-key-change-in-production

# ===== RAG CONFIGURATION =====
RAG_API_BASE_URL=http://127.0.0.1:8000
RAG_INTEGRATION_PATH=/api/v1/integration
RAG_TIMEOUT_SECONDS=90
RAG_TOP_K=5
RAG_ALLOW_LOCAL_FALLBACK=true

# ===== EXTERNAL APIs =====
NEWS_API_KEY=your-news-api-key

# ===== EMAIL (Password Reset) =====
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
EMAIL_FROM=no-reply@esg-platform.local
EMAIL_RESET_LINK_BASE_URL=http://localhost:5173/reset-password
```

---

## 4. Fonctionnalités Détaillées

### 4.1 Dashboard (/dashboard)

**Objectif:** Vue d'ensemble des KPIs ESG de l'entreprise

**Componentes:**
- **KPI Cards:** E/S/G scores, ESG rating
- **ESG Score Gauge:** Visualisation circulaire
- **Recommendations Count:** Nombre d'actions suggérées
- **Quick Actions:** Boutons vers Prediction, Analytics, Recommendations

**Implémentation:**
```tsx
// src/app/pages/Dashboard.tsx
export default function Dashboard() {
  - Récupère user depuis AuthContext
  - Affiche scores statiques (hardcodé pour MVP)
  - Cards animées avec Recharts
  - Navigation vers autres pages
}
```

**Data Flow:**
- Pas d'API call (MVP) - données locales
- Production: appelerait `/api/dashboard` pour données utilisateur

---

### 4.2 Prediction (Calculateur de Score ESG)

**Objectif:** Prédire le score ESG basé sur des indicateurs financiers

**Formulaire Inputs (18 features):**
```
Categorical:
- primary_industry (Technology, Finance, Energy, etc.)

Numerical:
- log_market_cap (log10 du market cap)
- co2_emissions (tonnes CO2)
- revenue (en millions USD)
- governance_score (0-100)
- social_score (0-100)
- environment_score (0-100)
- board_diversity_pct (%)
- female_employees_pct (%)
- employee_satisfaction (0-100)
- audit_frequency (fois/an)
- supply_chain_audits (0/1)
- carbon_offset_pct (%)
- renewable_energy_pct (%)
- water_efficiency (m³/revenue)
- waste_recycling_pct (%)
- community_investment_usd (USD)
- training_hours_per_employee (heures)
```

**Process:**
```
1. User remplit formulaire
2. Click "Prédire le Score ESG"
3. handleSubmit():
   - Valide données
   - POST /api/predict {form_data}
4. Backend MLService:
   - Target encode industry
   - Aligne features
   - Prédit CatBoost
5. Affiche score + 3 recommendations inline
6. "Voir tout" → navigate /recommendations?focus=Environmental
```

**Implémentation Frontend:**
```tsx
// src/app/pages/Prediction.tsx
const handleSubmit = async (e) => {
  const response = await fetchPrediction(formData);
  const { score } = await response.json();
  
  setScore(score);
  
  // Fetch recommendations basées sur le score
  const recommendations = await fetchRecommendations({
    score,
    focus_area: focusArea
  });
  setSuggestions(recommendations.slice(0, 3));
};
```

**API Endpoint:**
```
POST /api/predict
Request: { primary_industry, log_market_cap, ... }
Response: { score: 92.34 }
Status Codes:
- 200: Succès
- 400: Payload invalide
- 500: Erreur modèle
```

---

### 4.3 Analytics (Insights ML & Visualisations)

**Objectif:** Analyser tendances ESG et corrélations avec finances

**Visualisations:**
1. **Line Chart:** Tendances mensuelles E/S/G (6 mois)
2. **Scatter Plot:** Corrélation feature importance vs score
3. **Details Table:** Tableau 10+ métriques ESG

**Implémentation:**
```tsx
// src/app/pages/Analytics.tsx
- Hardcoded data pour MVP
- Recharts pour visualisations
- Responsive layout (mobile-friendly)
```

**Utilité:**
- ✅ Comprendre evolution ESG dans le temps
- ✅ Identifier corrélations (ex: renewable% ↔ score)
- ✅ Benchmark vs secteur (future)

---

### 4.4 Recommendations (Catalogue Complet)

**Objectif:** Afficher toutes les recommandations filtrées par catégorie/priorité

**Features:**
- Filter by Category (Environmental/Social/Governance)
- Filter by Priority (High/Medium/Low)
- Affiche: Title, Impact, Effort, Timeline, Description
- "See Details" pour expanser

**Implémentation:**
```tsx
// src/app/pages/RecommendationsRag.tsx
- Reçoit query params (?focus=Environmental)
- Appelle fetchRecommendations(filters)
- Affiche liste avec Recharts progress
- Supports query params pour deep linking
```

**API Integration:**
```
POST /api/v1/integration
Request: {
  message: "Provide prioritized ESG recommendations",
  signals: { esg_score, risk_level, focus_area }
}
Response: {
  recommendations: [{
    id, title, pillar, impact, effort, timeline, priority, justification
  }]
}
```

---

### 4.5 Chatbot (RAG-Powered Assistant)

**Objectif:** Assister utilisateurs sur ESG via conversational interface

**Features:**
- Chat interface persistant
- Powered by FAISS + LLM
- Contextual responses basées sur documents ESG
- Sources affichées (FAISS retrieval)

**Implémentation Frontend:**
```tsx
// src/app/pages/Chatbot.tsx
- Message input + button
- Display chat history
- Loading indicator
- Error handling
- Call fetchChatResponse(message)
```

**Backend RAG:**
```
POST /api/v1/integration
{
  message: "What is ESG?",
  top_k: 5,
  include_recommendations: false
}

Response:
{
  response: {
    answer: "ESG means Environmental, Social, Governance...",
    sources: ["source1.pdf", "source2.pdf"]
  }
}
```

**Utilité:**
- 🤖 Support 24/7 sans intervention humaine
- 📚 Répond basé sur base documentaire (FAISS)
- 🎯 Contextuel (understand user intent)

---

### 4.6 Authentication

**Objectif:** Sécuriser accès plateforme via JWT

**Flows:**

**Login:**
```
1. User POST /api/auth/login {email, password}
2. Backend:
   - Find user by email
   - Check bcrypt password
   - Generate JWT token
3. Frontend:
   - Store token in localStorage
   - Set AuthContext.user
   - Redirect /dashboard
```

**Registration:**
```
1. User POST /api/auth/register {name, email, password}
2. Backend:
   - Validate inputs
   - Hash password (bcrypt)
   - Create user
   - Generate JWT
3. Frontend:
   - Auto-login après registration
```

**Session Restore:**
```
1. App mounts
2. AuthContext.useEffect():
   - Récupère token from localStorage
   - Validate JWT format
   - GET /api/auth/me {Authorization: Bearer <token>}
   - Si 401/422: Clear token & redirect /login
   - Si 200: Set user + redirect /dashboard
```

**Password Reset:**
```
1. User POST /api/auth/forgot-password {email}
2. Backend:
   - Generate reset token
   - Send email link (si SMTP configuré)
3. User clicks link
4. POST /api/auth/reset-password {token, new_password}
5. Backend: Update password, mark token used
```

**Implémentation:**
```tsx
// src/app/contexts/AuthContext.tsx
- Centralized auth state
- JWT persistence in localStorage
- Auto-restore on app load
- Login/logout/restore functions
```

---

## 5. Modèle Machine Learning - CatBoost

### 5.1 Qu'est-ce que CatBoost?

**CatBoost** = Categorical Boosting (Yandex)

- **Type:** Gradient Boosting Decision Tree
- **Forces:** 
  - ✅ Gère bien features catégoriques
  - ✅ Fast training & inference
  - ✅ Robuste aux outliers
  - ✅ Optimisé CPU
- **Use Case:** Prédiction ESG score (0-100)

### 5.2 Architecture du Service ML

```python
# backend/services/ml_service.py

class MLService:
    """Singleton managing CatBoost model lifecycle"""
    
    def __init__(self):
        self.model = None              # CatBoostRegressor
        self.target_encoder = None     # TargetEncoder (industry)
        self.feature_names = []        # List[str] (18 features)
        self.is_loaded = False         # Prevent reloads
    
    def load_resources(self):
        """Load model, encoder, features (once)"""
        if self.is_loaded:
            return
        
        # 1. Import CatBoost (lazy - optional)
        from catboost import CatBoostRegressor
        
        # 2. Load binary model
        self.model = CatBoostRegressor()
        self.model.load_model('backend/model/catboost_model.cbm')
        
        # 3. Load target encoder (for categorical industry)
        self.target_encoder = joblib.load('backend/model/target_encoder.pkl')
        
        # 4. Load expected feature names
        with open('backend/model/feature_names.txt') as f:
            self.feature_names = [line.strip() for line in f]
        
        self.is_loaded = True
    
    def predict(self, data: dict) -> float:
        """Process input & return ESG score"""
        
        self.load_resources()  # Lazy load if first time
        
        # STEP 1: Target Encode categorical feature
        primary_industry = data.get('primary_industry', 'Unknown')
        industry_encoded = self.target_encoder.transform(
            pd.DataFrame([{'primary_industry': primary_industry}])
        )[0][0]
        data['industry_target_enc'] = industry_encoded
        
        # STEP 2: Create DataFrame
        input_df = pd.DataFrame([data])
        
        # STEP 3: Align columns (add missing, remove extra)
        for col in self.feature_names:
            if col not in input_df.columns:
                input_df[col] = None
        input_df = input_df[self.feature_names]
        
        # STEP 4: Predict
        prediction = self.model.predict(input_df)
        score = float(round(prediction[0], 2))
        
        return score

# Singleton instance
ml_service_instance = MLService()

def predict_esg(data: dict) -> float:
    return ml_service_instance.predict(data)
```

### 5.3 Fichiers du Modèle

```
backend/model/
├── catboost_model.cbm         # Modèle entraîné (~40MB)
│                               # Format binaire CatBoost
│                               # Contient: arbres, poids, hyperparams
├── target_encoder.pkl         # scikit-learn TargetEncoder
│                               # Encode 'primary_industry' → numeric
├── feature_names.txt          # List des 18 features attendues
│                               # Une feature par ligne
└── [training_notebook].ipynb   # Notebook d'entraînement (référence)
```

### 5.4 Pipeline de Prédiction (Détaillé)

**Input JSON (Exemple):**
```json
{
  "primary_industry": "Technology",
  "log_market_cap": 20.5,
  "co2_emissions": 150000,
  "revenue": 5000000,
  "governance_score": 75,
  "social_score": 68,
  "environment_score": 82,
  "board_diversity_pct": 35,
  "female_employees_pct": 42,
  "employee_satisfaction": 78,
  "audit_frequency": 2,
  "supply_chain_audits": 1,
  "carbon_offset_pct": 20,
  "renewable_energy_pct": 45,
  "water_efficiency": 3.2,
  "waste_recycling_pct": 65,
  "community_investment_usd": 500000,
  "training_hours_per_employee": 25
}
```

**Processing Steps:**
```
1. TARGET ENCODING (Categorical)
   Input: "Technology"
   ↓ TargetEncoder.transform()
   Output: 2.45 (numeric mean target for Technology companies)
   Insert: data['industry_target_enc'] = 2.45

2. DATAFRAME ALIGNMENT
   Input: data dict (18 keys)
   ↓ Create pandas DataFrame([data])
   ↓ Add missing columns as NaN
   ↓ Reorder to match self.feature_names
   Output: DataFrame(shape=(1, 18))

3. CATBOOST PREDICTION
   Input: DataFrame(shape=(1, 18))
   ↓ model.predict(input_df)
   Output: array([92.34])

4. POST-PROCESSING
   Extract first element: 92.34
   Round to 2 decimals
   Convert to float: 92.34
   Return: float(92.34)
```

**Output:**
```json
{
  "score": 92.34,
  "percentile": "Top 10%",
  "status": "success"
}
```

### 5.5 Gestion d'Erreurs

```python
def predict(self, data: dict) -> float:
    try:
        # Prediction logic
        ...
    except ValueError as ve:
        # Data validation errors
        raise ValueError(f"Invalid input: {ve}")
    except RuntimeError as re:
        # Model loading errors
        raise RuntimeError(f"Model error: {re}")
    except Exception as e:
        # Unexpected errors
        raise Exception(f"Unexpected: {e}")

# Flask route catches these & returns:
# - 400: ValueError (bad input)
# - 500: RuntimeError/Exception (server error)
```

### 5.6 Optimisations de Performance

**1. Singleton Pattern:**
- Modèle chargé une seule fois
- Shared across all requests
- Pas de rechargement = latence ~50-100ms

**2. Lazy Loading de CatBoost:**
- Import CatBoost seulement dans load_resources()
- Backend démarre même sans CatBoost
- Fails gracefully si CatBoost absent

**3. In-Memory Caching:**
```python
if self.is_loaded:
    return  # Skip reloading
```

### 5.7 Monitoring & Logging

```python
# backend/routes/prediction.py

@prediction_bp.post('/predict')
def predict():
    logger.info(f"Predict request received with keys: {list(data.keys())}")
    logger.debug(f"Full payload: {data}")
    
    score = predict_esg(data)
    
    logger.info(f"Prediction successful: score={score}")
    
    return jsonify({"score": score}), 200

# Logs appear in terminal during npm run dev:full
# Example:
# INFO:backend.routes.prediction:Predict request received with keys: ['primary_industry', 'log_market_cap', ...]
# INFO:backend.routes.prediction:Prediction successful: score=92.34
```

---

## 6. Système RAG (Retrieval-Augmented Generation)

### 6.1 Vue d'ensemble du RAG

**RAG** = Retrieval-Augmented Generation

**Problème résolu:**
- ❌ LLM seul: hallucine, connaissance limitée
- ✅ RAG: récupère contexte du corpus ESG, puis génère

**Workflow:**
```
Question utilisateur
    ↓
1. RETRIEVE: Cherche documents similaires (FAISS)
2. AUGMENT: Combine documents + question
3. GENERATE: LLM génère réponse basée sur contexte
    ↓
Réponse précise + sources
```

### 6.2 Architecture RAG

```
RAG_SYSTEM/
├── app.py                    # Flask app (port 8000)
├── requirements.txt          # Dependencies
├── src/
│   ├── __init__.py
│   ├── config.py            # Config (API tokens, paths)
│   ├── rag_engine.py        # Core RAG logic
│   ├── ingestion.py         # Document loading
│   ├── structured_transform.py  # Chunking
│   └── web_ui.py            # Optional UI
├── data/
│   ├── raw/
│   │   ├── pdfs/            # ESG documents (PDFs)
│   │   └── datasets/        # Excel files
│   └── processed/
│       ├── chunks.json      # Chunked documents
│       └── structured_chunks.json
└── storage/
    └── faiss_index/
        ├── index.faiss      # Vector database (FAISS)
        └── metadata.json    # Chunk metadata
```

### 6.3 Componentes Clés

**1. Document Ingestion:**
```python
# RAG_SYSTEM/src/ingestion.py

def ingest_sources():
    """Load PDFs, Excel files → chunks"""
    
    # Scan data/raw/pdfs/
    # Extract text from PDFs (PyPDF2)
    # Parse Excel files (openpyxl)
    # Save to data/processed/chunks.json
```

**2. Document Chunking:**
```python
# RAG_SYSTEM/src/structured_transform.py

def transform_chunks():
    """Split documents into semantic chunks"""
    
    # Read chunks.json
    # Split by sentences/paragraphs
    # Create overlapping windows (context)
    # Save structured_chunks.json
```

**3. Vector Embedding:**
```python
# RAG_SYSTEM/src/rag_engine.py

from sentence_transformers import SentenceTransformer

_EMBEDDER = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
# Converts text → 384-dim vector
# Semantic similarity-aware
```

**4. FAISS Index:**
```python
import faiss

# Create index from embedded chunks
index = faiss.IndexFlatL2(384)  # L2 distance
index.add(embeddings)           # Add all chunk vectors

# Save index + metadata
faiss.write_index(index, "storage/faiss_index/index.faiss")
```

**5. Query Processing:**
```python
def query(question: str, top_k=5) -> str:
    """Retrieve + Generate"""
    
    # 1. RETRIEVE
    q_embedding = _EMBEDDER.encode(question)
    distances, indices = index.search(q_embedding, top_k)
    chunks = [metadata[idx] for idx in indices]
    
    # 2. AUGMENT
    context = "\n".join(chunks)
    prompt = f"""Context: {context}\n\nQuestion: {question}\n\nAnswer:"""
    
    # 3. GENERATE
    response = llm.generate(prompt)
    
    return response
```

### 6.4 LLM Integration (OpenAI)

```python
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_answer(prompt: str) -> str:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=500
    )
    return response.choices[0].message.content
```

### 6.5 API Endpoints (Backend Integration)

**Endpoint 1: Chat**
```
POST /api/v1/query
{
  "question": "What is ESG?",
  "top_k": 5
}

Response:
{
  "answer": "ESG stands for Environmental, Social, Governance...",
  "sources": ["source1.pdf", "source2.pdf"],
  "confidence": 0.92
}
```

**Endpoint 2: Integration (Recommendations)**
```
POST /api/v1/integration
{
  "message": "Provide ESG recommendations",
  "signals": {"esg_score": 85, "focus_area": "Environmental"},
  "top_k": 5,
  "include_recommendations": true
}

Response:
{
  "response": {
    "answer": "...",
    "recommendations": [{
      "title": "Increase renewable energy",
      "impact": 12,
      "effort": "high",
      "timeline": "6-12 months"
    }],
    "sources": [...]
  }
}
```

### 6.6 Liason Backend ↔ RAG

**Frontend → Backend:**
```
POST http://localhost:5173/api/v1/integration
  (proxy via Vite)
↓
Vite reroutes to:
POST http://127.0.0.1:5050/api/v1/integration
```

**Backend → RAG:**
```python
# backend/services/integration_service.py

def query_rag(message: str, signals=None):
    """Call RAG system for recommendations"""
    
    try:
        response = requests.post(
            f"{RAG_API_BASE_URL}{RAG_INTEGRATION_PATH}",
            json={"message": message, "signals": signals},
            timeout=RAG_TIMEOUT_SECONDS
        )
        return response.json()
    except:
        # FALLBACK: Use local RAG
        if RAG_ALLOW_LOCAL_FALLBACK:
            return local_rag_fallback(message)
        raise
```

### 6.7 Error Handling & Fallback

**Scenario 1: RAG UP**
```
Request /api/v1/integration
  ↓
Backend queries RAG on 8000
  ↓
RAG returns results + sources
  ↓
200 OK with RAG response
```

**Scenario 2: RAG DOWN**
```
Request /api/v1/integration
  ↓
Backend tries RAG on 8000
  ↓
Timeout/Connection error
  ↓
If RAG_ALLOW_LOCAL_FALLBACK=true:
  Use local_rag_service (hardcoded responses)
  ↓
200 OK with fallback response
  ↓
Else:
  502 Bad Gateway
```

---

## 7. Base de Données

### 7.1 Architecture BD

**Options:**
- **Development:** SQLite (fichier local, zéro setup)
- **Production:** PostgreSQL (scalable, multi-user)

### 7.2 Schema SQLite/PostgreSQL

```sql
-- Users Table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,  -- bcrypt hashed
    role VARCHAR(64) NOT NULL DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Password Reset Tokens
CREATE TABLE password_reset_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(128) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX ix_users_email ON users(email);
CREATE INDEX ix_reset_tokens_hash ON password_reset_tokens(token_hash);
```

### 7.3 SQLAlchemy Models

```python
# backend/models/user.py

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(64), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, raw_password):
        self.password = bcrypt.generate_password_hash(raw_password).decode()
    
    def check_password(self, raw_password):
        return bcrypt.check_password_hash(self.password, raw_password)

class PasswordResetToken(db.Model):
    __tablename__ = 'password_reset_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey('users.id'), nullable=False)
    token_hash = db.Column(db.String(128), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### 7.4 Users de test

**Local development:** crée un compte de test via le formulaire d’inscription, puis utilise-le pour valider les parcours d’authentification.

**Production:** provisionne les comptes via votre process d’administration ou de migration, sans jamais embarquer d’identifiants en dur dans le code ou la documentation.
# Run with: flask seed-users
```

### 7.5 Migration (SQLite → PostgreSQL)

**Step 1: Export data**
```python
from backend.app import app
from backend.models.user import User
import json

with app.app_context():
    users = User.query.all()
    data = [u.to_dict() for u in users]
    with open("users_backup.json", "w") as f:
        json.dump(data, f)
```

**Step 2: Setup PostgreSQL**
```bash
# Install PostgreSQL (macOS):
brew install postgresql

# Start service:
brew services start postgresql

# Create database:
createdb esg_platform
```

**Step 3: Update .env**
```
DATABASE_URL=postgresql://postgres:password@localhost:5432/esg_platform
```

**Step 4: Restart backend**
```bash
npm run dev:full
# SQLAlchemy auto-creates schema
```

**Step 5: Restore data (if needed)**
```python
# Optional: import users from JSON backup
```

---

## 8. Docker & Déploiement

### 8.1 Fichiers Docker

**Dockerfile.backend** (Flask)
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 5050

# Run app
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0"]
```

**Dockerfile.frontend** (Node/Vite)
```dockerfile
FROM node:18-alpine as builder

WORKDIR /app

COPY package*.json .
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**Dockerfile.rag** (RAG System)
```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY RAG_SYSTEM/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY RAG_SYSTEM .

EXPOSE 8000
CMD ["python", "-m", "RAG_SYSTEM.app"]
```

### 8.2 Docker Compose

**docker-compose.yml**
```yaml
version: '3.8'

services:
  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    environment:
      - BACKEND_URL=http://backend:5050

  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "5050:5050"
    environment:
      DATABASE_URL: postgresql://postgres:password@postgres:5432/esg_platform
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      RAG_API_BASE_URL: http://rag:8000
    depends_on:
      - postgres
      - rag
    volumes:
      - ./backend:/app/backend

  rag:
    build:
      context: .
      dockerfile: Dockerfile.rag
    ports:
      - "8000:8000"
    environment:
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    volumes:
      - ./RAG_SYSTEM/storage:/app/storage

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      POSTGRES_DB: esg_platform
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### 8.3 Déploiement Local avec Docker

```bash
# Build images
docker-compose build

# Start services
docker-compose up

# Services disponibles:
# - Frontend: http://localhost
# - Backend: http://localhost:5050
# - RAG: http://localhost:8000
# - PostgreSQL: localhost:5432

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

### 8.4 Déploiement Production (Cloud)

**Exemple avec Heroku + PostgreSQL + OpenAI:**

```bash
# 1. Install Heroku CLI
# 2. Login
heroku login

# 3. Create app
heroku create esg-platform-prod

# 4. Add PostgreSQL addon
heroku addons:create heroku-postgresql:standard-0 --app esg-platform-prod

# 5. Set environment variables
heroku config:set JWT_SECRET_KEY=<secret> --app esg-platform-prod
heroku config:set OPENAI_API_KEY=<key> --app esg-platform-prod
heroku config:set DATABASE_URL=postgres://... --app esg-platform-prod

# 6. Deploy
git push heroku main

# 7. View logs
heroku logs -f --app esg-platform-prod
```

**Alternative: AWS + RDS + S3:**
- ECS Fargate pour services (frontend, backend, RAG)
- RDS PostgreSQL pour DB
- S3 pour FAISS index backup
- CloudFront CDN pour frontend

---

## 9. API Reference

### 9.1 Authentication APIs

**POST /api/auth/register**
```
Request:
{
  "name": "John Doe",
  "email": "john@company.com",
  "password": "SecurePass123!",
  "role": "user"
}

Response (201):
{
  "access_token": "eyJ0eXAiOiJKV1QiLC...",
  "user": {
    "id": 1,
    "name": "John Doe",
    "email": "john@company.com",
    "role": "user"
  }
}

Errors:
- 400: Missing fields
- 409: Email exists
```

**POST /api/auth/login**
```
Request:
{
  "email": "john@company.com",
  "password": "SecurePass123!"
}

Response (200):
{
  "access_token": "eyJ0eXAi...",
  "user": { ... }
}

Errors:
- 400: Missing credentials
- 401: Invalid credentials
```

**GET /api/auth/me**
```
Request:
Headers: {Authorization: "Bearer <token>"}

Response (200):
{
  "user": { ... }
}

Errors:
- 401: Invalid/missing token
```

**POST /api/auth/forgot-password**
```
Request:
{
  "email": "john@company.com"
}

Response (200):
{
  "message": "Reset email sent",
  "reset_token": "abc123..." (if SMTP disabled)
}
```

**POST /api/auth/reset-password**
```
Request:
{
  "token": "abc123...",
  "new_password": "NewPass456!"
}

Response (200):
{
  "message": "Password reset successfully"
}

Errors:
- 400: Invalid/expired token
```

### 9.2 Prediction API

**POST /api/predict**
```
Request:
{
  "primary_industry": "Technology",
  "log_market_cap": 20.5,
  "co2_emissions": 150000,
  "revenue": 5000000,
  ... (15 more fields)
}

Response (200):
{
  "score": 92.34
}

Errors:
- 400: Invalid input
- 500: Model error
```

### 9.3 Integration (RAG) API

**POST /api/v1/integration**
```
Request:
{
  "message": "Provide ESG recommendations",
  "signals": {
    "esg_score": 85,
    "risk_level": "medium",
    "focus_area": "Environmental"
  },
  "top_k": 5,
  "include_recommendations": true
}

Response (200):
{
  "request": {
    "question": "...",
    "top_k": 5
  },
  "response": {
    "answer": "...",
    "recommendations": [...],
    "sources": [...]
  },
  "meta": {
    "service": "RAG",
    "version": "1.0"
  }
}

Errors:
- 400: Bad payload
- 502: RAG unavailable (no fallback)
```

### 9.4 Health Check

**GET /api/health**
```
Response (200):
{
  "status": "ok"
}
```

---

## 10. Troubleshooting

### 10.1 Backend ne démarre pas

**Erreur: `ModuleNotFoundError: No module named 'catboost'`**

Cause: CatBoost non installé
```bash
# Fix:
pip install catboost
# Ou:
pip install -r backend/requirements.txt
```

**Erreur: `DatabaseURL not set`**

Cause: .env manquant
```bash
# Fix: Crée .env à la racine
DATABASE_URL=sqlite:///esg_pfe.db
JWT_SECRET_KEY=dev-key
```

### 10.2 Frontend ne charge pas les données

**Erreur: `GET /api/predict 404`**

Cause: Backend pas running
```bash
# Fix: Démarre backend
npm run dev:full
# Vérifie: http://127.0.0.1:5050/api/health → {"status": "ok"}
```

**Erreur: `CORS error`**

Cause: Vite proxy pas configuré
```bash
# Fix: Vérifie vite.config.ts
server: {
  proxy: {
    '/api': {
      target: 'http://127.0.0.1:5050',
      changeOrigin: true
    }
  }
}
```

### 10.3 Authentification échoue

**Erreur: `401 UNAUTHORIZED` sur login**

Cause: Mauvais email/password
```bash
# Fix: Vérifie les identifiants du compte de test que tu as créé localement
```

**Erreur: `422 UNPROCESSABLE ENTITY` sur /me**

Cause: Token invalide ou expiré
```bash
# Fix:
# 1. Efface localStorage
# 2. Reconnecte-toi
# 3. Devtools Network → vérifie Authorization header
```

### 10.4 Prediction retourne 400

**Erreur: `400 BAD REQUEST`**

Cause: Payload JSON invalide
```bash
# Fix: Vérifie formulaire
# - Tous les champs requis remplis?
# - Types corrects (number pour scores, etc)?

# Debug: Vérifie logs backend
# npm run dev:full → voyez:
# INFO:backend.routes.prediction:Predict request received with keys: [...]
```

### 10.5 RAG ne répond pas

**Erreur: Chatbot retourne réponse générique**

Cause: RAG service pas running
```bash
# Fix: Vérifie terminal npm run dev:full
# Doit montrer:
# * Running on http://127.0.0.1:8000

# Si absent: RAG fallback active
# Pas d'erreur, mais réponses limitées
```

### 10.6 Base de données vide

**Erreur: Login échoue (user pas trouvé)**

Cause: DB pas initialisée
```bash
# Fix: Redémarre backend
npm run dev:full

# Backend auto-crée:
# 1. Tables (via SQLAlchemy db.create_all())
# 2. Comptes de test selon votre workflow local

# Vérifie DB:
# sqlite3 esg_pfe.db "SELECT * FROM users;"
```

### 10.7 Logs & Debugging

**Activer debug logs:**
```python
# backend/app.py
logging.basicConfig(level=logging.DEBUG)

# Ou en .env:
FLASK_ENV=development
FLASK_DEBUG=True
```

**Inspecter requêtes:**
```bash
# Terminal 1: Démarre backend
npm run dev:full

# Terminal 2: Envoie requête
curl -X POST http://127.0.0.1:5050/api/predict \
  -H "Content-Type: application/json" \
  -d '{"primary_industry":"Technology",...}'

# Vois les logs de prediction dans Terminal 1
```

---

## Appendix A: Configuration Environment (.env) Complète

```bash
# ===== DATABASE CONFIGURATION =====
DATABASE_URL=sqlite:///esg_pfe.db
# Production: DATABASE_URL=postgresql://user:pass@host:5432/db_name

# ===== AUTHENTICATION =====
JWT_SECRET_KEY=change-this-in-production-12345

# ===== RAG SYSTEM =====
RAG_API_BASE_URL=http://127.0.0.1:8000
RAG_INTEGRATION_PATH=/api/v1/integration
RAG_TIMEOUT_SECONDS=90
RAG_TOP_K=5
RAG_ALLOW_LOCAL_FALLBACK=true
OPENAI_API_KEY=sk-...

# ===== EXTERNAL SERVICES =====
NEWS_API_KEY=your-api-key

# ===== EMAIL (Password Reset) =====
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
EMAIL_FROM=no-reply@esg-platform.local
EMAIL_RESET_LINK_BASE_URL=http://localhost:5173/reset-password

```

---

## Appendix B: Commandes Utiles

```bash
# Frontend
npm install              # Install dependencies
npm run dev             # Start Vite dev server
npm run build           # Build for production
npm run preview         # Preview production build

# Backend
pip install -r backend/requirements.txt  # Install deps
flask db init           # Init migrations (if using alembic)
flask db upgrade        # Apply migrations
flask seed-users        # Seed test users

# Development (Combined)
npm run dev:full        # Start Vite + Backend + RAG

# Docker
docker-compose build    # Build images
docker-compose up       # Start containers
docker-compose down     # Stop containers

# Database (SQLite)
sqlite3 esg_pfe.db      # Open DB shell
.tables                 # List tables
SELECT * FROM users;    # Query users

# RAG
python -m RAG_SYSTEM.app              # Start RAG directly
# Accès: http://127.0.0.1:8000

# Testing
curl -X POST http://127.0.0.1:5050/api/predict \
  -H "Content-Type: application/json" \
  -d '{...}'

pytest backend/tests/          # Run backend tests (if exists)
```

---

## Appendix C: Tech Stack Versions

```
Frontend:
- React: 18.3.1
- TypeScript: 5.3.3
- Vite: 6.3.5
- Tailwind CSS: 4.1.12
- Radix UI: 1.x
- Recharts: 2.10.x

Backend:
- Python: 3.11+
- Flask: 3.1.3
- SQLAlchemy: 2.0.49
- CatBoost: 1.2.10
- scikit-learn: 1.4.1
- flask-jwt-extended: 4.5.3
- flask-bcrypt: 1.0.1

RAG:
- FAISS: 1.8.x
- sentence-transformers: 2.2.x
- OpenAI: 1.x
- Flask: 3.1.3

Database:
- SQLite: 3.x (dev)
- PostgreSQL: 15+ (prod)

DevOps:
- Docker: 24+
- Docker Compose: 2.x
- Node.js: 18+
- npm: 9+
```

---

## Conclusion

Cette plateforme ESG offre une **solution complète** pour:
✅ Prédire scores ESG via ML (CatBoost)
✅ Recommander actions d'amélioration (RAG)
✅ Analyser tendances (Analytics)
✅ Assister utilisateurs (Chatbot)
✅ Gérer authentification (JWT + PostgreSQL)

**Prête pour:** MVP, prototypage, déploiement production avec Docker.

---

**Questions?** Consultez les sections troubleshooting ou contactez l'équipe dev.

---

**Dernière mise à jour:** May 4, 2026  
**Auteur:** ESG Platform Dev Team  
**License:** MIT
