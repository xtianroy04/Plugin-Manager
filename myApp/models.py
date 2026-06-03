from django.db import models


class App(models.Model):
    TYPE_CHOICES = [
        ('plugin', 'Plugin'),
        ('site', 'Site'),
    ]
    
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='plugin')
    version = models.CharField(max_length=50, default="1.0")
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='apps/logos/', blank=True, null=True)
    app_dir = models.CharField(max_length=500)
    config = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=False)  # True for sites, False for plugins
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"
