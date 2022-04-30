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
from django.views.i18n import JavaScriptCatalog

from backend.views import organization, preview, profile
from backend.views.widgets import martor_image_uploader

admin.autodiscover()

def paged_list_view(view, name):
    return include([
        path('', view.as_view(), name=name),
        path('<slug:page>', view.as_view(), name=name),
    ])

accounts_patterns = [
    path('accounts/register/', profile.RegistrationView.as_view(), name='register'),
    path('accounts/login/', profile.LoginView.as_view(), name='login'),
    path('accounts/logout/', profile.LogoutView.as_view(), name='logout'),
    path('accounts/change_password/', profile.PasswordChangeView.as_view(), name='change_password'),
    path('accounts/profile/', profile.UserPage.as_view(), name='user_page'),
    path('accounts/profile/<slug:user>/', include([
        path('', profile.UserPage.as_view(), name='user_page'),
        path('edit/', profile.EditProfile.as_view(), name='user_edit'),
    ]))
]

organization_patterns = [
    path('organizations/', organization.OrganizationList.as_view(), name='organization_list'),
    path('organization/<slug:organization>/', include([
        path('', organization.OrganizationHome.as_view(), name='organization_home'),
        path('users/', organization.OrganizationUsers.as_view(), name='organization_users'),
        path('join/', organization.JoinOrganization.as_view(), name='join_organization'),
        path('leave/', organization.LeaveOrganization.as_view(), name='leave_organization'),
        path('edit/', organization.EditOrganization.as_view(), name='edit_organization'),
        path('kick/', organization.KickUserWidgetView.as_view(), name='organization_kick_user'),

        path('request/', organization.RequestJoinOrganization.as_view(), name='request_organization'),
        path('request/<int:pk>/', organization.OrganizationRequestDetail.as_view(), name="request_organization_detail"),

        path('requests/', include([
            path('pending/', organization.OrganizationRequestView.as_view(), name="organization_requests_pending"),
            path('log/', organization.OrganizationRequestLog.as_view(), name='organization_requests_log'),
        ]))
    ])) 
]


urlpatterns = [
    path('admin/', admin.site.urls),
    path('martor/', include('martor.urls')),
    path("select2/", include("django_select2.urls")),
    path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
    path('', include('education.urls')),
    path('backend/', include('backend.urls')),
]


urlpatterns += accounts_patterns

urlpatterns += organization_patterns

urlpatterns += [
    path('users/', profile.UserList.as_view(), name='user_list')
]

preview_patterns = [
    path('', preview.MarkdownPreviewView.as_view(), name='markdown_preview'),
    path('self', preview.SelfDescriptionMarkdownPreviewView.as_view(), name='self_preview'),
    path('description', preview.DescriptionMarkdownPreviewView.as_view(), name='description_preview'),
    path('default', preview.DefaultPreviewView.as_view(), name='default_preview'),
    path('description_full', preview.DescriptionFullMarkdownPreviewView.as_view(), name='description_full')
]

urlpatterns += [
    path('widgets/', include([
        path('preview/', include(preview_patterns)),
        path('martor/', include([
            path('upload-image', martor_image_uploader, name='martor_image_uploader'),
        ])),
    ]))
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)