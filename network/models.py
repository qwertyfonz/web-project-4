from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    #numFollowers   = models.IntegerField(default=0)
    #numFollowing   = models.IntegerField(default=0)
    pass

class Post(models.Model):
    user        = models.ForeignKey(User, on_delete=models.CASCADE)
    createdDate = models.DateTimeField(null=True)
    numOfLikes  = models.IntegerField(default=0)
    content     = models.TextField(null=True)

class Following(models.Model):
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name="login_user")
    followUser  = models.ForeignKey(User, on_delete=models.CASCADE, related_name="followed_user", null=True)

class Likes(models.Model):
    user        = models.ForeignKey(User, on_delete=models.CASCADE)
    post        = models.ForeignKey(Post, on_delete=models.CASCADE, null=True)