from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.http import JsonResponse

from .models import CustomUser, Photo, Tag, Like, Dislike
from .forms import (
    CustomUserCreationForm,
    CustomUserChangeForm,
    CustomPasswordChangeForm,
    PhotoForm,
)


def register(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully.')
            return redirect('home')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = CustomUserCreationForm()

    return render(request, 'auth/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}.')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'auth/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('login')


def home(request):
    photos = Photo.objects.select_related('user').prefetch_related('tags')
    tags = Tag.objects.all()

    search_query = request.GET.get('search', '')
    selected_tags = request.GET.getlist('tags')

    if search_query:
        photos = photos.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    if selected_tags:
        photos = photos.filter(tags__id__in=selected_tags).distinct()

    context = {
        'photos': photos,
        'tags': tags,
        'search_query': search_query,
        'selected_tags': selected_tags,
    }

    return render(request, 'gallery/home.html', context)


def photo_detail(request, photo_id):
    photo = get_object_or_404(Photo.objects.select_related('user').prefetch_related('tags'), id=photo_id)

    user_like = None
    user_dislike = None

    if request.user.is_authenticated:
        user_like = Like.objects.filter(photo=photo, user=request.user).exists()
        user_dislike = Dislike.objects.filter(photo=photo, user=request.user).exists()

    context = {
        'photo': photo,
        'user_like': user_like,
        'user_dislike': user_dislike,
        'likes_count': photo.likes.count(),
        'dislikes_count': photo.dislikes.count(),
    }

    return render(request, 'gallery/photo_detail.html', context)


@login_required
def profile(request, username):
    user = get_object_or_404(CustomUser, username=username)
    user_photos = user.photos.all().prefetch_related('tags')

    context = {
        'profile_user': user,
        'photos': user_photos,
        'photo_count': user_photos.count(),
    }

    return render(request, 'profile/profile.html', context)


@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile', username=request.user.username)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = CustomUserChangeForm(instance=request.user)

    return render(request, 'profile/edit_profile.html', {'form': form})


@login_required
def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Password changed successfully.')
            return redirect('profile', username=request.user.username)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = CustomPasswordChangeForm(request.user)

    return render(request, 'profile/change_password.html', {'form': form})


@login_required
def upload_photo(request):
    if request.method == 'POST':
        form = PhotoForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            photo.user = request.user
            photo.save()
            form.save_m2m()
            messages.success(request, 'Photo uploaded successfully.')
            return redirect('home')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = PhotoForm()

    return render(request, 'gallery/upload_photo.html', {'form': form})


@login_required
def edit_photo(request, photo_id):
    photo = get_object_or_404(Photo, id=photo_id)

    if photo.user != request.user:
        messages.error(request, 'You do not have permission to edit this photo.')
        return redirect('photo_detail', photo_id=photo_id)

    if request.method == 'POST':
        form = PhotoForm(request.POST, request.FILES, instance=photo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Photo updated successfully.')
            return redirect('photo_detail', photo_id=photo_id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = PhotoForm(instance=photo)

    return render(request, 'gallery/edit_photo.html', {'form': form, 'photo': photo})


@login_required
def delete_photo(request, photo_id):
    photo = get_object_or_404(Photo, id=photo_id)

    if photo.user != request.user:
        messages.error(request, 'You do not have permission to delete this photo.')
        return redirect('photo_detail', photo_id=photo_id)

    if request.method == 'POST':
        photo.delete()
        messages.success(request, 'Photo deleted successfully.')
        return redirect('home')

    return render(request, 'gallery/delete_photo.html', {'photo': photo})


@login_required
@require_POST
def like_photo(request, photo_id):
    photo = get_object_or_404(Photo, id=photo_id)

    existing_like = Like.objects.filter(photo=photo, user=request.user).first()
    existing_dislike = Dislike.objects.filter(photo=photo, user=request.user).first()

    if existing_like:
        existing_like.delete()
    else:
        if existing_dislike:
            existing_dislike.delete()
        Like.objects.create(photo=photo, user=request.user)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'likes': photo.likes.count(),
            'dislikes': photo.dislikes.count(),
        })

    return redirect('photo_detail', photo_id=photo_id)


@login_required
@require_POST
def dislike_photo(request, photo_id):
    photo = get_object_or_404(Photo, id=photo_id)

    existing_dislike = Dislike.objects.filter(photo=photo, user=request.user).first()
    existing_like = Like.objects.filter(photo=photo, user=request.user).first()

    if existing_dislike:
        existing_dislike.delete()
    else:
        if existing_like:
            existing_like.delete()
        Dislike.objects.create(photo=photo, user=request.user)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'likes': photo.likes.count(),
            'dislikes': photo.dislikes.count(),
        })

    return redirect('photo_detail', photo_id=photo_id)


@login_required
def my_photos(request):
    photos = request.user.photos.all().prefetch_related('tags')

    context = {
        'photos': photos,
    }

    return render(request, 'gallery/my_photos.html', context)