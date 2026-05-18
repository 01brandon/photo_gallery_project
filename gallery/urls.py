from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('photo/<uuid:photo_id>/', views.photo_detail, name='photo_detail'),
    path('profile/<str:username>/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('upload/', views.upload_photo, name='upload_photo'),
    path('photo/<uuid:photo_id>/edit/', views.edit_photo, name='edit_photo'),
    path('photo/<uuid:photo_id>/delete/', views.delete_photo, name='delete_photo'),
    path('photo/<uuid:photo_id>/like/', views.like_photo, name='like_photo'),
    path('photo/<uuid:photo_id>/dislike/', views.dislike_photo, name='dislike_photo'),
    path('my-photos/', views.my_photos, name='my_photos'),
]