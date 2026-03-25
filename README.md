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
├── **backend/** # FastAPI Application (Python)
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
* **Retrieval:** Vector databases for efficient Information Retrieval (RAG).
* **Optimization:** Model quantization for efficient deployment.

## 📦 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/sjohannes/njere.git](https://github.com/sjohannes/njere.git)
   cd njere


   
