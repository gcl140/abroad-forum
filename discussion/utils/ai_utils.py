import os
import json
from datetime import datetime
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from discussion.models import Post, Reply, ReplytoAReply, ReplyToAnotherReply

def create_ai_content_directory():
    """Create directory for AI content files"""
    ai_content_dir = os.path.join(settings.BASE_DIR, 'ai_content')
    os.makedirs(ai_content_dir, exist_ok=True)
    return ai_content_dir

def serialize_user(user):
    """Serialize user data for JSON"""
    return {
        "id": user.id,
        "nickname": user.nickname,
        "email": user.email,
        "reputation": user.reputation,
        "badges": user.badges,
        "school": user.school or "",
        "grad_year": user.grad_year or ""
    }

def serialize_media_fields(obj):
    """Serialize media fields for JSON"""
    media = {}
    if hasattr(obj, 'image') and obj.image:
        media['image'] = obj.image.url
    if hasattr(obj, 'image2') and obj.image2:
        media['image2'] = obj.image2.url
    if hasattr(obj, 'video') and obj.video:
        media['video'] = obj.video.url
    if hasattr(obj, 'docs') and obj.docs:
        media['docs'] = obj.docs.url
    if hasattr(obj, 'link') and obj.link:
        media['link'] = obj.link
    return media

def generate_post_content_file(post):
    """Generate comprehensive discussion JSON file for a post"""
    ai_content_dir = create_ai_content_directory()
    file_path = os.path.join(ai_content_dir, f'post_{post.id}_discussion.json')
    
    # Build the complete discussion data structure
    discussion_data = {
        "post": {
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "tag": post.tag or "",
            "created_at": post.created_at.isoformat(),
            "upvotes": post.upvotes,
            "downvotes": post.downvotes,
            "author": serialize_user(post.author),
            "media": serialize_media_fields(post),
            "metadata": {
                "replies_count": post.replies.count(),
                "total_interactions": post.upvotes + post.downvotes,
                "discussion_depth": 0  # Will be calculated
            }
        },
        "discussion_thread": [],
        "ai_metadata": {
            "generated_at": datetime.now().isoformat(),
            "content_type": "forum_discussion",
            "discussion_levels": 3,
            "total_participants": set(),
            "topics_discussed": [],
            "content_summary": {
                "total_words": len(post.content.split()) if post.content else 0,
                "has_links": bool(post.link),
                "has_media": any([post.image, post.image2, post.video, post.docs]) if hasattr(post, 'image') else False
            }
        }
    }
    
    participants = {post.author.id}
    max_depth = 1
    total_words = len(post.content.split()) if post.content else 0
    
    # Level 1 Replies (Direct to Post)
    for reply in post.replies.all().order_by('created_at'):
        participants.add(reply.replyier.id)
        reply_words = len(reply.content.split()) if reply.content else 0
        total_words += reply_words
        
        reply_data = {
            "id": reply.id,
            "content": reply.content,
            "author": serialize_user(reply.replyier),
            "created_at": reply.created_at.isoformat(),
            "upvotes": reply.upvotes,
            "downvotes": reply.downvotes,
            "level": 1,
            "parent_type": "post",
            "parent_id": post.id,
            "media": serialize_media_fields(reply),
            "replies": []
        }
        
        # Level 2 Replies (Replies to Replies)
        for reply2 in reply.replies_to_reply.all().order_by('created_at'):
            participants.add(reply2.replyier.id)
            reply2_words = len(reply2.content.split()) if reply2.content else 0
            total_words += reply2_words
            max_depth = max(max_depth, 2)
            
            reply2_data = {
                "id": reply2.id,
                "content": reply2.content,
                "author": serialize_user(reply2.replyier),
                "created_at": reply2.created_at.isoformat(),
                "upvotes": reply2.upvotes,
                "downvotes": reply2.downvotes,
                "level": 2,
                "parent_type": "reply",
                "parent_id": reply.id,
                "replied_to": reply2.repliedto,
                "media": serialize_media_fields(reply2),
                "replies": []
            }
            
            # Level 3 Replies (Replies to Level 2 Replies)
            for reply3 in reply2.replies_to_another_reply.all().order_by('created_at'):
                participants.add(reply3.replyier.id)
                reply3_words = len(reply3.content.split()) if reply3.content else 0
                total_words += reply3_words
                max_depth = max(max_depth, 3)
                
                reply3_data = {
                    "id": reply3.id,
                    "content": reply3.content,
                    "author": serialize_user(reply3.replyier),
                    "created_at": reply3.created_at.isoformat(),
                    "upvotes": reply3.upvotes,
                    "downvotes": reply3.downvotes,
                    "level": 3,
                    "parent_type": "reply_to_reply",
                    "parent_id": reply2.id,
                    "media": serialize_media_fields(reply3)
                }
                
                reply2_data["replies"].append(reply3_data)
            
            reply_data["replies"].append(reply2_data)
        
        discussion_data["discussion_thread"].append(reply_data)
    
    # Update AI metadata
    discussion_data["post"]["metadata"]["discussion_depth"] = max_depth
    discussion_data["ai_metadata"]["total_participants"] = list(participants)
    discussion_data["ai_metadata"]["participants_count"] = len(participants)
    discussion_data["ai_metadata"]["content_summary"]["total_words"] = total_words
    discussion_data["ai_metadata"]["content_summary"]["discussion_depth"] = max_depth
    discussion_data["ai_metadata"]["content_summary"]["total_replies"] = len(discussion_data["discussion_thread"])
    
    # Extract topics/tags mentioned
    topics = set()
    if post.tag:
        topics.add(post.tag)
    discussion_data["ai_metadata"]["topics_discussed"] = list(topics)
    
    # Write JSON file
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(discussion_data, f, indent=2, ensure_ascii=False, cls=DjangoJSONEncoder)
    
    return file_path

