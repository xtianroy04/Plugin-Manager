from django.db import models


class Plugin(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    version = models.CharField(max_length=50, default="1.0")
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='plugins/logos/', blank=True, null=True)
    plugin_dir = models.CharField(max_length=500)
    config = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
