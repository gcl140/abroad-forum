from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import path, include
from django.views.static import serve
from django.conf.urls import handler404


handler404 = 'yuzzaz.views.custom_404_view'


def logout_then_google(request):
    logout(request)
    return redirect('/oauth/login/google-oauth2/?next=/profile/')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('yuzzaz.urls')),
    path('', include('discussion.urls')),
    path('oauth/', include('social_django.urls', namespace='social')),
    path('oauth/login/google/', logout_then_google, name='logout_then_google'),
    path("__reload__/", include("django_browser_reload.urls")),
]


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += [
        path('static/<path:path>/', serve, {'document_root': settings.STATIC_ROOT}),
        path('media/<path:path>/', serve, {'document_root': settings.MEDIA_ROOT}),
    ]
