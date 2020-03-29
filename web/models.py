from django.db import models


class Scan(models.Model):
    start_datetime = models.DateTimeField(auto_now_add=True)
    end_datetime = models.DateTimeField(null=True, default=None)
    domain = models.CharField(max_length=253)
    profile = models.CharField(max_length=255)
    is_public = models.BooleanField()
    task_id = models.CharField(max_length=255)
