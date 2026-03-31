from django.db.models import Count, Case, When, IntegerField, F, Q
from django.db.models.functions import Abs
from django.db.models import Q
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from .forms import PostForm
from django.contrib import messages
import random
import logging
from yuzzaz.models import CustomUser
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from .models import Post, UserPostInteraction
from django.core.paginator import Paginator
from django.urls import reverse
import json
from django.http import JsonResponse

logger = logging.getLogger(__name__)

def api_search_suggestions(request):
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'results': []})

    from django.urls import reverse
    from django.db.models import Count
    results = []

    # Tags first
    tag_qs = Post.objects.filter(tag__icontains=q).values('tag').annotate(c=Count('id')).order_by('-c')[:2]
    for t in tag_qs:
        tag = t['tag']
        if tag:
            results.append({
                'type': 'tag',
                'label': f'#{tag}',
                'sublabel': f'{t["c"]} post{"s" if t["c"] != 1 else ""}',
                'url': f'/discuss/?filter=recent&tag={tag}',
            })

    # Posts by title or content snippet
    posts = Post.objects.filter(
        Q(title__icontains=q) | Q(content__icontains=q) | Q(tag__icontains=q)
    ).only('id', 'title', 'tag', 'content')[:5]
    for post in posts:
        snippet = post.title
        sublabel = post.tag or ''
        if q.lower() not in post.title.lower() and q.lower() in post.content.lower():
            # query matched content, show snippet
            idx = post.content.lower().find(q.lower())
            start = max(0, idx - 30)
            raw = post.content[start:idx + 60].strip()
            sublabel = ('…' if start > 0 else '') + raw + '…'
        results.append({
            'type': 'post',
            'label': post.title,
            'sublabel': sublabel,
            'url': reverse('post_detail', args=[post.id]),
        })

    # Replies
    replies = Reply.objects.filter(
        Q(content__icontains=q)
    ).select_related('post').only('id', 'content', 'post__id', 'post__title')[:3]
    for reply in replies:
        idx = reply.content.lower().find(q.lower())
        start = max(0, idx - 20)
        snippet = reply.content[start:idx + 50].strip()
        results.append({
            'type': 'reply',
            'label': ('…' if start > 0 else '') + snippet + '…',
            'sublabel': f'Reply in: {reply.post.title}',
            'url': reverse('post_detail', args=[reply.post.id]),
        })

    return JsonResponse({'results': results[:8]})


def api_stats(request):
    from .models import Post, Story
    return JsonResponse({
        'users': CustomUser.objects.count(),
        'posts': Post.objects.count(),
        'stories': Story.objects.count(),
    })


def api_recent_activity(request, user_id):
    from django.utils.timesince import timesince
    from django.urls import reverse
    target = get_object_or_404(CustomUser, id=user_id)
    items = []

    for post in Post.objects.filter(author=target).order_by('-created_at')[:5]:
        items.append({
            'type': 'post',
            'label': 'Asked question',
            'title': post.title,
            'snippet': ' '.join(post.content.split()[:15]),
            'url': reverse('post_detail', args=[post.id]),
            'time': timesince(post.created_at) + ' ago',
            'ts': post.created_at.timestamp(),
            'color': 'blue',
        })

    for reply in Reply.objects.filter(replyier=target).order_by('-created_at')[:5]:
        items.append({
            'type': 'reply',
            'label': 'Replied',
            'title': reply.post.title,
            'snippet': ' '.join(reply.content.split()[:15]),
            'url': reverse('post_detail', args=[reply.post.id]),
            'time': timesince(reply.created_at) + ' ago',
            'ts': reply.created_at.timestamp(),
            'color': 'green',
        })

    for rtr in ReplytoAReply.objects.filter(replyier=target).order_by('-created_at')[:5]:
        items.append({
            'type': 'rtr',
            'label': 'Replied to reply',
            'title': None,
            'snippet': ' '.join(rtr.content.split()[:10]),
            'url': None,
            'time': timesince(rtr.created_at) + ' ago',
            'ts': rtr.created_at.timestamp(),
            'color': 'yellow',
        })

    items.sort(key=lambda x: x['ts'], reverse=True)
    return JsonResponse({'activity': items[:5]})


