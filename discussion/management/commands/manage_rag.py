from django.core.management.base import BaseCommand
from discussion.ai_rag import get_rag_manager
from discussion.models import AIRagFile, AIRagCorpusStats

class Command(BaseCommand):
    help = 'Enhanced RAG management with file mapping and updates'

    def add_arguments(self, parser):
        parser.add_argument('--upload-all', action='store_true', help='Upload all posts')
        parser.add_argument('--upload-post', type=int, help='Upload specific post ID')
        parser.add_argument('--check-updates', action='store_true', help='Check for files needing updates')
        parser.add_argument('--sync-updates', action='store_true', help='Sync files marked for update')
        parser.add_argument('--force-update', action='store_true', help='Force update all files')
        parser.add_argument('--list-files', action='store_true', help='List all RAG files')
        parser.add_argument('--stats', action='store_true', help='Show corpus statistics')
        parser.add_argument('--test-query', type=str, help='Test RAG query with a question')
        parser.add_argument('--test-ai', type=str, help='Test AI answer generation with a question')

    def handle(self, *args, **options):
        rag_manager = get_rag_manager()
        
        if options['upload_all']:
            self.stdout.write('🚀 Uploading all discussion files...')
            results = rag_manager.upload_all_posts(force_update=options['force_update'])
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Results: {len(results["uploaded"])} uploaded, '
                    f'{len(results["updated"])} updated, '
                    f'{len(results["failed"])} failed, '
                    f'{len(results["skipped"])} skipped'
                )
            )
            
            if results['failed']:
                self.stdout.write(self.style.WARNING(f'❌ Failed: {results["failed"]}'))
        
        if options['upload_post']:
            post_id = options['upload_post']
            self.stdout.write(f'📤 Uploading post {post_id}...')
            result = rag_manager.upload_post_file(post_id)
            if result:
                self.stdout.write(self.style.SUCCESS(f'✅ Uploaded: {result.rag_file_id}'))
            else:
                self.stdout.write(self.style.ERROR(f'❌ Failed to upload post {post_id}'))
        
        if options['check_updates']:
            self.stdout.write('🔍 Checking for file updates...')
            updates_needed = rag_manager.check_for_updates()
            if updates_needed:
                self.stdout.write(f'📝 Files needing update: {updates_needed}')
            else:
                self.stdout.write('✅ All files up to date')
        
        if options['sync_updates']:
            self.stdout.write('🔄 Syncing updated files...')
            results = rag_manager.sync_updated_files()
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Updated: {len(results["updated"])}, Failed: {len(results["failed"])}'
                )
            )
        
        if options['list_files']:
            self.stdout.write('📋 Listing RAG files...')
            files = rag_manager.list_all_rag_files()
            for display_name, full_name in files:
                file_id = full_name.split('/')[-1]
                self.stdout.write(f'  • {display_name} -> {file_id}')
        
        if options['test_query']:
            question = options['test_query']
            self.stdout.write(f'🔍 Testing RAG query: "{question}"')
            try:
                response = rag_manager.query_discussions(question)
                self.stdout.write('📝 Retrieved contexts:')
                for i, context in enumerate(response.contexts.contexts, 1):
                    self.stdout.write(f'  {i}. {context.text[:200]}...')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Query failed: {str(e)}'))
        
        if options['test_ai']:
            question = options['test_ai']
            self.stdout.write(f'🤖 Testing AI answer for: "{question}"')
            try:
                answer = rag_manager.generate_ai_answer(question)
                self.stdout.write('💡 AI Answer:')
                self.stdout.write(f'{answer}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ AI generation failed: {str(e)}'))
        
        if options['stats'] or not any(options.values()):
            # Show stats by default if no specific command
            self.stdout.write('\n📊 Corpus Statistics:')
            stats = AIRagCorpusStats.objects.filter(corpus_id=rag_manager.corpus_id).first()
            if stats:
                self.stdout.write(f'  Corpus ID: {stats.corpus_id}')
                self.stdout.write(f'  Total Files: {stats.total_files}')
                self.stdout.write(f'  Posts Indexed: {stats.total_posts_indexed}')
                self.stdout.write(f'  Last Sync: {stats.last_full_sync_at or "Never"}')
            
            # Show file mappings
            file_mappings = AIRagFile.objects.filter(is_uploaded=True)[:10]
            if file_mappings:
                self.stdout.write(f'\n🗂️ Recent File Mappings:')
                for mapping in file_mappings:
                    status = "✅" if not mapping.needs_update else "⚠️"
                    self.stdout.write(f'  {status} Post {mapping.post_id} -> {mapping.rag_file_id}')
            
            # Show environment info
            self.stdout.write(f'\n🔧 Configuration:')
            self.stdout.write(f'  Project: {rag_manager.project_id}')
            self.stdout.write(f'  Location: {rag_manager.location}')
            self.stdout.write(f'  Corpus: {rag_manager.corpus_id}')