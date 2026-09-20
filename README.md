# 🎙️ Roxstar AI Voice Room Assistant

A real-time AI voice room assistant built using **LiveKit Agents, Gemini Realtime AI, Python, FastAPI, and Vite**.  
Supports natural conversations in **Hindi, Hinglish, and English** with two AI personas:

- 👨 **Roxstar AI Dost** — **friendly, casual male assistant**  
- 👩 **Roxstar AI Sathi** — **warm, cheerful female assistant**  

---

## 📌 Overview

Roxstar AI Voice Room enables **multi-user, real-time voice interaction** with AI participants.  
It integrates **LiveKit** for communication and **Gemini Realtime AI** for conversational intelligence.

### ✨ Features
- **Real-time voice conversations** with natural turn-taking  
- **Multi-language support** (Hindi, Hinglish, English)  
- **Two distinct AI personas** with handoff capability  
- **Conversational context retention**  
- **Multi-user room participation**  
- **Error handling, logging, and diagnostics**  

---

## 🧠 Architecture

```text
Frontend (Vite/JS)
       ↓
FastAPI Token Server
       ↓
LiveKit Room (WebRTC)
       ↓
LiveKit Agent (Dost / Sathi)
       ↓
Gemini Realtime AI
       ↓
AI Voice Reply

🛠️ Technology Stack
 
Component	                        Technology
Real-time communication	            LiveKit
AI Agent Framework	                LiveKit Agents
AI Model	                        Gemini Realtime
Backend	                            Python + FastAPI
Frontend	                        Vite + JavaScript
Config	                            python-dotenv
SSL Certificates	                Certifi
Testing/Diagnostics	                Python / pytest


📁 Project Structure

roxstar-ai-voice-room/
│
├── backend/
│   ├── main.py
│   ├── agent.py
│   ├── agent_sathi.py
│   ├── diagnose_dispatch.py
│   └── venv/
│
├── frontend/
│   ├── index.html
│   ├── app.js
│   ├── style.css
│   └── ...
│
├── docs/
│
├── .env
├── .gitignore
└── README.md

⚙️ Installation

Prerequisites

Python 3.x
Node.js + npm
LiveKit Cloud account
Google Gemini API access

Backend Setup

bash
cd backend
python -m venv venv
source venv/bin/activate   # (Linux/Mac)
.\venv\Scripts\activate    # (Windows)
pip install -r requirements.txt


Environment Configuration
Create .env in project root:

Bash
LIVEKIT_URL=your_livekit_url
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
GOOGLE_API_KEY=your_google_api_key
⚠️ Do not commit .env to GitHub.

▶️ Running the Application
Start FastAPI server

bash
cd backend
python main.py
Runs at: http://127.0.0.1:8000

Start LiveKit Agent

bash
cd backend
python agent.py dev
Start Frontend

bash
cd frontend
npm install
npm run dev
Open the Vite dev URL in your browser.

🧑‍💻 Example Conversations
Hindi / Hinglish

Code
User: Yaar aaj kaafi tired feel ho raha hai.
Dost: Haan, lagta hai aaj kaafi hectic day tha. Thoda break lena bhi important hai.
English

Code
User: What is machine learning?
Dost: Machine learning is a way of teaching computers to learn patterns from data.


🔐 Security
Secrets stored in .env
.gitignore excludes sensitive files
API credentials never exposed in logs

📊 Logging & Diagnostics
Backend logs key events: [ROOM] DOST JOINED, [HANDOFF] Dost -> Sathi
Diagnostic script: diagnose_dispatch.py to trace agent dispatch lifecycle
