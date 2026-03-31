from django.core.management.base import BaseCommand
from discussion.models import Post
from discussion.utils.ai_utils import generate_post_content_file
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Generate AI content JSON files for all existing posts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--post-id',
            type=int,
            help='Generate content file for a specific post ID only',
        )
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Remove old .txt files and regenerate as JSON',
        )

    def handle(self, *args, **options):
        ai_content_dir = os.path.join(settings.BASE_DIR, 'ai_content')
        
        # Clean old .txt files if requested
        if options['clean']:
            self.stdout.write('Cleaning old .txt files...')
            if os.path.exists(ai_content_dir):
                for filename in os.listdir(ai_content_dir):
                    if filename.endswith('.txt'):
                        old_file_path = os.path.join(ai_content_dir, filename)
                        os.remove(old_file_path)
                        self.stdout.write(f'Removed: {filename}')
        
        if options['post_id']:
            # Generate for specific post
            try:
                post = Post.objects.get(id=options['post_id'])
                file_path = generate_post_content_file(post)
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Generated JSON file for Post {post.id}: {os.path.basename(file_path)}')
                )
            except Post.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'❌ Post with ID {options["post_id"]} not found')
                )
        else:
            # Generate for all posts
            posts = Post.objects.all()
            
            self.stdout.write(f'Generating JSON content files for {posts.count()} posts...')
            
            success_count = 0
            error_count = 0
            
            for post in posts:
                try:
                    file_path = generate_post_content_file(post)
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Post {post.id}: {os.path.basename(file_path)}')
                    )
                    success_count += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Post {post.id}: {str(e)}')
                    )
                    error_count += 1
            
            self.stdout.write(
                self.style.SUCCESS(f'\n✅ Successfully processed {success_count} posts')
            )
            if error_count > 0:
                self.stdout.write(
                    self.style.WARNING(f'⚠️ {error_count} posts failed to process')
                )
            
            self.stdout.write(f'\n📁 Files saved to: {ai_content_dir}')
            self.stdout.write('📄 File format: post_{{id}}_discussion.json')