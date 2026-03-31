from .models import Post, Reply, Notification, UserPostInteraction, ReplyInteraction
from .views import get_online_users, get_tag_choices  # adjust import paths as needed

def context_to_extend(request):
    online_users, online_count, everyone_count = get_online_users()
    tag_choices = get_tag_choices()
    posts = Post.objects.all().order_by('-created_at')

    user = request.user if request.user.is_authenticated else None

    # Default values
    replies = Reply.objects.none()
    notifications = Notification.objects.none()
    unreadnotificationcount = 0

    if user:
        upvoted_post_ids = set(
            UserPostInteraction.objects.filter(
                user=user, interaction_type='upvote'
            ).values_list('post_id', flat=True)
        )

        for post in posts:
            post.user_has_upvoted = post.id in upvoted_post_ids

        replies = Reply.objects.filter(post__in=posts).select_related('replyier')

        upvoted_reply_ids = set(
            ReplyInteraction.objects.filter(
                user=user, interaction_type='upvote'
            ).values_list('reply_id', flat=True)
        )

        for reply in replies:
            reply.user_has_upvoted = reply.id in upvoted_reply_ids

        replies_by_post = {}
        for reply in replies:
            replies_by_post.setdefault(reply.post_id, []).append(reply)

        for post in posts:
            post.annotated_replies = replies_by_post.get(post.id, [])

        notifications = Notification.objects.filter(user=user).order_by('-created_at')
        unreadnotificationcount = Notification.objects.filter(
            statuses__user=user,
            statuses__is_read=False
        ).count()

    return {
        'online_users': online_users,
        'online_count': online_count,
        'everyone_count': everyone_count,
        'tag_choices': tag_choices,
        'posts': posts,
        'replies': replies,
        'notifications': notifications,
        'user': user,
        'unreadnotificationcount': unreadnotificationcount
    }

