# Abroad Forum - AI-Powered Q&A System

A Django-based forum application with integrated AI features for intelligent question answering using RAG (Retrieval Augmented Generation) technology.

## 📋 Table of Contents
- [Project Overview](#project-overview)
- [AI Features](#ai-features)
- [Installation & Setup](#installation--setup)
- [AI Content System](#ai-content-system)
- [Database Structure](#database-structure)
- [API Reference](#api-reference)
- [Development Guide](#development-guide)
- [Future Enhancements](#future-enhancements)

## 🎯 Project Overview

Abroad Forum is a comprehensive discussion platform designed for students and professionals seeking guidance on studying abroad. The platform features a sophisticated AI system that can answer questions based on the collective knowledge from all forum discussions.

### Core Features
- **Multi-level threaded discussions** (3 levels deep)
- **Google OAuth integration** for seamless authentication
- **AI-powered content indexing** for RAG implementation
- **Real-time content file generation** for AI processing
- **User reputation system** with badges
- **Rich media support** (images, videos, documents)

### Technology Stack
- **Backend**: Django 4.2.11
- **Database**: SQLite (development) / PostgreSQL (production ready)
- **Authentication**: Google OAuth2 + Django Auth
- **AI Platform**: Google Cloud AI Platform (ready for integration)
- **Frontend**: HTML/CSS/JavaScript with Tailwind CSS
- **File Storage**: Local filesystem + Media files

## 🤖 AI Features

### Current Implementation

#### 1. **Automatic Content Indexing**
- Every post and reply automatically generates a structured text file
- Files are created/updated in real-time using Django signals
- Content is formatted for optimal AI processing

#### 2. **File Generation System**
```
ai_content/
├── post_1_discussion.txt    # Complete discussion thread for post ID 1
├── post_2_discussion.txt    # Complete discussion thread for post ID 2
└── ...
```

#### 3. **Content Structure**
Each generated file contains:
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

### AI System Architecture

#### Components Implemented
1. **AI Utils Module** (`discussion/ai_utils.py`)
   - `generate_post_content_file()` - Creates comprehensive discussion files
   - `update_post_content_file()` - Updates files when content changes
   - `delete_post_content_file()` - Cleans up when posts are deleted

2. **Django Signals** (in `discussion/models.py`)
   - Auto-generates files on post creation
   - Updates files on reply additions
   - Handles all 3 levels of threaded discussions

3. **Management Commands**
   - `python manage.py generate_ai_content` - Generate files for all existing posts
   - `python manage.py generate_ai_content --post-id 123` - Generate for specific post

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8+
- pip
- Virtual environment

### Setup Instructions

1. **Clone and Navigate**
   ```bash
   cd /mnt/CA34A79834A78653/abroad-forum
   ```

2. **Activate Virtual Environment**
   ```bash
   source .venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r req.txt
   ```

4. **Configure Database**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

5. **Generate AI Content Files (for existing posts)**
   ```bash
   python manage.py generate_ai_content
   ```

6. **Run Development Server**
   ```bash
   python manage.py runserver 8001
   ```

### Google OAuth Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to APIs & Services → Credentials
3. Configure OAuth 2.0 Client with these redirect URIs:
   - `http://127.0.0.1:8000/oauth/complete/google-oauth2/`
   - `http://127.0.0.1:8001/oauth/complete/google-oauth2/`
   - `http://localhost:8000/oauth/complete/google-oauth2/`

## 🗃️ Database Structure

### Core Models

#### User Model (`yuzzaz.CustomUser`)
```python
- email (EmailField) - Primary identifier
- username (EmailField) - Uses email
- telephone, profile_picture, gender, bio
- school, grad_year, instagram_username
- Properties: nickname, questions_asked, reputation, badges, answers_posted
```

#### Discussion Models (`discussion.models`)

**Post Model**
```python
- author (ForeignKey to User)
- title, content, tag
- image, image2, video, docs, link
- created_at
- Properties: upvotes, downvotes, replies_list, threaded_replies
```

**Reply Model** (Level 1)
```python
- post (ForeignKey to Post)
- replyier (ForeignKey to User)
- content, tag, media fields
- created_at
```

**ReplytoAReply Model** (Level 2)
```python
- reply (ForeignKey to Reply)
- parent (ForeignKey to self) - for threading
- replyier, content, media fields
```

**ReplyToAnotherReply Model** (Level 3)
```python
- reply (ForeignKey to ReplytoAReply)
- replyier, content, media fields
```

### Interaction Models
- `UserPostInteraction` - Tracks views, upvotes, downvotes on posts
- `ReplyInteraction` - Tracks interactions on replies
- `ReplytoReplyInteraction` - Tracks interactions on nested replies

## 📡 API Reference

### AI Content Management

#### Generate Content Files
```bash
# Generate for all posts
python manage.py generate_ai_content

# Generate for specific post
python manage.py generate_ai_content --post-id 123
```

#### File Locations
- **AI Content Directory**: `ai_content/`
- **File Pattern**: `post_{id}_discussion.txt`

### Django Signals (Automatic)
- `post_save` on Post → Creates/updates content file
- `post_save` on any Reply model → Updates parent post's content file
- `post_delete` on Post → Deletes associated content file

## 💻 Development Guide

### Adding New AI Features

#### 1. Vector Embeddings (Next Step)
```python
# Example implementation location: discussion/ai_embeddings.py
def generate_embeddings(content_file_path):
    # Use Google Cloud AI Platform
    # Generate vector embeddings from text files
    pass

def store_embeddings(post_id, embeddings):
    # Store in database or vector database
    pass
```

#### 2. Semantic Search (Next Step)
```python
# Example implementation location: discussion/ai_search.py
def semantic_search(query, top_k=5):
    # Search through embeddings
    # Return most relevant discussions
    pass
```

#### 3. AI Question Answering (Next Step)
```python
# Example implementation location: discussion/ai_qa.py
def answer_question(question, relevant_contexts):
    # Use Google's Gemini/PaLM API
    # Generate answers based on forum content
    pass
```

### Extending Content Generation

To modify the content file format, edit `discussion/ai_utils.py`:

```python
def generate_post_content_file(post):
    # Modify content_parts list to change format
    # Add new metadata fields
    # Customize threading structure
```

### Adding New Signal Handlers

```python
# In discussion/models.py
@receiver(post_save, sender=YourNewModel)
def handle_new_model_change(sender, instance, created, **kwargs):
    from .ai_utils import update_post_content_file
    # Determine which post to update
    update_post_content_file(post_id)
```

## 🔮 Future Enhancements

### Phase 1: Vector Search (Ready for Implementation)
- [ ] Generate embeddings using Google Cloud AI
- [ ] Implement vector similarity search
- [ ] Add semantic search API endpoints

### Phase 2: AI Question Answering
- [ ] Integrate Google Gemini/PaLM API
- [ ] Build context-aware response system
- [ ] Add citation tracking (which posts/replies informed the answer)

### Phase 3: Advanced Features
- [ ] Real-time AI suggestions while typing
- [ ] Duplicate question detection
- [ ] Automatic post categorization
- [ ] Sentiment analysis on discussions

### Phase 4: Optimization
- [ ] Move to vector database (Pinecone/Weaviate)
- [ ] Implement caching for embeddings
- [ ] Add A/B testing for AI responses
- [ ] Performance monitoring and analytics

## 🔧 Configuration

### Environment Variables
```env
# Google AI Platform
GOOGLE_AI_PROJECT_ID=your-project-id
GOOGLE_AI_REGION=us-central1

# Google OAuth
GOOGLE_OAUTH2_KEY=your-oauth-key
GOOGLE_OAUTH2_SECRET=your-oauth-secret
```

### Settings Configuration
```python
# forum/settings.py
AI_CONTENT_DIR = os.path.join(BASE_DIR, 'ai_content')
GOOGLE_AI_PROJECT_ID = os.getenv('GOOGLE_AI_PROJECT_ID')
GOOGLE_AI_REGION = os.getenv('GOOGLE_AI_REGION', 'us-central1')
```

## 📝 Important Notes

### Content File Generation
- Files are generated **AFTER** database commits (using `post_save` signals)
- This ensures data consistency between database and AI content files
- Files are automatically updated when any part of a discussion thread changes

### Performance Considerations
- Current implementation is suitable for moderate traffic
- For high-volume sites, consider:
  - Async file generation using Celery
  - Vector database instead of text files
  - Caching strategies for embeddings

### Security
- AI content files should not be publicly accessible
- Consider implementing rate limiting for AI endpoints
- Validate and sanitize all user inputs before AI processing

## 🤝 Contributing

When adding new AI features:

1. **Follow the established patterns** in `ai_utils.py`
2. **Update Django signals** if new models affect discussions
3. **Add management commands** for batch processing
4. **Update this README** with new features
5. **Test thoroughly** with the existing signal system

## 📞 Support

For technical issues or questions about the AI implementation:
- Check the Django logs for signal execution
- Verify AI content files are being generated in `ai_content/`
- Test with the management command first before relying on signals
- Monitor file permissions and disk space

---

**Last Updated**: August 26, 2025  
**Version**: 1.0 (AI Content Foundation)  
**Next Release**: Vector Embeddings & Semantic Search