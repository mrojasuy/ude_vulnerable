from django.urls.conf import path
from equipo.views import CrearJugador, \
EditarJugador, EliminarJugador, EditarTrofeo, EliminarTrofeo, VincularTrofeo, \
    EditarEquipo, CrearEquipo, DetalleEquipo, EliminarEquipo, \
    cargar_desde_archivo, PreEliminarJugadores, eliminar_jugadores_masivo

app_name = 'equipo'
urlpatterns = [
    path('editar/equipo/<pk>', EditarEquipo.as_view(), name='equipo-editar'),
    path('crear/equipo', CrearEquipo.as_view(), name='equipo-crear'),
    path('detalle/equipo/<pk>/', DetalleEquipo.as_view(), 
         name='equipo-detalle'),
    path('eliminar/equipo/<pk>', EliminarEquipo.as_view(), 
         name='equipo-eliminar'),

    path('crear/jugador/<pk>', CrearJugador.as_view(), name='jugador-crear'),
    path('editar/jugador/<pk>', EditarJugador.as_view(), name='jugador-editar'),
    path('eliminar/jugador/<pk>', EliminarJugador.as_view(), 
         name='jugador-eliminar'),
    
    path('pre-eliminar/jugadores/masivo/', PreEliminarJugadores.as_view(), 
         name='pre-eliminar-jugadores-masivo'),
    path('eliminar/jugadores/masivo/', eliminar_jugadores_masivo, 
         name='jugador-eliminar-masivo'),
    
    path('crear/trofeo/<pk>', VincularTrofeo.as_view(), name='trofeo-crear'),
    path('editar/trofeo/<pk>', EditarTrofeo.as_view(), name='trofeo-editar'),
    path('eliminar/trofeo/<pk>', EliminarTrofeo.as_view(), 
         name='trofeo-eliminar'),

    path('crear/jugador/archivo/', cargar_desde_archivo, 
         name='crear-jugador-archivo'),

]
