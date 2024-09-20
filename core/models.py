from django.db import models
from django.contrib.auth.models import User


class Placement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    page_url = models.URLField()
    data = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.page_url}"


class PlacementAnalytics(models.Model):
    placement = models.ForeignKey(
        Placement, on_delete=models.CASCADE, related_name="analytics"
    )
    event_type = models.CharField(max_length=50)
    event_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.placement.page_url} - {self.event_type}"
