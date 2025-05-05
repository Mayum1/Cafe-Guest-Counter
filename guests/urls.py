from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('process_image/', views.process_image_ajax, name='process_image'),
    path('process_video/', views.process_video_ajax, name='process_video'),
    path('process_rtsp/', views.process_rtsp_ajax, name='process_rtsp'),
    path('download_report/', views.download_report, name='download_report'),
]

