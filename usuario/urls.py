from usuario.views import Detalle, EditarHinchaView, EditarDirigenteView, Ayuda
from django.urls.conf import path
app_name = 'usuario'
urlpatterns = [
    path('detalle/<pk>/', Detalle.as_view(), name='detalle'),
    path('ayuda/', Ayuda.as_view(), name='ayuda'),

    path('editar/hincha/<pk>/', EditarHinchaView.as_view(), name='editar-hincha'),
    path('editar/dirigente/<pk>/', EditarDirigenteView.as_view(), name='editar-dirigente'),
]