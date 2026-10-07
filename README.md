# ⏱️ Minute AI: AI-Powered Meeting Transcript to Jira Action Item Dashboard

**Minute AI** is an intelligent, cloud-ready web application that transforms raw meeting transcripts into structured, reviewable Jira action items. Built with **Streamlit**, **Groq AI (Whisper Large V3 + LLaMA 3.3)**, **Pydantic**, and **Supabase PostgreSQL (Row Level Security)**, it bridges the gap between meeting discussions and issue tracking workflows.

> **Important**: In this version, Minute AI identifies action items, maps them to configured Jira projects, stores them securely in Supabase, and provides review and export workflows. It **does not** alter or create tickets directly in your live Jira instance.

---

## 🌟 Key Features

1. **User Authentication & Multi-Tenancy**:
   - Secure login and registration powered by **Supabase Auth**.
   - Strict **Row Level Security (RLS)** ensuring users only ever access their own projects, transcripts, and action items.
   - Built-in **Offline / Evaluation Demo Mode** allowing immediate local evaluation without requiring external credentials upfront.

2. **Executive Main Dashboard**:
   - **Dynamic Summary Cards**: Real-time counts of Total Transcripts, Total Action Items, Awaiting Review, Requiring Clarification, Jira Projects, and Approved Tasks.
   - **Interactive Plotly Visualizations**:
     - Action items distribution by Jira project
     - Task breakdown by review status (donut chart)
     - Tasks grouped by priority
     - Meeting extraction activity over time
   - **Recent Meeting Activity**: Click-to-inspect past meetings and extracted tasks.

3. **Multi-Format Transcript Processing**:
   - **5 Input Methods**:
     - Paste raw text
     - Upload `.txt` files
     - Upload `.vtt` (WebVTT subtitle files with cue stripping and speaker tagging)
     - Upload `.srt` (SubRip subtitle files)
     - Upload audio recordings (`.mp3`, `.wav`, `.m4a`, `.ogg`, `.webm`, `.flac`)
   - **Audio Transcription**: High-speed speech-to-text powered by **Groq Whisper Large V3**.
   - **Smart Parser**: Strips timestamps and formatting tags, consolidates speaker turns, and calculates meeting statistics (word count, speaker count, read time).
   - **Duplicate Detection**: Prevents accidental re-processing of duplicate meeting names and dates.

4. **AI-Powered Action Item Extraction & Jira Mapping**:
   - Strict prompt engineering following the **13 extraction rules**:
     - Distinguishes explicit commitments from casual suggestions or general discussion.
     - **No Hallucination**: Assignees, deadlines, priorities, and Jira project keys are strictly left `null` unless explicitly stated in the discussion.
     - Includes verbatim `source_excerpt` for auditability.
     - Flags uncertain items with `clarification_required` and clear reasoning.
   - **Pydantic Validation & Controlled Retry**: Auto-validates output JSON schema; automatically retries with error feedback if the LLM output is malformed.
   - **Semantic Project Classification**: Maps tasks to user-configured Jira projects based on project scope, keywords, and descriptions.

5. **Action Items Management & Human-in-the-Loop Review**:
   - Filter by Jira Project, Assignee, Priority, Review Status, Meeting Name, and Action Type.
   - Global full-text search across titles, descriptions, and excerpts.
   - Quick one-click approval workflows: **Approve**, **Needs Clarification**, **Reject**.
   - Full inline editing of task titles, assignees, deadlines, and project mappings.
   - Export filtered action items to **CSV** and styled **Excel (.xlsx)**.

6. **Transcript History & Safe Reprocessing**:
   - Searchable historical archive of all processed transcripts.
   - Inspect original transcript alongside extracted tasks.
   - Safe **Reprocess** feature that updates action items without creating orphan or duplicate records.

---

## 🏗️ Architecture & Project Structure

