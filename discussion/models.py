from django.urls import reverse
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()
def user_upload_path(instance, filename):
    # Replace '@' with an underscore or any other character
    username = instance.author.username.replace('@', '_')
    return f"posts/{username}/{filename}"

def reply_upload_path(instance, filename):
    # Replace '@' with an underscore or any other character
    username = instance.replyier.username.replace('@', '_')
    return f"replies/{username}/{filename}"

TAG_CHOICES = [
    ('general', 'General'),
    ('question', 'Question'),
    ('discussion', 'Discussion'),
    ('feedback', 'Feedback'),
    ('announcement', 'Announcement'),
]

STORY_TAG_CHOICES = [
    ('admission', 'Admission Journey'),
    ('scholarship', 'Scholarship'),
    ('visa', 'Visa Experience'),
    ('campus_life', 'Campus Life'),
    ('summer_program', 'Summer Program'),
    ('tips', 'Tips & Advice'),
    ('other', 'Other'),
]

def story_cover_upload_path(instance, filename):
    username = instance.author.username.replace('@', '_')
    return f"stories/{username}/{filename}"


class Story(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stories')
    title = models.CharField(max_length=200)
    summary = models.CharField(max_length=300, help_text="One-line description shown in preview cards")
    body = models.TextField(help_text="Full story content ,  markdown/plain text supported")
    cover_image = models.ImageField(upload_to=story_cover_upload_path, null=True, blank=True)
    tag = models.CharField(max_length=50, choices=STORY_TAG_CHOICES, default='other')
    views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Story"
        verbose_name_plural = "Stories"

    def __str__(self):
        return f"{self.title} by {self.author.nickname}"

    def get_absolute_url(self):
        return reverse('story_detail', args=[self.id])

class Notification(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True,
        help_text="Target user for the notification. Leave blank for public announcements."
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_public = models.BooleanField(default=False, help_text="Public announcements visible to all users.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    @property
    def is_read(self):
        if not self.user:
            return False
        return self.user.notification_statuses.filter(notification=self, is_read=True).exists()

    def __str__(self):
        recipient = self.user.get_full_name() if self.user else "All Users"
        return f"{self.title} → {recipient}"

class UserNotificationStatus(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notification_statuses')
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='statuses')
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'notification')
        verbose_name = "User Notification Status"
        verbose_name_plural = "User  Notification Statuses"
    
    def __str__(self):
        return f"{self.user.username} - {self.notification.title} ({'Read' if self.is_read else 'Unread'})"

class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = models.TextField()
    image = models.ImageField(upload_to=user_upload_path, blank=True, null=True)
    image2 = models.ImageField(upload_to=user_upload_path, blank=True, null=True)
    video = models.FileField(upload_to=user_upload_path, blank=True, null=True)
    docs = models.FileField(upload_to=user_upload_path, blank=True, null=True)
    link = models.URLField(blank=True, null=True)
    tag = models.CharField(max_length=50, blank=True, null=True, choices=TAG_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def upvotes(self):
        return self.user_interactions.filter(interaction_type='upvote').count()

    @property
    def downvotes(self):
        return self.user_interactions.filter(interaction_type='downvote').count()

    @property
    def replies_count(self):
        return self.replies.count()

    @property
    def replies_list(self):
        return self.replies.all().order_by('created_at')
    @property
    def threaded_replies(self):
        return self.replies.all().order_by('created_at')
    
    def has_user_upvoted(self, user):
        if user.is_authenticated:
            return self.user_interactions.filter(user=user, interaction_type='upvote').exists()
        return False
        
    def get_absolute_url(self):
        return reverse("post_detail", args=[self.id])

    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Post"
        verbose_name_plural = "Posts"
    def __str__(self):
        return f"{self.title} by {self.author.nickname}"

class UserPostInteraction(models.Model):
    INTERACTION_TYPES = (
        ('view', 'View'),
        ('reply', 'Reply'),
        ('upvote', 'Upvote'),
        ('downvote', 'Downvote'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_interactions')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='user_interactions')
    interaction_type = models.CharField(max_length=10, choices=INTERACTION_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'post', 'interaction_type')
    
    def __str__(self):
        return f"{self.user.username} - {self.post.title} ({self.get_interaction_type_display()})"

class Reply(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='replies')
    replyier = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=reply_upload_path, blank=True, null=True)
    image2 = models.ImageField(upload_to=reply_upload_path, blank=True, null=True)
    video = models.FileField(upload_to=reply_upload_path, blank=True, null=True)
    docs = models.FileField(upload_to=reply_upload_path, blank=True, null=True)
    link = models.URLField(blank=True, null=True)
    content = models.TextField()
    tag = models.CharField(max_length=50, blank=True, null=True, choices=TAG_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    @property
    def upvotes(self):
        return self.reply_interactions.filter(interaction_type='upvote').count()

    @property
    def downvotes(self):
        return self.reply_interactions.filter(interaction_type='downvote').count()

    @property
    def replies_count(self):
        return self.replies_to_reply.count()

    def has_user_upvoted(self, user):
        if user.is_authenticated:
            return self.reply_interactions.filter(user=user, interaction_type='upvote').exists()
        return False
    
    def __str__(self):
        return f"{self.content[:20]} - Reply by {self.replyier.nickname} on {self.post.title} at {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"

class ReplyInteraction(models.Model):
    INTERACTION_TYPES = (
        ('view', 'View'),
        ('reply', 'Reply'),
        ('upvote', 'Upvote'),
        ('downvote', 'Downvote'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_reply_interactions')
    reply = models.ForeignKey(Reply, on_delete=models.CASCADE, related_name='reply_interactions')
    interaction_type = models.CharField(max_length=10, choices=INTERACTION_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'reply', 'interaction_type')
    
    def __str__(self):
        return f"{self.user.username} - {self.reply.content} ({self.get_interaction_type_display()})"

class ReplytoAReply(models.Model):
    reply = models.ForeignKey(
        Reply,
        on_delete=models.CASCADE,
        related_name='replies_to_reply',
        blank=True,
        null=True
    )
    parent = models.ForeignKey(
        'ReplytoAReply',
        # 'self',
        on_delete=models.CASCADE,
        related_name='child_replies',
        blank=True,
        null=True
    )
    replyier = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=reply_upload_path, blank=True, null=True)
    image2 = models.ImageField(upload_to=reply_upload_path, blank=True, null=True)
    video = models.FileField(upload_to=reply_upload_path, blank=True, null=True)
    docs = models.FileField(upload_to=reply_upload_path, blank=True, null=True)
    link = models.URLField(blank=True, null=True)
    content = models.TextField(default="hi")
    tag = models.CharField(max_length=50, blank=True, null=True, choices=TAG_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def upvotes(self):
        return self.reply_to_interactions.filter(interaction_type='upvote').count()

    @property
    def downvotes(self):
        return self.reply_to_interactions.filter(interaction_type='downvote').count()

    @property
    def replies_count(self):
        return self.child_replies.count()

    @property
    def repliedto(self):
        if self.parent:
            return self.parent.replyier.nickname
        elif self.reply:
            return self.reply.replyier.nickname
        return "Unknown"

    def __str__(self):
        # Determine the parent information string based on whether a parent exists
        if self.parent:
            parent_info = f"parent comment: {self.parent.content[:20]}"
        else:
            parent_info = f"original comment: {self.reply.content[:20]}"

        # Construct and return the full string in a single line
        return f"Reply: {self.content} | Replied to: {parent_info} | By: {self.replyier.nickname} | On: {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
class ReplytoReplyInteraction(models.Model):
    INTERACTION_TYPES = (
        ('view', 'View'),
        ('reply', 'Reply'),
        ('upvote', 'Upvote'),
        ('downvote', 'Downvote'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_reply_to_reply_interactions')
    reply = models.ForeignKey(ReplytoAReply, on_delete=models.CASCADE, related_name='reply_to_interactions')
    interaction_type = models.CharField(max_length=10, choices=INTERACTION_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'reply', 'interaction_type')
    
    def __str__(self):
        return f"{self.user.username} - {self.reply.content} ({self.get_interaction_type_display()})"

class ReplyToAnotherReply(models.Model):
    reply = models.ForeignKey(
        ReplytoAReply,
        on_delete=models.CASCADE,
        related_name='replies_to_another_reply',
        blank=True,
        null=True
    )
    replyier = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=reply_upload_path, blank=True, null=True)
    video = models.FileField(upload_to=reply_upload_path, blank=True, null=True)
    docs = models.FileField(upload_to=reply_upload_path, blank=True, null=True)
    link = models.URLField(blank=True, null=True)
    content = models.TextField()
    tag = models.CharField(max_length=50, blank=True, null=True, choices=TAG_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def upvotes(self):
        return self.reply_to_another_reply_interactions.filter(interaction_type='upvote').count()

    @property
    def downvotes(self):
        return self.reply_to_another_reply_interactions.filter(interaction_type='downvote').count()

    @property
    def replies_count(self):
        return self.reply_to_another_reply_interactions.filter(interaction_type='reply').count()

    def __str__(self):
        parent_info = self.reply.content[:20] if self.reply else "unknown"
        return f"Reply to {parent_info} by {self.replyier.nickname} on {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"

class ReplyToAnotherReplyInteraction(models.Model):
    INTERACTION_TYPES = (
        ('view', 'View'),
        ('reply', 'Reply'),
        ('upvote', 'Upvote'),
        ('downvote', 'Downvote'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_reply_to_another_reply_interactions')
    reply = models.ForeignKey(ReplyToAnotherReply, on_delete=models.CASCADE, related_name='reply_to_another_reply_interactions')
    interaction_type = models.CharField(max_length=10, choices=INTERACTION_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'reply', 'interaction_type')
    
    def __str__(self):
        return f"{self.user.username} - {self.reply.content} ({self.get_interaction_type_display()})"

class AIRagFile(models.Model):
    """Track files uploaded to RAG corpus with precise mapping"""
    post_id = models.IntegerField(unique=True, help_text="Discussion post ID")
    rag_file_name = models.CharField(max_length=500, help_text="Full Vertex AI File name (e.g., projects/.../ragFiles/123)")
    rag_file_id = models.CharField(max_length=100, help_text="Just the file ID (e.g., 5509377323857763591)")
    display_name = models.CharField(max_length=255, help_text="Display name in Vertex AI")
    local_file_path = models.CharField(max_length=500, help_text="Path to local JSON file")
    
    # File tracking
    uploaded_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)
    file_size = models.IntegerField(default=0, help_text="File size in bytes")
    file_hash = models.CharField(max_length=64, help_text="SHA256 hash of file content")
    
    # Status tracking
    is_uploaded = models.BooleanField(default=False)
    needs_update = models.BooleanField(default=False)
    last_sync_error = models.TextField(blank=True, help_text="Last error message if any")
    
    class Meta:
        verbose_name = "AI RAG File"
        verbose_name_plural = "AI RAG Files"
        indexes = [
            models.Index(fields=['post_id']),
            models.Index(fields=['rag_file_id']),
        ]
    
    def __str__(self):
        return f"Post {self.post_id} -> {self.rag_file_id}"
    
    @property
    def short_rag_file_id(self):
        """Extract just the file ID from the full name"""
        if self.rag_file_name:
            return self.rag_file_name.split('/')[-1]
        return self.rag_file_id

class AIRagCorpusStats(models.Model):
    """Track overall corpus statistics"""
    corpus_id = models.CharField(max_length=100, unique=True)
    total_files = models.IntegerField(default=0)
    total_posts_indexed = models.IntegerField(default=0)
    last_full_sync_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Corpus {self.corpus_id}: {self.total_files} files"

# Django Signals for AI Content File Management
import threading
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

def _run_async(fn, *args):
    threading.Thread(target=fn, args=args, daemon=True).start()

@receiver(post_save, sender=Post)
def handle_post_change(sender, instance, created, **kwargs):
    from .utils.ai_utils import sync_post_to_rag
    _run_async(sync_post_to_rag, instance.id)

@receiver(post_save, sender=Reply)
def handle_reply_change(sender, instance, created, **kwargs):
    from .utils.ai_utils import sync_post_to_rag
    _run_async(sync_post_to_rag, instance.post.id)
    _broadcast_reply_count(instance.post_id)

@receiver(post_save, sender=ReplytoAReply)
def handle_reply2_change(sender, instance, created, **kwargs):
    from .utils.ai_utils import sync_post_to_rag
    if instance.reply:
        _run_async(sync_post_to_rag, instance.reply.post.id)

@receiver(post_save, sender=ReplyToAnotherReply)
def handle_reply3_change(sender, instance, created, **kwargs):
    from .utils.ai_utils import sync_post_to_rag
    if instance.reply and instance.reply.reply:
        _run_async(sync_post_to_rag, instance.reply.reply.post.id)

@receiver(post_delete, sender=Post)
def handle_post_delete(sender, instance, **kwargs):
    from .utils.ai_utils import remove_post_from_rag
    _run_async(remove_post_from_rag, instance.id)

@receiver(post_delete, sender=Reply)
def handle_reply_delete(sender, instance, **kwargs):
    _broadcast_reply_count(instance.post_id)


def _broadcast_reply_count(post_id):
    """Push updated reply count to all WebSocket clients watching this post."""
    def _send():
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
        count = Reply.objects.filter(post_id=post_id).count()
        layer = get_channel_layer()
        async_to_sync(layer.group_send)(
            'reply_counts',
            {
                'type': 'reply.count.update',
                'post_id': post_id,
                'count': count,
            }
        )
    threading.Thread(target=_send, daemon=True).start()
