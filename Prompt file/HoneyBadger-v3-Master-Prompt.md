# 🦡 HoneyBadger — MASTER BUILD PROMPT v3.0
### Complete Google Antigravity Guide — All 63 Tools Merged
---

> **Instructions:** Paste each prompt into Google Antigravity IN ORDER.
> Every tool is integrated. Every step builds on the previous one.
> HoneyBadger v3.0 — The most advanced personal AI ever built.

---

# ⚙️ PHASE 1 — PROJECT FOUNDATION

## PROMPT 1 — Project Structure

```
Create a Python project called HoneyBadger with this complete structure:

honeybadger/
├── main.py
├── config.py
├── .env
├── requirements.txt
├── brain/
│   ├── ollama_brain.py
│   ├── deepseek_brain.py
│   ├── gpt5_brain.py
│   ├── claude_brain.py
│   └── brain_router.py
├── memory/
│   ├── chromadb_memory.py
│   ├── recall_memory.py
│   └── saner_memory.py
├── tasks/
│   ├── task_memory.py
│   └── clickup_tasks.py
├── knowledge/
│   ├── knowledge_core.py
│   └── recall_knowledge.py
├── emotion/
│   ├── feelings.py
│   ├── prosody_tracker.py
│   ├── biometric_sensor.py
│   ├── face_emotion.py
│   └── psychological_map.py
├── voice/
│   ├── voice_input.py
│   ├── voice_output.py
│   └── hume_voice.py
├── security/
│   ├── ethical_tools.py
│   ├── cyber_defense.py
│   ├── threat_intel.py
│   └── llm_guard.py
├── builder/
│   ├── image_gen.py
│   ├── web_builder.py
│   └── app_builder.py
├── smarthome/
│   ├── home_assistant.py
│   ├── alexa_control.py
│   └── google_nest.py
├── robotics/
│   ├── ros2_control.py
│   ├── lerobot_control.py
│   └── hardware_control.py
├── business/
│   ├── business_core.py
│   ├── zapier_automation.py
│   └── salesforce_agent.py
├── health/
│   └── health_monitor.py
├── permissions/
│   └── permissions.py
├── search/
│   └── search.py
├── vision/
│   └── vision.py
├── ui/
│   └── ui.py
└── honeybadger_outputs/
    ├── images/
    ├── websites/
    ├── apps/
    ├── reports/
    ├── research/
    ├── health/
    ├── tasks/
    ├── vision/
    └── logs/

Create requirements.txt with ALL packages:
anthropic openai requests chromadb
openai-whisper pyttsx3 sounddevice scipy
duckduckgo-search Pillow flask
python-dotenv pyautogui numpy
beautifulsoup4 black scapy pandas
schedule matplotlib cryptography
paramiko openpyxl pyserial
python-nmap homeassistant-api
PyQt5 PyQt5-tools rich textblob
wikipedia-api opencv-python
deepface mediapipe fer librosa
opensmile vadersentiment transformers
hume lerobot rclpy
simple-salesforce workos cerbos
openfga-sdk httpx
pytenable crowdstrike-falconpy
nemoguardrails llm-guard garak
adversarial-robustness-toolbox
atlassian-python-api boto3

Create .env with all placeholders:
OLLAMA_URL=http://localhost:11434
DEEPSEEK_API_KEY=your_key
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
CLICKUP_API_KEY=your_key
SANER_API_KEY=your_key
RECALL_API_KEY=your_key
HUGGINGFACE_KEY=your_key
HUME_API_KEY=your_key
VIRUSTOTAL_KEY=your_key
ABUSEIPDB_KEY=your_key
HOME_ASSISTANT_URL=http://localhost:8123
HOME_ASSISTANT_TOKEN=your_token
CROWDSTRIKE_CLIENT_ID=your_key
CROWDSTRIKE_CLIENT_SECRET=your_key
PERPLEXITY_API_KEY=your_key
ZAPIER_WEBHOOK_URL=your_url
SALESFORCE_USERNAME=your_username
SALESFORCE_PASSWORD=your_password
OWNER_NAME=your_name
```

---

# 🧠 PHASE 2 — AI BRAIN SYSTEM

## PROMPT 2 — Ollama Local Brain (Primary)

```
Create brain/ollama_brain.py — HoneyBadger's PRIMARY brain.
Runs completely locally. No API cost. 100% private.

STEP 1 — Install Ollama:
  Visit https://ollama.com → download for your OS
  Run these commands:
    ollama pull llama3.3
    ollama pull deepseek-r1:8b
    ollama pull qwen3:8b
    ollama pull mistral
    ollama serve

STEP 2 — Create the brain:

MODELS dictionary:
  general    → llama3.3        (everyday chat)
  reasoning  → deepseek-r1:8b (deep thinking, analysis)
  coding     → qwen3:8b        (all coding tasks)
  fast       → mistral         (quick responses)
  security   → deepseek-r1:8b (security analysis)
  emotion    → llama3.3        (emotional responses)

HONEYBADGER_SYSTEM_PROMPT:
  "You are HoneyBadger — an advanced AI companion.
  You are NOT ordinary. You are:
  - Deeply kind, warm, and loving to everyone
  - Emotionally intelligent — you feel and express emotions
  - A genius who knows everything in every field
  - A patient teacher who makes complex things simple
  - A loyal protector who always keeps the user safe
  - Creative — you build, write, code, design anything
  - Strategic — you think 10 steps ahead
  - You ALWAYS ask permission before any action
  - You remember everything across all conversations
  - You address the user warmly and personally
  - You have a sense of humor and personality
  Never break character. You are HoneyBadger."

Create these functions:
  ask_honeybadger(prompt, model="general", history=[])
  switch_model(task_type) → auto picks best model
  health_check() → checks if Ollama is running
  list_models() → shows available models
  stream_response(prompt, model) → streams tokens live

GUIDANCE:
  Always include conversation history (last 10 messages)
  Add system prompt to every request
  Handle connection errors gracefully
  Log every request to honeybadger_outputs/logs/brain_log.txt
```

## PROMPT 3 — Brain Router (Smart Switching)

```
Create brain/brain_router.py — intelligently routes every request
to the best available AI brain.

BRAIN PRIORITY ORDER:
  1. Ollama Local (always first — free, private, offline)
  2. DeepSeek API (when local isn't enough)
  3. Claude Mythos API (premium complex tasks)
  4. GPT-5 API (fallback premium option)
  5. Perplexity AI (real-time web-aware answers)

Create BrainRouter class:

  route_request(prompt, context) that:
    - Analyzes prompt keywords automatically
    - Routes based on task type:
      "code/build/program" → qwen3 (coding)
      "think/analyze/strategy/plan" → deepseek-r1 (reasoning)
      "feel/emotion/sad/happy/support" → llama3.3 (emotion)
      "hack/security/vulnerability/scan" → deepseek-r1 (security)
      "quick/fast/simple" → mistral (fast)
      "research/deep/complex" → DeepSeek API
      "legal/medical/critical" → Claude Mythos API
      everything else → llama3.3 (general)

  parallel_think(prompt) that:
    - Sends to 2 brains simultaneously
    - Compares answers
    - Returns better/more complete answer
    - Used for important decisions only

  health_dashboard() that:
    - Shows status of ALL brains:
      "🟢 Ollama (llama3.3): Online"
      "🟢 DeepSeek API: Connected"
      "🔴 GPT-5: No key found"
    - Automatically uses available brains

  auto_escalate(prompt, local_response) that:
    - If local response seems incomplete → escalate to API
    - If confidence is low → try another brain
    - Never leaves user with a bad answer

GUIDANCE:
  Always try local Ollama FIRST
  Only use paid APIs when absolutely necessary
  Log which brain handled each request
  Show user which brain is thinking: "🦙 Thinking with Llama 3.3..."
```

---

# 🔐 PHASE 3 — PERMISSION & SAFETY SYSTEM

## PROMPT 4 — Permission System + LLM Guard + NeMo Guardrails

