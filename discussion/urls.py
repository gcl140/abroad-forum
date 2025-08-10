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
]
