from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from .models import (
    Notification, 
    UserNotificationStatus,
    Post,
    Reply,
    ReplytoAReply,
    UserPostInteraction,
    ReplytoReplyInteraction,
    ReplyInteraction,
    ReplyToAnotherReply,
    ReplyToAnotherReplyInteraction
)

User = get_user_model()

# Custom Admin Classes
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user_or_public', 'created_at', 'is_public')
    list_filter = ('is_public', 'created_at')
    search_fields = ('title', 'message', 'user__username', 'user__email')
    readonly_fields = ('created_at',)
    fieldsets = (
        (None, {
            'fields': ('user', 'is_public')
        }),
        ('Content', {
            'fields': ('title', 'message')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def user_or_public(self, obj):
        return obj.user.get_full_name() if obj.user else "Public Announcement"
    user_or_public.short_description = "Recipient"


@admin.register(UserNotificationStatus)
class UserNotificationStatusAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_title', 'is_read', 'read_at')
    list_filter = ('is_read',)
    search_fields = ('user__username', 'notification__title')
    readonly_fields = ('read_at',)
    
    def notification_title(self, obj):
        return obj.notification.title
    notification_title.short_description = "Notification"


class ReplyInline(admin.TabularInline):
    model = Reply
    extra = 0
    fields = ('replyier', 'content_preview', 'created_at')
    readonly_fields = ('content_preview', 'created_at')
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = "Content"


class ReplyToReplyInline(admin.TabularInline):
    model = ReplytoAReply
    extra = 0
    fields = ('replyier', 'content_preview', 'created_at')
    readonly_fields = ('content_preview', 'created_at')
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = "Content"


class UserPostInteractionInline(admin.TabularInline):
    model = UserPostInteraction
    extra = 0
    fields = ('user', 'interaction_type', 'timestamp')
    readonly_fields = ('timestamp',)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'title', 
        'author', 
        'tag', 
        'created_at', 
        'reply_count',
        'interaction_count',
        'media_preview'
    )
    list_filter = ('tag', 'created_at')
    search_fields = ('title', 'content', 'author__username')
    readonly_fields = ('created_at', 'media_preview')
    fieldsets = (
        (None, {
            'fields': ('author', 'title', 'content', 'tag')
        }),
        ('Media & Links', {
            'fields': (
                'image', 
                'image2', 
                'video', 
                'docs', 
                'link',
                'media_preview'
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    inlines = [ReplyInline, UserPostInteractionInline]
    
    def reply_count(self, obj):
        return obj.replies.count()
    reply_count.short_description = "Replies"
    
    def interaction_count(self, obj):
        return obj.user_interactions.count()
    interaction_count.short_description = "Interactions"
    
    def media_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />', 
                obj.image.url
            )
        elif obj.video:
            return "Video file uploaded"
        elif obj.docs:
            return "Document file uploaded"
        return "No media"
    media_preview.short_description = "Media Preview"


@admin.register(Reply)
class ReplyAdmin(admin.ModelAdmin):
    list_display = (
        'content_preview', 
        'post_title', 
        'replyier', 
        'created_at',
        'nested_reply_count'
    )
    list_filter = ('created_at', 'tag')
    search_fields = ('content', 'post__title', 'replyier__username')
    readonly_fields = ('created_at', 'media_preview')
    fieldsets = (
        (None, {
            'fields': ('post', 'replyier', 'content', 'tag')
        }),
        ('Media & Links', {
            'fields': (
                'image', 
                'image2', 
                'video', 
                'docs', 
                'link',
                'media_preview'
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    inlines = [ReplyToReplyInline]
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = "Content"
    
    def post_title(self, obj):
        return obj.post.title
    post_title.short_description = "Post"
    
    def nested_reply_count(self, obj):
        return obj.replies_to_reply.count()
    nested_reply_count.short_description = "Nested Replies"
    
    def media_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />', 
                obj.image.url
            )
        elif obj.video:
            return "Video file uploaded"
        elif obj.docs:
            return "Document file uploaded"
        return "No media"
    media_preview.short_description = "Media Preview"


@admin.register(ReplytoAReply)
class ReplyToReplyAdmin(admin.ModelAdmin):
    list_display = (
        'content_preview', 
        'parent_reply', 
        'replyier', 
        'created_at'
    )
    list_filter = ('created_at', 'tag')
    search_fields = ('content', 'reply__content', 'replyier__username')
    readonly_fields = ('created_at', 'media_preview')
    fieldsets = (
        (None, {
            'fields': ('reply','parent', 'replyier', 'content', 'tag')
        }),
        ('Media & Links', {
            'fields': (
                'image', 
                'video', 
                'docs', 
                'link',
                'media_preview'
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = "Content"
    
    def parent_reply(self, obj):
        parent_obj = obj.parent or obj.reply
        if parent_obj and parent_obj.content:
            content = parent_obj.content
            return content[:50] + '...' if len(content) > 50 else content
        return "—"

    
    def media_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />', 
                obj.image.url
            )
        elif obj.video:
            return "Video file uploaded"
        elif obj.docs:
            return "Document file uploaded"
        return "No media"
    media_preview.short_description = "Media Preview"


@admin.register(UserPostInteraction)
class UserPostInteractionAdmin(admin.ModelAdmin):
    list_display = (
        'user', 
        'post_title', 
        'interaction_type', 
        'timestamp'
    )
    list_filter = ('interaction_type', 'timestamp')
    search_fields = (
        'user__username', 
        'post__title', 
        'post__content'
    )
    readonly_fields = ('timestamp',)
    
    def post_title(self, obj):
        return obj.post.title
    post_title.short_description = "Post"


@admin.register(ReplytoReplyInteraction)
class ReplytoReplyInteractionAdmin(admin.ModelAdmin):
    list_display = (
        'user', 
        'reply',
        'interaction_type', 
        'timestamp'
    )
    list_filter = ('interaction_type', 'timestamp')
    search_fields = (
        'user__username', 
        'reply__content'
    )
    readonly_fields = ('timestamp',)


@admin.register(ReplyInteraction)
class ReplyInteractionAdmin(admin.ModelAdmin):
    list_display = (
        'user', 
        'reply', 
        'interaction_type', 
        'timestamp'
    )
    list_filter = ('interaction_type', 'timestamp')
    search_fields = (
        'user__username', 
        'reply__content'
    )
    readonly_fields = ('timestamp',)


@admin.register(ReplyToAnotherReply)
class ReplyToAnotherReplyAdmin(admin.ModelAdmin):
    list_display = ('replyier', 'parent_summary', 'tag', 'created_at')
    search_fields = ('replyier__username', 'content', 'tag')
    list_filter = ('tag', 'created_at')

    def parent_summary(self, obj):
        return obj.reply.content[:50] if obj.reply else "—"
    parent_summary.short_description = 'Replying To'


# @admin.register(ReplyToAnotherReply)
# class ReplyToAnotherReplyAdmin(admin.ModelAdmin):
#     list_display = (
#         'content_preview', 
#         'parent_reply', 
#         'replyier', 
#         'created_at'
#     )
#     list_filter = ('created_at', 'tag')
#     search_fields = ('content', 'reply__content', 'replyier__username')
#     readonly_fields = ('created_at', 'media_preview')
#     fieldsets = (
#         (None, {
#             'fields': ('reply', 'replyier', 'content', 'tag')
#         }),
#         ('Media & Links', {
#             'fields': (
#                 'image', 
#                 'video', 
#                 'docs', 
#                 'link',
#                 'media_preview'
#             ),
#             'classes': ('collapse',)
#         }),
#         ('Metadata', {
#             'fields': ('created_at',),
#             'classes': ('collapse',)
#         })
#     )
    
#     def content_preview(self, obj):
#         return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
#     content_preview.short_description = "Content"
    
#     def parent_reply(self, obj):
#         return obj.reply.content[:50] + '...' if len(obj.reply.content) > 50 else obj.reply.content
#     parent_reply.short_description = "In Reply To"
    
#     def media_preview(self, obj):
#         if obj.image:
#             return format_html(
#                 '<img src="{}" style="max-height: 100px; max-width: 100px;" />', 
#                 obj.image.url
#             )
#         elif obj.video:
#             return "Video file uploaded"
#         elif obj.docs:
#             return "Document file uploaded"
#         return "No media"
#     media_preview.short_description = "Media Preview"


@admin.register(ReplyToAnotherReplyInteraction)
class ReplyToAnotherReplyInteractionAdmin(admin.ModelAdmin):
    list_display = ('user', 'reply_summary', 'interaction_type', 'timestamp')
    search_fields = ('user__username', 'reply__content', 'interaction_type')

    def reply_summary(self, obj):
        return obj.reply.content[:50]
    reply_summary.short_description = 'Reply Preview'