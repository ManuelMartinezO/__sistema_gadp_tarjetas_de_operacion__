from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('logup/', views.logup_view, name='logup'),
    path('logout/', views.logout_view, name='logout'),
    path('login/', views.login_view, name='login'),
]