@login_required
def api_notifications(request):
    page = int(request.GET.get('page', 1))
    per_page = 10
    offset = (page - 1) * per_page
    qs = Notification.objects.filter(
        Q(user=request.user) | Q(is_public=True)
    ).order_by('-created_at')
    total = qs.count()
    items = qs[offset:offset + per_page]
    unread_ids = set(
        UserNotificationStatus.objects.filter(
            user=request.user, notification__in=items, is_read=True
        ).values_list('notification_id', flat=True)
    )
    data = []
    for n in items:
        data.append({
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'created_at': n.created_at.strftime('%b %d, %Y'),
            'is_read': n.id in unread_ids,
        })
    return JsonResponse({
        'notifications': data,
        'total': total,
        'has_more': offset + per_page < total,
        'page': page,
        'unread_count': qs.exclude(
            id__in=UserNotificationStatus.objects.filter(
                user=request.user, is_read=True
            ).values_list('notification_id', flat=True)
        ).count(),
    })


def landing(request):
    if request.user.is_authenticated:
        return redirect('questions')
    from .models import Story
    context = {
        'year': datetime.now().year,
        "all_users": CustomUser.objects.all().count(),
        "all_posts": Post.objects.all().count(),
        "latest_stories": Story.objects.select_related('author').all()[:3],
    }
    return render(request, 'yuzzaz/landing.html', context)

  
def context_to_extend(request):
    online_users, online_count, everyone_count = get_online_users()  # session-based
    tag_choices = get_tag_choices()
    posts = Post.objects.all().order_by('-created_at')

    user = request.user
    if user.is_authenticated:
        # Get all post IDs user has upvoted
        upvoted_post_ids = set(
            UserPostInteraction.objects.filter(
                user=user, interaction_type='upvote'
            ).values_list('post_id', flat=True)
        )
    else:
        upvoted_post_ids = set()

    # Attach a flag on each post object
    for post in posts:
        post.user_has_upvoted = post.id in upvoted_post_ids




    replies = Reply.objects.filter(post__in=posts).select_related('replyier')
    if user.is_authenticated:
        upvoted_reply_ids = set(
            ReplyInteraction.objects.filter(
                user=user, interaction_type='upvote'
            ).values_list('reply_id', flat=True)
        )
    else:
        upvoted_reply_ids = set()

    # Attach the flag
    for reply in replies:
        reply.user_has_upvoted = reply.id in upvoted_reply_ids

    # If you have a threaded_replies property, assign them
    replies_by_post = {}
    for reply in replies:
        replies_by_post.setdefault(reply.post_id, []).append(reply)

    for post in posts:
        post.annotated_replies = replies_by_post.get(post.id, [])

    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    unreadnotificationcount = Notification.objects.filter(
            statuses__user=request.user,
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
        'user': request.user,
        'unreadnotificationcount': unreadnotificationcount
    }

def get_online_users(use_last_seen=False, minutes=5):
    User = get_user_model()
    all_users = User.objects.all()

    if use_last_seen:
        cutoff = timezone.now() - timedelta(minutes=minutes)
        online_users = User.objects.filter(last_seen__gte=cutoff)
    else:
        sessions = Session.objects.filter(expire_date__gte=timezone.now())
        user_ids = []
        for session in sessions:
            data = session.get_decoded()
            uid = data.get('_auth_user_id')
            if uid:
                user_ids.append(uid)
        online_users = User.objects.filter(id__in=user_ids)

    return online_users, online_users.count(), all_users.count()


def get_tag_choices():
    return Post._meta.get_field('tag').choices


