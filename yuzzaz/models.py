from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True, verbose_name="Official Email")
    username = models.EmailField(unique=True, blank=True, null=True)  # Use email as the username
    telephone = models.CharField(max_length=15)  # Add telephone field
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)

    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
        ('Prefer not to say', 'Prefer not to say'),
    ]
    gender = models.CharField(max_length=50, choices=GENDER_CHOICES, default='Prefer not to say')
    bio = models.TextField(blank=True, null=True)
    school = models.CharField(max_length=100, blank=True, null=True)
    grad_year = models.PositiveIntegerField(blank=True, null=True)
    instagram_username = models.CharField(max_length=100, blank=True, null=True)



    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    # @property
    # def nickname(self):
    #     return f"{self.first_name.lower()}{self.last_name.lower()}".strip() if self.first_name or self.last_name else self.username

    @property
    def nickname(self):
        if self.email:
            return self.email.split('@')[0].lower()
        return self.username
    
    @property
    def questions_asked(self):
        from discussion.models import Post
        return Post.objects.filter(author=self).count()
    
    @property
    def reputation(self):
        from discussion.models import Post, Reply, ReplytoAReply, UserPostInteraction, ReplyInteraction, ReplytoReplyInteraction
        user_posts = Post.objects.filter(author=self)
        user_replies = Reply.objects.filter(replyier=self)
        user_reply2s = ReplytoAReply.objects.filter(replyier=self)

        # Sum upvotes received on those objects
        post_upvotes = UserPostInteraction.objects.filter(post__in=user_posts, interaction_type='upvote').count()
        reply_upvotes = ReplyInteraction.objects.filter(reply__in=user_replies, interaction_type='upvote').count()
        reply2_upvotes = ReplytoReplyInteraction.objects.filter(reply__in=user_reply2s, interaction_type='upvote').count()

        return post_upvotes + reply_upvotes + reply2_upvotes


    @property
    def badges(self):
        reputaion = self.reputation
        badges = []
        if reputaion >= 1000:
            badges.append('Gold')
        if reputaion >= 500:
            badges.append('Silver')
        if reputaion >= 100:
            badges.append('Bronze')
        if reputaion < 100:
            badges.append('Newbie')
        return badges

    @property
    def answers_posted(self):
        from discussion.models import Reply, ReplytoAReply
        reply_count = Reply.objects.filter(replyier=self).count()
        nested_reply_count = ReplytoAReply.objects.filter(replyier=self).count()
        return reply_count + nested_reply_count

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