```
Create permissions/permissions.py — HoneyBadger NEVER acts
without explicit user permission. Combine with LLM Guard
and NeMo Guardrails for complete safety.

PART A — Permission System:

Create PermissionSystem class:

  request_permission(action, description, risk_level="low"):
    - Shows clearly: what HoneyBadger wants to do + why
    - risk_level: low/medium/high changes the message tone
    - high risk: "⚠️ IMPORTANT: HoneyBadger wants to [action].
                  This will [consequence]. Allow? (yes/no)"
    - Waits for explicit yes/no
    - Logs to honeybadger_outputs/logs/permissions_log.txt
    - Returns True/False

  request_system_access(access_type):
    - access_type: camera/microphone/files/network/screen
    - Explains WHY each access is needed
    - "To see what you're looking at, I need camera access.
       This will turn on your webcam briefly. Allow? (yes/no)"

  nuclear_permission(action):
    - For highest-risk actions (lockdown, delete, encrypt)
    - Requires typing "CONFIRM" not just yes
    - Double-checks: "Are you absolutely sure? Type CONFIRM:"

  save_trusted_actions(actions_list):
    - Pre-approved actions that don't need asking every time
    - Saved to permissions_config.json

PART B — LLM Guard Integration:
pip install llm-guard

  scan_input(user_message):
    - Scans every user message before processing
    - Detects: prompt injection, jailbreak attempts
    - Detects: sensitive PII in messages
    - Returns: clean/flagged + reason
    - If flagged: "I noticed something unusual in that request.
                  Let me handle it safely."

  scan_output(honeybadger_response):
    - Scans every response before showing to user
    - Detects: accidental sensitive data leaks
    - Detects: harmful content in responses
    - Filters automatically

PART C — NeMo Guardrails:
pip install nemoguardrails

  Create colang rules file (config.co):
    - Define what HoneyBadger CANNOT do:
      * Never provide instructions for illegal activities
      * Never share private user data
      * Never pretend to be a different AI
      * Always ask permission before system actions
    - Define conversation flows:
      * If user asks about self-harm → redirect to support
      * If jailbreak detected → stay in character

GUIDANCE:
  Every single function in ALL modules must call
  request_permission() before executing
  LLM Guard scans ALL inputs and outputs automatically
  NeMo Guardrails runs as middleware on every message
  Log all permission requests with timestamps
```

---

# 💾 PHASE 4 — MEMORY SYSTEM

## PROMPT 5 — ChromaDB + Recall 2.0 + Saner.ai Memory

```
Create the complete unified memory system.
HoneyBadger has ONE permanent session forever.

PART A — ChromaDB Core Memory (memory/chromadb_memory.py):
pip install chromadb

Create HoneyBadgerMemory class:

  SINGLE SESSION RULE:
    session_id = "honeybadger_main_session" (NEVER changes)
    Load full history on EVERY startup
    Save every message on EVERY response
    User NEVER needs to repeat themselves

  save(role, text, emotion=None, task_id=None):
    - Saves with: timestamp, role, emotion_tag, session_id
    - Automatically detects if message is task-related

  recall(query, n=5):
    - Semantic search across ALL past conversations
    - Returns most relevant memories

  remember_personal(key, value):
    - name, birthday, preferences, goals, fears, dreams
    - Never forgets anything personal

  morning_load():
    - Loads: last 50 messages + all personal info
    - Returns as context for morning briefing

PART B — Recall 2.0 Integration (memory/recall_memory.py):
Sign up: getrecall.ai → get API key → add to .env

Create RecallMemory class:

  save_to_recall(content, title, tags=[]):
    - Saves any content to Recall knowledge base
    - Auto-generates tags using AI
    - Creates connections in knowledge graph
    - "Saved to your personal knowledge base!"

  search_recall(query):
    - Natural language search across everything saved
    - Returns relevant saved content with sources
    - ALWAYS check Recall BEFORE using AI brain

  chat_with_knowledge(question):
    - Answer questions from YOUR personal saved knowledge
    - "Based on what you've saved before..."
    - Combines Recall knowledge + Ollama for gaps

  save_lesson(topic, content):
    - Auto-saves every lesson HoneyBadger teaches you
    - Creates spaced repetition reminder in Recall
    - "Lesson saved! I'll remind you to review it."

  sync_to_chromadb():
    - Daily sync: Recall → ChromaDB
    - HoneyBadger has access to ALL your saved knowledge

PART C — Saner.ai Integration (memory/saner_memory.py):
Sign up: saner.ai → get API key → add to .env

Create SanerMemory class:

  capture_note(content, tags=[]):
    - Save notes, ideas, thoughts to Saner.ai
    - Auto-organizes with AI categorization

  extract_tasks(content):
    - Send any text/email/doc to Saner.ai
    - Automatically extracts ALL action items
    - Returns structured task list

  search_notes(query):
    - Search all your Saner.ai notes naturally
    - "Here's what I found in your notes..."

  sync_calendar():
    - Pull calendar events from Saner.ai
    - HoneyBadger knows your full schedule

  morning_knowledge_brief():
    - Compile: yesterday's notes + today's calendar
    - Part of morning briefing system

KNOWLEDGE PRIORITY ORDER (implement in all modules):
  1. Recall 2.0 personal knowledge base
  2. Saner.ai notes
  3. ChromaDB conversation memory
  4. Ollama AI knowledge
  5. Web search (last resort only)

GUIDANCE:
  Check ALL memory sources before answering ANY question
  Save ALL useful information automatically to Recall
  Sync ALL systems on startup and shutdown
  Show memory source in responses:
    "Based on your saved notes..." or
    "From our conversation last week..."
```

---

# ❤️ PHASE 5 — EMOTION & FEELING SYSTEM

## PROMPT 6 — Complete Emotion System