def search_content(request):
    query = request.GET.get('q', '').strip()
    
    if not query:
        return render(request, 'discussion/search.html', {'query': ''})
    
    # Search across all relevant models
    posts = Post.objects.filter(
        Q(title__icontains=query) |
        Q(content__icontains=query) |
        Q(tag__icontains=query)
    ).distinct()
    
    replies = Reply.objects.filter(
        Q(content__icontains=query) |
        Q(tag__icontains=query)
    ).distinct()
    
    reply_to_replies = ReplytoAReply.objects.filter(
        Q(content__icontains=query) |
        Q(tag__icontains=query)
    ).distinct()
    
    reply_to_another_replies = ReplyToAnotherReply.objects.filter(
        Q(content__icontains=query) |
        Q(tag__icontains=query)
    ).distinct()
    
    notifications = Notification.objects.filter(
        Q(title__icontains=query) |
        Q(message__icontains=query)
    ).distinct()


    viewing_user = request.user if request.user.is_authenticated else None



    context = {
        'query': query,
        'posts': posts,
        'replies': replies,
        'reply_to_replies': reply_to_replies,
        'reply_to_another_replies': reply_to_another_replies,
        'notifications': notifications,
        'user': request.user,
        # 'viewing_user': viewing_user,
        'unreadnotificationcount': Notification.objects.filter(
            statuses__user=request.user,
            statuses__is_read=False
        ).count() if request.user.is_authenticated else 0
    }
    
    return render(request, 'discussion/search.html', context)

def questions(request):
    if not request.user.is_authenticated:
        return redirect(f"/accounts/login/?next={request.path}")
    online_users, online_count, everyone_count = get_online_users()  # session-based
    filter_option = request.GET.get('filter', 'recent')
    posts = Post.objects.all()
    
    tag = request.GET.get('tag')  # get tag from query params
    if tag:
        posts = posts.filter(tag=tag)

    if filter_option == 'top':
        posts = posts.annotate(
            upvote_count=Count(Case(
                When(user_interactions__interaction_type='upvote', then=1),
                output_field=IntegerField()
            )),
            downvote_count=Count(Case(
                When(user_interactions__interaction_type='downvote', then=1),
                output_field=IntegerField()
            )),
        ).annotate(
            score=F('upvote_count') - F('downvote_count')
        ).order_by('-score', '-created_at')

    elif filter_option == 'controversial':
        posts = posts.annotate(
            upvote_count=Count(Case(
                When(user_interactions__interaction_type='upvote', then=1),
                output_field=IntegerField()
            )),
            downvote_count=Count(Case(
                When(user_interactions__interaction_type='downvote', then=1),
                output_field=IntegerField()
            )),
        ).annotate(
            total_votes=F('upvote_count') + F('downvote_count'),
            vote_diff=Abs(F('upvote_count') - F('downvote_count'))
        ).order_by('vote_diff', '-total_votes', '-created_at')
    elif filter_option == 'popular':
        posts = posts.annotate(
            total_votes=Count(Case(
                When(user_interactions__interaction_type__in=['upvote', 'downvote'], then=1),
                output_field=IntegerField()
            ))
        ).order_by('-total_votes', '-created_at')
    else:  # 'recent' or unknown filter
        posts = posts.order_by('-created_at')
    
    user = request.user
    if user.is_authenticated:
        # Get all post IDs user has upvoted
        upvoted_post_ids = set(
            UserPostInteraction.objects.filter(
                user=user, interaction_type='upvote'
            ).values_list('post_id', flat=True)
        )
    else:
        upvoted_post_ids = set()

    # Attach a flag on each post object
    for post in posts:
        post.user_has_upvoted = post.id in upvoted_post_ids
    replies = Reply.objects.filter(post__in=posts).select_related('replyier')
    if user.is_authenticated:
        upvoted_reply_ids = set(
            ReplyInteraction.objects.filter(
                user=user, interaction_type='upvote'
            ).values_list('reply_id', flat=True)
        )
    else:
        upvoted_reply_ids = set()

    # Attach the flag
    for reply in replies:
        reply.user_has_upvoted = reply.id in upvoted_reply_ids

    # If you have a threaded_replies property, assign them
    replies_by_post = {}
    for reply in replies:
        replies_by_post.setdefault(reply.post_id, []).append(reply)

    for post in posts:
        post.annotated_replies = replies_by_post.get(post.id, [])

    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    unreadnotificationcount = Notification.objects.filter(
            statuses__user=request.user,
            statuses__is_read=False
        ).count()
    

    # detect AJAX/HTMX request to return only the new chunk

    paginator = Paginator(posts, 10)  # Show 10 posts per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)


    if request.headers.get("Hx-Request"):  
        return render(request, "partials/question_list_items.html", {"page_obj": page_obj})

    context = {
        # 'posts': posts,
        'page_obj': page_obj,
        'viewing_user': request.user,
        # 'user': request.user,
        'tag_choices': get_tag_choices(),
        "notifications": notifications,
        'unreadnotificationcount': unreadnotificationcount,
        'online_users': online_users,
        'online_count': online_count,
        'everyone_count': everyone_count,
        'tag': tag,
    }
    return render(request, 'discussion/questions-land.html', context)


