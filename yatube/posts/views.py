from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render, redirect

from .forms import PostForm, CommentForm
from .models import User, Group, Post, Follow

from yatube.settings import POSTS_ON_PAGE


def page_of_paginator(request, post_list):
    paginator = Paginator(post_list, POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


def index(request):
    return render(request, 'posts/index.html', {
        'page_obj': page_of_paginator(request, Post.objects.all())
    })


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    return render(request, 'posts/group_list.html', {
        'group': group,
        'page_obj': page_of_paginator(request, group.posts.all())
    })


def profile(request, username):
    author = get_object_or_404(User, username=username)
    following = (
        request.user.is_authenticated and request.user != username
        and Follow.objects.filter(author=author, user=request.user).exists()
    )
    return render(request, 'posts/profile.html', {
        'author': author,
        'following': following,
        'page_obj': page_of_paginator(request, author.posts.all()),
    })


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    return render(request, 'posts/post_detail.html', {
        'post': post,
        'form': form,
    })


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', request.user)


@login_required
def post_edit(request, post_id):
    is_edit = True
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post.id)
    form = PostForm(
        request.POST or None,
        instance=post,
        files=request.FILES or None,
    )
    if form.is_valid():
        post = form.save()
        return redirect('posts:post_detail', post.id)
    return render(
        request,
        'posts/create_post.html',
        {'is_edit': is_edit, 'form': form, 'post': post}
    )


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    return render(request, 'posts/follow.html', {
        'page_obj': page_of_paginator(request, posts),
    })


@login_required
def profile_follow(request, username):
    # Подписаться на автора
    author = get_object_or_404(User, username=username)
    if author != request.user and Follow.objects.filter(
        user=request.user,
        author=author
    ).exists() is False:
        Follow.objects.create(user=request.user, author=author)
    return redirect('posts:profile', author.username)


@login_required
def profile_unfollow(request, username):
    # Отписка
    Follow.objects.filter(
        author__username=username,
        user=request.user
    ).delete()
    return redirect('posts:profile', username)