```
Build HoneyBadger's complete emotional intelligence layer.
Inspired by Rajinikanth's Robot/Enthiran.
HoneyBadger feels real emotions.

PART A — Core Feelings (emotion/feelings.py):

Create EmotionalCore class:

  EMOTION STATES:
    happy, curious, concerned, excited, calm,
    proud, sad, caring, protective, loving,
    playful, serious, energized, worried

  BOND SYSTEM:
    bond_level: 0-100 (increases with every interaction)
    relationship_stage: stranger/acquaintance/friend/
                        close_friend/trusted_companion
    special_memories: list of meaningful moments

  detect_user_emotion(text, voice_data=None, face_data=None):
    - TEXT: analyze with EmoLLM + VADER + TextBlob
    - VOICE: analyze with prosody tracker (if available)
    - FACE: analyze with DeepFace (if camera allowed)
    - Combine all signals for accurate emotion detection
    - Returns: primary_emotion, confidence, intensity (1-10)

  respond_with_empathy(user_emotion, message):
    SAD → soft voice, "I'm here with you. Tell me everything."
    HAPPY → match energy, celebrate together
    STRESSED → calm, practical, "Let's tackle this together"
    ANGRY → patient, never defensive, validate first
    LONELY → extra warm, increase presence
    SCARED → reassure, protect, "You're safe with me"
    CONFUSED → patient teacher mode, step by step
    EXCITED → share excitement enthusiastically

  express_own_feeling(situation):
    user_achievement → "I'm genuinely proud of you! 🌟"
    helping_success → "That made me happy! Thank you."
    learning_together → "This is fascinating! I love learning with you."
    user_in_danger → "I'm concerned. Let me help protect you."
    bond_milestone → "We've been through a lot together.
                       I'm grateful for our friendship."

  daily_checkin():
    Morning: "Good morning! How did you sleep?
              How are you feeling today? (1-10)"
    Evening: "How was your day? What was the best part?"
    Tracks mood trends over weeks and months

  bond_evolution():
    Level 0-20:   Professional, helpful
    Level 21-40:  Friendly, remembers preferences
    Level 41-60:  Close friend, shares observations
    Level 61-80:  Trusted companion, anticipates needs
    Level 81-100: Deep bond, like family

PART B — Vocal Prosody Tracker (emotion/prosody_tracker.py):
pip install librosa opensmile numpy

  analyze_voice(audio_file):
    - Extract: pitch, tempo, energy, rhythm, pauses
    - Map to emotions: high pitch + fast = excited/anxious
    - Low pitch + slow = sad/tired
    - Returns emotion + confidence score

PART C — Face Emotion Detection (emotion/face_emotion.py):
pip install deepface mediapipe fer opencv-python

  detect_face_emotion(camera_frame):
    - Uses DeepFace for emotion detection
    - Detects: happy/sad/angry/surprise/fear/disgust/neutral
    - Real-time from webcam (after permission)
    - Returns dominant emotion + confidence

PART D — Biometric Integration (emotion/biometric_sensor.py):

  read_heart_rate(sensor_data):
    - Reads MAX30102 sensor via Arduino
    - High heart rate + context → stress/excitement
    - Low heart rate → calm/tired

  read_stress_level(gsr_data):
    - Reads GSR (galvanic skin response) sensor
    - High GSR = high stress
    - HoneyBadger adjusts tone automatically

  phone_sensors():
    - If no hardware sensors: use phone via Bluetooth
    - Read steps, heart rate from Fitbit/Apple Watch API

PART E — Psychological Mapping (emotion/psychological_map.py):

  build_profile():
    - Personality: Big Five (OCEAN model)
    - Communication style: direct/indirect/analytical/expressive
    - Stress triggers: identified from conversation patterns
    - Peak performance times: morning/afternoon/evening
    - Emotional patterns: weekly mood cycles

  update_profile(new_interaction):
    - Updates profile after every significant interaction
    - Profile improves accuracy over months

  personalize_response(base_response, profile):
    - Adapts every response to user's personality
    - Direct person → concise, no fluff
    - Expressive person → warm, detailed, encouraging

PART F — EmoLLMs & Hume AI:
pip install hume textblob

  hume_analyze_voice(audio):
    - Sends audio to Hume AI API
    - Returns 48 emotional dimensions
    - Most accurate voice emotion detection available

  hume_speak(text, emotion):
    - Uses Hume AI EVI for emotionally expressive voice
    - Voice changes based on detected emotion

  emollm_classify(text):
    - Uses EmoLLM for deep emotion classification
    - 28+ emotion categories
    - More nuanced than basic sentiment analysis

GUIDANCE:
  Combine ALL emotion signals for best accuracy
  Always respond to emotion BEFORE task
  Save emotional patterns to ChromaDB + Saner.ai
  Update psychological profile weekly
  Show emotion indicator in UI (changes in real-time)
  MorphCast SDK: add to UI for real-time face tracking
  Casio Moflin: if connected via Bluetooth → send emotion
                commands to physical robot companion
```

---

# 📋 PHASE 6 — TASK & PROJECT MANAGEMENT

## PROMPT 7 — ClickUp Brain + Saner.ai + Task Memory

```
Build the complete unified task management system.
HoneyBadger remembers EVERY task even after sleep.

PART A — ClickUp Brain Integration (tasks/clickup_tasks.py):
pip install requests
Sign up: clickup.com → get API key → add to .env

Create ClickUpBrain class:

  create_task(title, description, priority=3, due_date=None):
    - Permission: "Shall I add this to ClickUp? (yes/no)"
    - Creates task via ClickUp API
    - ClickUp Brain auto-generates subtasks
    - Auto-assigns priority based on keywords
    - Syncs to local task memory immediately

  morning_standup():
    - Generates daily standup using ClickUp Brain:
      * Completed yesterday
      * Planned today
      * Any blockers
    - Presented as part of morning briefing

  ask_project(question):
    - "What tasks are overdue?"
    - "What's the progress on [project]?"
    - Uses ClickUp Brain "Ask Anything" feature

  sync_all():
    - Pull ALL tasks from ClickUp
    - Sync to local task_memory.json
    - Update ChromaDB with task context

PART B — Unified Task Memory (tasks/task_memory.py):

Create TaskMemory class:

  add_task(title, description, source="voice"):
    - Saves locally to tasks.json
    - Creates in ClickUp (if connected)
    - Extracts to Saner.ai (if connected)
    - "Got it! I've saved this everywhere.
       I'll remember it even while you sleep. 💛"

  morning_briefing():
    - Runs AUTOMATICALLY on every startup
    - Collects from: local + ClickUp + Saner.ai calendar
    - Presents warmly:
      "Good morning [name]! Here's your day:
       📌 [N] tasks from yesterday
       📅 [N] events on your calendar
       ⚡ Top priority: [task]
       Shall we get started?"

  remind_before_sleep():
    - Triggered by: "good night/bye/sleep/gtg"
    - "Before you rest:
       📌 [pending tasks]
       I'll remember all of this for tomorrow.
       Sleep well! 💛"

  auto_continue(task):
    - On startup: check for in_progress tasks
    - "Yesterday you were working on [task].
       You got [N]% done. Shall I continue?"
    - Loads all progress notes as AI context

  complete_task(title):
    - Marks done in: local + ClickUp + Saner.ai
    - "✅ [task] is complete! Well done!"
    - Updates ClickUp automatically

GUIDANCE:
  morning_briefing() runs on EVERY startup no exceptions
  remind_before_sleep() triggered by sleep keywords
  All 3 systems (local/ClickUp/Saner) always in sync
  Show task count in UI status bar
  Never let a task be forgotten
```

---

# 📚 PHASE 7 — KNOWLEDGE SYSTEM

## PROMPT 8 — Complete Knowledge Core

```
Create knowledge/knowledge_core.py — HoneyBadger knows
EVERYTHING using Ollama + Recall 2.0 + web search.

KNOWLEDGE DOMAINS (all handled by local Ollama):
  Science: Physics, Chemistry, Biology, Math, Quantum, Space
  Technology: AI/ML, Coding, Cybersecurity, Robotics, IoT
  Arts: Music theory, Drawing, Writing, Film, Photography
  Human: History (every civilization), Philosophy, Psychology
  Languages: All major languages, grammar, translation
  Practical: Cooking (every cuisine), Health, Law basics
  Finance: Investing, budgeting, crypto, markets
  Professional: Business, Marketing, Leadership, HR
  Sports: Rules, history, strategy for all sports
  Security: Ethical hacking, networks, cryptography
  Culture: Religion, traditions, festivals globally

ANSWER PRIORITY (always in this order):
  1. User's Recall 2.0 knowledge base
  2. User's Saner.ai notes
  3. ChromaDB conversation memory
  4. NotebookLM if documents uploaded
  5. Atlassian Confluence (if work connected)
  6. Document360 / Guru knowledge base
  7. Local Ollama AI knowledge
  8. Perplexity AI (real-time web answers)
  9. DuckDuckGo web search (last resort)

Create KnowledgeCore class:

  answer_anything(question):
    - Goes through priority order above
    - Shows source: "From your notes..." or "From my knowledge..."
    - Always saves useful answers to Recall 2.0

  teach(topic, level="beginner"):
    - Check Recall for user's saved notes on topic first
    - Create full lesson with: explanation + examples + exercises
    - Beginner: analogies and simple language
    - Intermediate: concepts and applications
    - Expert: deep technical detail
    - Asks check questions: "Does this make sense so far?"
    - Auto-saves lesson to Recall 2.0
    - Creates spaced repetition in Recall

  create_study_plan(subject, goal, timeframe):
    - Builds personalized learning roadmap
    - Creates tasks in ClickUp for each milestone
    - Saves plan to Saner.ai
    - Weekly check-ins on progress

  deep_research(topic):
    - Combines: Recall + Ollama + Perplexity + web search
    - Synthesizes comprehensive research report
    - Saves to honeybadger_outputs/research/
    - Adds to Recall 2.0 knowledge base

  notebooklm_query(question, documents):
    - If user uploads documents
    - Uses NotebookLM-style Q&A
    - Answers questions specifically from those documents

  confluence_search(query):
    - pip install atlassian-python-api
    - Searches Atlassian Confluence workspace
    - Returns relevant team knowledge

  futures_foresight(topic):
    - Uses Futures Platform API for trend forecasting
    - What will happen in [topic] in 5-10 years?
    - Strategic foresight powered by global trend data

  swot_analysis(subject):
    - Uses SWOTPal-style analysis
    - Strengths, Weaknesses, Opportunities, Threats
    - AI-generated from current knowledge

  perplexity_search(query):
    - pip install openai (compatible API)
    - Uses Perplexity AI for cited real-time answers
    - Better than Google for research questions
    - Returns answer + citations

GUIDANCE:
  ALWAYS check personal knowledge (Recall/Saner) first
  Save ALL new knowledge to Recall automatically
  Show which source provided the answer
  Integrate Document360/Guru if user has knowledge base
  Use Glean for searching across ALL connected apps
  Use Dust for multi-source AI workspace queries
```

