from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from .models import Notification, Post, Reply, Interaction

# Inline Admin Classes
class InteractionInline(GenericTabularInline):
    model = Interaction
    extra = 0
    readonly_fields = ('created_at',)
    fields = ('user', 'interaction_type', 'created_at')
    ct_field = 'content_type'
    ct_fk_field = 'object_id'

class ReplyInline(admin.TabularInline):
    model = Reply
    extra = 0
    fields = ('author', 'content_preview', 'vote_count', 'created_at')
    readonly_fields = ('content_preview', 'vote_count', 'created_at')
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = "Content"

# Model Admin Classes
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'recipient', 'is_public', 'created_at')
    list_filter = ('is_public', 'created_at')
    search_fields = ('title', 'message', 'user__username')
    readonly_fields = ('created_at',)
    
    def recipient(self, obj):
        return obj.user.username if obj.user else "All Users"
    recipient.short_description = "Recipient"

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'tag', 'vote_count', 'reply_count', 'created_at')
    list_filter = ('tag', 'created_at')
    search_fields = ('title', 'content', 'author__username')
    readonly_fields = ('vote_count', 'reply_count', 'created_at', 'media_preview')
    fieldsets = (
        (None, {
            'fields': ('author', 'title', 'content', 'tag')
        }),
        ('Media', {
            'fields': ('image', 'video', 'docs', 'link', 'media_preview'),
            'classes': ('collapse',)
        }),
        ('Stats', {
            'fields': ('vote_count', 'reply_count', 'created_at'),
            'classes': ('collapse',)
        })
    )
    inlines = [ReplyInline, InteractionInline]
    
    def media_preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" style="max-height: 100px;" />'
        return "No media"
    media_preview.allow_tags = True
    media_preview.short_description = "Preview"

@admin.register(Reply)
class ReplyAdmin(admin.ModelAdmin):
    list_display = ('content_preview', 'author', 'post', 'parent_reply', 'vote_count', 'created_at')
    list_filter = ('created_at', 'tag')
    search_fields = ('content', 'author__username', 'post__title')
    readonly_fields = ('vote_count', 'created_at', 'content_preview', 'media_preview')
    fieldsets = (
        (None, {
            'fields': ('author', 'post', 'parent_reply', 'content', 'tag')
        }),
        ('Media', {
            'fields': ('image', 'video', 'docs', 'link', 'media_preview'),
            'classes': ('collapse',)
        }),
        ('Stats', {
            'fields': ('vote_count', 'created_at'),
            'classes': ('collapse',)
        })
    )
    inlines = [InteractionInline]
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = "Content"
    
    def media_preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" style="max-height: 100px;" />'
        return "No media"
    media_preview.allow_tags = True
    media_preview.short_description = "Preview"

@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ('user', 'content_object', 'interaction_type', 'created_at')
    list_filter = ('interaction_type', 'created_at')
    search_fields = ('user__username',)
    readonly_fields = ('created_at', 'content_type', 'object_id')
    
    def has_add_permission(self, request):
        return False  # Interactions should be created via the system, not admin