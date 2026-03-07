from django.db import models
from equipo.models import Equipo, Jugador
from datetime import date

# Create your models here.


class Partido(models.Model):
    equipo_local = models.ForeignKey(Equipo, related_name='local', on_delete=models.CASCADE)
    equipo_visitante = models.ForeignKey(Equipo, related_name='visitante', on_delete=models.CASCADE)
    fecha = models.DateTimeField()
    goles_local = models.IntegerField(default=0)
    goles_visitante = models.IntegerField(default=0)
    jugadores_goles = models.ManyToManyField(Jugador, through='Gol', related_name='goles_jugador')
    ya_jugado = models.BooleanField(default=False)
    
    def se_puede_jugar(self):
        return self.fecha.date() <= date.today()
    
    def get_resultado(self):
        return '{0} - {1}'.format(self.goles_local, self.goles_visitante)
    
    def __str__(self):
        return "{0} vs. {1} - {2}".format(
            self.equipo_local.nombre, self.equipo_visitante.nombre,
            self.fecha)
    
    def obtener_goles_equipo_local(self):
        goles_equipo_local = Gol.objects.filter(partido=self, jugador__equipo=self.equipo_local)
        goles_equipo_local = goles_equipo_local.order_by('minuto')  # Ordenar por minuto
        lista_goles = []

        for gol in goles_equipo_local:
            texto = '{0} ({1})'.format(gol.jugador.__str__(),
                                       gol.minuto
                                       )
            lista_goles.append(texto)

        return lista_goles
    
    def obtener_goles_equipo_visitante(self):
        goles_equipo_visitante = Gol.objects.filter(partido=self, jugador__equipo=self.equipo_visitante)
        goles_equipo_visitante = goles_equipo_visitante.order_by('minuto') 
        lista_goles = []

        for gol in goles_equipo_visitante:
            texto = '{0} ({1})'.format(gol.jugador.__str__(),
                                       gol.minuto
                                       )
            lista_goles.append(texto)

        return lista_goles
        
    def actualizar_jugadores_goles(self):
        jugadores_goles_local = Jugador.objects.filter(gol__partido=self, gol__jugador__equipo=self.equipo_local)
        jugadores_goles_visitante = Jugador.objects.filter(gol__partido=self, gol__jugador__equipo=self.equipo_visitante)
        self.jugadores_goles.set(list(jugadores_goles_local) + list(jugadores_goles_visitante))

    class Meta:
        verbose_name_plural = "Partidos"
        permissions = (
            ("simular_partido", "Le permite al usuario simular partido"),
        )

        
class Gol(models.Model):
    jugador = models.ForeignKey(Jugador, on_delete=models.CASCADE)
    partido = models.ForeignKey(Partido, on_delete=models.CASCADE)
    minuto = models.PositiveIntegerField()

    def __str__(self):
        return "{0} - {1}".format(
            self.jugador, self.partido)

    class Meta:
        verbose_name_plural = "Goles"