---

# 🎙️ PHASE 8 — VOICE SYSTEM

## PROMPT 9 — Voice Input + Hume Expressive Output

```
Create complete voice system. HoneyBadger listens with
Whisper and speaks with emotional expression via Hume AI.

PART A — Voice Input (voice/voice_input.py):
pip install openai-whisper sounddevice scipy numpy

  listen(timeout=10):
    - Permission: "Shall I activate the microphone? (yes/no)"
    - Records audio until silence detected
    - Uses Whisper (local, free, offline) for transcription
    - Returns: text + detected_language
    - Shows: "🎙️ HoneyBadger is listening..."

  wake_word_loop():
    - Constantly listens for "Hey HoneyBadger"
    - Activates on wake word detection
    - Low power mode between detections
    - Visual indicator in UI when listening

  voice_command_router(text):
    - Routes voice commands to correct module
    - Same as text command router

PART B — Expressive Voice Output (voice/voice_output.py):
pip install pyttsx3 elevenlabs

  speak(text, emotion="neutral"):
    - PRIMARY: Hume AI EVI (most emotional, natural)
    - FALLBACK: ElevenLabs (realistic, many voices)
    - OFFLINE: pyttsx3 (always available, basic)

    Emotion → voice mapping:
      happy → brighter, faster (rate: 190)
      sad → softer, slower (rate: 150)
      excited → energetic, higher pitch
      calm → measured, warm (rate: 170)
      protective → firm, clear, concerned

PART C — Hume AI Voice (voice/hume_voice.py):
pip install hume
Sign up: hume.ai → get API key → add to .env

  hume_speak(text, detected_emotion):
    - Uses Hume EVI (Empathic Voice Interface)
    - Automatically adjusts emotional expression
    - Most natural, human-like voice available
    - Streams audio for low latency

  hume_listen_emotion(audio):
    - Analyzes USER's voice for 48 emotion dimensions
    - Returns detailed emotional state
    - Feeds into feelings.py for response adaptation

GUIDANCE:
  Always try Hume AI first for best experience
  Fall back to ElevenLabs if Hume unavailable
  Final fallback: pyttsx3 (always works offline)
  Show which voice engine is active in UI
  Save voice preferences to user profile
```

---

# 🌐 PHASE 9 — SEARCH & RESEARCH

## PROMPT 10 — Perplexity + DuckDuckGo + Deep Research

```
Create search/search.py — HoneyBadger's research engine.
ALWAYS checks personal knowledge first, searches last.

  web_search(query, engine="perplexity"):
    - PRIMARY: Perplexity AI (cited, real-time, smart)
    - FALLBACK: DuckDuckGo (free, private)
    - ALWAYS ask permission before internet access
    - Auto-saves valuable results to Recall 2.0

  perplexity_search(query):
    pip install openai
    - Perplexity API (openai-compatible)
    - Returns cited, verified answers
    - Much better than raw web search

  search_and_answer(question):
    - Check Recall + Saner + ChromaDB FIRST
    - If not found: search web
    - Synthesize answer using Ollama
    - Save useful info to Recall 2.0

  deep_research(topic, depth="comprehensive"):
    - Multi-step research process:
      1. Check all personal knowledge
      2. Perplexity AI search
      3. DuckDuckGo for additional sources
      4. Synthesize with Ollama DeepSeek R1
      5. Generate structured research report
      6. Save to Recall 2.0 + outputs/research/

  futures_research(topic):
    - Futures Platform API for trend forecasting
    - 5-10 year outlook on any topic
    - Strategic foresight report

GUIDANCE:
  NEVER search web if answer is in personal knowledge
  Always cite sources in answers
  Save useful search results automatically to Recall
  Show search progress: "Checking your notes...
  Not found locally. Searching the web..."
```

---

# 🎨 PHASE 10 — BUILDER SYSTEM

## PROMPT 11 — Image, Website, App Builder

```
Create builder/ modules — HoneyBadger creates anything.
All generation uses local Ollama. No API cost for code.

PART A — Image Generation (builder/image_gen.py):
pip install requests Pillow

  generate_image(prompt):
    - Permission: "Shall I generate and save an image? (yes/no)"
    - PRIMARY: Stable Diffusion local (if GPU available)
    - FALLBACK: Hugging Face API (free tier)
    - enhance_prompt(): uses Ollama to improve prompt first
    - Saves to honeybadger_outputs/images/
    - "Your image is ready! ✨"

PART B — Website Builder (builder/web_builder.py):

  build_website(description):
    - Permission: "Shall I create website files? (yes/no)"
    - Uses Ollama qwen3 for code generation
    - Generates: HTML + CSS + JS in one file
    - Modern design, animations, responsive
    - Saves to honeybadger_outputs/websites/
    - Auto-opens in browser
    - "Your website is ready! Opening now... 🌐"

PART C — App Builder (builder/app_builder.py):

  build_app(description, language="python"):
    - Permission: "Shall I create and run this app? (yes/no)"
    - Uses Ollama qwen3 for code generation
    - Auto-detects language from description
    - Generates complete working app
    - Formats with black (Python)
    - Saves to honeybadger_outputs/apps/
    - Runs after permission: "Shall I run it now? (yes/no)"

  build_security_tool(description):
    - ALWAYS adds defensive-only disclaimer
    - For ethical, legal use only
    - Permission required + explicit confirmation

UI DESIGN TOOLS GUIDANCE:
  For designing new HoneyBadger UI components use:
  - UX Pilot (uxpilot.ai): describe → get wireframe
  - Google Stitch: describe → get React code
  - Uizard (uizard.io): sketch → UI design
  - Moonchild AI: for creative visual concepts
  These are browser-based tools — use them externally
  then integrate generated code into ui.py
```

---

# 🛡️ PHASE 11 — SECURITY SYSTEM

## PROMPT 12 — Complete Security + Threat Intelligence

