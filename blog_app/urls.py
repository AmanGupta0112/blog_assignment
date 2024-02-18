from django.urls import path
from . import views

urlpatterns = [
    path("user_blogs/", views.user_blog, name="user_blogs"),
    path("create_blog/", views.create_blog, name="create_blog"),
    path("delete_blog/", views.delete_blog, name="delete_blog"),
    path("see_blog/<id>", views.see_blog, name="see_blog"),
    path("edit_blog/<id>", views.edit_blog,name="edit_blog"),
]
