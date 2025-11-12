# Easy Local Chat LLM

🤖 **Local Chat System with AI Assistant**

[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.9+-green.svg)](https://www.python.org/)
[![Ollama](https://img.shields.io/badge/ollama-required-orange.svg)](https://ollama.ai/)

Real-time chat system with WebSocket communication and local LLM bot powered by Ollama (Gemma3). Ideal for research purposes with built-in data export and experiment management features.

[日本語 README](README.ja.md)

> This project is based on [easy-local-chat](https://github.com/yamanori99/easy-local-chat)

## ✨ Features

- **Real-time Chat**: Low-latency WebSocket communication
- **AI Bot**: Local LLM (e.g., Gemma3) with conversation history
- **Experiment Management**: Multiple conditions, random assignment
- **Data Management**: Auto-save sessions/messages, JSON/CSV export
- **Admin Panel**: Data visualization, real-time statistics, session monitoring

## Requirements

- **Python 3.9+**
- **Ollama** (for LLM bot)
- Modern web browser

> ⚠️ Virtual environment recommended for macOS/Linux

## 🚀 Quick Start

### 1. Setup Ollama

**Install:**

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows: Download from https://ollama.ai/
```

**Start service and download model:**

```bash
# Start service
ollama serve &

# Download model (default: gemma3:4b)
ollama pull gemma3:4b
```

**Available models:**

| Model | Size | Memory | Notes |
|-------|------|--------|-------|
| `gemma3:1b` | 815MB | 4GB | Lightweight & fast |
| `gemma3:4b` | 3.3GB | 8GB | Balanced (recommended) |
| `gemma3:12b` | 8.1GB | 16GB | High performance |

### 2. Setup Project

```bash
# Clone repository
git clone https://github.com/yamanori99/easy-local-chat.git
cd easy-local-chat

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# .\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Start Server

```bash
# Using startup script (recommended)
./deployment/start_server_dev.sh

# Or direct start
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Admin credentials will be set on first startup.

### 4. Access

**Local (same computer):**
- Admin: `http://localhost:8000/admin`
- Participant login: `http://localhost:8000/login`

**Network (other devices):**
- Admin: `http://YOUR_IP:8000/admin`
- Participant login: `http://YOUR_IP:8000/login`

(IP address displayed on server startup)

## 📖 Usage

### Basic Experiment Workflow

1. **Access admin panel** → `http://localhost:8000/admin`

2. **Create new experiment**
   - Enter experiment name, description, researcher name
   - Set max concurrent sessions if needed

3. **Create experimental conditions**
   - Click "Create New Template" in experiment detail page
   - Configure condition name, bot model, system prompt
   - Create multiple conditions (automatically added to experiment)
   - Optional: Set time limit, instructions, and survey

4. **Start experiment**
   - Click "Start Experiment" button

5. **Share participant URL**
   - Send login URL (`http://YOUR_IP:8000/login`) to participants
   - Participants are automatically assigned to random conditions

6. **Collect data**
   - View real-time statistics in admin panel
   - Download JSON/CSV using "Export" button
   - Survey responses are automatically saved

## 📊 Data Structure

Readable directory names are created for each experiment:

```
data/
└── user_study_2024/         # Auto-generated from experiment name
    ├── experiments/         # Experiment configuration
    ├── conditions/          # Experimental conditions
    ├── sessions/            # Session information
    ├── messages/            # Message data
    └── exports/             # Exported data
```

**Important behavior:**
- Active experiment directories are automatically reused
- Settings and data persist after server restart
- Bot messages are recorded as `message_type: "bot"`

## 📝 Survey Feature

Display surveys to participants at the end of the experiment. Perfect for measuring psychological scales.

### Supported Question Types

1. **Likert Scale** (`likert`)
   - Example: "Strongly disagree (1) ~ Strongly agree (7)"
   - Settings: `scale_min`, `scale_max`, `scale_min_label`, `scale_max_label`

2. **Free Text** (`text`)
   - Example: "Please share your thoughts about the experiment"
   - Settings: `max_length` (maximum characters)

3. **Single Choice** (`single_choice`)
   - Example: "Select your gender"
   - Settings: `choices` (list of options)

4. **Multiple Choice** (`multiple_choice`)
   - Example: "Select all that apply"
   - Settings: `choices` (list of options)

### Example Survey Configuration (JSON)

```json
{
  "survey_title": "Post-Experiment Survey",
  "survey_description": "Thank you for participating. Please answer the following questions.",
  "survey_questions": [
    {
      "question_id": "q1",
      "question_text": "Was the AI's response natural?",
      "question_type": "likert",
      "scale_min": 1,
      "scale_max": 7,
      "scale_min_label": "Not natural at all",
      "scale_max_label": "Very natural",
      "required": true
    },
    {
      "question_id": "q2",
      "question_text": "Please share your thoughts about the experiment",
      "question_type": "text",
      "max_length": 500,
      "required": false
    }
  ]
}
```

### Exporting Survey Data

- **Per Session**: `/api/sessions/{session_id}/export/survey?format=csv`
- **Entire Experiment**: `/api/experiments/{experiment_id}/export/survey?format=csv`

Survey responses are automatically saved per participant and can be exported in CSV/JSON format.

## ⚙️ Customization

### Change Bot Model

Specify when creating experimental conditions, or edit `src/main.py`:

```python
bot_manager = BotManager(model="gemma3:4b", bot_client_id="bot")
```

### Change Admin Account

```bash
# Delete credentials file and restart
rm data/admin_credentials.json
./deployment/start_server_dev.sh
```

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| Bot not responding | Check Ollama: `ps aux \| grep ollama`<br>Check models: `ollama list` |
| Slow response | Use lighter model (`gemma3:1b`)<br>Recommended: 8GB+ RAM |
| Connection error | Check port 8000 usage |
| Model download fails | Restart Ollama: `killall ollama && ollama serve &` |

## 🛠️ Tech Stack

- **Backend**: FastAPI, WebSocket, Ollama
- **Frontend**: HTML5, CSS3, JavaScript
- **LLM**: Gemma3 (Google)

## 📖 Documentation

- [CHANGELOG.md](CHANGELOG.md) - Version history
- [deployment/README.md](deployment/README.md) - Deployment guide
- API: `http://localhost:8000/docs` (after startup)

## 🔗 Links

- [Ollama Official Site](https://ollama.ai/)
- [Original Project](https://github.com/yamanori99/easy-local-chat)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## License

MIT License