def update_post_content_file(post_id):
    """Update content file when post or replies change"""
    try:
        post = Post.objects.get(id=post_id)
        return generate_post_content_file(post)
    except Post.DoesNotExist:
        return None

def delete_post_content_file(post_id):
    """Delete content file when post is deleted"""
    ai_content_dir = create_ai_content_directory()
    file_path = os.path.join(ai_content_dir, f'post_{post_id}_discussion.json')
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False

def sync_post_to_rag(post_id):
    """Generate local JSON file then upload to Vertex AI RAG corpus"""
    import logging
    logger = logging.getLogger(__name__)
    try:
        # Step 1: regenerate local JSON
        file_path = update_post_content_file(post_id)
        if not file_path:
            logger.warning(f"sync_post_to_rag: no local file generated for post {post_id}")
            return False
        # Step 2: upload to RAG
        from discussion.utils.ai_rag import get_rag_manager
        rag_manager = get_rag_manager()
        result = rag_manager.upload_post_file(post_id)
        if result:
            logger.info(f"sync_post_to_rag: post {post_id} synced to RAG")
            return True
        else:
            logger.error(f"sync_post_to_rag: upload failed for post {post_id}")
            return False
    except Exception as e:
        logger.error(f"sync_post_to_rag: error for post {post_id}: {e}")
        return False

def remove_post_from_rag(post_id):
    """Remove post from Vertex AI RAG corpus and delete local file"""
    import logging
    logger = logging.getLogger(__name__)
    try:
        from discussion.utils.ai_rag import get_rag_manager
        rag_manager = get_rag_manager()
        rag_manager.remove_post_from_corpus(post_id)
    except Exception as e:
        logger.error(f"remove_post_from_rag: error for post {post_id}: {e}")
        # Still delete local file even if RAG removal fails
        delete_post_content_file(post_id)

def get_discussion_summary(post_id):
    """Get a summary of the discussion for AI processing"""
    ai_content_dir = create_ai_content_directory()
    file_path = os.path.join(ai_content_dir, f'post_{post_id}_discussion.json')
    
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return {
            "post_id": post_id,
            "title": data["post"]["title"],
            "participants_count": data["ai_metadata"]["participants_count"],
            "total_words": data["ai_metadata"]["content_summary"]["total_words"],
            "replies_count": data["ai_metadata"]["content_summary"]["total_replies"],
            "discussion_depth": data["ai_metadata"]["content_summary"]["discussion_depth"],
            "topics": data["ai_metadata"]["topics_discussed"],
            "created_at": data["post"]["created_at"]
        }
    return None

def extract_text_for_ai(post_id):
    """Extract plain text content for AI processing (embeddings, etc.)"""
    ai_content_dir = create_ai_content_directory()
    file_path = os.path.join(ai_content_dir, f'post_{post_id}_discussion.json')
    
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract all text content for AI processing
        text_parts = []
        
        # Main post
        text_parts.append(f"Title: {data['post']['title']}")
        text_parts.append(f"Content: {data['post']['content']}")
        
        # All replies
        def extract_replies(replies, level=1):
            for reply in replies:
                text_parts.append(f"Reply (Level {level}): {reply['content']}")
                if reply.get('replies'):
                    extract_replies(reply['replies'], level + 1)
        
        extract_replies(data['discussion_thread'])
        
        return "\n\n".join(text_parts)
    
    return None