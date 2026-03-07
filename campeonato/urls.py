from django.urls.conf import path
from campeonato.views import TablaDeGoleadores, Calendario, generar_fixture,\
    cargar_goles_al_azar, TablaPosiciones
app_name = 'campeonato'
urlpatterns = [
    path('listado/goleadores/', TablaDeGoleadores.as_view(), name='tabla-de-goleadores'),
    path('listado/posiciones/', TablaPosiciones.as_view(), name='tabla-de-posiciones'),
    path('generar-fixture/', generar_fixture, name="generar-fixture"),
    path('fixture/', Calendario.as_view(), name='fixture'),
    path('partido/jugar/<id_partido>/', cargar_goles_al_azar, name='partido-jugar'),
]