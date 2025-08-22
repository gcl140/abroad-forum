from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView
from django.shortcuts import redirect
from django.contrib.auth import logout


def logout_then_google(request):
    logout(request)
    return redirect('/oauth/login/google-oauth2/?next=/profile/')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('yuzzaz.urls')),
    path('', include('discussion.urls')),
    path('oauth/', include('social_django.urls', namespace='social')),
    path('oauth/login/google/', logout_then_google, name='logout-then-google'),
    path("__reload__/", include("django_browser_reload.urls")),
    path('accounts/login/', RedirectView.as_view(url='/login/', permanent=True)),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
