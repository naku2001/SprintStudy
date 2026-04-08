# 💡 SprintStudy: Your AI-Native Study Companion

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://njere.streamlit.app)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Njere** (Shona for *Wisdom*) is a smart study ecosystem designed to bridge the gap between raw information and deep academic understanding. Built with **Applied AI**, it goes beyond simple note-taking by leveraging NLP to provide context-aware tutoring and knowledge retention tools.

---

# Smart Study App

## Project Structure

```
**smart-study-app/**
├── **backend/** # Flask Application (Python)
│   ├── `main.py`               # App entry point & API routes
│   ├── **services/** # Gemini API integration & NLP logic
│   ├── **models/** # Pydantic schemas for data validation
│   └── `requirements.txt`
│
├── **frontend/** # React Application (Vite + Tailwind)
│   ├── **src/**
│   │   ├── **components/** # UI logic for Flashcards & Quizzes
│   │   └── **api/** # Axios/Fetch backend connectors
│   └── `package.json`
│
└── `docker-compose.yml`        # Orchestrates both services
```
## 🚀 Key Features

* **Smart Summarization:** Transform dense academic papers or lecture notes into concise, digestible insights using state-of-the-art LLMs.
* **Contextual Q&A:** An AI tutor that understands your specific course materials to answer complex questions in real-time.
* **Automated Knowledge Graphs:** Visualize connections between different topics to build a stronger mental model.
* **Flashcard Generation:** Convert notes into active-recall sets (Anki-style) automatically.
* **Optimized Performance:** Built with model optimization techniques (Quantization/Pruning) for fast inference and low-latency responses.

## 🛠️ Tech Stack

* **Frontend:** [Streamlit](https://streamlit.io/) for a clean, mobile-friendly user interface.
* **Core AI:** [PyTorch](https://pytorch.org/) & [Hugging Face Transformers](https://huggingface.co/).
* **Data Layer:** [Pinecone](https://www.pinecone.io/) as the unified vector+metadata store for notes, summaries, Q&A context, and flashcards.
* **Optimization:** Model quantization for efficient deployment.

## 📦 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/sjohannes/njere.git](https://github.com/sjohannes/njere.git)
   cd njere


   

## Study Note Summary API (Implemented)

### 1) Install backend dependencies

```bash
pip install -r backend/requirements.txt
```

### 2) Configure environment

Update `.env` with:

- `GEMINI_API_KEY`
- `GEMINI_MODEL=gemini-2.5-flash`
- `PINECONE_API_KEY`
- `PINECONE_INDEX_NAME`
- `PINECONE_NAMESPACE`
- `PINECONE_CLOUD`
- `PINECONE_REGION`
- `EMBEDDING_DIMENSION`

### 3) Run API

```bash
python backend/main.py
```

### 4) Open web UI

Open:

`http://localhost:8000/`

Then upload one `.pdf` or `.txt` and click **Summarize**.

### 5) (Optional) Call summarize endpoint directly

`POST /api/study-notes/summarize` with multipart file upload (`.pdf` or `.txt`).

For streaming markdown output (recommended):

`POST /api/study-notes/summarize-stream`

Example:

```bash
curl -X POST "http://localhost:8000/api/study-notes/summarize" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@./your_note.pdf"
```

### 6) Manage stored notes

- `GET /api/study-notes`  
  List stored notes (filename, note_id, chunk count, local file existence).
- `GET /api/study-notes/<note_id>`  
  View chunks and embedding preview for one note.
- `POST /api/study-notes/<note_id>/resummarize`  
  Re-run summary generation using stored chunks in Pinecone (no re-upload needed).
- `POST /api/study-notes/<note_id>/resummarize-stream`  
  Re-run summary generation as streaming markdown output.
- `DELETE /api/study-notes/<note_id>`  
  Delete Pinecone vectors and local uploaded file for one note.
