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
    def riplies(self):
        return self.user_interactions.filter(interaction_type='reply').count()
    
    @property
    def replies_list(self):
        return self.replies.all().order_by('created_at')
    # @property
    # def threaded_replies(self):
    #     threads = []
    #     for reply in self.replies.all().order_by('created_at'):
    #         children = []
    #         for child in reply.replies_to_reply.all().order_by('created_at'):
    #             childrenzz = child.replies_to_another_reply.all().order_by('created_at')
    #             children.append({
    #                 'reply': child,
    #                 'children': childrenzz
    #             })
    #         threads.append({
    #             'reply': reply,
    #             'children': children
    #         })
    #     return threads
    @property
    def threaded_replies(self):
        return self.replies.all().order_by('created_at')
    
    def has_user_upvoted(self, user):
        if user.is_authenticated:
            return self.user_interactions.filter(user=user, interaction_type='upvote').exists()
        return False

    
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
    def riplies(self):
        return self.reply_interactions.filter(interaction_type='reply').count()
    
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
    def riplies(self):
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
    def riplies(self):
        return self.reply_to_another_reply_interactions.filter(interaction_type='reply').count()

    def __str__(self):
        # parent_info = self.reply.content[:20] if self.reply else self.parent.content[:20]
        parent_info = self.reply.content[:20] if self.reply else self.reply.content[:20]
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






# from django.contrib.contenttypes.models import ContentType
# from django.contrib.contenttypes.fields import GenericForeignKey

# class ReplyInteraction(models.Model):
#     INTERACTION_TYPES = (
#         ('view', 'View'),
#         ('reply', 'Reply'),
#         ('upvote', 'Upvote'),
#         ('downvote', 'Downvote'),
#     )

#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_reply_interactions')
    
#     content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
#     object_id = models.PositiveIntegerField()
#     reply_object = GenericForeignKey('content_type', 'object_id')

#     interaction_type = models.CharField(max_length=10, choices=INTERACTION_TYPES)
#     timestamp = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         unique_together = ('user', 'content_type', 'object_id', 'interaction_type')

#     def __str__(self):
#         return f"{self.user.username} - {self.reply_object} ({self.get_interaction_type_display()})"




# class ReplytoAReply(models.Model):
#     reply = models.ForeignKey(Reply, on_delete=models.CASCADE, related_name='replies_to_reply')
#     replyier = models.ForeignKey(User, on_delete=models.CASCADE)
#     image = models.ImageField(upload_to=reply_upload_path, blank=True, null=True)
#     video = models.FileField(upload_to=reply_upload_path, blank=True, null=True)
#     docs = models.FileField(upload_to=reply_upload_path, blank=True, null=True)
#     link = models.URLField(blank=True, null=True)
#     content = models.TextField()
#     tag = models.CharField(max_length=50, blank=True, null=True, choices=TAG_CHOICES)
#     created_at = models.DateTimeField(auto_now_add=True)

#     @property
#     def upvotes(self):
#         return self.reply_to_interactions.filter(interaction_type='upvote').count()

#     @property
#     def downvotes(self):
#         return self.reply_to_interactions.filter(interaction_type='downvote').count()

#     @property
#     def riplies(self):
#         return self.reply_to_interactions.filter(interaction_type='reply').count()
    
#     def __str__(self):
#         return f"Reply to {self.reply.content[:20]} by {self.replyier.nickname} on {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
