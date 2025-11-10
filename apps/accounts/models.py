from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    # Exemple : ajout d'un champ 'phone_number' si nécessaire
    phone_number = models.CharField(max_length=20, blank=True, null=True)  # type: ignore

    def __str__(self):
        return self.username
