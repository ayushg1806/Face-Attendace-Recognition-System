from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('register-face/', views.register_face_view, name='register_face'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('recognize/', views.recognize_view, name='recognize'),
    path('attendance-list/', views.attendance_list_view, name='attendance_list'),
]
