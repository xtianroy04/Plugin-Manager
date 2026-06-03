from django.urls import path
from . import views


urlpatterns = [
    path('', views.plugin_list, name='plugin_list'),
    path('upload/', views.plugin_upload, name='plugin_upload'),
    
    # Generic Plugin Config API endpoints (for ANY plugin)
    path('<slug:slug>/api/config/', views.plugin_get_config, name='plugin_get_config'),
    path('<slug:slug>/api/config/set/', views.plugin_set_config, name='plugin_set_config'),
    path('<slug:slug>/api/config/update/', views.plugin_update_config, name='plugin_update_config'),
    
    path('<slug:slug>/', views.plugin_detail, name='plugin_detail'),
    path('<slug:slug>/delete/', views.plugin_delete, name='plugin_delete'),
]