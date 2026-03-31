from django.core.management.base import BaseCommand
from discussion.utils.ai_rag import get_rag_manager
import json

class Command(BaseCommand):
    help = 'Debug RAG corpus status and test retrieval'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-query',
            type=str,
            default='university admission',
            help='Test query to run against RAG corpus',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔍 Debugging RAG Corpus Status...'))
        
        rag_manager = get_rag_manager()
        
        # Get debug info
        debug_info = rag_manager.debug_corpus_status()
        
        self.stdout.write("\n📊 Corpus Status:")
        self.stdout.write(f"  Project ID: {debug_info['project_id']}")
        self.stdout.write(f"  Location: {debug_info['location']}")
        self.stdout.write(f"  Corpus Name: {debug_info['corpus_name']}")
        self.stdout.write(f"  Local JSON files: {debug_info['local_files_count']}")
        self.stdout.write(f"  Database records: {debug_info['db_files_count']}")
        self.stdout.write(f"  RAG corpus files: {debug_info['rag_files_count']}")
        
        if debug_info.get('local_files'):
            self.stdout.write(f"  Sample local files: {debug_info['local_files']}")
        
        if debug_info.get('rag_files'):
            self.stdout.write(f"  Sample RAG files: {debug_info['rag_files']}")
        
        if debug_info.get('sample_retrieval'):
            self.stdout.write(f"  Sample retrieval: {debug_info['sample_retrieval']}")
        
        if debug_info.get('errors'):
            self.stdout.write(self.style.ERROR("\n❌ Errors found:"))
            for error in debug_info['errors']:
                self.stdout.write(f"  • {error}")
        
        # Test AI answer generation
        self.stdout.write(f"\n🤖 Testing AI answer with query: '{options['test_query']}'")
        try:
            answer = rag_manager.generate_ai_answer(options['test_query'])
            self.stdout.write(self.style.SUCCESS("✅ AI Answer generated:"))
            self.stdout.write(f"{answer[:500]}{'...' if len(answer) > 500 else ''}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ AI Answer failed: {e}"))