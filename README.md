# Spending Spotlight
 
AI-powered bank statement analyzer. Upload a PDF bank statement, pick your expected spending categories, and instantly see which transactions were expected vs unexpected.
 
🔗 Live Demo: https://spending-spotlight.vercel.app
 
## How It Works
1. Select categories — Choose what you normally spend on (groceries, gas, bills, etc.)
2. Upload your statement — Drop in a PDF bank statement (up to 15MB)
3. Get results — GPT-4o-mini extracts every transaction and classifies each one as Expected or Unexpected
## Security
 
Every request to the backend is screened by [Sentinel AI](https://github.com/inderpreet-k/sentinel-ai), a real-time ML-powered security API, before it's processed. Malicious input (SQL injection, XSS, etc.) is detected and blocked automatically.
 
Try it yourself on the live demo: enter `<script>alert('XSS')</script>` in the "Add Custom Category" field and continue — the request gets blocked before it reaches the analysis pipeline.
 
## Tech Stack
 
| Layer | Tech |
|---|---|
| Frontend | React (Create React App) |
| Backend | Python, Flask |
| AI | OpenAI GPT-4o-mini |
| PDF parsing | pdfplumber |
| Security | Sentinel AI (custom ML web application firewall) |
| Hosting | Vercel (client), Render (server) |
 
## Running Locally
 
### Prerequisites
- Node.js
- Python 3.11+
- An OpenAI API key
- A Sentinel AI API key (register free at [sentinel-ai-web.onrender.com](https://sentinel-ai-web.onrender.com))
### 1. Clone the repo
```
git clone https://github.com/inderpreet-k/spending-spotlight
cd spending-spotlight
```
 
### 2. Set up the server
```
cd server
pip install -r requirements.txt
```
 
Create a `.env` file in the `server/` folder:
```
OPENAI_API_KEY=sk-...
```
 
Download `sentinel.py` from [sentinel-ai/sdks/python](https://github.com/inderpreet-k/sentinel-ai/tree/main/sdks/python) and place it in the `server/` folder, next to `app.py`. Update the Sentinel API key in `app.py` with your own.
 
Start the server:
```
python app.py
```
Server runs at http://localhost:5000
 
### 3. Set up the client
Open a second terminal:
```
cd client
npm install
npm start
```
App opens at http://localhost:3000
 
Note: For local testing, update the API URL in `client/src/components/FileUpload.js` from the production Render URL to `http://localhost:5000`. Remember to revert before pushing.
 
## Deployment
- Client → Vercel (auto-deploys from main) — https://spending-spotlight.vercel.app
- Server → Render (configured via `server/render.yaml`) — https://spending-spotlight-api.onrender.com
Make sure `OPENAI_API_KEY` is set in your Render environment variables.
 
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
    ├── sentinel.py           # Sentinel AI SDK — request screening
    ├── requirements.txt
    └── render.yaml
```
 
















