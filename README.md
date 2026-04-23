# SkillMap

<div align="center">

**AI-powered resume intelligence platform — clusters candidates by real skill signals and provides ATS resume optimization.**

[![React](https://img.shields.io/badge/Frontend-React%2018-61DAFB?style=for-the-badge&logo=react&logoColor=06111f)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Build-Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev/)
[![Flask](https://img.shields.io/badge/Backend-Flask-FFFFFF?style=for-the-badge&logo=flask&logoColor=000000)](https://flask.palletsprojects.com/)
[![Python](https://img.shields.io/badge/ML-Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)

</div>

SkillMap turns a resume folder into a searchable talent map. Upload resumes, cluster them by skill embeddings, and optimize individual resumes for ATS compatibility — all from a single dashboard.

## Features

- **Skill Clustering** — Groups resumes into clusters using SentenceTransformer embeddings + KMeans.
- **Single Resume Analysis** — Predicts best-fit cluster with confidence scoring.
- **Bulk Screening** — Batch analysis for up to 50 resumes with CSV export.
- **Insights Dashboard** — Skill distributions, cluster analytics, and top-skill charts.
- **ATS Resume Editor** — Upload a resume, get an instant ATS compatibility score (0–100), domain detection, and actionable improvement suggestions. Edit inline with a split-view A4 preview.

## Architecture

```mermaid
flowchart LR
    A[Resume PDF / DOCX / Text] --> B[Flask API]
    B --> C[Text cleanup + spaCy NER skill extraction]
    C --> D[SentenceTransformer embeddings]
    D --> E[KMeans clustering]
    E --> F[Cluster labels + confidence + analytics]
    F --> G[React dashboard]
    G --> H[Dashboard · Analyze · Bulk Upload · Insights · ATS Editor]
```

## Screens

| Screen | Description |
|---|---|
| **Dashboard** | Cluster cards, top skills, high-level metrics |
| **Analyze** | Single-resume upload and cluster prediction |
| **Bulk Upload** | Batch processing with exportable results |
| **Insights** | Cluster and skill distribution charts |
| **ATS Editor** | Upload → Score → Edit → Export workflow |

## Tech Stack

### Backend
- Flask + Flask-CORS
- SentenceTransformers (BERT embeddings)
- scikit-learn (KMeans clustering)
- spaCy (NER-based skill extraction)
- pandas, NumPy, joblib
- pdfminer.six, python-docx (file parsing)

### Frontend
- React 18 + React Router
- Vite (build tool)
- Framer Motion (animations)
- Recharts (charts)
- Lucide React (icons)
- pdfjs-dist, mammoth (client-side file extraction)

### Model Artifacts
- `models/bert_model_name.pkl` — BERT model identifier
- `models/kmeans_model.pkl` — trained KMeans clustering model
- `models/cluster_names.pkl` — cluster label mapping
- `models/cluster_results.csv` — pre-computed cluster assignments

## Project Structure

```text
SkillMap/
├── backend/
│   ├── app.py              # Flask API (7 endpoints)
│   ├── ats_scorer.py        # Backend ATS scoring engine
│   ├── skills.py            # spaCy NLP skill extraction
│   ├── extractors.py        # PDF/DOCX text extraction
│   ├── train.py             # Model training script
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/           # Route pages
│   │   ├── context/         # React context providers
│   │   ├── lib/             # Scoring engine + utilities
│   │   ├── data/            # Skill databases (JSON)
│   │   └── styles/          # ATS editor tokens
│   ├── index.html
│   └── package.json
├── models/                  # Trained ML artifacts
├── Resume.csv               # Training dataset
└── README.md
```

## Local Setup

### 1. Backend

```bash
python3 -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows

pip install -r backend/requirements.txt
python3 -m spacy download en_core_web_sm
```

Start the API on port 5001:

```bash
FLASK_PORT=5001 python3 backend/app.py
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

The app runs on `http://localhost:5173`.

### 3. Environment Variables

Copy `.env.example` to `.env` and adjust as needed:

```
FLASK_PORT=5001
FLASK_DEBUG=false
NUMBA_DISABLE_JIT=1
```

## API Reference

| Method | Route | Purpose |
|---|---|---|
| POST | `/predict` | Predict cluster for one resume |
| GET | `/clusters` | All clusters and metadata |
| POST | `/bulk-predict` | Batch cluster prediction (up to 50) |
| GET | `/stats` | Analytics, totals, top skills |
| GET | `/clusters/<id>/resumes` | Paginated resumes in a cluster |
| POST | `/ats/score` | ATS compatibility scoring (NLP-powered) |
| GET | `/health` | Health check with model status |

## Training

To retrain models on new data:

```bash
python3 backend/train.py
```

This reads `Resume.csv`, generates embeddings, runs KMeans, and saves artifacts to `models/`.

## Deployment Notes

- Backend must run on port **5001** (macOS reserves 5000 for AirPlay).
- Set `NUMBA_DISABLE_JIT=1` to avoid JIT errors on newer Python versions.
- For production, use Gunicorn: `gunicorn -w 2 -b 0.0.0.0:5001 backend.app:app`
- The ATS editor works standalone (client-side scoring) if the backend is unavailable.

## Data

`Resume.csv` (54 MB) is excluded from git due to GitHub's file size limit. Download it from the original dataset source and place it in the project root before running `train.py`.
