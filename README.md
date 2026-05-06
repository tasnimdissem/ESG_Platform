# 🌿 ESG Prediction & Analysis Platform

[![Status](https://img.shields.io/badge/Status-Active-success.svg)]()
[![Stack](https://img.shields.io/badge/Stack-React%20%7C%20Flask%20%7C%20RAG-blue.svg)]()
[![PFE](https://img.shields.io/badge/Project-PFE--2026-blueviolet.svg)]()

A comprehensive, AI-powered platform for **Environmental, Social, and Governance (ESG)** scoring and analysis. This project integrates predictive modeling, real-time news tracking, and a Retrieval-Augmented Generation (RAG) system to provide actionable ESG insights.

---

## ✨ Key Features

- **📊 Interactive Dashboard**: Real-time visualization of ESG scores, risk levels, and historical trends.
- **🤖 RAG Chatbot**: Intelligent assistant capable of answering complex ESG questions using indexed corporate reports and documents.
- **🔍 Advanced Analytics**: Detailed breakdowns of Environmental, Social, and Governance metrics with interactive charts.
- **💡 Smart Recommendations**: Machine Learning-driven suggestions for improving ESG performance based on current data.
- **📰 News Integration**: Automated fetching and analysis of the latest ESG-related news and global trends.
- **🏗️ Multi-Service Architecture**: Decoupled Frontend, Backend, and RAG services for scalability and modularity.

---

## 🏗️ Architecture Overview

The platform is built using a modern 3-tier architecture:

1.  **Frontend (React/TypeScript)**: A high-performance SPA built with Vite, Tailwind CSS 4, and Radix UI.
2.  **Orchestration Backend (Flask)**: Manages authentication, data aggregation, news fetching, and integrates with the RAG service.
3.  **RAG System (Flask/LangChain)**: Handles document ingestion, vector embedding (using `all-MiniLM-L6-v2`), and intelligent querying via FAISS.

---

## 🛠️ Tech Stack

### Frontend
- **Framework**: React 18 / TypeScript
- **Build Tool**: Vite 6
- **Styling**: Tailwind CSS 4, Lucide Icons, Radix UI
- **Charts**: Recharts
- **Animations**: Motion (Framer Motion)

### Backend & AI
- **Language**: Python 3.10+
- **Framework**: Flask
- **Database**: SQLite / PostgreSQL (SQLAlchemy)
- **RAG Engine**: FAISS, LangChain
- **Embeddings**: Sentence-Transformers (`all-MiniLM-L6-v2`)
- **LLM Integration**: Groq (Llama), OpenAI (GPT-4o), or local Ollama

---

## 🚀 Getting Started

### 1. Prerequisites
- **Node.js**: v18+
- **Python**: v3.10+
- **Git**

### 2. Installation

Clone the repository and install dependencies for all modules:

```bash
# Install Frontend dependencies
npm install

# Install Backend dependencies
pip install -r backend/requirements.txt

# Install RAG System dependencies
pip install -r RAG_SYSTEM/requirements.txt
```

### 3. Configuration

Create a `.env` file in the root directory (using `.env.example` as a template):

```bash
cp .env.example .env
```

**Key Environment Variables:**
- `RAG_API_BASE_URL`: URL where the RAG service is running (default: `http://localhost:8000`)
- `GROQ_API_KEY`: Required for LLM synthesis (optional if using OpenAI or Ollama)
- `DATABASE_URL`: Your database connection string

---

## 🏃 Running the Platform

You can start the different components individually or all at once.

### Option A: Complete Full-Stack (Recommended)
This starts the Frontend, Backend, and RAG services concurrently.
```bash
npm run dev:full
```

### Option B: Individual Components
```bash
# Start Frontend (Port 5173)
npm run dev

# Start Orchestration Backend (Port 5000)
npm run dev:backend

# Start RAG Service (Port 8000)
cd RAG_SYSTEM && python app.py
```

---

## 🧠 RAG System Usage

The RAG service allows you to query your own documents:

1.  **Ingest Data**: Place your PDF or text files in `RAG_SYSTEM/data/raw/`.
2.  **Build Index**:
    ```bash
    curl -X POST http://localhost:8000/api/v1/ingest
    ```
3.  **Ask Questions**:
    ```bash
    curl -X POST http://localhost:8000/api/v1/ask \
      -H "Content-Type: application/json" \
      -d '{"question": "What is the company carbon footprint strategy?"}'
    ```

---

## 🎨 Design System

The project follows a "Premium & Modern" aesthetic:
- **Color Palette**: Sophisticated greens and deep slates for an eco-tech feel.
- **Glassmorphism**: Subtle blur effects on cards and navigation.
- **Micro-interactions**: Smooth hover states and transitions for a living UI.

---

## 📄 License & Attribution

Original design inspired by [Figma ESG Prediction Platform](https://www.figma.com/design/8mLtfTH9W7kWxCcBaJuwg9/ESG-Prediction-Platform).  
Developed as part of a **Professional Final Project (PFE)**.