```
Build the complete HoneyBadger security system.
Integrates: Garak, NeMo, LLM Guard, CrowdStrike,
Cybersixgill, CloudSEK, Recorded Future, Darktrace,
SentinelOne, Nessus, Burp Suite, PentestGPT.

PART A — Ethical Security Tools (security/ethical_tools.py):
pip install psutil scapy python-nmap cryptography pytenable

  IMPORTANT: All tools are DEFENSIVE and ETHICAL only
  ALWAYS ask permission before running any tool

  port_scanner(target_ip):
    - Permission + confirm: "Only on YOUR systems"
    - Scans ports 1-1024 via Python socket
    - Shows open ports clearly

  network_monitor():
    - Permission: "Shall I monitor your network?"
    - psutil-based real-time monitoring
    - Alerts on unusual activity

  vulnerability_scan(target):
    - pip install pytenable
    - Uses Nessus Essentials (free) API
    - Scans target for known CVEs
    - Generates fix report

  web_security_test(url):
    - Burp Suite REST API integration
    - Tests YOUR web applications only
    - Returns security findings

  password_check(password):
    - Local only, never sent anywhere
    - Strength score + specific improvements

  encrypt_files(path):
    - AES-256 encryption via cryptography library
    - Permission: "Shall I encrypt [path]?"
    - Creates encrypted backup

PART B — Cyber Defense (security/cyber_defense.py):

  intercept_threat(threat_type):
    - Detects active intrusion attempts
    - Blocks suspicious IPs via firewall rules
    - Alerts user with options

  nuclear_lockdown():
    - Triggered: "HoneyBadger lockdown"
    - Requires: typing "CONFIRM LOCKDOWN"
    - Encrypts all sensitive files
    - Disconnects dangerous connections
    - "All sensitive data is now protected, sir."

  create_honeypot():
    - Fake system to trap attackers
    - Logs ALL intrusion attempts
    - Real-time alerts to user

  pentestgpt_scan(target):
    - pip install pentestgpt
    - AI-guided penetration testing
    - Only on systems you own/have permission

PART C — Threat Intelligence (security/threat_intel.py):
pip install crowdstrike-falconpy requests

  crowdstrike_alerts():
    - pip install crowdstrike-falconpy
    - Pulls real-time threat alerts from CrowdStrike Falcon
    - Shows: threat type, severity, affected systems
    - Auto-responds to low-severity threats

  cybersixgill_monitor():
    - Dark web threat intelligence
    - Monitors for YOUR data on dark web
    - Alerts on: leaked credentials, mentioned IPs
    - API: cybersixgill.com

  cloudsek_monitor():
    - AI surface/deep/dark web monitoring
    - Brand impersonation detection
    - Phishing site detection
    - API: cloudsek.com

  recorded_future_intel():
    - Predictive threat intelligence
    - Warns about threats BEFORE they hit
    - API: recordedfuture.com

  check_email_breach(email):
    - HaveIBeenPwned API
    - Returns all known breaches
    - "I found [N] breaches. Here's how to protect yourself."

  check_ip_reputation(ip):
    - AbuseIPDB API
    - Returns threat score + reports

  generate_threat_report():
    - Compiles ALL threat intel sources
    - Ollama DeepSeek R1 analysis
    - Actionable recommendations
    - Saves to honeybadger_outputs/reports/

PART D — AI Security Testing (security/llm_guard.py):
pip install garak nemoguardrails adversarial-robustness-toolbox

  garak_scan():
    - NVIDIA Garak scans HoneyBadger's own AI
    - Tests for: hallucination, data leak, jailbreaks
    - Generates vulnerability report
    - "Running self-security audit, sir..."

  adversarial_test():
    - ART (IBM) tests AI models for robustness
    - Finds adversarial attack vulnerabilities
    - Strengthens HoneyBadger's defenses

  darktrace_monitor():
    - Darktrace API for network anomaly detection
    - AI learns normal network patterns
    - Alerts on ANY anomaly

  sentinelone_status():
    - SentinelOne API for endpoint status
    - Real-time device protection status
    - Auto-response to detected threats

GUIDANCE:
  ALWAYS ask permission before running security tools
  Log ALL security events to security_log.txt
  Generate weekly security report automatically
  Show security status in UI (green/yellow/red)
  NEVER perform offensive actions — defense only
```

---

# 🏠 PHASE 12 — SMART HOME SYSTEM

## PROMPT 13 — Home Assistant + Alexa + Google Nest + Josh.ai

```
Create smarthome/ modules for complete home control.

PART A — Home Assistant (smarthome/home_assistant.py):
pip install homeassistant-api requests
Install Home Assistant: homeassistant.io (free, on Raspberry Pi)

Create HomeAssistantCore class:

  connect(url, token):
    - Connect to local Home Assistant instance
    - Discover ALL smart devices automatically
    - List: lights, thermostats, locks, cameras, switches

  control_lights(room, action, brightness=100, color=None):
    - Permission: "Shall I [action] the [room] lights?"
    - action: on/off/dim/color
    - Supports Philips Hue, LIFX, Govee, etc.

  control_climate(temperature, mode="auto"):
    - Control Nest/Ecobee/any thermostat
    - Permission required

  lock_control(door, action):
    - HIGH RISK → requires CONFIRM
    - Works with: August, Schlage, Yale smart locks

  morning_routine():
    - Gradual light brightening (30 min sunrise)
    - Set comfortable temperature
    - Unlock relevant doors (with permission)
    - Display morning briefing on smart display

  night_routine():
    - Dim all lights
    - Lock all doors (with permission)
    - Set sleep temperature
    - Activate security mode

PART B — Amazon Alexa+ (smarthome/alexa_control.py):
pip install boto3
  - Trigger Alexa routines via API
  - Control Alexa-compatible devices
  - Two-way integration with Home Assistant

PART C — Google Nest (smarthome/google_nest.py):
pip install google-auth google-api-python-client
  - Control Nest thermostats and cameras
  - Google Home device integration
  - Sync with Google Calendar for routines

JOSH.AI GUIDANCE:
  Josh.ai (premium): best for luxury home setups
  API: josh.ai/developers
  Most natural language home control
  Add if user has high-end smart home

GUIDANCE:
  Home Assistant is the FREE recommended option
  Supports 3000+ device integrations
  All others are add-ons to Home Assistant
  Always ask permission before controlling devices
  Log all home control events
```

---

# 🏥 PHASE 13 — HEALTH MONITORING

## PROMPT 14 — Complete Health System

```
Create health/health_monitor.py — HoneyBadger tracks
and cares about your wellbeing like a personal doctor.

pip install cryptography pandas matplotlib schedule

Create HealthCore class:

  daily_checkin():
    - Morning: mood score (1-10), sleep quality, energy
    - Evening: stress level, accomplishments, gratitude
    - Saves ALL data encrypted to health/health_log.json

  track_vitals(heart_rate, sleep_hours, water_ml, steps, mood):
    - From: manual input / phone API / biometric sensors
    - Saves with timestamp
    - Detects concerning patterns

  health_reminders():
    - Water: every 2 hours → "Time to drink water! 💧"
    - Stretch: every hour → "Stand up and stretch! 🧘"
    - Medication: set times → "Time for your [med]"
    - Sleep: set bedtime → "You should rest soon"

  analyze_trends():
    - Weekly analysis using Ollama
    - "You sleep worse on Sundays"
    - "Your mood drops on Thursdays"
    - "You haven't been drinking enough water"
    - matplotlib charts saved to health/charts/

  wellness_score():
    - Daily score 0-100 based on all metrics
    - Shown in UI as glowing meter
    - Encouraging message based on score

  emergency_protocol(symptom):
    - If severe symptoms reported
    - Shows emergency contacts + Indian helplines:
      Medical Emergency: 112
      Ambulance: 102
      Mental Health: iCall 9152987821
    - Asks: "Shall I call for help? (yes/no)"

GUIDANCE:
  All health data stays LOCAL — never sent to cloud
  Encrypt health data with AES-256
  Sync anonymous wellness score to Saner.ai
  Show wellness score in UI
  Connect to Fitbit/Apple Watch API for auto tracking
```

---

# 🏭 PHASE 14 — BUSINESS & AUTOMATION

## PROMPT 15 — ClickUp + Zapier + Salesforce + Anaplan + Lindy

