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
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from .models import Post, UserPostInteraction

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

@login_required
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

    context = {
        'posts': posts,
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
    post = get_object_or_404(Post, id=post_id)
    return render(request, 'partials/replies_count.html', {'post': post})




def toggle_upvote(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    user = request.user
    if not user.is_authenticated:
        return HttpResponse("Unauthorized", status=401)

    upvote = UserPostInteraction.objects.filter(user=user, post=post, interaction_type='upvote')
    print(f"Upvote exists? {upvote.exists()} for user {user} and post {post.id}")

    if upvote.exists():
        print("Deleting upvote")
        upvote.delete()  # remove upvote
        post.user_has_upvoted = False
    else:
        print("Creating upvote")
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


from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Reply, ReplyInteraction, ReplytoAReply, ReplytoReplyInteraction

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
            print(f"Adding reply to Reply ID: {reply_id}")
        elif parent_id:
            parent_instance = get_object_or_404(ReplytoAReply, id=parent_id)
            print(f"Adding reply to ReplytoAReply ID: {parent_id}")

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
