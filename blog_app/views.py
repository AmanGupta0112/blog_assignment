from django.shortcuts import  get_object_or_404
from django.http import JsonResponse
from django.db.models import Count,Q
from . import models
from django.views.decorators.csrf import csrf_exempt
import json
from django.core.serializers import serialize
from django.utils import timezone


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
    return JsonResponse(None,safe=False)


@csrf_exempt
def create_blog(request):
    if request.method == "POST":
        request_body = json.loads(request.body.decode("utf-8"))
        name = request_body.get("name")
        content = request_body.get("content")

        new_blog = models.Blog.objects.create(
            name=name,
            content=content,
            author_id= 1,
        )
        return JsonResponse(json.loads(serialize("json", [new_blog])), safe=False)


@csrf_exempt
def delete_blog(request):
    if request.method == "POST":
        try:
            blog_id = json.loads(request.body.decode("utf-8")).get("id")
            blog = get_object_or_404(models.Blog, id=blog_id)
            if 1 == blog.author.id:
                blog.delete()
                return JsonResponse({"message": "Blog deleted successfully!!"})
            else:
                return JsonResponse({"message": "You are not the owner!!"})
        except Exception as e:
            print("Error deleting blog", e)
            return JsonResponse({"message": "Something went wrong!!"})


@csrf_exempt
def see_blog(request,id=None):
    try:
        blog = get_object_or_404(models.Blog, id=id)
        return JsonResponse(json.loads(serialize("json", [blog])), safe=False)
    except Exception as e:
        print("Error during view", e)
        return JsonResponse({"message":f"Blog didn't found with id : {id}!! Try again with correct id!!!"})


@csrf_exempt
def edit_blog(request,id=None):
    try:
        if request.method == "POST":
            request_body = json.loads(request.body.decode("utf-8"))
            blog_to_update = get_object_or_404(models.Blog, id=id)
            if 2 == blog_to_update.author.id:
                blog_to_update.name = (
                    request_body.get('name', " ")
                    if request_body.get('name'," ") != " "
                    else blog_to_update.name
                )
                blog_to_update.content = (
                    request_body.get("content")
                    if request_body.get("content", " ") != " "
                    else blog_to_update.content
                )
                blog_to_update.save()
                return JsonResponse(json.loads(serialize("json", [blog_to_update])), safe=False)
            else:
                return JsonResponse({"message":"You are not allowed to edit this blog!!"}, safe=False)
    except Exception as e:
        print("Error deleting blog", e)
        return JsonResponse({"message":f"{e}"})
