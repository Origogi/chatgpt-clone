# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a ChatGPT clone project built with Python, utilizing the OpenAI Agents SDK (`openai-agents`) for creating multi-agent conversational systems with persistent memory storage.

## Architecture

### Agent System
- **Main Components**: The project uses the `openai-agents` library to build conversational agents with:
  - Multi-agent architecture with agent handoffs
  - SQLite-based conversation memory (`SQLiteSession`)
  - Function tools for extending agent capabilities
  - Graph visualization for agent interactions

### Key Patterns
- **Agent Definition**: Agents are created with `name`, `instructions`, and optional `handoffs` for routing between specialized agents
- **Session Management**: `SQLiteSession(user_id, db_file)` provides persistent conversation memory across sessions
- **Runner**: `Runner.run(agent, message, session=session)` executes agent interactions
- **Streaming**: `Runner.run_streamed()` provides real-time event streaming for agent responses

### Database
- SQLite database (`ai-memory.db`) stores conversation history
- Sessions are user-scoped with user IDs
- Session operations: `add_items()`, `pop_item()`, `clear_session()`

## Development Commands

### Environment Setup
```bash
# Activate virtual environment (already exists)
source .venv/bin/activate

# Install dependencies
uv sync

# Add new dependencies
uv add <package-name>
```

### Running Code
```bash
# Run main script
python main.py

# Run Jupyter notebooks (for agent experimentation)
jupyter notebook
# or
jupyter lab
```

### Key Notebooks
- `agent-handoff.ipynb`: Demonstrates multi-agent handoff patterns with geography and economics agents
- `dummy-agent.ipynb`: Simple agent with SQLiteSession memory demonstration

## Environment Variables
- `OPENAI_API_KEY`: Required for OpenAI API access (set in `.env` file)

## Dependencies
- `openai-agents[viz]`: Core agent framework with visualization
- `python-dotenv`: Environment variable management
- `streamlit`: (Likely for web UI, though not yet implemented in visible code)
- `graphviz`: Agent interaction graph visualization
- `ipykernel`: Jupyter notebook support

## Notes
- The project uses Python 3.13
- Package management is handled by `uv` (modern Python package manager)
- Agent configurations support both synchronous and streaming execution modes
- Memory persistence allows agents to recall previous conversation context across sessions
