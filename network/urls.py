from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
   

    # API Routes
    path("like", views.like, name="like"),
    path("followingview", views.followingView, name="followingview"),
    path("followunfollow", views.followUnfollow, name="followunfollow"),
    path("edit", views.edit, name="edit"),

    path("<str:username>", views.profile, name="profile")
]
