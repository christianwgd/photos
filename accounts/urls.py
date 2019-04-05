from django.urls import path

from . import views as local_views
from django.contrib.auth import views as auth_views
from rest_framework.authtoken import views as rest_framework_views

urlpatterns = [
    # Session Login
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='accounts/logged_out.html'), name='logout'),
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='accounts/password_change_form.html'), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='accounts/password_change_done.html'), name='password_change_done'),
    path('get_auth_token/', rest_framework_views.obtain_auth_token,
         name='get_auth_token'),
]