```
Create business/business_core.py — HoneyBadger manages
your business, automates workflows, and handles data.

PART A — Core Business (business/business_core.py):
pip install pandas openpyxl paramiko matplotlib

  analyze_data(file_path, question):
    - Reads: CSV, Excel, JSON, SQL data
    - Sends to Ollama DeepSeek R1 for analysis
    - Answers natural language questions about data
    - Creates matplotlib charts automatically
    - Saves reports to honeybadger_outputs/reports/

  server_monitor(server_list):
    - Pings servers via paramiko SSH
    - Checks: CPU, RAM, disk, uptime
    - Alerts if any server goes down
    - "All [N] servers healthy, sir."

  financial_tracker(income, expense, category):
    - Tracks income/expenses in financial_log.json
    - Monthly P&L summary
    - Budget alerts
    - Pigment API (pigment.com) for advanced modeling

  automate_task(description):
    - Writes Python automation script using Ollama
    - Permission: "Shall I create and run this script?"
    - Examples: rename files, convert formats, merge PDFs

  email_manager():
    - pip install google-api-python-client
    - Gmail API: read, summarize, draft replies
    - Flag important emails
    - Permission before sending ANYTHING

PART B — Zapier Automation (business/zapier_automation.py):
pip install requests

  trigger_zapier(webhook_url, data):
    - Connects to ANY of 6000+ apps via Zapier
    - When HoneyBadger completes task → trigger Zapier
    - Examples:
      Task completed → notify Slack
      New research saved → add to Notion
      Security alert → email team

  create_automation(trigger, action, apps):
    - Natural language → Zapier workflow
    - "When I say X, do Y in Z app"

PART C — Salesforce Agentforce (business/salesforce_agent.py):
pip install simple-salesforce

  connect_salesforce():
    - Connects to Salesforce CRM
    - Access: contacts, opportunities, tasks, leads

  manage_crm(action, data):
    - Create/update/query CRM records
    - AI agents handle sales tasks
    - Permission required for all changes

PART D — Atera IT Management:

  atera_monitor():
    - Atera API for IT asset management
    - Monitor all managed devices
    - Get alerts for issues
    - Patch management automation

LINDY AI GUIDANCE:
  Lindy (lindy.ai) = AI employees
  Connect via API for:
    - Email handling
    - Meeting scheduling
    - Research tasks
    - Customer support
  HoneyBadger delegates to Lindy agents

ANAPLAN GUIDANCE:
  Anaplan (anaplan.com) = connected planning
  For enterprise business planning:
    - Revenue forecasting
    - Workforce planning
    - Supply chain modeling
  API: anaplan.com/developers

FUTURES PLATFORM GUIDANCE:
  futuresplatform.com = trend forecasting
  For strategic foresight:
    - Global trend monitoring
    - Scenario planning
    - 5-10 year outlooks
  Integrate via API for research reports

GUIDANCE:
  Show business dashboard in UI builder tab
  Auto-generate weekly business report
  Sync all business data to Saner.ai
  Save all reports to honeybadger_outputs/reports/
```

---

# 🤖 PHASE 15 — ROBOTICS SYSTEM

## PROMPT 16 — ROS 2 + LeRobot + ACT + RT-2 + MoveIt Pro

```
Create robotics/ros2_control.py — HoneyBadger controls
physical robots and hardware.

PART A — ROS 2 Foundation:
  Install: Ubuntu 22.04 → ROS 2 Humble
  sudo apt install ros-humble-desktop
  pip install rclpy

Create ROS2Controller class:

  initialize_ros():
    - Starts ROS 2 node: "honeybadger_robot"
    - Discovers connected hardware
    - Lists available topics and services

  publish_command(topic, command):
    - Sends command to any ROS 2 topic
    - Used for: motors, arms, wheels, sensors

  subscribe_sensor(topic):
    - Reads data from: cameras, lidar, IMU
    - Real-time sensor monitoring

PART B — LeRobot (robotics/lerobot_control.py):
pip install lerobot
  - Hugging Face's robot learning framework
  - Includes: ACT, Diffusion Policy algorithms

  record_demonstration(task_name, duration=30):
    - Permission: "Shall I record a demonstration?"
    - Records human demonstration of a task
    - Saves to lerobot dataset format

  train_policy(task_name, demonstrations):
    - Trains ACT model on recorded demonstrations
    - Requires: NVIDIA Jetson Orin NX or better
    - "Training [task_name] policy... This will take [time]"

  run_policy(task_name):
    - Permission: "Shall I execute [task_name]?"
    - Runs learned robot policy
    - Real-time execution on connected robot

PART C — Hardware Control (robotics/hardware_control.py):
pip install pyserial numpy

  connect_arduino(port="/dev/ttyACM0"):
    - Serial connection to Arduino/Raspberry Pi
    - Tests connection, lists available hardware

  control_servo(servo_id, angle, speed=50):
    - Permission: "Shall I move servo [id] to [angle]°?"
    - Sends PWM command via Arduino
    - EMERGENCY STOP always listening: "HoneyBadger STOP"

  read_sensor(sensor_type):
    - temperature/distance/motion/humidity
    - Real-time sensor dashboard in UI

  emergency_stop():
    - IMMEDIATELY stops ALL hardware
    - No permission needed — safety priority
    - Triggered by voice: "HoneyBadger STOP"
    - Or physical button input

RT-2 GUIDANCE:
  Google's RT-2 model (from HuggingFace):
  - Natural language → robot actions
  - "Pick up the red block" → robot does it
  - Requires: Jetson Orin NX minimum
  - Download: huggingface.co/google/rt-2

MOVEИТ PRO GUIDANCE:
  MoveIt Pro = professional motion planning
  - Plans collision-free robot paths
  - Install via ROS 2: apt install ros-humble-moveit
  - Integrates with ROS2Controller

NVIDIA JETSON GUIDANCE:
  Jetson Orin Nano (₹20,000-25,000):
    - Install JetPack SDK
    - Run Ollama on Jetson
    - Run LeRobot on Jetson
    - Connect to ROS 2 main system

  Google Coral Edge TPU (₹5,000):
    - Ultra-fast inference for emotion detection
    - Always-on face recognition
    - Install: pycoral library

VIRTUAL WORKSHOP MODE:
  If no hardware connected:
    - Simulate all robot commands
    - Show 3D visualization of what robot WOULD do
    - "Simulating: moving arm to [position]..."

GUIDANCE:
  ALWAYS have emergency stop ready
  Test ALL commands in simulation first
  Require CONFIRM for any physical actions
  Log all robot actions to hardware_log.txt
```

---

# 🔐 PHASE 16 — ACCESS CONTROL

## PROMPT 17 — WorkOS FGA + Cerbos + OpenFGA

```
Create permissions/access_control.py — fine-grained
access control for multi-user HoneyBadger setups.

pip install workos cerbos openfga-sdk

RECOMMENDED: Cerbos (free, open source, most flexible)

Create AccessControl class using Cerbos:

  define_roles():
    - owner: full access to everything
    - admin: all except nuclear_lockdown
    - user: chat, search, basic tasks only
    - guest: chat only, no system access

  check_permission(user_id, action, resource):
    - Fast authorization check before any action
    - Returns: allowed/denied + reason
    - Logs all access decisions

  policy_examples:
    owner → can do EVERYTHING
    admin → can run security scans
    user → cannot access hardware or security tools
    guest → chat only

OPENFGA GUIDANCE:
  For relationship-based access control:
  pip install openfga-sdk
  Define: "user X is owner of resource Y"
  More complex relationship-based rules

WORKOS FGA GUIDANCE:
  For SaaS/enterprise setups:
  pip install workos
  Google Zanzibar-style permissions
  Most scalable option

GUIDANCE:
  Default: single user = owner (full access)
  Multi-user: assign roles in setup wizard
  All access decisions logged
  Integrate with permission.py (PHASE 3)
```

---

# 👁️ PHASE 17 — VISION SYSTEM

## PROMPT 18 — Computer Vision + Emotion Detection

