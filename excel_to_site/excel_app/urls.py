from django.urls import path

from . import views

urlpatterns = [
    path('get_data/', views.get_data, name='get_data'),
    path('upload/', views.upload_file, name='upload_file'),
    path('uploaded_files/', views.uploaded_files, name='uploaded_files'),
    path('uploaded_files/<int:file_id>/', views.view_data, name='view_data'),
]
