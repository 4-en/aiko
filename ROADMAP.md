# Roadmap

## Core Features
- [x] Basic pipeline to generate replies
- [x] Retrieval Components
  - [x] Evaluator that extracts information and possible queries
  - [x] Retriever that retrieves information based on queries
    - [x] Local Retriever using Embeddings
    - [x] Web Retriever using APIs
  - [x] Reranker that re-ranks retrieved information
  - [x] Summarizer that summarizes retrieved information
- [x] Memory System
  - [x] Add new memories based on Evaluator output
  - [ ] Update memories based on new information
  - [x] Retrieve memories based on queries
  - [ ] Forget memories based on time or relevance
  - [ ] Check for duplicates or contradictions
- [ ] GraphDB for Memory with NER
  - [ ] Extend local retriever to use GraphDB
  - [ ] use NER to extract information from messages / documents and extend embedding based retrieval
  - [ ] Retrieval Expansion based on GraphDB
- [ ] function calling
    - [ ] math functions
    - [ ] mood functions
    - [ ] relationship functions
    - [ ] memory functions
    - [ ] custom functions (eg. for games or productivity)
      - eg: control npc, set reminders, notes, smart home, etc.
- [ ] Logging functions to improve future quality
  - [ ] Log inputs/outputs for relevant components
  - [ ] Use as training data for future models
- [ ] Visual Input for thinking/commentating on images/videos
  - [ ] pass directly if multimodal model
  - [ ] use image captioning / video transcription for text based models
- [ ] Different pipelines for deep retrieval (eg. recursive, parallel, etc.)
  - [ ] Recursive pipeline for deep retrieval
    - After retrieval, re-evaluate message based on retrieved information
    - Generate new queries based on re-evaluation
    - Retrieve new information
    - Continue until a certain depth or relevance is reached
  - [ ] Parallel pipeline for multiple retrievals
    - Split into multiple sub-tasks to simplify problem
    - Research each sub-task in parallel
    - Combine results for final summary

## Integration
- [x] Discord Integration
- [ ] General API
  - simple REST API
- [ ] Web UI
  - compatible with API
- [ ] Local GUI
  - Qt based GUI to interact with the system
- [ ] Android App
  - similar to web UI, connect to API

## AI Models
- [x] OpenAI API
- [x] Support for other APIs
- [x] Local LLM
- [ ] Finetune OpenAI Model
  - less robotic responses, try to include personality in system messages during training
- [ ] Finetune Local Model
  - explore different methods of including personality
    - via system messages
    - LoRA for each character
    - embedding injection (hypernetworks?)

## Character Features
- [x] Distinct Personality
  - interests, likes, dislikes, background, etc.
- [x] Persistent Memory
  - long-term and short-term memory
  - [x] long-term memory in form of database with embeddings and NER
  - [ ] short-term memory in form of chain-of-thought in message context
- [ ] Multi-Character Support
  - config files for characters and parameter in pipeline
- [ ] Deep Personality System
  - attributes, traits, etc.
  - integrate with memory system and personality embedding
- [ ] Personality Embedding
  - train a model to generate personality embeddings based on some source, eg. chat history of a person
  - use these embeddings to generate responses similar to the source
  - use these embeddings to generate personalities for characters by combining or modifying them
- [ ] Intrinsic Drive System / Real Time Activities
  - [ ] Activities (reading, watching, playing, etc.)
  - [ ] Goals (short-term and long-term)
  - [ ] Interests (topics, hobbies, etc.)
  - [ ] Engagement (how much the character is interested in the conversation/activity)
  - [ ] Personality and Mood weighting for activities
    - Categories: Novelty and Learning, Story and Emotion, Relaxation and Passive Enjoyment, Challenge and Skill Growth, Social and Shared Experience, Humor and Fun
  - [ ] Relationships (with users and other characters)
  - [ ] Memory (long-term and short-term)
- [ ] Mood and Relationship System

## Extras
- [ ] Obsidian Integration
  - use Obsidian as a knowledge base for RAG
  - "talk" to your notes
- [ ] GUI RAG Pipeline Builder
  - drag and drop interface to build custom pipelines
- [ ] Game with NPC's
  - create a demo game with characters that can be interacted with
  - maybe simple 3d environment or visual novel style
- [ ] Audio Input/Output
  - modules for voice-based interactions, especially real-time
  - [ ] Audio Input
  - [ ] Speech Generation, with different voices
- [ ] Real Time Visual Input (like watching a video together)
  - chain of thought and commentary on images/videos
  - maybe process in chunks and generate responses
- [ ] Facial/Body tracking marker generation based on output/state
  - generate markers for facial expressions and body language that can be used with compatible software
  - could be used for 3d characters or avatars, or live2d models
- [ ] Character generation based on user data (Twitter profile, chat history, etc.)
  - "clone" a character based on a user's data
  - could be used for personal assistants or chatbots
  - clone yourself if you're too lazy to chat with people :D
  - use llm to fill out questionaire based on user data and use that to generate a character
  - possible sources: Twitter, Facebook, Reddit, Discord, etc.
- [ ] Desktop Companion
  - 2d/3d character
  - can be interacted with via voice or text
  - can be used for various tasks like reminders, notes, etc. using function calling
- simple Dockerfile for easy deployment

## Documentation
- [ ] Full Documentation
- [ ] Examples
- [ ] Tutorials
- [ ] API Documentation

