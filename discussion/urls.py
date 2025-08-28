from django.urls import path
from discussion import views

urlpatterns = [

    path('', views.questions, name='questions'),
    path('profile/<int:id>/', views.view_profile, name='view_profile'),
    path('post/<int:id>/', views.post_detail, name='post_detail'),
    path('add-post/', views.add_post, name='add_post'),
    path('search/', views.search_content, name='search_content'),

    #test
    path('add_reply/<int:post_id>/', views.add_reply, name='add_reply'),
    path('get_replies_count/<int:post_id>/', views.get_replies_count, name='get_replies_count'),
    path("toggle-upvote/<int:post_id>/", views.toggle_upvote, name="toggle_upvote"),
    path('reply/<int:reply_id>/upvote/', views.toggle_reply_upvote, name='toggle_reply_upvote'),
    # path('reply/<int:group_id>/upvote/', views.toggle_reply_upvote, name='toggle_reply_upvote'),
    
    
    
    path("reply-to-reply/<int:reply_id>/", views.add_reply_to_reply, name="add_reply_to_reply"),
    path("reply-to-a-reply/<int:parent_id>/", views.add_reply_to_reply, name="add_reply_to_a_reply"),
    path("toggle-rtr-upvote/<int:rtr_id>/", views.toggle_reply_to_reply_upvote, name="toggle_reply_to_reply_upvote"),

    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    
    # AI Assistant routes
    path('ai/', views.ai_assistant_view, name='ai_assistant'),
    path('api/ai-query/', views.ai_query_api, name='ai_query_api'),
]