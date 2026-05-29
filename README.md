# 💰 Spending Spotlight

AI-powered bank statement analyzer. Upload a PDF bank statement, pick your expected spending categories, and instantly see which transactions were expected vs unexpected.

🔗 **Live Demo:** https://spending-spotlight.vercel.app

---

## How It Works

1. **Select categories** — Choose what you normally spend on (groceries, gas, bills, etc.)
2. **Upload your statement** — Drop in a PDF bank statement (up to 15MB)
3. **Get results** — GPT-4o-mini extracts every transaction and classifies each one as Expected or Unexpected

---

## Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | React (Create React App) |
| Backend | Python, Flask |
| AI | OpenAI GPT-4o-mini |
| PDF parsing | pdfplumber |
| Hosting | Vercel (client), Render (server) |

---

## Running Locally

### Prerequisites
- Node.js
- Python 3.11+
- An OpenAI API key

### 1. Clone the repo
```bash
git clone https://github.com/inderpreet-k/spending-spotlight
cd spending-spotlight
```

### 2. Set up the server
```bash
cd server
pip install -r requirements.txt
```

Create a `.env` file in the `server/` folder:
```
OPENAI_API_KEY=sk-...
```

Start the server:
```bash
python app.py
```
Server runs at `http://localhost:5000`

### 3. Set up the client

Open a second terminal:
```bash
cd client
npm install
npm start
```
App opens at `http://localhost:3000`

> **Note:** For local testing, update the API URL in `client/src/components/FileUpload.js` from the production Render URL to `http://localhost:5000`. Remember to revert before pushing.

---

## Deployment

- **Client** → Vercel (auto-deploys from `main`) — https://spending-spotlight.vercel.app
- **Server** → Render (configured via `server/render.yaml`) — https://spending-spotlight-api.onrender.com

Make sure `OPENAI_API_KEY` is set in your Render environment variables.

---

## Project Structure

```
spending-spotlight/
├── client/                  # React frontend
│   └── src/
│       ├── components/
│       │   ├── CategorySelection.js
│       │   ├── FileUpload.js
│       │   └── Results.js
│       └── App.js
└── server/                  # Flask backend
    ├── app.py
    ├── requirements.txt
    └── render.yaml
```