```
minute-AI/
├── app.py                             # Streamlit main entrypoint & navigation
├── requirements.txt                   # Production dependencies
├── .env.example                       # Environment configuration template
├── .gitignore                         # Git exclusion rules
├── README.md                          # Documentation & deployment guide
│
├── pages/                             # Streamlit page modules
│   ├── dashboard_page.py              # Main dashboard with Plotly analytics
│   ├── process_transcript_page.py     # Multi-format transcript input & AI pipeline
│   ├── action_items_page.py           # Table, filters, editing, and approvals
│   ├── transcript_history_page.py     # Archive, inspection, and safe reprocessor
│   ├── jira_projects_page.py          # Jira target project management
│   └── settings_page.py               # AI models, threshold slider, profile
│
├── services/                          # Business logic & AI integrations
│   ├── groq_service.py                # Groq API client with JSON mode & retry
│   ├── transcription_service.py       # Groq Whisper Large V3 audio transcription
│   ├── action_extractor.py            # AI prompt pipeline & Pydantic validation
│   ├── project_mapper.py              # Semantic Jira project classification
│   └── export_service.py              # CSV and styled Excel exporter
│
├── database/                          # Supabase PostgreSQL data layer
│   ├── supabase_client.py             # Supabase client factory + Mock storage
│   └── repositories/
│       ├── project_repo.py            # Jira projects CRUD
│       ├── transcript_repo.py         # Transcripts CRUD & duplicate checks
│       ├── action_item_repo.py        # Action items CRUD & dynamic metrics
│       └── profile_repo.py            # User profile data access
│
├── models/                            # Pydantic schemas & data entities
│   ├── action_item.py                 # ActionItemExtraction, Batch, Record
│   ├── jira_project.py                # JiraProjectCreate, Update, Record
│   └── transcript.py                  # TranscriptCreate, Record
│
├── utils/                             # Utilities & helpers
│   ├── transcript_parser.py           # VTT, SRT, and Text parser & cleaner
│   ├── validators.py                  # Audio, text, and project key validators
│   ├── helpers.py                     # Badges, similarity & deduplication
│   └── auth.py                        # Supabase Auth & session manager
│
├── supabase/
│   └── migrations/
│       └── 001_initial_schema.sql     # PostgreSQL tables, RLS policies, triggers
│
├── sample_data/                       # Sample meeting files for evaluation
│   ├── sample_meeting.txt             # Plain text engineering sync
│   ├── sample_meeting.vtt             # WebVTT subtitle meeting transcript
│   └── sample_meeting.srt             # SubRip subtitle meeting transcript
│
└── tests/                             # Comprehensive automated pytest suite
    ├── conftest.py                    # Fixtures and test data
    ├── test_transcript_parser.py      # Text, VTT, and SRT parsing tests
    ├── test_action_extractor.py       # Pydantic schema & retry tests
    ├── test_project_mapper.py         # Semantic classification tests
    ├── test_duplicate_detection.py    # Deduplication & similarity tests
    ├── test_export_service.py         # CSV & Excel export tests
    └── test_database_repositories.py  # Repository CRUD & data isolation tests
```

---

## 🚀 Quickstart & Local Setup

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.11, 3.12, 3.13, 3.14)
- [`uv`](https://github.com/astral-sh/uv) (recommended) or standard `pip`

### 2. Clone and Setup Environment

```bash
cd minute-AI

# Create virtual environment
uv venv .venv
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt
```

*(Or using standard pip: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`)*

### 3. Environment Configuration

Copy the sample environment file:
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```env
# Groq API Credentials
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_TRANSCRIPTION_MODEL=whisper-large-v3
GROQ_LLM_MODEL=llama-3.3-70b-versatile

# Supabase Credentials
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key_here

# App Parameters
CONFIDENCE_THRESHOLD=0.70
DEFAULT_PRIORITY=Medium
```

> 💡 **Tip**: If you do not have Supabase credentials yet, you can still launch Minute AI immediately! The app will automatically run in **Evaluation / Demo Mode** with pre-seeded projects, sample meetings, and local in-memory storage.

### 4. Run the Application

```bash
./run.sh
```
Open your browser to [http://localhost:8000](http://localhost:8000).
- **Modern Minimalist UI**: [http://localhost:8000](http://localhost:8000)
- **Interactive OpenAPI Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 🗄️ Supabase Cloud Database Setup

1. Create a free project at [supabase.com](https://supabase.com).
2. Go to the **SQL Editor** in your Supabase Dashboard.
3. Open `supabase/migrations/001_initial_schema.sql` from this repository.
4. Copy the entire contents, paste into the Supabase SQL Editor, and click **Run**.
5. This creates:
   - `profiles` table linked to `auth.users` with automated signup triggers.
   - `jira_projects` table with uniqueness constraints.
   - `transcripts` table with timestamps and status triggers.
   - `action_items` table with foreign keys and cascading deletes.
   - Complete **Row Level Security (RLS)** policies ensuring user isolation.
   - Optimized indexes for fast dashboard queries.
6. Retrieve your **Project URL** and **Anon Public Key** from **Project Settings > API**, and add them to `.env`.

---

## ☁️ Deployment to Streamlit Community Cloud

Minute AI is ready for one-click deployment on [Streamlit Community Cloud](https://share.streamlit.io):

1. Push your repository to GitHub (e.g. `github.com/your-username/minute-ai`).
2. Log in to Streamlit Community Cloud and click **New App**.
3. Select your repository, branch (`main`), and set the main file path to `app.py`.
4. Under **Advanced Settings > Secrets**, paste your configuration in TOML format:

```toml
GROQ_API_KEY = "gsk_your_groq_api_key"
GROQ_TRANSCRIPTION_MODEL = "whisper-large-v3"
GROQ_LLM_MODEL = "llama-3.3-70b-versatile"

SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_ANON_KEY = "your_supabase_anon_key"
SUPABASE_SERVICE_ROLE_KEY = "your_supabase_service_role_key"

CONFIDENCE_THRESHOLD = 0.70
DEFAULT_PRIORITY = "Medium"
```

5. Click **Deploy**. Streamlit Cloud will install dependencies from `requirements.txt` and launch the app.

---

## 🧪 Running Automated Tests

Run the full pytest suite:

```bash
pytest tests/ -v
```

All 23 unit tests run with mocked Groq and Supabase services, validating:
- Subtitle parsing (`.vtt`, `.srt`, `.txt`) and speaker turn consolidation
- Pydantic schema validation and JSON retry mechanisms
- Non-hallucination of assignees, priorities, and deadlines
- Jira semantic project classification and confidence scoring
- Duplicate action item and duplicate meeting detection
- CSV and styled Excel (`.xlsx`) export generation
- Multi-tenant database repository CRUD and Row Level Security isolation

---

## 📄 License
MIT License. Built for engineering teams converting meeting discussions into actionable Jira tickets.
