
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

def user_upload_path(instance, filename):
    """Generate upload path for user content"""
    username = instance.author.username.replace('@', '_')
    return f"posts/{username}/{filename}"

def reply_upload_path(instance, filename):
    """Generate upload path for replies"""
    username = instance.author.username.replace('@', '_')
    return f"replies/{username}/{filename}"

TAG_CHOICES = [
    ('general', 'General'),
    ('question', 'Question'),
    ('discussion', 'Discussion'),
    ('feedback', 'Feedback'),
    ('announcement', 'Announcement'),
]

INTERACTION_TYPES = (
    ('view', 'View'),
    ('reply', 'Reply'),
    ('upvote', 'Upvote'),
    ('downvote', 'Downvote'),
)

class TimestampModel(models.Model):
    """Abstract model for created_at timestamp"""
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        abstract = True

class Notification(TimestampModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_public = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} → {self.user or 'All Users'}"

class Post(TimestampModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = models.TextField()
    image = models.ImageField(upload_to=user_upload_path, blank=True, null=True)
    video = models.FileField(upload_to=user_upload_path, blank=True, null=True)
    docs = models.FileField(upload_to=user_upload_path, blank=True, null=True)
    link = models.URLField(blank=True, null=True)
    tag = models.CharField(max_length=50, blank=True, null=True, choices=TAG_CHOICES)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} by {self.author.username}"

    @property
    def vote_count(self):
        """Return net votes (upvotes - downvotes)"""
        return (
            self.interactions.filter(interaction_type='upvote').count() -
            self.interactions.filter(interaction_type='downvote').count()
        )

    @property
    def reply_count(self):
        return self.replies.count()

class Reply(TimestampModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='replies')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    parent_reply = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='child_replies',
        null=True,
        blank=True
    )
    content = models.TextField()
    image = models.ImageField(upload_to=reply_upload_path, blank=True, null=True)
    video = models.FileField(upload_to=reply_upload_path, blank=True, null=True)
    docs = models.FileField(upload_to=reply_upload_path, blank=True, null=True)
    link = models.URLField(blank=True, null=True)
    tag = models.CharField(max_length=50, blank=True, null=True, choices=TAG_CHOICES)

    class Meta:
        ordering = ['created_at']  # Oldest first for replies

    def __str__(self):
        return f"Reply by {self.author.username}"

    @property
    def vote_count(self):
        """Return net votes for this reply"""
        return (
            self.interactions.filter(interaction_type='upvote').count() -
            self.interactions.filter(interaction_type='downvote').count()
        )

    @property
    def is_top_level(self):
        """Check if this is a top-level reply to a post"""
        return self.parent_reply is None

class Interaction(TimestampModel):
    """Generic interaction model for both posts and replies"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interactions')
    interaction_type = models.CharField(max_length=10, choices=INTERACTION_TYPES)
    
    # Generic foreign key approach
    content_type = models.ForeignKey('contenttypes.ContentType', on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        unique_together = ('user', 'content_type', 'object_id', 'interaction_type')
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f"{self.user.username} {self.get_interaction_type_display()} on {self.content_object}"