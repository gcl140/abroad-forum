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
from yuzzaz.models import CustomUser
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.db.models import Q


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
        print("top order")
        print(posts)

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
        print("controversial order")
        print(posts)
    elif filter_option == 'popular':
        posts = posts.annotate(
            total_votes=Count(Case(
                When(user_interactions__interaction_type__in=['upvote', 'downvote'], then=1),
                output_field=IntegerField()
            ))
        ).order_by('-total_votes', '-created_at')
        print("popular order")
        print(posts)
    else:  # 'recent' or unknown filter
        posts = posts.order_by('-created_at')
        print("normal order")

    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    unreadnotificationcount = Notification.objects.filter(
        statuses__user=request.user,
        statuses__is_read=False
    ).count()

    context = {
        'posts': posts,
        'viewing_user': request.user,
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
    recent_posts = Post.objects.filter(author=viewing_user).order_by('-created_at')[:2]
    recent_replies = Reply.objects.filter(replyier=viewing_user).order_by('-created_at')[:2] 
    recent_child_replies = ReplytoAReply.objects.filter(replyier=viewing_user).order_by('-created_at')[:2] 
    
    context = {
        'viewing_user': viewing_user,
        'is_own_profile': is_own_profile,
        'recent_posts': recent_posts,
        'recent_replies': recent_replies,
        'recent_child_replies': recent_child_replies,
        'tag_choices': get_tag_choices(),
        'color': "#{:06x}".format(random.randint(0, 0xFFFFFF))
    }
    
    return render(request, 'yuzzaz/view_profiles.html', context)


def post_detail(request, id):
    post = get_object_or_404(Post, id=id)
    all_other_posts = Post.objects.exclude(id=post.id)
    random_posts = random.sample(list(all_other_posts), min(5, all_other_posts.count()))  # max 3 or whatever is available

    context = {
        'post': post,
        'posts': random_posts,
        'viewing_user': request.user,
        'tag_choices': get_tag_choices(),

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
            messages.success(request, 'Post added successfully!')
            return redirect('post_detail', id=post.id)
    else:
        form = PostForm()

    return render(request, 'yuzzaz/partials/add_post_modal.html', {'form': form, 'viewing_user': request.user})























# Create your views here.
# def questions(request):
#     posts = Post.objects.all().order_by('-created_at')
#     notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
#     unreadnotificationcount = Notification.objects.filter(
#         statuses__user=request.user,
#         statuses__is_read=False
#     ).count()

#     context = {
#         'posts': posts,
#         'viewing_user': request.user,
#         'tag_choices': get_tag_choices(),
#         "notifications": notifications,
#         # "unread_count": sum(1 for n in notifications if not n["is_read"]),
#         'unreadnotificationcount': unreadnotificationcount

#     }
#     return render(request, 'discussion/questions-land.html', context)





# def view_profile(request, id):
#     user_profile = get_object_or_404(CustomUser, id=id)
#     is_owner = request.user.id == user_profile.id
#     return render(request, 'yuzzaz/view_profiles.html', {
#         'user_profile': user_profile,
#         'is_owner': is_owner
#     })



# @login_required




def add_reply(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        content = request.POST.get('reply')
        if content:
            reply = Reply.objects.create(
                post=post,
                replyier=request.user,
                content=content
            )
            if request.headers.get('HX-Request'):
                return render(request, 'partials/threaded_replies copy.html')
            
            messages.success(request, 'Reply added successfully!')
            return redirect('post_detail', id=post.id)
        else:
            messages.error(request, 'Reply content cannot be empty.')
    
    # return redirect('post_detail', id=post.id)
    # return render(request, 'partials/threaded_replies.html', {'post': post})
    return render(request, 'partials/threaded_replies copy.html', {'post': post})
