# Aiko 2.0 - Adaptive Intelligent Knowledge Orchestrator ✨

## Overview

Aiko is a lightweight, modular Retrieval-Augmented Generation (RAG) framework designed to create personalized AI chat assistants. It is optimized to run efficiently on low-end hardware, such as the Raspberry Pi 5, while leveraging external APIs (e.g., OpenAI, Gemini) or small local models.

With support for custom knowledge bases, embedding based text retrieval, web search, and user-specific memory, Aiko provides a robust yet accessible AI assistant experience. Future plans include API and Discord integrations.

## 🌟 Features

- **Personalized AI Assistants** – Custom memory for each user and AI character.
- **Efficient RAG Pipelines** – Optimized for resource-constrained hardware.
- **Hybrid Retrieval** – Use NanoVectorDB for local, vector-based retrieval and web search for external data.
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

- **Python 3.12** (Recommended: Create a virtual environment)
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
Notes 
- You may need to install [PyTorch](https://pytorch.org/get-started/locally/) manually before installing requirements.txt.
- To enable certain hardware acceleration backends for llama-cpp, follow instruction from [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) and [llama-cpp](https://github.com/ggerganov/llama.cpp/blob/master/docs/build.md)


## Key Goals
- **Realistic conversations** via web or chat applications
- **API integration** for external services (e.g., OpenAI, Gemini)
- **Local models** for independent operation
- **Hybrid retrieval** for local and web-based information
  - **Embedding-based retrieval** for local data in vector databases
  - **Web search** for external data
  - **NER** for named entity recognition in graph databases
    - NER for initial message
    - NER for retrieved information to expand retrieval
- **Custom knowledge bases** for user-specific data
- **Function/Tool integration** for math, mood, etc.
- **Distinct personality** per AI assistant
  - **System Instruction Based** e.g. "You are a..."
  - **Personality Embedding** 
- **Persistent memory** for both:
  - **Users** (Aiko remembers past interactions)
  - **Characters** (Each AI has its own unique memory)
- **Seamless switching** between AI personas and conversations
- **Discord bot** integration
- **Web version** (aiko.lol)
- **Real Time Character Simulation** (RTCS) for AI characters
  - **Mood** (happy, sad, angry, etc.)
  - **Relationships** (with users and other characters)
  - **Memory** (long-term and short-term)
  - **Activities** (e.g., reading, watching, playing)
- **Audio Input/Output** for voice-based interactions
- **Real Time Visual Input** for thinking/commentating on images/videos

## Progress
- [x] create basic api to reply to messages
- [x] integrate api into discord
- [x] use openai (or other) api for replies (no finetuning)
- [x] use local LLM for replies
- [ ] finetune openai model
- [ ] integrate web ui
- [x] integrate RAG
- [x] memory system
- [ ] finetune local model
- [ ] full character creation using config files
- [ ] logging for all relevant components to improve future quality

## Some Ideas
- GUI with Qt
- Desktop companion
- android app
- GUI RAG pipeline builder
- complex interactions between characters / characters acting without being prompted first (simulation/game)
- character creation tool
- game with npc's that can be interacted with

## Components

### Pipeline
The pipeline is the core of the system. It handles the retrieval and generation of messages. It is responsible for the following:
- Accept input message
- Evaluate message based on connversation context
  - Set reply expectation (0-1)
  - generate queries for retriever
  - create memories based on new information in message
  - call functions (TODO)
    - eg. math, mood, increase/decrease relationship, etc.
- Retrieve relevant information
  - local
  - web
  - memories
- Rerank and summarize retrieved information
- Re-evaluate message based on retrieved information if necessary
- Generate reply
- Refine reply
- Return reply

### Retrieval Loop
```
1. Accept input message
2. Pre-retrieval based on raw message (embedding+NER)
3. Generate queries for retriever using pre-retrieval information
4. Retrieve information (query embedding)
4b. Expand Retrieval (retrieval embedding/NER, max depth, min relevance)
5. Rerank and summarize retrieved information
6. loop back to 3 if necessary/configured
7. Final summary in thought like format
8. Use summary to generate reply
          
```
          