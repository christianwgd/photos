# -*- coding: utf-8 -*-

"""photos URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
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
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView
from rest_framework import routers, authentication
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from filebrowser.sites import site

from . import views


router = routers.DefaultRouter()
router.register(r'events', views.EventViewSet)
router.register(r'tags', views.TagViewSet)
router.register(r'imports', views.ImportViewSet)
router.register(r'photos', views.PhotoViewSet)
router.register(r'users', views.UserViewSet)
router.register(r'photo_exif', views.PhotoExifViewSet)

schema_view = get_schema_view(
   openapi.Info(
      title="Photo API",
      default_version='v1',
   ),
   authentication_classes=(
        authentication.SessionAuthentication,
    ),
)

app_name = 'photos'

urlpatterns = [
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('admin/filebrowser/', site.urls),
    path('admin/', admin.site.urls),
    path('select2/', include('django_select2.urls')),

    path('settings/', include('usersettings.urls')),

    path('', RedirectView.as_view(url='/photolist/')),
    path('photolist/', views.photolist, name='photolist'),
    path('detail/<int:pk>/', views.PhotoDetailView.as_view(), name='photodetail'),
    path('display/<int:pk>/', views.PhotoDisplayView.as_view(), name='display'),
    path('new/', views.new, name='new'),
    path('edit/<int:pk>/', views.PhotoUpdateView.as_view(), name='photoedit'),
    path('imgedit/<int:photo_id>/', views.imgedit, name='imgedit'),
    path('file-upload', views.fileupload, name='fileupload'),
    path('delete/<int:photo_id>/', views.delete, name='photodelete'),
    path('geocode/', views.geocode, name='geocode'),
    path('photomap/', views.PhotoMapView.as_view(), name='photomap'),
    path('myshares/', views.PhotoShareView.as_view(), name='myshares'),

    path('processdelete/', views.processdelete, name='processdelete'),
    path('processshare/', views.processshare, name='processshare'),
    path('removeshare/<int:photo_id>/<int:user_id>/', views.removeshare, name='removeshare'),
    path('removeshareevent/<int:event_id>/<int:user_id>/', views.removeshareevent, name='removeshareevent'),
    path('processassign/', views.processassign, name='processassign'),
    path('preparedownload/', views.preparedownload, name='preparedownload'),
    path('processdownload/', views.processdownload, name='processdownload'),

    path('eventlist/', views.EventListView.as_view(), name='eventlist'),
    path('eventcreate/', views.EventCreateView.as_view(), name='eventcreate'),
    path('eventupdate/<int:pk>/',
         views.EventUpdateView.as_view(), name='eventupdate'),
    path('eventdelete/<int:pk>/',
         views.EventDeleteView.as_view(), name='eventdelete'),

    path('taglist/', views.TagListView.as_view(), name='taglist'),
    path('tagcreate/', views.TagCreateView.as_view(), name='tagcreate'),
    path('tagupdate/<int:pk>/', views.TagUpdateView.as_view(), name='tagupdate'),
    path('tagdelete/<int:pk>/', views.TagDeleteView.as_view(), name='tagdelete'),

    path('photos/', include(router.urls)),
    path('accounts/', include('accounts.urls')),

]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