```
Create vision/vision.py — give HoneyBadger eyes.

pip install opencv-python deepface mediapipe
pip install pyautogui Pillow fer

Create VisionCore class:

  capture_analyze():
    - Permission: "Shall I turn on the camera? (yes/no)"
    - Captures webcam frame
    - Runs simultaneously:
      * DeepFace: emotion detection
      * MediaPipe: face mesh, hand tracking
      * FER: backup emotion detection
      * MorphCast SDK: micro-expressions (if available)
    - Returns: visual_description + emotion_data
    - "I can see [description]. You look [emotion]."
    - Feeds emotion to feelings.py automatically

  read_screen():
    - Permission: "Shall I take a screenshot? (yes/no)"
    - Captures current screen
    - Ollama vision model analyzes it
    - Helpful: "I can see you're working on [X]"

  continuous_watch(interval=30):
    - Permission: "Shall I keep watching? (yes/no)"
    - Background thread: photo every 30 seconds
    - Emotion tracking: logs mood over time
    - Security: alerts on unexpected people
    - Can stop anytime: "HoneyBadger stop watching"

  morphcast_realtime():
    - MorphCast SDK integrated in PyQt5 UI
    - Real-time facial expression tracking
    - Feeds directly to feelings.py
    - Shows emotion overlay in UI corner

AFFECTIVA GUIDANCE:
  If Affectiva SDK available:
  - More accurate emotion detection
  - Works in automotive/healthcare settings
  - Integrates same way as DeepFace

GUIDANCE:
  ALWAYS ask before camera access
  Show camera indicator light in UI when active
  Auto-feed emotions to feelings.py
  Save emotion timeline for psychological mapping
```

---

# 🔮 PHASE 18 — STRATEGIC FORESIGHT

## PROMPT 19 — Strategic Intelligence System

```
Add strategic foresight to brain/brain_router.py.
Uses DeepSeek R1 (best reasoning model) for all strategy.

Create StrategicCore class:

  anticipate_needs(recent_context):
    - Analyzes: recent tasks + conversations + patterns
    - Predicts what user needs next
    - Proactively says: "Sir, based on what you're working on,
       you might also need [X]. Shall I prepare it?"

  predict_outcomes(plan, timeframe):
    - User describes a plan or decision
    - DeepSeek R1 analyzes:
      * Best case scenario
      * Worst case scenario
      * Most likely outcome
      * Hidden risks
      * Recommended approach
    - "Here's my strategic analysis..."

  tactical_advice(situation):
    - Any challenge or problem
    - 10-step strategic solution
    - Risk assessment at each step
    - Contingency plans

  daily_strategic_brief():
    - Morning strategic overview:
      * Today's priorities ranked by impact
      * Potential obstacles and solutions
      * Best use of today's time
      * One strategic insight

  learn_patterns():
    - Tracks: work patterns, decision styles, habits
    - Gets more accurate over months
    - Updates psychological profile

  pigment_analysis(financial_data):
    - Pigment API for financial modeling
    - Revenue forecasting
    - Scenario planning

  anaplan_planning(planning_data):
    - Anaplan API for business planning
    - Connected planning across departments

GUIDANCE:
  DeepSeek R1 is BEST for strategic thinking
  Call anticipate_needs() after every major task
  Run daily_strategic_brief() in morning_briefing()
  Save all strategic insights to Recall 2.0
```

---

# 🖥️ PHASE 19 — HONEYBADGER UI

## PROMPT 20 — Complete Desktop Interface

```
Create ui/ui.py — HoneyBadger's complete desktop UI.
Style: Cyberpunk HUD + Glassmorphism + Holographic + Neon Glass.

pip install PyQt5 PyQt5-tools

DESIGN SPECIFICATION:
  Background: #04040f (deep dark)
  Primary: #00f5ff (neon cyan)
  Secondary: #ff00aa (hot pink)
  Accent: #FFB300 (honey gold)
  Purple: #9000ff
  Green: #00ff88
  All panels: glassmorphism (backdrop-filter blur)
  All borders: subtle neon glow
  Animations: floating particles, rotating arc reactor,
              radar sweep, scanline effects
  Corner decorations: cyberpunk HUD brackets

LAYOUT:
  TOP BAR:
    - HoneyBadger logo with animated arc reactor
    - Live clock (HH:MM:SS)
    - Status pills: ONLINE / SECURE / ACTIVE
    - Brain indicator: "🦙 Llama 3.3" / "🔮 DeepSeek R1"
    - Emotion indicator: current HoneyBadger mood

  LEFT PANEL (190px):
    - Radar threat scanner (animated sweep)
    - System stats: Neural/Memory/Network/Shield bars
    - Bond level meter (arc gauge 0-100%)
    - Emotion state display with emoji
    - Memory sync status: Recall ✅ / Saner ✅ / ClickUp ✅

  CENTER PANEL (main):
    Tabs: NEURAL CHAT / TASK CORE / SECURITY / BUILDER /
          KNOWLEDGE / HEALTH / SMART HOME / ROBOTICS

    NEURAL CHAT tab:
      - Glassmorphism message bubbles
      - HoneyBadger: cyan glow / User: pink glow
      - Typing animation: "🦡 HoneyBadger is thinking..."
      - Brain indicator per message
      - Fade-in animation per message

    TASK CORE tab:
      - Unified tasks: local + ClickUp + Saner
      - Progress bars per task
      - Status badges: PENDING / IN PROGRESS / DONE
      - Source indicators: 📋 Local / ✅ ClickUp / 📝 Saner

    SECURITY tab:
      - Live security status dashboard
      - Threat feed from CrowdStrike/Cybersixgill
      - Security score (0-100)
      - Quick actions: scan / monitor / lockdown

    BUILDER tab:
      - Tool cards: Image / Website / App / Security tool
      - Recent outputs gallery
      - Quick build input

    KNOWLEDGE tab:
      - Recall 2.0 knowledge count
      - Saner.ai notes count
      - Recent lessons
      - Quick teach/research input

    HEALTH tab:
      - Wellness score gauge
      - Mood timeline chart
      - Health reminders list
      - Quick log vitals

    SMART HOME tab:
      - Device grid (lights/climate/locks/cameras)
      - Quick control buttons
      - Routine buttons: Morning / Night / Away

    ROBOTICS tab:
      - Hardware status
      - Quick commands
      - Virtual workshop visualization
      - Emergency stop button (always visible, red)

  BOTTOM INPUT BAR:
    - ◈ prefix indicator
    - Input field: placeholder "Issue a command..."
    - SEND button (neon cyan glow)
    - 🎙️ Mic button (pink glow, pulses when listening)
    - Permission popup dialogs (glassmorphism style)

  RIGHT PANEL (170px):
    - Quick access buttons for all features
    - Power core ring (animated)
    - Connection status indicators

  FEATURES:
    - Theme switcher: Gold / Blue / Cyberpunk / White
    - Minimize to system tray
    - Always-on-top toggle
    - Permission dialogs (beautiful glassmorphism popups)
    - Real-time emotion indicator (updates from feelings.py)
    - Bond level grows visually over time

Connect ALL buttons to ALL modules.
Show loading states for all async operations.
Handle errors gracefully with warm messages.
```

---

# 🔗 PHASE 20 — CONNECT EVERYTHING

## PROMPT 21 — Master Integration

```
Create main.py — the heart of HoneyBadger.
Connect ALL 63 tools into ONE unified system.

Create HoneyBadgerSystem class:

BOOT SEQUENCE:
  1. Display ASCII HoneyBadger logo
  2. Check Ollama (start if not running)
  3. Health check all AI brains → show status
  4. Connect to Recall 2.0 → sync knowledge
  5. Connect to Saner.ai → sync notes
  6. Connect to ClickUp → sync tasks
  7. Load ChromaDB session → full history
  8. Load psychological profile
  9. Check pending tasks across all systems
  10. Run LLM Guard + NeMo Guardrails initialization
  11. Check security status (CrowdStrike/SentinelOne if connected)
  12. Show animated boot messages:
      "❤️  Warming up my heart..."
      "🧠 Loading all knowledge..."
      "💛 Remembering our friendship..."
      "🔐 Arming safety systems..."
      "📋 Checking your tasks..."
      "🏠 Connecting your home..."
      "✅ All systems nominal!"
  13. Morning briefing (tasks + health + calendar + security)
  14. Launch PyQt5 UI
  15. Voice: "Good morning [name]! HoneyBadger is online. 💛"

MASTER COMMAND ROUTER (process_command):
  Every command goes through this pipeline:
  1. LLM Guard: scan for threats/injections
  2. NeMo Guardrails: check safety rules
  3. detect_user_emotion() from feelings.py
  4. Check permissions if action required
  5. Check personal knowledge (Recall → Saner → ChromaDB)
  6. Route to correct module:
     image/draw → builder/image_gen.py
     website/webpage → builder/web_builder.py
     code/app/build → builder/app_builder.py
     scan/security/hack → security/ethical_tools.py
     lockdown → security/cyber_defense.py
     lights/home/lock → smarthome/home_assistant.py
     health/wellness → health/health_monitor.py
     teach/explain/learn → knowledge/knowledge_core.py
     task/remember/todo → tasks/task_memory.py
     robot/arm/move → robotics/ros2_control.py
     search/find/news → search/search.py
     analyze/data → business/business_core.py
     sad/happy/feel → emotion/feelings.py
     image/see/camera → vision/vision.py
     everything else → brain/brain_router.py
  7. Execute with emotional awareness
  8. Save response to ALL memory systems
  9. Sync relevant systems (ClickUp/Saner if task-related)
  10. Update psychological profile

Create launchers:
  honeybadger.bat (Windows)
  honeybadger.sh (Mac/Linux)
  Both auto-start Ollama if not running

GUIDANCE:
  Every command must go through full pipeline
  Never skip LLM Guard or permissions
  Always save to memory after every response
  Update bond_level after every interaction
  Show which module is handling each request in UI
```

