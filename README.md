# Njere / SprintStudy

A study-note companion app for PDF/TXT uploads.
It chunks documents, embeds and stores chunks in Pinecone, and generates structured summaries via streaming.

## Features

- Upload `.pdf` / `.txt`
- Streaming summary output
- Library of notes
- Re-summarize from stored chunks
- Open previously saved summary
- Rename note filename
- View stored chunks and embedding preview
- Delete note (Pinecone + local file)
- Selectable models in UI
  - Embedding model: Gemini (default) or BAAI/bge-small-zh
  - Summary model: Gemini 2.5 Flash (default) or openai/gpt-oss-120b

## Tech Stack

- Backend: Flask
- Frontend: React + Vite + Tailwind
- Embedding/Summary: Gemini, Together-compatible model option
- Vector DB: Pinecone
- PDF parsing: PyMuPDF
- Streaming: SSE

## Quick Start

### 0) Install prerequisites (Python + Node.js)

You need both:

- Python 3.10+
- Node.js 20+ (includes `npm`)

Check first:

```bash
python --version
node --version
npm --version
```

If `npm`/`node` is missing, install Node.js from https://nodejs.org/  
or install with command line:

macOS (Homebrew):

```bash
brew install node@20
```

Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y nodejs npm
```

Windows (winget):

```powershell
winget install OpenJS.NodeJS.LTS
```

If you use conda, this is an optional alternative:

```bash
conda install -c conda-forge nodejs=20 -y
```

### 1) Prepare environment file

```bash
cp .env.example .env
```

PowerShell alternative:

```powershell
Copy-Item .env.example .env
```

### 2) Fill required keys in `.env`

Required for default flow:

- `GEMINI_API_KEY`
- `PINECONE_API_KEY`

Optional only when you choose those models in UI:

- `TOGETHER_API_KEY` for `openai/gpt-oss-120b`
- `HUGGINGFACE_API_KEY` for `BAAI/bge-small-zh`

### 3) Install backend deps and run backend

```bash
pip install -r backend/requirements.txt
python backend/main.py
```

Backend runs on `http://localhost:8000`.

### 4) Install frontend deps and run frontend (new terminal)

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:3000`.

### 5) Verify services

- Backend health: `http://localhost:8000/health`
- Frontend page opens and can upload files

## Quick Start (Conda, Optional)

```bash
conda activate <your_env>
pip install -r backend/requirements.txt
python backend/main.py
```

New terminal:

```bash
conda activate <your_env>
cd frontend
npm install
npm run dev
```

## API Overview

- `POST /api/study-notes/summarize-stream`
- `GET /api/study-notes`
- `GET /api/study-notes/<note_id>`
- `POST /api/study-notes/<note_id>/resummarize-stream`
- `PATCH /api/study-notes/<note_id>` (rename)
- `DELETE /api/study-notes/<note_id>`

## Common Setup Issues

### `npm` not recognized

Follow **Quick Start -> Step 0** to install Node.js, then reopen terminal and verify:

```bash
node --version
npm --version
```

If you use conda, this is an optional alternative:

```bash
conda install -c conda-forge nodejs=20 -y
```

### Pinecone dimension mismatch

Make sure `.env` model and `EMBEDDING_DIMENSION` match:

- Gemini embedding: usually `768`
- `BAAI/bge-small-zh`: usually `512`

If mismatch exists, app may recreate index (old vectors lost).

### No saved summary shown

Use `Open Summary` button in Library card.
Saved summary appears after summarize/re-summarize completes.

## Project Structure

See [`folder structure.txt`](./folder%20structure.txt) for a concise tree and startup checklist.

## License

MIT
