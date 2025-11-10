from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)  # type: ignore
    phone_number = models.CharField(max_length=20, blank=True, null=True)  # type: ignore

    def __str__(self):
        return self.username
