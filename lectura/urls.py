from django.urls import path
from . import views


urlpatterns = [
    path('', views.bienvenida),
    path('archivo', views.cargar_archivo),
    path('foto', views.subir_foto),
]