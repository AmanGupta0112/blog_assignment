from django.shortcuts import get_object_or_404, render, redirect
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from . import models
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
import json
from django.core.serializers import serialize
from django.utils import timezone
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth import logout


def logout_view(request):
    logout(request)
    return redirect("/login/")


def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, "Login successful.")
            return redirect("/blog/user_blogs/")
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, "blog_app/login.html")


@login_required
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_blog(request):
    if request.user.is_authenticated:
        blogs = models.Blog.objects.filter(author_id=request.user.id).annotate(
            likes_count=Count("response", filter=Q(response__like=True)),
            dislikes_count=Count("response", filter=Q(response__dislike=True)),
            comments_count=Count("comment"),
        )
        top_commented_blogs = (
            models.Blog.objects.filter(author_id=request.user.id)
            .annotate(comments_count=Count("comment"))
            .order_by("-comments_count")[:5]
        )
        three_days_ago = timezone.now() - timezone.timedelta(days=3)
        top_liked_blogs = (
            models.Blog.objects.filter(
                author_id=request.user.id,
                response__like=True,
                response__response_date__gte=three_days_ago,
            )
            .annotate(likes_count=Count("response"))
            .order_by("-likes_count")[:5]
        )

        top_disliked_blogs = (
            models.Blog.objects.filter(
                author_id=request.user.id,
                response__dislike=True,
                response__response_date__gte=three_days_ago,
            )
            .annotate(dislikes_count=Count("response"))
            .order_by("-dislikes_count")[:5]
        )
        context = {
            "author": request.user.username,
            "blogs": json.loads(serialize("json", blogs)),
            "top_commented_blogs": json.loads(serialize("json", top_commented_blogs)),
            "top_liked_blogs": json.loads(serialize("json", top_liked_blogs)),
            "top_disliked_blogs": json.loads(serialize("json", top_disliked_blogs)),
        }

        return JsonResponse(context, safe=False)
    return JsonResponse(None, safe=False)


@login_required
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_blog(request):
    if request.method == "POST":
        request_body = json.loads(request.body.decode("utf-8"))
        name = request_body.get("name")
        content = request_body.get("content")

        new_blog = models.Blog.objects.create(
            name=name,
            content=content,
            author_id=request.user.id,
        )
        return JsonResponse(json.loads(serialize("json", [new_blog])), safe=False)


@login_required
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def delete_blog(request):
    if request.method == "POST":
        try:
            blog_id = json.loads(request.body.decode("utf-8")).get("id")
            blog = get_object_or_404(models.Blog, id=blog_id)
            if request.user.id == blog.author.id:
                blog.delete()
                return JsonResponse({"message": "Blog deleted successfully!!"})
            else:
                return JsonResponse({"message": "You are not the owner!!"})
        except Exception as e:
            print("Error deleting blog", e)
            return JsonResponse({"message": "Something went wrong!!"})


@login_required
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def see_blog(request, id=None):
    try:
        blog = get_object_or_404(models.Blog, id=id)
        return JsonResponse(json.loads(serialize("json", [blog])), safe=False)
    except Exception as e:
        print("Error during view", e)
        return JsonResponse(
            {
                "message": f"Blog didn't found with id : {id}!! Try again with correct id!!!"
            }
        )


@login_required
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def edit_blog(request, id=None):
    try:
        if request.method == "POST":
            request_body = json.loads(request.body.decode("utf-8"))
            blog_to_update = get_object_or_404(models.Blog, id=id)
            if request.user.id == blog_to_update.author.id:
                blog_to_update.name = (
                    request_body.get("name", " ")
                    if request_body.get("name", " ") != " "
                    else blog_to_update.name
                )
                blog_to_update.content = (
                    request_body.get("content")
                    if request_body.get("content", " ") != " "
                    else blog_to_update.content
                )
                blog_to_update.save()
                return JsonResponse(
                    json.loads(serialize("json", [blog_to_update])), safe=False
                )
            else:
                return JsonResponse(
                    {"message": "You are not allowed to edit this blog!!"}, safe=False
                )
    except Exception as e:
        print("Error deleting blog", e)
        return JsonResponse({"message": f"{e}"})


@login_required
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_recent_liked_blogs(request):
    user = request.user
    my_recent_liked_blogs = models.Blog.objects.filter(
        response__user=user, response__like=True
    ).order_by("-response__response_date")[:5]
    my_comment_history = models.Comment.objects.filter(user=user)

    author_id = request.GET.get("author_id")
    if author_id:
        author = get_object_or_404(User, id=author_id)
        my_comment_history_for_author = models.Comment.objects.filter(
            user=user, blog__author=author
        )

    context = {
        "my_recent_liked_blogs": json.loads(serialize("json", my_recent_liked_blogs)),
        "my_comment_history": json.loads(serialize("json", my_comment_history)),
        "my_comment_history_for_author": json.loads(
            serialize("json", my_comment_history_for_author)
        ),
    }

    return JsonResponse(context, safe=False)
