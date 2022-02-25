"""emath URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

from backend.views import UserPage, ProfileMarkdownPreviewView, preview
from backend.views.profile import UserList

admin.autodiscover()

def paged_list_view(view, name):
    return include([
        path('', view.as_view(), name=name),
        path('<slug:page>', view.as_view(), name=name),
    ])

urlpatterns = [
    path('admin/', admin.site.urls),
    path('martor/', include('martor.urls')),
    path('', include('education.urls')),
]

urlpatterns += [
    path('users/', UserList.as_view(), name='user_list'),
    path('user/', UserPage.as_view(), name='user_page'),
    path('user/<slug:user>', include([
        path('', UserPage.as_view(), name='user_page'),
    ]))
]

preview_patterns = [
    path('', preview.MarkdownPreviewView.as_view(), name='markdown_preview'),
    path('profile', ProfileMarkdownPreviewView.as_view(), name='profile_preview'),
]

urlpatterns += [
    path('widgets/', include([
        path('preview/', include(preview_patterns)),
    ]))
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)