def view_profile(request, id):
    viewing_user = get_object_or_404(CustomUser, id=id)
    is_own_profile = request.user.id == viewing_user.id
    online_users, online_count, everyone_count = get_online_users()
    unreadnotificationcount = Notification.objects.filter(
        statuses__user=request.user, statuses__is_read=False
    ).count() if request.user.is_authenticated else 0

    context = {
        'viewing_user': viewing_user,
        'is_own_profile': is_own_profile,
        'tag_choices': get_tag_choices(),
        'color': "#{:06x}".format(random.randint(0, 0xFFFFFF)),
        'unreadnotificationcount': unreadnotificationcount,
        'online_count': online_count,
        'everyone_count': everyone_count,
    }

    return render(request, 'yuzzaz/view_profiles.html', context)


def post_detail(request, id):
    post = get_object_or_404(Post, id=id)
    all_other_posts = Post.objects.exclude(id=post.id)
    random_posts = random.sample(list(all_other_posts), min(5, all_other_posts.count()))  # max 3 or whatever is available

    post.user_has_upvoted = post.has_user_upvoted(request.user)



    user = request.user
    if user.is_authenticated:
        upvoted_post_ids = set(
            UserPostInteraction.objects.filter(
                user=user, interaction_type='upvote'
            ).values_list('post_id', flat=True)
        )
    else:
        upvoted_post_ids = set()

    for p in random_posts:
        p.user_has_upvoted = p.id in upvoted_post_ids

    context = {
        'post': post,
        'posts': random_posts,
        'viewing_user': request.user,
        'tag_choices': get_tag_choices(),

        'user_has_upvoted': post.user_has_upvoted
    }
    return render(request, 'discussion/post_detail.html', context)

@login_required
def add_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            
            # Auto-update RAG corpus with new post
            try:
                from .utils.ai_rag import get_rag_manager
                rag_manager = get_rag_manager()
                rag_manager.update_corpus_with_new_post(post)
                messages.success(request, 'Post added successfully and indexed for AI assistant!')
            except Exception as e:
                logger.warning(f"Failed to update RAG corpus: {e}")
                messages.success(request, 'Post added successfully!')
            
            return redirect('post_detail', id=post.id)
    else:
        form = PostForm()

    return render(request, 'yuzzaz/partials/add_post_modal.html', {'form': form, 'viewing_user': request.user})



