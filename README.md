# ForumAbroad — AI-Powered Q&A for Tanzanian Students

A Django-based community platform built for Tanzanian students studying abroad. Features threaded discussions, a Stories section, Google OAuth, and an AI assistant powered by Vertex AI RAG and the Anthropic SDK.

Live at: **tztoabroad.tech**

## Table of Contents
- [Project Overview](#project-overview)
- [Tech Stack](#tech-stack)
- [AI Features](#ai-features)
- [Installation & Setup](#installation--setup)
- [Database Structure](#database-structure)
- [Development Guide](#development-guide)
- [Future Enhancements](#future-enhancements)

## Project Overview

ForumAbroad is a Q&A community where Tanzanian students can ask questions, share stories, and get AI-assisted answers based on collective forum knowledge.

### Core Features
- **Multi-level threaded discussions** (3 levels deep)
- **Stories section** — share and read experiences abroad
- **Google OAuth integration** for seamless authentication
- **AI-powered Q&A** using Vertex AI RAG + Anthropic SDK
- **Real-time content indexing** via Django signals
- **WebSocket support** via Django Channels + Daphne
- **User reputation system** with badges
- **Rich media support** (images, videos, documents)

### App Structure
| App | Responsibility |
|---|---|
| `discussion` | Forum Q&A, Stories |
| `yuzzaz` | Auth, landing page |
| `forum` | Settings, root URLs |

### Key URLs
| Path | Description |
|---|---|
| `/` | Q&A feed (login required) |
| `/about/` | Marketing landing page |
| `/stories/` | Stories list (public) |
| `/stories/<id>/` | Story detail (public) |
| `/stories/create/` | Create story (login required) |
| `/login/`, `/register/` | Auth pages |

## Tech Stack

- **Backend**: Django 4.2, Django Channels 4 (WebSockets), Daphne
- **Database**: MySQL (production) / SQLite (local dev)
- **Authentication**: Google OAuth2 (`social-auth-app-django`)
- **AI**: Google Cloud Vertex AI (RAG), Anthropic SDK, LangSmith
- **Frontend**: Tailwind CSS (forum/dark theme), Bootstrap 5 (auth pages), Alpine.js, HTMX
- **File Storage**: Local filesystem + media files

## AI Features

### Content Indexing (Implemented)

Every post and reply automatically generates a structured text file used as context for the AI assistant.

**File location:** `ai_content/post_{id}_discussion.txt`

**File format:**
```
POST ID: 123
TITLE: How to apply for scholarships in Germany?
AUTHOR: john.doe
TAG: question
CREATED: 2025-08-26 10:30:00
UPVOTES: 15
CONTENT: I'm looking for information about...

================================================================================
DISCUSSION THREAD:

[REPLY by jane.smith at 2025-08-26 11:00:00]
UPVOTES: 8
CONTENT: Here are some great resources...

  └─[REPLY to jane.smith by mark.wilson at 2025-08-26 11:30:00]
    UPVOTES: 3
    CONTENT: Thanks for sharing! I would also add...
```

### AI System Modules

| Module | Purpose |
|---|---|
| `discussion/ai_utils.py` | Generate, update, and delete content files |
| Django signals in `discussion/models.py` | Auto-trigger file generation on save/delete |
| Vertex AI RAG | Retrieve relevant forum context |
| Anthropic SDK | Generate answers from context |
| LangSmith | Tracing and observability |

### Management Commands
```bash
# Generate AI content files for all existing posts
python manage.py generate_ai_content

# Generate for a specific post
python manage.py generate_ai_content --post-id 123
```

## Installation & Setup

### Prerequisites
- Python 3.9+
- MySQL (for production) or SQLite (local dev)
- Node.js (for Tailwind CSS)

### Setup

1. **Clone the repo**
   ```bash
   git clone <repo-url>
   cd abroad-forum
   ```

2. **Activate virtual environment**
   ```bash
   source venv/bin/activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r req.txt
   ```

4. **Install frontend dependencies**
   ```bash
   npm install
   ```

5. **Set environment variables**
   ```env
   GOOGLE_OAUTH2_KEY=your-oauth-key
   GOOGLE_OAUTH2_SECRET=your-oauth-secret
   GOOGLE_AI_PROJECT_ID=your-gcp-project-id
   GOOGLE_AI_REGION=us-central1
   ANTHROPIC_API_KEY=your-anthropic-key
   DB_NAME=your-db-name
   DB_USER=your-db-user
   DB_PASSWORD=your-db-password
   DB_HOST=your-db-host
   ```

6. **Run migrations**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

7. **Generate AI content files (for existing posts)**
   ```bash
   python manage.py generate_ai_content
   ```

8. **Run development server**
   ```bash
   python manage.py runserver 8001
   ```

### Google OAuth Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to APIs & Services → Credentials
3. Configure OAuth 2.0 Client with these redirect URIs:
   - `http://127.0.0.1:8001/oauth/complete/google-oauth2/`
   - `https://tztoabroad.tech/oauth/complete/google-oauth2/`

## Database Structure

### User Model (`yuzzaz.CustomUser`)
```python
- email (EmailField) — primary identifier
- telephone, profile_picture, gender, bio
- school, grad_year, instagram_username
- Properties: nickname, questions_asked, reputation, badges, answers_posted
```

### Discussion Models (`discussion`)

**Post** — top-level question or discussion  
**Reply** — level 1 reply to a post  
**ReplytoAReply** — level 2 (reply to a reply, supports `parent` self-FK for threading)  
**ReplyToAnotherReply** — level 3  

**Interaction models:** `UserPostInteraction`, `ReplyInteraction`, `ReplytoReplyInteraction` — track views, upvotes, downvotes.

## Development Guide

### Django Signals (Automatic AI Indexing)
```python
# In discussion/models.py
@receiver(post_save, sender=Post)      # Creates/updates content file
@receiver(post_save, sender=Reply)     # Updates parent post's file
@receiver(post_delete, sender=Post)    # Deletes content file
```

### Adding a Signal for a New Model
```python
@receiver(post_save, sender=YourNewModel)
def handle_new_model_change(sender, instance, created, **kwargs):
    from .ai_utils import update_post_content_file
    update_post_content_file(post_id)
```

### Performance Notes
- AI file generation happens **after** DB commits (data consistency guaranteed)
- For high traffic, consider async generation with Celery
- WebSocket connections handled by Daphne + Django Channels

## Future Enhancements

### Phase 1 — Vector Search
- [ ] Generate embeddings via Google Cloud AI
- [ ] Vector similarity search
- [ ] Semantic search API endpoints

### Phase 2 — Advanced AI Q&A
- [ ] Context-aware responses with citations (which posts informed the answer)
- [ ] Real-time AI suggestions while typing
- [ ] Duplicate question detection

### Phase 3 — Optimization
- [ ] Move to a vector database (Pinecone / Weaviate)
- [ ] Embedding caching
- [ ] Sentiment analysis on discussions
- [ ] A/B testing for AI responses

## Security Notes
- AI content files must not be publicly accessible
- All user inputs are validated before AI processing
- Rate limiting should be applied to AI endpoints in production

---

**Last Updated**: March 31, 2026  
**Version**: 1.1  
**Stack**: Django 4.2 · MySQL · Vertex AI · Anthropic · Tailwind CSS · HTMX · Alpine.js
