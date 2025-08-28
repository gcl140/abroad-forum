import os
import json
import hashlib
import logging
import time
from datetime import datetime
from django.conf import settings
from dotenv import load_dotenv
from vertexai import rag, init as vertexai_init
from vertexai.generative_models import GenerativeModel, Tool
from .models import Post, AIRagFile, AIRagCorpusStats

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class EnhancedRAGManager:
    """Enhanced RAG Manager with file mapping and update tracking"""
    
    def __init__(self):
        self.project_id = os.getenv('PROJECT_ID')
        self.location = os.getenv('LOCATION')
        self.corpus_id = os.getenv('RAG_CORPUS_ID')
        self.corpus_name = f"projects/{self.project_id}/locations/{self.location}/ragCorpora/{self.corpus_id}"
        
        # Initialize Vertex AI
        vertexai_init(project=self.project_id, location=self.location)
        
        # Ensure corpus stats record exists
        self.corpus_stats, _ = AIRagCorpusStats.objects.get_or_create(
            corpus_id=self.corpus_id,
            defaults={'total_files': 0, 'total_posts_indexed': 0}
        )
    
    def calculate_file_hash(self, file_path):
        """Calculate SHA256 hash of file content"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def convert_json_to_text(self, json_file_path):
        """Keep JSON structure but save as .txt file for RAG upload"""
        with open(json_file_path, 'r', encoding='utf-8') as f:
            json_content = f.read()  # Read the raw JSON as text
        
        # Return the JSON content as-is (but it will be saved as .txt)
        return json_content
    
    def upload_post_file(self, post_id):
        """Upload a single post's discussion file to RAG corpus"""
        try:
            # Check if post exists
            try:
                post = Post.objects.get(id=post_id)
            except Post.DoesNotExist:
                logger.error(f"Post {post_id} not found in database")
                return None
            
            # Prepare file paths
            ai_content_dir = os.path.join(settings.BASE_DIR, 'ai_content')
            json_file_path = os.path.join(ai_content_dir, f'post_{post_id}_discussion.json')
            
            if not os.path.exists(json_file_path):
                logger.error(f"JSON file not found: {json_file_path}")
                return None
            
            # Calculate file hash
            current_hash = self.calculate_file_hash(json_file_path)
            
            # Check if file already uploaded and unchanged
            existing_file = AIRagFile.objects.filter(post_id=post_id).first()
            if existing_file and existing_file.file_hash == current_hash and existing_file.is_uploaded:
                logger.info(f"Post {post_id} already uploaded and unchanged, skipping...")
                return existing_file
            
            # Convert to text format
            text_content = self.convert_json_to_text(json_file_path)
            
            # Create temporary text file
            temp_text_file = os.path.join(ai_content_dir, f'post_{post_id}_rag_temp.txt')
            with open(temp_text_file, 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            try:
                # If file exists in RAG, delete it first
                if existing_file and existing_file.is_uploaded:
                    try:
                        rag.delete_file(name=existing_file.rag_file_name)
                        logger.info(f"Deleted existing RAG file for post {post_id}")
                    except Exception as e:
                        logger.warning(f"Could not delete existing file: {str(e)}")
                
                # Upload to Vertex AI RAG
                rag_file = rag.upload_file(
                    corpus_name=self.corpus_name,
                    path=temp_text_file,
                    display_name=f"post_{post_id}_discussion",
                    description=f"Forum discussion for post {post_id}: {post.title[:100]}"
                )
                
                # Extract file ID from the response
                rag_file_id = rag_file.name.split('/')[-1]
                
                # Save or update file record
                file_record, created = AIRagFile.objects.update_or_create(
                    post_id=post_id,
                    defaults={
                        'rag_file_name': rag_file.name,
                        'rag_file_id': rag_file_id,
                        'display_name': rag_file.display_name,
                        'local_file_path': json_file_path,
                        'file_size': os.path.getsize(temp_text_file),
                        'file_hash': current_hash,
                        'is_uploaded': True,
                        'needs_update': False,
                        'last_sync_error': ''
                    }
                )
                
                # Clean up temp file
                os.remove(temp_text_file)
                
                logger.info(f"✅ {'Updated' if not created else 'Uploaded'} post {post_id} -> {rag_file_id}")
                return file_record
                
            except Exception as e:
                # Clean up temp file on error
                if os.path.exists(temp_text_file):
                    os.remove(temp_text_file)
                
                # Update error status
                if existing_file:
                    existing_file.last_sync_error = str(e)
                    existing_file.needs_update = True
                    existing_file.save()
                
                logger.error(f"❌ Failed to upload post {post_id}: {str(e)}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error processing post {post_id}: {str(e)}")
            return None
    
    def upload_all_posts(self, force_update=False):
        """Upload all discussion files to RAG corpus"""
        posts = Post.objects.all()
        results = {
            'uploaded': [],
            'updated': [],
            'failed': [],
            'skipped': []
        }
        
        logger.info(f"Starting upload of {posts.count()} posts...")
        
        for post in posts:
            try:
                existing_file = AIRagFile.objects.filter(post_id=post.id).first()
                
                # Skip if already uploaded and not forcing update
                if not force_update and existing_file and existing_file.is_uploaded and not existing_file.needs_update:
                    results['skipped'].append(post.id)
                    continue
                
                file_record = self.upload_post_file(post.id)
                
                if file_record:
                    if existing_file:
                        results['updated'].append(post.id)
                    else:
                        results['uploaded'].append(post.id)
                else:
                    results['failed'].append(post.id)
                    
            except Exception as e:
                logger.error(f"Error processing post {post.id}: {str(e)}")
                results['failed'].append(post.id)
        
        # Update corpus stats
        self.update_corpus_stats()
        
        return results
    
    def check_for_updates(self):
        """Check which files need updates based on file hash changes"""
        ai_content_dir = os.path.join(settings.BASE_DIR, 'ai_content')
        files_needing_update = []
        
        for file_record in AIRagFile.objects.filter(is_uploaded=True):
            json_file_path = os.path.join(ai_content_dir, f'post_{file_record.post_id}_discussion.json')
            
            if os.path.exists(json_file_path):
                current_hash = self.calculate_file_hash(json_file_path)
                if current_hash != file_record.file_hash:
                    file_record.needs_update = True
                    file_record.save()
                    files_needing_update.append(file_record.post_id)
            else:
                # File doesn't exist locally, mark for investigation
                file_record.needs_update = True
                file_record.last_sync_error = "Local JSON file not found"
                file_record.save()
        
        return files_needing_update
    
    def sync_updated_files(self):
        """Sync files that have been marked as needing updates"""
        files_to_update = AIRagFile.objects.filter(needs_update=True)
        results = {'updated': [], 'failed': []}
        
        for file_record in files_to_update:
            updated_record = self.upload_post_file(file_record.post_id)
            if updated_record and not updated_record.needs_update:
                results['updated'].append(file_record.post_id)
            else:
                results['failed'].append(file_record.post_id)
        
        return results
    
    def update_corpus_stats(self):
        """Update corpus statistics"""
        total_files = AIRagFile.objects.filter(is_uploaded=True).count()
        self.corpus_stats.total_files = total_files
        self.corpus_stats.total_posts_indexed = total_files
        self.corpus_stats.last_full_sync_at = datetime.now()
        self.corpus_stats.save()
    
    def query_discussions(self, question, top_k=5, threshold=0.3):
        """Query RAG corpus for relevant discussions"""
        try:
            response = rag.retrieval_query(
                rag_resources=[
                    rag.RagResource(rag_corpus=self.corpus_name)
                ],
                text=question,
                rag_retrieval_config=rag.RagRetrievalConfig(
                    top_k=top_k,
                    filter=rag.utils.resources.Filter(vector_distance_threshold=threshold),
                ),
            )
            return response
        except Exception as e:
            logger.error(f"Error querying RAG corpus: {str(e)}")
            raise
    
    def debug_corpus_status(self):
        """Debug method to check corpus status and content"""
        debug_info = {
            'corpus_name': self.corpus_name,
            'project_id': self.project_id,
            'location': self.location,
            'corpus_id': self.corpus_id,
            'local_files_count': 0,
            'db_files_count': 0,
            'rag_files_count': 0,
            'sample_retrieval': None,
            'errors': []
        }
        
        try:
            # Check local JSON files
            ai_content_dir = os.path.join(settings.BASE_DIR, 'ai_content')
            if os.path.exists(ai_content_dir):
                json_files = [f for f in os.listdir(ai_content_dir) if f.endswith('.json')]
                debug_info['local_files_count'] = len(json_files)
                debug_info['local_files'] = json_files[:5]  # First 5 files
            
            # Check database records
            debug_info['db_files_count'] = AIRagFile.objects.filter(is_uploaded=True).count()
            
            # Try to list RAG files
            try:
                rag_files = rag.list_files(corpus_name=self.corpus_name)
                rag_files_list = list(rag_files)  # Convert pager to list
                debug_info['rag_files_count'] = len(rag_files_list)
                debug_info['rag_files'] = [(f.display_name, f.name) for f in rag_files_list[:3]]
            except Exception as e:
                debug_info['errors'].append(f"Failed to list RAG files: {str(e)}")
            
            # Test basic retrieval
            try:
                test_response = rag.retrieval_query(
                    rag_resources=[
                        rag.RagResource(rag_corpus=self.corpus_name)
                    ],
                    text="university admission",
                    rag_retrieval_config=rag.RagRetrievalConfig(
                        top_k=3,
                        filter=rag.utils.resources.Filter(vector_distance_threshold=0.8),  # More lenient
                    ),
                )
                if hasattr(test_response, 'contexts') and test_response.contexts:
                    debug_info['sample_retrieval'] = f"Found {len(test_response.contexts.contexts)} contexts"
                else:
                    debug_info['sample_retrieval'] = "No contexts found in retrieval"
            except Exception as e:
                debug_info['errors'].append(f"Failed retrieval test: {str(e)}")
            
        except Exception as e:
            debug_info['errors'].append(f"General error: {str(e)}")
        
        return debug_info

    def generate_ai_answer(self, question, model_name="gemini-2.5-flash"):
        """Generate AI answer using RAG-enhanced model"""
        try:
            # First, test direct retrieval to see what content we have
            try:
                test_retrieval = rag.retrieval_query(
                    rag_resources=[rag.RagResource(rag_corpus=self.corpus_name)],
                    text=question,
                    rag_retrieval_config=rag.RagRetrievalConfig(
                        top_k=5,
                        filter=rag.utils.resources.Filter(vector_distance_threshold=0.7),
                    ),
                )
                
                # Extract content from retrieval for logging
                if hasattr(test_retrieval, 'contexts') and test_retrieval.contexts:
                    retrieved_content = []
                    for context in test_retrieval.contexts.contexts:
                        retrieved_content.append(context.text[:200] + "...")
                    logger.info(f"Retrieved {len(retrieved_content)} contexts for question: {question}")
                    logger.info(f"Sample context: {retrieved_content[0] if retrieved_content else 'None'}")
                else:
                    logger.warning(f"No contexts retrieved for question: {question}")
                    
            except Exception as e:
                logger.error(f"Direct retrieval test failed: {e}")
            
            # Create RAG-enhanced model with more aggressive retrieval
            rag_retrieval_tool = Tool.from_retrieval(
                retrieval=rag.Retrieval(
                    source=rag.VertexRagStore(
                        rag_resources=[rag.RagResource(rag_corpus=self.corpus_name)],
                        rag_retrieval_config=rag.RagRetrievalConfig(
                            top_k=10,
                            filter=rag.utils.resources.Filter(vector_distance_threshold=0.5),  # More lenient
                        ),
                    ),
                )
            )
            
            rag_model = GenerativeModel(
                model_name=model_name, 
                tools=[rag_retrieval_tool]
            )
            
            # Enhanced anti-hallucination prompt with greeting detection
            enhanced_prompt = f"""You are an AI assistant for ForumAbroad, a community forum for Tanzanian students studying abroad.

STEP 1 - GREETING AND INTENT DETECTION:
First, analyze the user's input to determine if it's:
1. A GREETING (hi, hello, hey, good morning, what's up, how are you, etc.)
2. A VAGUE REQUEST (help, help me, advice, tips, guidance, what should I do, etc.)
3. A SUBSTANTIVE QUESTION about studying abroad

User's input: "{question}"

RESPONSE RULES BY INPUT TYPE:

IF IT'S A GREETING:
- DO NOT use the retrieval tool to search for the literal greeting words
- Respond with a warm welcome message
- Introduce yourself as the ForumAbroad AI assistant
- Ask them what they'd like to know about studying abroad
- Suggest specific topic areas they can ask about (admissions, scholarships, visas, etc.)
- DO NOT search for or mention forum posts that contain greeting words

IF IT'S A VAGUE REQUEST FOR HELP:
- DO NOT use retrieval tool for overly general terms
- Provide a helpful response asking for more specificity
- List specific areas you can help with
- Encourage them to ask a more detailed question

IF IT'S A SUBSTANTIVE QUESTION:
- ALWAYS use the retrieval tool to search our forum discussions FIRST
- Follow the anti-hallucination rules below

CRITICAL ANTI-HALLUCINATION RULES FOR SUBSTANTIVE QUESTIONS:
1. ALWAYS use the retrieval tool to search our forum discussions FIRST
2. If you find relevant discussions in the retrieval results, cite them directly and use ONLY that information
3. NEVER make up fake community members, usernames, or specific posts that don't exist in the retrieval results
4. NEVER invent quotes, conversations, or experiences that aren't in the actual retrieved content
5. If the retrieval tool returns no relevant content or empty results, you MUST be honest about it

RESPONSE FORMAT FOR SUBSTANTIVE QUESTIONS:

IF RETRIEVAL FINDS RELEVANT CONTENT:
Start with: "Based on our forum discussions, here's what I found..."
- Use only information from the actual retrieved content
- Reference specific posts or users ONLY if they appear in the retrieval results
- Quote or paraphrase actual content from the retrieved discussions

IF NO RELEVANT CONTENT IS FOUND:
Start with: "I searched our forum discussions but didn't find specific content about this topic. However, I can provide some general guidance..."
- Be completely honest that no forum content was found
- Provide helpful general advice about studying abroad
- Suggest that the user post their question in the forum for community input

ABSOLUTELY FORBIDDEN:
- Searching for greeting words like "hi", "hello", "hey" in forum discussions
- Creating fake usernames like "TzScholar", "MimiAbroad", "JifunzeAbroad" etc.
- Inventing specific posts, quotes, or user experiences
- Making up detailed scenarios that sound like they come from the forum
- Pretending to have access to discussions that don't exist in the retrieval results

Remember: For greetings, be warm and welcoming without searching the forum. For substantive questions, honesty about sources is more important than sounding knowledgeable. It's better to admit you don't have specific forum content than to make it up."""
            
            response = rag_model.generate_content(enhanced_prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating AI answer: {str(e)}")
            # Fallback to direct model without RAG
            try:
                fallback_model = GenerativeModel(model_name="gemini-1.5-flash")
                fallback_response = fallback_model.generate_content(f"""
                You are an AI assistant for a studying abroad forum. A user said: {question}
                
                If this is a greeting (hi, hello, hey, etc.), respond warmly and ask what they'd like to know about studying abroad.
                If it's a substantive question, be completely honest that you're experiencing technical difficulties and cannot access the forum discussions. 
                Provide helpful general advice about studying abroad, but clearly state it's general knowledge, not from the forum community.
                Do NOT make up fake forum members or specific discussions.
                """)
                return f"⚠️ **Technical Issue**: I'm having trouble accessing our forum discussions right now.\n\n{fallback_response.text}"
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
                return f"I'm sorry, I'm experiencing technical difficulties right now. Please try again later or post your question in the forum for community help!"

    def get_file_mapping(self, post_id):
        """Get RAG file mapping for a specific post"""
        try:
            return AIRagFile.objects.get(post_id=post_id, is_uploaded=True)
        except AIRagFile.DoesNotExist:
            return None
    
    def list_all_rag_files(self):
        """List all files in the RAG corpus"""
        try:
            files = rag.list_files(corpus_name=self.corpus_name)
            return [(f.display_name, f.name) for f in files]
        except Exception as e:
            logger.error(f"Error listing RAG files: {str(e)}")
            return []
    
    def list_rag_files(self):
        """Alias for list_all_rag_files for compatibility"""
        return self.list_all_rag_files()
    
    def delete_rag_file(self, file_name):
        """Delete a specific RAG file by its full name"""
        try:
            rag.delete_file(name=file_name)
            logger.info(f"✅ Deleted RAG file: {file_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to delete RAG file {file_name}: {e}")
            raise e
    
    def generate_discussion_data_for_post(self, post):
        """Generate discussion data structure for a post"""
        from .models import Reply, ReplytoAReply
        
        # Get all replies for this post
        replies = Reply.objects.filter(post=post).order_by('created_at')
        
        post_data = {
            "post": {
                "id": post.id,
                "title": post.title,
                "content": post.content,
                "tag": post.tag,
                "created_at": post.created_at.isoformat(),
                "upvotes": post.upvotes,
                "downvotes": post.downvotes,
                "author": {
                    "id": post.author.id,
                    "nickname": post.author.nickname,
                    "email": post.author.email,
                    "reputation": getattr(post.author, 'reputation', 0),
                    "badges": getattr(post.author, 'badges', ["Newbie"]),
                    "school": getattr(post.author, 'school', ""),
                    "grad_year": getattr(post.author, 'grad_year', "")
                },
                "media": {
                    "has_image": bool(post.image),
                    "has_image2": bool(post.image2),
                    "has_video": bool(post.video),
                    "has_docs": bool(post.docs),
                    "has_link": bool(post.link)
                },
                "metadata": {
                    "replies_count": replies.count(),
                    "total_interactions": post.upvotes + post.downvotes,
                    "discussion_depth": 1 if replies.exists() else 0
                }
            },
            "discussion_thread": [],
            "ai_metadata": {
                "generated_at": datetime.now().isoformat(),
                "content_type": "forum_discussion",
                "discussion_levels": 3,
                "total_participants": list(set([post.author.id] + list(replies.values_list('replyier_id', flat=True)))),
                "topics_discussed": [post.tag] if post.tag else [],
                "content_summary": {
                    "total_words": len(post.content.split()) + sum(len(r.content.split()) for r in replies),
                    "has_links": 'http' in post.content or any('http' in r.content for r in replies),
                    "has_media": bool(post.image or post.image2) or any(r.image or r.image2 for r in replies),
                    "discussion_depth": 1 if replies.exists() else 0,
                    "total_replies": replies.count()
                },
                "participants_count": len(set([post.author.id] + list(replies.values_list('replyier_id', flat=True))))
            }
        }
        
        # Add replies to discussion thread
        for reply in replies:
            # Get nested replies (ReplytoAReply)
            nested_replies = ReplytoAReply.objects.filter(reply=reply).order_by('created_at')
            
            nested_reply_data = []
            for nested_reply in nested_replies:
                nested_data = {
                    "id": nested_reply.id,
                    "content": nested_reply.content,
                    "author": {
                        "id": nested_reply.replyier.id,
                        "nickname": nested_reply.replyier.nickname,
                        "email": nested_reply.replyier.email,
                        "reputation": getattr(nested_reply.replyier, 'reputation', 0),
                    },
                    "created_at": nested_reply.created_at.isoformat(),
                    "upvotes": nested_reply.upvotes,
                    "downvotes": nested_reply.downvotes,
                    "level": 2,
                    "media": {
                        "has_image": bool(nested_reply.image),
                        "has_video": bool(nested_reply.video),
                        "has_docs": bool(nested_reply.docs),
                        "has_link": bool(nested_reply.link)
                    }
                }
                nested_reply_data.append(nested_data)
            
            reply_data = {
                "id": reply.id,
                "content": reply.content,
                "author": {
                    "id": reply.replyier.id,
                    "nickname": reply.replyier.nickname,
                    "email": reply.replyier.email,
                    "reputation": getattr(reply.replyier, 'reputation', 0),
                    "badges": getattr(reply.replyier, 'badges', ["Newbie"]),
                    "school": getattr(reply.replyier, 'school', ""),
                    "grad_year": getattr(reply.replyier, 'grad_year', "")
                },
                "created_at": reply.created_at.isoformat(),
                "upvotes": reply.upvotes,
                "downvotes": reply.downvotes,
                "level": 1,
                "media": {
                    "has_image": bool(reply.image),
                    "has_image2": bool(reply.image2),
                    "has_video": bool(reply.video),
                    "has_docs": bool(reply.docs),
                    "has_link": bool(reply.link)
                },
                "nested_replies": nested_reply_data
            }
            post_data["discussion_thread"].append(reply_data)
        
        return post_data
    
    def save_discussion_json(self, post_id, post_data):
        """Save discussion data to JSON file"""
        ai_content_dir = os.path.join(settings.BASE_DIR, 'ai_content')
        
        # Create ai_content directory if it doesn't exist
        os.makedirs(ai_content_dir, exist_ok=True)
        
        json_file_path = os.path.join(ai_content_dir, f'post_{post_id}_discussion.json')
        
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(post_data, f, indent=2, ensure_ascii=False)
        
        return json_file_path
    
    def update_corpus_with_new_post(self, post):
        """Add new post to RAG corpus immediately after creation"""
        try:
            logger.info(f"🔄 Updating RAG corpus with new post {post.id}: {post.title}")
            
            # Generate discussion data for the new post
            post_data = self.generate_discussion_data_for_post(post)
            
            # Save to JSON file
            json_file_path = self.save_discussion_json(post.id, post_data)
            
            # Upload to RAG corpus
            file_record = self.upload_post_file(post.id)
            
            if file_record:
                logger.info(f"✅ Successfully added post {post.id} to RAG corpus")
                # Update corpus stats
                self.update_corpus_stats()
                return True
            else:
                logger.error(f"❌ Failed to add post {post.id} to RAG corpus")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to update RAG corpus with new post {post.id}: {e}")
            return False
    
    def update_corpus_with_new_reply(self, reply):
        """Update RAG corpus when new reply is added"""
        try:
            logger.info(f"🔄 Updating RAG corpus with new reply for post {reply.parent_id}")
            
            # Get the parent post to rebuild the discussion
            if reply.parent_type == 'post':
                from .models import Post
                try:
                    post = Post.objects.get(id=reply.parent_id)
                    
                    # Regenerate discussion data with the new reply
                    post_data = self.generate_discussion_data_for_post(post)
                    
                    # Save updated JSON
                    json_file_path = self.save_discussion_json(post.id, post_data)
                    
                    # Re-upload to RAG corpus (this will update the existing file)
                    file_record = self.upload_post_file(post.id)
                    
                    if file_record:
                        logger.info(f"✅ Successfully updated post {post.id} discussion in RAG corpus")
                        return True
                    else:
                        logger.error(f"❌ Failed to update post {post.id} discussion in RAG corpus")
                        return False
                        
                except Post.DoesNotExist:
                    logger.error(f"Parent post {reply.parent_id} not found")
                    return False
            else:
                logger.warning(f"Reply parent type {reply.parent_type} not supported for RAG updates")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to update RAG corpus with new reply: {e}")
            return False
    
    def remove_post_from_corpus(self, post_id):
        """Remove a post from RAG corpus (e.g., when post is deleted)"""
        try:
            logger.info(f"🗑️ Removing post {post_id} from RAG corpus")
            
            # Get existing file record
            existing_file = AIRagFile.objects.filter(post_id=post_id, is_uploaded=True).first()
            
            if existing_file:
                # Delete from Vertex AI RAG
                try:
                    rag.delete_file(name=existing_file.rag_file_name)
                    logger.info(f"✅ Deleted RAG file for post {post_id}")
                except Exception as e:
                    logger.warning(f"Could not delete RAG file: {str(e)}")
                
                # Mark as not uploaded in database
                existing_file.is_uploaded = False
                existing_file.last_sync_error = "Post deleted from forum"
                existing_file.save()
                
                # Delete local JSON file if it exists
                ai_content_dir = os.path.join(settings.BASE_DIR, 'ai_content')
                json_file_path = os.path.join(ai_content_dir, f'post_{post_id}_discussion.json')
                if os.path.exists(json_file_path):
                    os.remove(json_file_path)
                
                # Update corpus stats
                self.update_corpus_stats()
                
                return True
            else:
                logger.info(f"Post {post_id} was not in RAG corpus")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to remove post {post_id} from RAG corpus: {e}")
            return False

    def extract_sources_from_retrieval(self, question, top_k=5):
        """Extract source information from RAG retrieval for reference links"""
        try:
            retrieval_response = rag.retrieval_query(
                rag_resources=[rag.RagResource(rag_corpus=self.corpus_name)],
                text=question,
                rag_retrieval_config=rag.RagRetrievalConfig(
                    top_k=top_k,
                    filter=rag.utils.resources.Filter(vector_distance_threshold=0.5),
                ),
            )
            
            sources = []
            if hasattr(retrieval_response, 'contexts') and hasattr(retrieval_response.contexts, 'contexts'):
                for i, context in enumerate(retrieval_response.contexts.contexts, 1):
                    try:
                        import json as json_module
                        content_json = json_module.loads(context.text)
                        post_info = content_json.get('post', {})
                        
                        if post_info.get('id'):
                            sources.append({
                                'reference_id': i,
                                'post_id': post_info.get('id'),
                                'title': post_info.get('title', 'Untitled Discussion'),
                                'author': post_info.get('author', {}).get('nickname', 'Anonymous'),
                                'content_snippet': post_info.get('content', '')[:200] + '...' if post_info.get('content') else '',
                                'tag': post_info.get('tag', ''),
                                'upvotes': post_info.get('upvotes', 0),
                                'replies_count': content_json.get('ai_metadata', {}).get('total_replies', 0),
                                'created_at': post_info.get('created_at', ''),
                                'confidence_score': getattr(context, 'distance', 0.0)
                            })
                    except Exception as e:
                        logger.warning(f"Failed to parse source {i}: {e}")
                        # Add fallback source
                        sources.append({
                            'reference_id': i,
                            'post_id': None,
                            'title': 'Discussion Thread',
                            'author': 'Community',
                            'content_snippet': context.text[:200] + '...',
                            'tag': '',
                            'upvotes': 0,
                            'replies_count': 0,
                            'created_at': '',
                            'confidence_score': getattr(context, 'distance', 0.0)
                        })
            
            return sources
            
        except Exception as e:
            logger.error(f"Failed to extract sources: {e}")
            return []

# Singleton instance
_rag_manager = None

def get_rag_manager():
    """Get singleton RAG manager instance"""
    global _rag_manager
    if _rag_manager is None:
        _rag_manager = EnhancedRAGManager()
    return _rag_manager