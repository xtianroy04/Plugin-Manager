from django.urls import path
from . import views


urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('activity-log/', views.activity_log, name='activity_log'),
    
    # Generic App Config API endpoints (for ANY app/plugin/site)
    # These need to come BEFORE the plugin/site detail views!
    path('plugins/<slug:slug>/api/config/', views.app_get_config, name='plugin_get_config'),
    path('plugins/<slug:slug>/api/config/set/', views.app_set_config, name='plugin_set_config'),
    path('plugins/<slug:slug>/api/config/update/', views.app_update_config, name='plugin_update_config'),
    path('plugins/<slug:slug>/api/<str:method_name>/', views.app_custom_api, name='plugin_custom_api'),

    path('sites/<slug:slug>/api/config/', views.app_get_config, name='site_get_config'),
    path('sites/<slug:slug>/api/config/set/', views.app_set_config, name='site_set_config'),
    path('sites/<slug:slug>/api/config/update/', views.app_update_config, name='site_update_config'),
    path('sites/<slug:slug>/api/<str:method_name>/', views.app_custom_api, name='site_custom_api'),
    
    # Plugin URLs
    path('plugins/', views.plugin_list, name='plugin_list'),
    path('plugins/upload/', views.plugin_upload, name='plugin_upload'),
    path('plugins/<slug:slug>/', views.plugin_detail, name='plugin_detail'),
    path('plugins/<slug:slug>/delete/', views.plugin_delete, name='plugin_delete'),
    
    # Site URLs
    path('sites/upload/', views.site_upload, name='site_upload'),
    path('sites/<slug:slug>/', views.site_public, name='site_public'),
    path('sites/<slug:slug>/edit/', views.site_edit, name='site_edit'),
    path('sites/<slug:slug>/delete/', views.site_delete, name='site_delete'),
    path('sites/<slug:slug>/toggle-visibility/', views.site_toggle_visibility, name='site_toggle_visibility'),
    
    # Generic App Config API endpoints (for ANY app/plugin/site)
    path('<slug:slug>/api/config/', views.app_get_config, name='app_get_config'),
    path('<slug:slug>/api/config/set/', views.app_set_config, name='app_set_config'),
    path('<slug:slug>/api/config/update/', views.app_update_config, name='app_update_config'),
]
