from django.core.management.base import BaseCommand
from discussion.ai_rag import get_rag_manager
from discussion.models import Post

class Command(BaseCommand):
    help = 'Force upload all existing posts to RAG corpus'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-upload even if files are already uploaded',
        )
        parser.add_argument(
            '--delete-all',
            action='store_true',
            help='Delete all existing RAG files before uploading (DESTRUCTIVE!)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Force uploading all posts to RAG corpus...'))
        
        rag_manager = get_rag_manager()
        
        # NEW: Delete all existing RAG files if requested
        if options['delete_all']:
            self.stdout.write(self.style.WARNING('🗑️ DELETING ALL EXISTING RAG FILES...'))
            try:
                # Get all existing RAG files
                existing_files = rag_manager.list_rag_files()
                self.stdout.write(f"Found {len(existing_files)} existing files to delete")
                
                deleted_count = 0
                for file_info in existing_files:
                    try:
                        # Delete each file from the RAG corpus
                        rag_manager.delete_rag_file(file_info[1])  # file_info[1] is the full file name
                        deleted_count += 1
                        self.stdout.write(f"  🗑️ Deleted: {file_info[0]}")
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"  ❌ Failed to delete {file_info[0]}: {e}"))
                
                self.stdout.write(self.style.SUCCESS(f"✅ Deleted {deleted_count} existing RAG files\n"))
                
                # Clear local database records too
                from discussion.models import AIRagFile
                AIRagFile.objects.all().delete()
                self.stdout.write("✅ Cleared local database records\n")
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error during deletion: {e}"))
                return
        
        # First, let's regenerate discussion JSON files for all posts
        posts = Post.objects.all()
        self.stdout.write(f"Found {posts.count()} posts to process")
        
        for post in posts:
            try:
                # Regenerate discussion data
                post_data = rag_manager.generate_discussion_data_for_post(post)
                
                # Save to JSON
                json_path = rag_manager.save_discussion_json(post.id, post_data)
                self.stdout.write(f"  ✅ Generated JSON for post {post.id}: {post.title[:50]}...")
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ❌ Failed to generate JSON for post {post.id}: {e}"))
        
        # Now upload all to RAG corpus (force=True since we want fresh uploads)
        self.stdout.write("\n📤 Uploading to RAG corpus...")
        results = rag_manager.upload_all_posts(force_update=True)
        
        self.stdout.write(f"\n📊 Upload Results:")
        self.stdout.write(f"  ✅ Uploaded: {len(results['uploaded'])} posts")
        self.stdout.write(f"  🔄 Updated: {len(results['updated'])} posts") 
        self.stdout.write(f"  ⏭️ Skipped: {len(results['skipped'])} posts")
        self.stdout.write(f"  ❌ Failed: {len(results['failed'])} posts")
        
        if results['failed']:
            self.stdout.write(self.style.WARNING(f"\nFailed post IDs: {results['failed']}"))
        
        self.stdout.write(self.style.SUCCESS("\n✅ Force upload completed!"))