def add_reply(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        content = request.POST.get('reply')
        if content:
            reply = Reply.objects.create(
                post=post,
                replyier=request.user,
                content=content,
                image=request.FILES.get('image'),  # Add these fields
                image2=request.FILES.get('image2'),
                video=request.FILES.get('video'),
                docs=request.FILES.get('docs'),
                link=request.POST.get('link'),  # Also handle link if needed
                tag=request.POST.get('tag')    # And tag if needed
            )
            
            # Auto-update RAG corpus with new reply
            try:
                from .utils.ai_rag import get_rag_manager
                rag_manager = get_rag_manager()
                rag_manager.update_corpus_with_new_reply(reply)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to update RAG corpus with reply: {e}")
            
            # --- Create notification for post.author ---
            if post.author != request.user:  # Avoid notifying self
                post_url = request.build_absolute_uri(
                    reverse("post_detail", args=[post.id])  # make sure your URL name is 'post_detail'
                )

                # Create the notification with HTML link inside message
                notification = Notification.objects.create(
                    user=post.author,
                    title="New reply to your question",
                    # message=f'{request.user.nickname} replied to your question: <a href="{post_url}">{post.title}</a>',
                    message=(
                    f'{request.user.nickname} replied to your question: '
                    f'<a href="{post_url}" class="text-maroon hover:underline">{post.title}</a>'
                ),  
                )
                # Create unread status
                UserNotificationStatus.objects.create(
                    user=post.author,
                    notification=notification,
                    is_read=False
                )
            if request.headers.get('HX-Request'):
                return render(request, 'partials/threaded_replies.html', {
                    'group': reply
                })
            messages.success(request, 'Reply added successfully!')
            return redirect('post_detail', id=post.id)
        else:
            messages.error(request, 'Reply content cannot be empty.')
    return render(request, 'partials/threaded_replies.html', {'post': post})



def get_replies_count(request, post_id):
    from .models import Reply
    count = Reply.objects.filter(post_id=post_id).count()
    return HttpResponse(count)


def replies_counts_api(request):
    from .models import Reply
    from django.db.models import Count
    ids_param = request.GET.get('ids', '')
    post_ids = [int(i) for i in ids_param.split(',') if i.strip().isdigit()]
    if not post_ids:
        return JsonResponse({'counts': {}})
    rows = (Reply.objects
            .filter(post_id__in=post_ids)
            .values('post_id')
            .annotate(count=Count('id')))
    counts = {str(row['post_id']): row['count'] for row in rows}
    for pid in post_ids:
        counts.setdefault(str(pid), 0)
    return JsonResponse({'counts': counts})




def toggle_upvote(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    user = request.user
    if not user.is_authenticated:
        return HttpResponse("Unauthorized", status=401)

    upvote = UserPostInteraction.objects.filter(user=user, post=post, interaction_type='upvote')

    if upvote.exists():
        upvote.delete()  # remove upvote
        post.user_has_upvoted = False
    else:
        UserPostInteraction.objects.filter(user=user, post=post, interaction_type='downvote').delete()
        UserPostInteraction.objects.create(user=user, post=post, interaction_type='upvote')
        post.user_has_upvoted = True

    if request.headers.get('HX-Request'):
        return render(request, "partials/upvote_button.html", {"post": post, "user_has_upvoted": post.user_has_upvoted})

    return redirect("post_detail", id=post.id)


def toggle_reply_upvote(request, reply_id):
    reply = get_object_or_404(Reply, id=reply_id)
    user = request.user
    
    if not user.is_authenticated:
        return HttpResponse("Unauthorized", status=401)

    upvote = ReplyInteraction.objects.filter(
        user=user, 
        reply=reply, 
        interaction_type='upvote'
    )

    if upvote.exists():
        upvote.delete()  # remove upvote
        reply.has_user_upvoted = False
    else:
        # Remove any existing downvote before adding upvote
        ReplyInteraction.objects.filter(
            user=user, 
            reply=reply, 
            interaction_type='downvote'
        ).delete()
        
        ReplyInteraction.objects.create(
            user=user, 
            reply=reply, 
            interaction_type='upvote'
        )
        reply.has_user_upvoted = True

    if request.headers.get('HX-Request'):
        return render(request, "partials/reply_upvote_button.html", {
            "group": reply,
            "has_user_upvoted": reply.has_user_upvoted
        })

    return redirect("post_detail", id=reply.post.id)


# @login_required
# def add_reply_to_reply(request, reply_id=None, parent_id=None):
#     """
#     Handles creating a reply to either:
#     - A Reply (reply_id is set)
#     - Another ReplytoAReply (parent_id is set)
#     """
#     if request.method == "POST":
#         reply_instance = None
#         parent_instance = None

#         if reply_id:
#             reply_instance = get_object_or_404(Reply, id=reply_id)
#         elif parent_id:
#             parent_instance = get_object_or_404(ReplytoAReply, id=parent_id)

#         new_reply = ReplytoAReply(
#             reply=reply_instance,
#             parent=parent_instance,
#             replyier=request.user,
#             content=request.POST.get("reply", "")
#         )

#         # Handle file uploads
#         for field in ["image", "image2", "video", "docs", "link"]:
#             if field in request.FILES:
#                 setattr(new_reply, field, request.FILES[field])
#             elif field in request.POST and request.POST.get(field):
#                 setattr(new_reply, field, request.POST.get(field))

#         new_reply.save()
        
#         if reply_id:
#             if request.headers.get("HX-Request"):
#                 return render(request, "partials/child_dict_replies.html", {
#                     "child_dict": new_reply
#                 })
#         elif parent_id:
#             if request.headers.get("HX-Request"):
#                 return render(request, "partials/grandchild_replies.html", {
#                     "grandchild": new_reply
#                 })

#         # Redirect back to post detail
#         if reply_instance:
#             return redirect("post_detail", id=reply_instance.post.id)
#         elif parent_instance:
#             return redirect("post_detail", id=parent_instance.reply.post.id)

#     return HttpResponse("Invalid request", status=400)


@login_required
def add_reply_to_reply(request, reply_id=None, parent_id=None):
    """
    Handles creating a reply to either:
    - A Reply (reply_id is set)
    - Another ReplytoAReply (parent_id is set)
    """
    if request.method == "POST":
        reply_instance = None
        parent_instance = None

        if reply_id:
            reply_instance = get_object_or_404(Reply, id=reply_id)
        elif parent_id:
            parent_instance = get_object_or_404(ReplytoAReply, id=parent_id)

        new_reply = ReplytoAReply(
            reply=reply_instance,
            parent=parent_instance,
            replyier=request.user,
            content=request.POST.get("reply", "")
        )

        # Handle file uploads
        for field in ["image", "image2", "video", "docs", "link"]:
            if field in request.FILES:
                setattr(new_reply, field, request.FILES[field])
            elif field in request.POST and request.POST.get(field):
                setattr(new_reply, field, request.POST.get(field))

        new_reply.save()
# 🔔 Create notification for the correct user
        if reply_instance:  # replying to a Reply
            post = reply_instance.post
            post_url = reverse("post_detail", args=[post.id])
            if reply_instance.replyier != request.user:  # don’t notify self
                notification = Notification.objects.create(
                    user=reply_instance.replyier,
                    title="New reply to your comment",
                    message=(
                        f'{request.user.nickname} replied to your comment on: '
                        f'<a href="{post_url}" class="text-maroon hover:underline">{reply_instance.content}</a>'
                    ),
                )
                # Create unread status
                UserNotificationStatus.objects.create(
                    user=reply_instance.replyier,
                    notification=notification,
                    is_read=False
                )

        elif parent_instance:  # replying to a ReplytoAReply
            # post = parent_instance.reply.post
            # climb up until we hit a Reply that has a post
            root = parent_instance
            while root.parent:  # keep moving up if there's another parent
                root = root.parent

            post = root.reply.post

            post_url = reverse("post_detail", args=[post.id])
            if parent_instance.replyier != request.user:  # don’t notify self
                notification = Notification.objects.create(
                    user=parent_instance.replyier,
                    title="New reply to your thread",
                    message=(
                        f'{request.user.nickname} replied to your thread on: '
                        f'<a href="{post_url}" class="text-maroon hover:underline">{parent_instance.content}</a>'
                    ),
                )
                # Create unread status
                UserNotificationStatus.objects.create(
                    user=parent_instance.replyier,
                    notification=notification,
                    is_read=False
                )


        # Handle HTMX partial return
        if reply_id:
            if request.headers.get("HX-Request"):
                return render(request, "partials/child_dict_replies.html", {
                    "child_dict": new_reply
                })
        elif parent_id:
            if request.headers.get("HX-Request"):
                return render(request, "partials/grandchild_replies.html", {
                    "grandchild": new_reply
                })

        # Redirect back to post detail
        if reply_instance:
            return redirect("post_detail", id=reply_instance.post.id)
        elif parent_instance:
            return redirect("post_detail", id=parent_instance.reply.post.id)

    return HttpResponse("Invalid request", status=400)


@login_required
def toggle_reply_to_reply_upvote(request, rtr_id):
    """Toggle upvote for a ReplytoAReply object"""
    reply_obj = get_object_or_404(ReplytoAReply, id=rtr_id)
    user = request.user

    upvote = ReplytoReplyInteraction.objects.filter(
        user=user,
        reply=reply_obj,
        interaction_type="upvote"
    )

    if upvote.exists():
        upvote.delete()
        reply_obj.has_user_upvoted = False
    else:
        # Remove downvote first
        ReplytoReplyInteraction.objects.filter(
            user=user,
            reply=reply_obj,
            interaction_type="downvote"
        ).delete()

        ReplytoReplyInteraction.objects.create(
            user=user,
            reply=reply_obj,
            interaction_type="upvote"
        )
        reply_obj.has_user_upvoted = True

    if request.headers.get("HX-Request"):
        return render(request, "partials/reply_to_reply_upvote_button.html", {
            "reply": reply_obj,
            "has_user_upvoted": reply_obj.has_user_upvoted
        })

    return redirect("post_detail", id=reply_obj.reply.post.id)



@login_required
def mark_all_notifications_read(request):
    user = request.user
    UserNotificationStatus.objects.filter(user=user, is_read=False).update(is_read=True, read_at=timezone.now())

    # HTMX response: return empty or a small snippet to update the count
    return HttpResponse('')  # or return a snippet to remove/update the badge


def ai_assistant_view(request):
    """AI Assistant page for asking questions"""
    # Get the same context data that other views use
    online_users, online_count, everyone_count = get_online_users()
    
    # Get unread notification count if user is authenticated
    unreadnotificationcount = 0
    if request.user.is_authenticated:
        unreadnotificationcount = Notification.objects.filter(
            statuses__user=request.user,
            statuses__is_read=False
        ).count()
    
    context = {
        'page_title': 'AI Assistant',
        'user': request.user if request.user.is_authenticated else None,
        'viewing_user': request.user if request.user.is_authenticated else None,
        'unreadnotificationcount': unreadnotificationcount,
        'online_users': online_users,
        'online_count': online_count,
        'everyone_count': everyone_count,
        'tag_choices': get_tag_choices(),
    }
    return render(request, 'discussion/ai_assistant.html', context)

def ai_query_api(request):
    """API endpoint for AI queries"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        data = json.loads(request.body)
        question = data.get('question', '').strip()
        
        if not question:
            return JsonResponse({'error': 'Question is required'}, status=400)
        
        from .utils.ai_rag import get_rag_manager
        rag_manager = get_rag_manager()
        
        # Get AI answer with sources
        try:
            # Extract sources using the new enhanced method
            sources = rag_manager.extract_sources_from_retrieval(question, top_k=5)
            
            # Generate AI answer
            ai_answer = rag_manager.generate_ai_answer(question)
            
            # Format sources for frontend with proper URLs
            formatted_sources = []
            for source in sources:
                if source.get('post_id'):
                    formatted_sources.append({
                        'reference_id': source['reference_id'],
                        'post_id': source['post_id'],
                        'title': source['title'],
                        'author': source['author'],
                        'content_snippet': source['content_snippet'],
                        'tag': source['tag'],
                        'upvotes': source['upvotes'],
                        'replies_count': source['replies_count'],
                        'url': f'/post/{source["post_id"]}/',  # Updated URL format
                        'confidence_score': source['confidence_score']
                    })
            
            return JsonResponse({
                'success': True,
                'answer': ai_answer,
                'sources': formatted_sources,
                'question': question,
                'sources_count': len(formatted_sources)
            })
            
        except Exception as e:
            return JsonResponse({
                'error': f'AI service error: {str(e)}',
                'fallback_message': 'Sorry, the AI assistant is currently unavailable. Please try again later.'
            }, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ── Stories ────────────────────────────────────────────────────────────────────

def story_list(request):
    from .models import Story, STORY_TAG_CHOICES
    stories = Story.objects.select_related('author').all()
    tag_filter = request.GET.get('tag')
    if tag_filter:
        stories = stories.filter(tag=tag_filter)
    context = {
        'stories': stories,
        'tag_filter': tag_filter,
        'story_tags': STORY_TAG_CHOICES,
    }
    if request.user.is_authenticated:
        online_users, online_count, everyone_count = get_online_users()
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
        unreadnotificationcount = Notification.objects.filter(
            statuses__user=request.user, statuses__is_read=False
        ).count()
        context.update({
            'online_users': online_users,
            'online_count': online_count,
            'everyone_count': everyone_count,
            'notifications': notifications,
            'unreadnotificationcount': unreadnotificationcount,
            'viewing_user': request.user,
        })
    return render(request, 'discussion/stories_list.html', context)


def stories_filter_api(request):
    from .models import Story
    tag = request.GET.get('tag', '')
    stories_qs = Story.objects.select_related('author').all()
    if tag:
        stories_qs = stories_qs.filter(tag=tag)
    data = []
    for story in stories_qs:
        data.append({
            'id': story.id,
            'title': story.title,
            'summary': story.summary,
            'tag': story.tag,
            'tag_display': story.get_tag_display(),
            'views': story.views,
            'created_at': story.created_at.isoformat(),
            'cover_image': story.cover_image.url if story.cover_image else None,
            'author_nickname': story.author.nickname,
            'author_profile_picture': story.author.profile_picture.url if story.author.profile_picture else None,
        })
    return JsonResponse({'stories': data, 'tag': tag})


def story_detail(request, id):
    from .models import Story
    story = get_object_or_404(Story, id=id)
    story.views += 1
    story.save(update_fields=['views'])
    context = {'story': story}
    if request.user.is_authenticated:
        online_users, online_count, everyone_count = get_online_users()
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
        unreadnotificationcount = Notification.objects.filter(
            statuses__user=request.user, statuses__is_read=False
        ).count()
        context.update({
            'online_users': online_users,
            'online_count': online_count,
            'everyone_count': everyone_count,
            'notifications': notifications,
            'unreadnotificationcount': unreadnotificationcount,
            'viewing_user': request.user,
        })
    return render(request, 'discussion/story_detail.html', context)


@login_required
def create_story(request):
    from .models import Story, STORY_TAG_CHOICES
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        summary = request.POST.get('summary', '').strip()
        body = request.POST.get('body', '').strip()
        tag = request.POST.get('tag', 'other')
        cover_image = request.FILES.get('cover_image')
        if title and summary and body:
            story = Story.objects.create(
                author=request.user,
                title=title,
                summary=summary,
                body=body,
                tag=tag,
                cover_image=cover_image,
            )
            messages.success(request, 'Your story has been published!')
            return redirect('story_detail', id=story.id)
        else:
            messages.error(request, 'Please fill in all required fields.')
    online_users, online_count, everyone_count = get_online_users()
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    unreadnotificationcount = Notification.objects.filter(
        statuses__user=request.user, statuses__is_read=False
    ).count()
    context = {
        'story_tags': STORY_TAG_CHOICES,
        'online_users': online_users,
        'online_count': online_count,
        'everyone_count': everyone_count,
        'notifications': notifications,
        'unreadnotificationcount': unreadnotificationcount,
        'viewing_user': request.user,
    }
    return render(request, 'discussion/create_story.html', context)