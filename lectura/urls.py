from django.urls import path
from . import views


urlpatterns = [
    path('', views.bienvenida),
    path('archivo', views.cargar_archivo),
    path('foto', views.subir_foto),
    
    
    path('modify-json/', views.modify_json, name='modify_json'),
    path('get-user-files/<str:username>', views.get_user_files, name='get_user_files')
]