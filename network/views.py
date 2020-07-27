import json
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .forms import *
from .models import *


def index(request):
    postForm = PostForm(request.POST)
    allPosts = Post.objects.all().order_by("-createdDate")

    # Creates pagination with 10 posts a page
    paginator = Paginator(allPosts, 10)
    page = request.GET.get("page")

    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)

    # Capture values from form input and save new Post
    if request.method == "POST":
        if postForm.is_valid():
            postForm                = postForm.save(commit=False)
            postForm.user           = request.user
            postForm.createdDate    = datetime.now()
            postForm.numOfLikes     = 0
            postForm.save()
            return redirect("index")
    else:
        postForm = PostForm()
    
    # Render all posts page
    return render(request, "network/index.html", {
        "postForm": PostForm(),
        "page"    : page,
        "posts"   : posts
        
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
        username    = request.POST["username"]
        email       = request.POST["email"]

        # Ensure password matches confirmation
        password        = request.POST["password"]
        confirmation    = request.POST["confirmation"]
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
    # Get info for a profile page
    try:
        profileName         = User.objects.get(username=username)
        loggedInUserID      = loggedInUser.id
        usernameID          = profileName.id

        # Check to see if user is already following a profile
        followStatus        = len(Following.objects.filter(user=loggedInUserID, followUser=usernameID)) > 0
    except User.DoesNotExist:
        profileName = None
        followStatus = False
    
    # Checks for number of followers, following, and a list of the profile's posts
    numFollowing    = Following.objects.filter(user=profileName).count()
    numFollowers    = Following.objects.filter(followUser=profileName).count()
    listOfMyPosts   = Post.objects.filter(user=profileName).order_by("-createdDate")

    # Creates pagination with 10 posts a page
    paginator = Paginator(listOfMyPosts, 10)
    page = request.GET.get("page")

    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)

    return render(request, "network/profile.html", {
        "numFollowing"    : numFollowing,
        "numFollowers"    : numFollowers,
        "profileName"     : username,
        "loggedInUser"    : loggedInUser,
        "posts"           : posts,
        "followStatus"    : followStatus,
        "page"            : page
    })

@csrf_exempt
def like(request):
    
    # Get necessary parameters for a like (user, post)
    try:
        requestUser    = request.user
        data           = json.loads(request.body)
        postId         = data.get("postId")
        post           = Post.objects.filter(id=postId).first()

        # Checks to see if a user has liked a post before
        likedPost      = Likes.objects.filter(user=requestUser, post=post)
        ifLikeExists   = len(likedPost) > 0 
        likeStatus     = False

        # If like already exists, then unlike the post
        if ifLikeExists:
            post.numOfLikes = post.numOfLikes - 1
            likedPost.delete()
            

        # If not liked yet, then like the post
        else:
            post.numOfLikes = post.numOfLikes + 1
            likePost = Likes.objects.create(user=requestUser, post=post)
            likeStatus = True
        
        # Save the number of likes on the post
        post.save()

    except:
        return JsonResponse({"error": "Unable to like/unlike."}, status=404)
    return JsonResponse({"numOfLikes": post.numOfLikes, "likeStatus": likeStatus}, status=201)


@login_required
def followingView(request):

    # Query for all distinct followed users
    usersFollowed = Following.objects.filter(user=request.user).values("followUser").distinct()

    # Filter all Posts by those the user follows
    followingPosts = Post.objects.filter(user__in = usersFollowed).order_by("-createdDate")

    # Creates pagination with 10 posts a page
    paginator = Paginator(followingPosts, 10)
    page = request.GET.get("page")

    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)

    return render(request, "network/following.html", {
        "posts" : posts,
        "page"  : page
    })    

def followUnfollow(request):

    # Get necessary variables to follow another user (follow status, username)
    try:
        requestUser     = request.user
        data            = json.loads(request.body)
        action          = data.get("action")
        profileName     = data.get("userProfile")
        userProfile     = User.objects.get(username=profileName)

        # Checks to see if a user is already following another user
        following       = Following.objects.filter(user=requestUser, followUser=userProfile)
        numFollowers    = len(following)
        isFollowing     = numFollowers  > 0 
        followStatus    = False
        
        # If follow button is pressed, then create a new Following object
        if action == "follow" and not isFollowing:
            followingObj = Following.objects.create(user=requestUser, followUser=userProfile)
            numFollowers += 1
            followStatus = True
        # Else, unfollow the user
        else:
            following.delete()
            numFollowers -= 1
            followStatus = False

    except:
        return JsonResponse({"error": "Unable to follow/unfollow."}, status=404)
    return JsonResponse({"numFollowers": numFollowers, "followStatus": followStatus}, status=201)


def edit(request):
    try:
        data        = json.loads(request.body)
        postContent = data.get("postContent")
        postId      = data.get("postId")

        post = Post.objects.filter(id=postId).first()
        post.content = postContent
        post.save()
    except:
        return JsonResponse({"error": "Could not save post."}, status=404)
    return JsonResponse({"success": "Post updated."}, status=201)

