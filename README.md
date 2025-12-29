# Voice-Activated Multi-Agent System

## Overview

This project implements a stateful voice assistant capable of cyclical reasoning and RAG (Retrieval-Augmented Generation). Unlike traditional linear chatbots, this agent uses **LangGraph** to self-correct and manage complex conversational states.

## Architecture

- **Orchestration:** LangGraph (Stateful Multi-Agent Workflow)
- **Inference:** Groq LPU (Llama-3-8b) for <800ms latency
- **Memory:** Pinecone Vector Database (RAG Pipeline)
- **Voice I/O:** OpenAI Whisper (STT) & gTTS (TTS)

## Current Status: v1.0 (In Development)

- [x] System Architecture Design
- [x] Environment Setup & API Security
- [ ] Groq API Integration
- [ ] LangGraph Cyclic Loop Implementation
- [ ] Pinecone Knowledge Base Ingestion

_Active development is happening on the `dev` branch._
