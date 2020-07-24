from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from datetime import datetime

from .forms import *
from .models import *


def index(request):
    postForm = PostForm(request.POST)

    if request.method == "POST":
        if postForm.is_valid():
            postForm                = postForm.save(commit=False)
            postForm.user           = request.user
            postForm.createdDate    = datetime.now()
            postForm.numOfLikes     = 0
            postForm.save()
            return redirect('index')
    else:
        postForm = PostForm()
    
    return render(request, "network/index.html", {
        "postForm": PostForm(),
        "allPosts": Post.objects.all().order_by('-createdDate')
    })

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")

def profile(request, username):
    loggedInUser = request.user
    profileName = User.objects.get(username=username) 
    numFollowing = Following.objects.filter(user=loggedInUser).count()
    numFollowers = Following.objects.filter(followUser=loggedInUser).count()
    listOfMyPosts = Post.objects.filter(user=profileName).order_by('-createdDate')
    
    if request.method == "POST":
        buttonValue = request.POST.get("button-click", None)

    return render(request, "network/profile.html", {
        "numFollowing": numFollowing,
        "numFollowers": numFollowers,
        "profileName" : username,
        "loggedInUser": request.user.username,
        "myPosts"     : listOfMyPosts
    })
