# Aiko 2.0 - Adaptive Intelligent Knowledge Orchestrator ✨

## Overview

Aiko is a lightweight, modular Retrieval-Augmented Generation (RAG) framework designed to create personalized AI chat assistants. It is optimized to run efficiently on low-end hardware, such as the Raspberry Pi 5, while leveraging external APIs (e.g., OpenAI, Gemini) or small local models.

With support for custom knowledge bases, embedding based text retrieval, web search, and user-specific memory, Aiko provides a robust yet accessible AI assistant experience. Future plans include API and Discord integrations.

## 🌟 Features

- **Personalized AI Assistants** – Custom memory for each user and AI character.
- **Efficient RAG Pipelines** – Optimized for resource-constrained hardware.
- **Hybrid Retrieval** – Use NanoVectorDB for local retrieval and web search for external data.
- **API Integration** – Seamlessly connect with OpenAI, Gemini, and other services.
- **Modular Design** – Easily extend with new retrieval and generation methods.
- **Multi-Platform Support** – Designed for Raspberry Pi 5 but runs on any Linux/Windows system.
- **Discord Bot** – Bring Aiko-powered AI to Discord communities.

## 📂 Project Structure
```
aiko/
│── api/             # API for Aiko
│── client/          # Clients to for using/testing Aiko
│── config/          # Configuration files and settings
│── discord/         # Discord bot integration (planned)
│── evaluator/       # Prompt evaluator (generate queries, call functions, ...)
│── generator/       # Text generation logic (LLMs, APIs)
│── pipeline/        # Core RAG pipeline (retrieval + generation)
│── refiner/         # Post-processing and response refinement
│── retriever/       # FAISS, web search, and hybrid retrieval
│── tests/           # Unit tests and validation
│── utils/           # Helper functions and utilities
│── core/            # Core data structures (Message, Conversation, User)
│── __main__.py      # Main entry point
```
## 🚀 Installation & Setup

### Prerequisites

Before installing, ensure you have:

- **Python 3.11** (Recommended: Create a virtual environment)
- **pip** (Python package manager)
- **API Keys** (for OpenAI, Gemini, or any other external services)

### Installation

Clone the repository:
```sh
git clone https://github.com/4-en/aiko.git
cd aiko
```
Install dependencies:
```sh
pip install -r requirements.txt
```

## 🛠 Roadmap

- Implement NanoVectorDB-based local retrieval 🛠
- Web search integration 🛠
- Persistent memory for users & characters 🛠
- Discord bot integration 🛠
- API for external applications 🛠

## Key Goals
- **Realistic conversations** via web or chat applications
- **Distinct personality** per AI assistant
- **Persistent memory** for both:
  - **Users** (Aiko remembers past interactions)
  - **Characters** (Each AI has its own unique memory)
- **Seamless switching** between AI personas and conversations
- **Discord bot** integration
- **Web version** (aiko.lol)

## Improvements to 1.0
- use more complex model as a base
- use llm api (eg openai)
- later, test different local approaches and fine-tune using LoRA
- improve training data and training process
- use RAG to access long term memory
- use text to speech for audio output
- add inputs for audio/video
- run using fastapi for better integration 

## Progress
- [x] create basic api to reply to messages
- [x] integrate api into discord
- [x] use openai api for replies (no finetuning)
- [ ] finetune openai model
- [ ] integrate web ui
- [ ] integrate RAG
- [ ] memory system
- [ ] train and use local LLM
- [ ] full character creation using config files
- [ ] logging for all relevant components to improve future quality

## Unlikely
- GUI with Qt
- Desktop companion
- android app
- GUI RAG pipeline builder
- complex interactions between characters / characters acting without being prompted first (simulation/game)
