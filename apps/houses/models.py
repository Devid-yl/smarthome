from django.db import models
from django.conf import settings  # <- important


class House(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="houses")   # type: ignore
    name = models.CharField(max_length=100)  # type: ignore
    address = models.CharField(max_length=255, blank=True, null=True)   # type: ignore

    def __str__(self):
        return f"{self.name} - {self.owner.username}"


class Room(models.Model):
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name="rooms")   # type: ignore
    name = models.CharField(max_length=100)   # type: ignore

    def __str__(self):
        return f"{self.name} ({self.house.name})"
