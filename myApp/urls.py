from django.urls import path
from . import views


urlpatterns = [
    path('', views.plugin_list, name='plugin_list'),
    path('upload/', views.plugin_upload, name='plugin_upload'),
    path('<slug:slug>/', views.plugin_detail, name='plugin_detail'),
    path('<slug:slug>/delete/', views.plugin_delete, name='plugin_delete'),
]