# Njere AI Study Companion

**Njere** means *Wisdom* in Shona. The name feels right because the whole point of this app is to take a wall of academic text and turn it into something you can actually learn from.

Upload a PDF or a text file, and Njere reads it, breaks it into chunks, embeds each chunk with Google Gemini, stores everything in Pinecone, then streams a structured summary back to you — key takeaways, topic flow, review questions and all. It's built to feel fast and to stay out of your way.

---

## What it does right now

- **Smart summarization**
- **Persistent library** 
- **Re-summarize anytime** 
- **Note detail view**

## What's being built

- **Flashcards** *(35% done)* 
- **Performance tracking**

---

## Tech stack

| Layer | What we use |
|---|---|
| Backend | Python + Flask |
| AI — generation | Google Gemini 2.5 Flash |
| AI — embeddings | Gemini Embedding (`gemini-embedding-001`, 768-dim) |
| Vector store | Pinecone (serverless, AWS) |
| PDF parsing | PyMuPDF |
| Streaming | Server-Sent Events (SSE) |
| Frontend | React 18 + Vite 5 + Tailwind CSS 3 |
| Fonts | Playfair Display · Plus Jakarta Sans · IBM Plex Mono |

---

## Project structure

```
njere/
├── backend/
│   ├── main.py                   # Flask app and all API routes
│   ├── config/
│   │   └── settings.py           # Env config (Gemini + Pinecone)
│   ├── models/
│   │   └── study_note.py         # Pydantic response schema
│   ├── services/
│   │   ├── study_note_service.py # Core pipeline: chunk → embed → store → summarize
│   │   └── pinecone_store.py     # Pinecone read/write/delete
│   ├── templates/
│   │   └── index.html            # Fallback HTML UI (served by Flask)
│   ├── data/
│   │   └── uploads_tmp/          # Temp storage for uploaded files
│   └── requirements.txt
│
├── frontend/                     # React app (the main UI)
│   ├── src/
│   │   ├── App.jsx               # Root layout + page routing
│   │   ├── api/studyNotes.js     # All API calls to the backend
│   │   ├── utils/
│   │   │   ├── sse.js            # SSE stream reader
│   │   │   └── markdown.js       # Markdown normalizer + HTML renderer
│   │   └── components/
│   │       ├── Nav.jsx
│   │       ├── UploadZone.jsx
│   │       ├── SummaryPanel.jsx
│   │       ├── Library.jsx
│   │       ├── NoteCard.jsx
│   │       ├── NoteDetailModal.jsx
│   │       ├── StatusBar.jsx
│   │       └── FlashcardsWIP.jsx
│   ├── package.json
│   └── vite.config.js            # Proxies /api/* → Flask on :8000
│
├── .env                          # Your secrets (never commit this)
├── .env.example                  # Template — copy this to .env to get started
└── README.md
```

---

## Getting started

### 1. Clone and configure

```bash
git clone https://github.com/your-username/njere.git
cd njere
cp .env.example .env
```

Open `.env` and fill in your keys:

```env
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
PINECONE_API_KEY=your_key_here
PINECONE_INDEX_NAME=sprintstudy-main
PINECONE_NAMESPACE=default
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1
EMBEDDING_DIMENSION=768
```

### 2. Run the backend

```bash
pip install -r backend/requirements.txt
python backend/main.py
# → running on http://localhost:8000
```

### 3. Run the frontend

```bash
cd frontend
npm install
npm run dev
# → running on http://localhost:3000
```

The Vite dev server automatically proxies all `/api/*` requests to the Flask backend, so you don't need to touch CORS or configure anything.

---

## API reference

| Method | Endpoint | What it does |
|---|---|---|
| `POST` | `/api/study-notes/summarize-stream` | Upload a file, get a streaming SSE summary |
| `GET` | `/api/study-notes` | List all stored notes |
| `GET` | `/api/study-notes/:id` | Get chunks + embedding preview for one note |
| `POST` | `/api/study-notes/:id/resummarize-stream` | Re-summarize from stored Pinecone chunks |
| `DELETE` | `/api/study-notes/:id` | Delete note — removes Pinecone vectors + local file |

Streaming endpoints emit `event: status`, `event: meta`, `event: token`, and `event: done` SSE events. The frontend consumes these to render the summary progressively as it arrives.

---

## A note on the Pinecone index

If you already have a Pinecone index under the same name with a different dimension (e.g. 1024 from a previous project), the app will detect the mismatch on startup, delete the old index, and recreate it at 768 dimensions. You'll lose whatever was in it, but since the dimension would've been incompatible anyway, there's nothing to save.

---

## License

MIT
