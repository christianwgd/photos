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
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

from . import views


urlpatterns = [
    path('admin/', admin.site.urls),

    path('accounts/login/', auth_views.login,
         {'template_name': 'auth/login.html'}, name='login'),
    path('accounts/logout/', auth_views.logout,
         {'template_name': 'auth/logged_out.html'}, name='logout'),
    path('accounts/password_change/', auth_views.password_change,
         {'template_name': 'auth/password_change_form.html'}, name='password_change'),
    path('accounts/password_change/done/', auth_views.password_change_done,
         {'template_name': 'auth/password_change_done.html'}, name='password_change_done'),

    path('settings/', views.settings, name='settings'),

    path('', views.photolist, name='photolist'),
    path('detail/<int:photo_id>/', views.detail, name='photodetail'),
    path('new/', views.new, name='new'),
    path('file-upload', views.fileupload, name='fileupload'),
    path('delete/<int:photo_id>/', views.delete, name='photodelete'),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
