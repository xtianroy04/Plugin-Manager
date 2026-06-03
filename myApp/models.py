from django.db import models
from django.contrib.auth import get_user_model


class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('plugin_upload', 'Plugin Uploaded'),
        ('plugin_delete', 'Plugin Deleted'),
        ('site_upload', 'Site Uploaded'),
        ('site_delete', 'Site Deleted'),
    ]
    
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()} at {self.timestamp}"


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
