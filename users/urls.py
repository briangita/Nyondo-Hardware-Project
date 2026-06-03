from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import (register,CustomLoginView,approve_users,approve_user,reject_user,manage_users,toggle_user_status)
from django.shortcuts import redirect


urlpatterns = [

    # Authentication
    path('', lambda request: redirect('login')),
    path('register/', register, name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),

    # Admin User Management
    path('approvals/', approve_users, name='approve_users'),
    path('approve/<int:user_id>/', approve_user, name='approve_user'),
    path('reject/<int:user_id>/', reject_user, name='reject_user'),
    
    path('manage/', manage_users, name='manage_users'),
    path('toggle-user/<int:user_id>/', toggle_user_status, name='toggle_user'),

]