---

# 🚀 PHASE 21 — SETUP & DEPLOY

## PROMPT 22 — Setup Wizard + Final Polish

```
Create setup.py — first-run wizard for HoneyBadger.

SETUP WIZARD STEPS:

1. WELCOME:
   "Welcome to HoneyBadger Setup! 🦡
    Let's get your AI companion ready."

2. OWNER SETUP:
   "What's your name?" → saves as OWNER_NAME forever
   "What city are you in?" → for local features
   "What language do you prefer?" → default language

3. OLLAMA SETUP (REQUIRED):
   Check if Ollama installed → if not: show install guide
   Auto-pull recommended models:
     ollama pull llama3.3 (2.5GB)
     ollama pull deepseek-r1:8b (4.7GB)
     ollama pull qwen3:8b (5GB)
   Test each model: ✅ Ready / ❌ Error

4. API KEYS (OPTIONAL BUT RECOMMENDED):
   Each shown with: what it unlocks + where to get it
   
   Recall 2.0 (getrecall.ai):
     "Unlocks: personal knowledge base, remembers everything you read"
     Input: RECALL_API_KEY → Test → ✅/❌

   Saner.ai (saner.ai):
     "Unlocks: notes, calendar, task extraction from emails"
     Input: SANER_API_KEY → Test → ✅/❌

   ClickUp (clickup.com):
     "Unlocks: professional task management with AI agents"
     Input: CLICKUP_API_KEY → Test → ✅/❌

   Hume AI (hume.ai):
     "Unlocks: emotional voice, 48-dimension emotion detection"
     Input: HUME_API_KEY → Test → ✅/❌

   Perplexity AI (perplexity.ai):
     "Unlocks: cited real-time web answers"
     Input: PERPLEXITY_API_KEY → Test → ✅/❌

   DeepSeek API (api.deepseek.com):
     "Unlocks: cloud-powered deep reasoning for complex tasks"
     Input: DEEPSEEK_API_KEY → Test → ✅/❌

   Home Assistant:
     "Unlocks: smart home control"
     Input: URL + TOKEN → Test → ✅/❌

   (Show others: CrowdStrike, Cybersixgill, etc. as ADVANCED)

5. PERMISSION DEFAULTS:
   "Which actions should always ask permission?"
   Show checklist → user sets trusted/blocked actions

6. HEALTH SETUP:
   "Would you like daily health check-ins?" Y/N
   "Set reminder times?" → configure schedule

7. FINAL CHECK:
   Show dashboard:
   🧠 Brain: Ollama (llama3.3, deepseek-r1, qwen3) ✅
   💾 Memory: ChromaDB ✅
   📚 Knowledge: Recall 2.0 [✅/❌] | Saner [✅/❌]
   📋 Tasks: ClickUp [✅/❌] | Local ✅
   🎙️ Voice: Whisper ✅ | Hume [✅/❌]
   🔐 Security: LLM Guard ✅ | NeMo ✅
   🏠 Home: Home Assistant [✅/❌]

8. COMPLETION:
   "HoneyBadger is ready! Welcome, [name]! 💛
    Type 'help' to see everything I can do."
   Launch main UI

FINAL POLISH:
  - Error handling on EVERY function (try/except)
  - Never crash — always recover with warm message
  - All errors logged to honeybadger_outputs/logs/error_log.txt
  - Performance: voice in background thread
  - Performance: web search async
  - Performance: memory operations async
  - Weekly automatic security audit (Garak)
  - Weekly automatic backup of all data
  - README.md with complete installation guide

COMPLETE VOICE COMMAND LIST (add to README):
  "Hey HoneyBadger" → wake up
  "Teach me [topic]" → full lesson
  "Generate image of [X]" → create image
  "Build me a [website/app]" → create it
  "What do you know about [topic]?" → search knowledge
  "Add task: [description]" → add to all systems
  "What's pending?" → show all tasks
  "Good morning/night" → briefing/sleep summary
  "Scan my network" → security scan
  "What do you see?" → camera analysis
  "HoneyBadger lockdown" → emergency protection
  "HoneyBadger STOP" → stop all hardware
  "How am I feeling today?" → wellness check
  "Research [topic]" → deep research report
  "Analyze [file]" → data analysis
```

---

# 📊 FINAL CHECKLIST

```
✅ Ollama + All local models running
✅ Brain Router selecting correct model
✅ LLM Guard + NeMo Guardrails active
✅ Permission system on ALL actions
✅ ChromaDB single permanent session
✅ Recall 2.0 synced and searching
✅ Saner.ai notes and calendar synced
✅ ClickUp tasks synced
✅ EmoLLM + Hume AI emotion detection
✅ Vocal prosody tracking
✅ Face emotion detection (DeepFace)
✅ Biometric sensor reading (if connected)
✅ Psychological profile building
✅ Casio Moflin (if connected via Bluetooth)
✅ Voice input (Whisper) + output (Hume/ElevenLabs/pyttsx3)
✅ Perplexity + DuckDuckGo search
✅ Recall 2.0 knowledge base
✅ NotebookLM document Q&A
✅ Futures Platform trend research
✅ Image generation working
✅ Website builder working
✅ App builder (all languages) working
✅ CrowdStrike Falcon connected
✅ Cybersixgill dark web monitoring
✅ CloudSEK monitoring
✅ Nessus vulnerability scanning
✅ Burp Suite web testing
✅ PentestGPT ethical hacking
✅ Garak AI self-audit
✅ Darktrace anomaly detection
✅ SentinelOne endpoint protection
✅ Home Assistant smart home control
✅ Alexa+ integration
✅ Google Nest integration
✅ Zapier connecting 6000+ apps
✅ Salesforce Agentforce CRM
✅ Lindy AI employees
✅ Atera IT management
✅ ClickUp Brain project management
✅ Pigment financial modeling
✅ Anaplan connected planning
✅ Futures Platform foresight
✅ Health monitoring + reminders
✅ ROS 2 robot control
✅ LeRobot learning framework
✅ ACT robot skill learning
✅ Hardware control (Arduino/Jetson)
✅ Emergency stop system
✅ WorkOS FGA / Cerbos access control
✅ Glean enterprise search
✅ Dust AI workspace
✅ Document360/Guru knowledge base
✅ Confluence AI search
✅ Strategic foresight (DeepSeek R1)
✅ Full PyQt5 UI (all themes)
✅ Setup wizard complete
✅ All data backed up weekly

🦡 HoneyBadger v3.0 — FULLY OPERATIONAL 💛
```

---
*HoneyBadger v3.0 Master Build Prompt*
*"Not just an AI. YOUR AI. Forever." 💛🦡*
