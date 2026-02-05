#  Voice-Activated Multi-Agent System (JARVIS)

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![LangGraph](https://img.shields.io/badge/LangGraph-Cyclical%20AI-orange?style=for-the-badge)
![Groq](https://img.shields.io/badge/Groq-LPU%20Inference-purple?style=for-the-badge)
![Pinecone](https://img.shields.io/badge/Pinecone-Vector%20DB-green?style=for-the-badge)

> **A real-time, hands-free AI assistant capable of cyclical reasoning, long-term memory, and "Chat with PDF" functionality.**

##  Project Overview

This project is an advanced AI agent designed to replicate the experience of J.A.R.V.I.S. It moves beyond simple "chatbot" scripts by integrating **LangGraph** for stateful multi-step reasoning and **RAG (Retrieval-Augmented Generation)** for handling custom documents.

It features a modern, GPU-accelerated GUI built with **Flet** and uses **Edge TTS** for ultra-realistic, low-latency voice output.

---

##  Key Features

- **Sub-800ms Latency:** Powered by **Groq's LPU** (Linear Processing Unit) for near-instantaneous LLM inference.
- **Real-Time Voice Pipeline:**
  - **Input:** OpenAI Whisper (Turbo) for robust speech-to-text.
  - **Output:** Microsoft Edge TTS for neural, human-like speech.
- **Cyclical Reasoning (LangGraph):** The agent "thinks" before it speaks. It can route tasks, decide to search the web, or access internal memory based on context.
- **Long-Term Memory:** Stores user facts and conversations in **Pinecone (Vector DB)**, allowing it to remember context across sessions.
- **RAG / PDF Chat:** Upload a PDF (Resume, Research Paper), and the agent instantly ingests it to answer specific questions.
- **Sci-Fi GUI:** A "Glassmorphism" interface with a breathing reactive orb animation using **Flet (Flutter for Python)**.

---

## 🛠️ Tech Stack

| Component         | Technology Used                     |
| :---------------- | :---------------------------------- |
| **Orchestration** | LangChain, LangGraph                |
| **LLM**           | Llama 3 (via Groq Cloud)            |
| **Vector DB**     | Pinecone                            |
| **Voice Input**   | SpeechRecognition, Whisper-v3-Turbo |
| **Voice Output**  | Edge TTS (Neural)                   |
| **GUI**           | Flet (Python Wrapper for Flutter)   |
| **Backend**       | Python 3.10+                        |

---

##  Installation & Setup

### 1. Clone the Repository

```bash
git clone [https://github.com/Kambammohankalyan/voice-agent-langgraph.git](https://github.com/Kambammohankalyan/voice-agent-langgraph.git)
cd voice-agent-langgraph
```

### 2. Create Virtual Environment

```bash

python -m venv venv
# Windows
.\venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash

pip install -r requirements.txt
# Ensure Flet and Audio drivers are ready
pip install flet edge-tts pygame pyaudio
```

### 4. Configure Environment Variables

Create a .env file in the root directory and add your API keys:

```bash

GROQ_API_KEY=gsk_your_groq_key_here
PINECONE_API_KEY=pcsk_your_pinecone_key_here
PINECONE_INDEX_NAME=voice-agent-memory
TAVILY_API_KEY=tvly_your_tavily_key_here
```

###  Usage

Run the main application to launch the Desktop Interface:

```bash

# Launch the Modern GUI
python gui_modern.py
Start System: Click the button to initialize the Voice Loop.

Hands-Free: Just speak. The orb turns Cyan when listening and Purple when thinking.

Commands:

"Who am I?" (Tests Memory)

"Search Google for stock prices." (Tests Tools)

"Exit." (Shuts down system)

```

###  Project Structure

```bash

voice-agent-langgraph/
├── backend/
│   ├── core.py          # LangGraph Brain & Logic
│   ├── rag_engine.py    # Pinecone Memory Handlers
├── voice/
│   ├── listener.py      # Whisper Speech-to-Text
│   ├── speaker.py       # Edge TTS Output
├── gui_modern.py        # Flet GUI (Main Entry Point)
├── requirements.txt     # Dependencies
├── .env                 # API Keys (Not uploaded)
└── README.md            # Documentation
```
