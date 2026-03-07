from django.db import models
from equipo.enum import EquipoPais, JugadorPie, JugadorPosicion, \
    EquipoTrofeoOpcion
from datetime import date
from conf.validators import CustomValidators
from django.db.models import Sum, Case, When, F, IntegerField, Q

# Create your models here.


class Equipo(models.Model):
    nombre = models.CharField(max_length=64, unique=True)
    escudo = models.FileField(upload_to='escudos/', blank=True, null=True)
    pais = models.IntegerField(choices=EquipoPais.choices, default=EquipoPais.URUGUAY)
    fecha_fundado = models.DateField(null=True, blank=True)
    historia = models.TextField(null=True, blank=True)

    CREAR_TITULO_TEMPLATE = 'Crear equipo'
    EDITAR_TITULO_TEMPLATE = 'Editar datos del equipo' 
    
    def es_uruguay(self):
        return self.pais == EquipoPais.URUGUAY
           
    def get_jugadores(self):
        return Jugador.objects.filter(equipo=self).order_by('posicion')
    
    def get_trofeos(self):
        return EquipoTrofeo.objects.filter(equipo=self)
    
    def obtener_puntos(self):
        from campeonato.models import Partido

        partidos_jugados = Partido.objects.filter(
            Q(equipo_local=self) | Q(equipo_visitante=self),
            ya_jugado=True
        )

        puntaje = partidos_jugados.annotate(
            puntaje=Sum(
                Case(
                    When(Q(equipo_local=self) & Q(goles_local__gt=F('goles_visitante')), then=3),
                    When(Q(equipo_local=self) & Q(goles_local=F('goles_visitante')), then=1),
                    When(Q(equipo_visitante=self) & Q(goles_local__lt=F('goles_visitante')), then=3),
                    default=0,
                    output_field=IntegerField()
                )
            )
        ).aggregate(puntaje_total=Sum('puntaje'))['puntaje_total']

        return puntaje if puntaje else 0
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        ordering = ["nombre"]
        verbose_name_plural = "Equipos"

        
class EquipoTrofeo(models.Model):
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE)
    trofeo = models.IntegerField(choices=EquipoTrofeoOpcion.choices)
    cantidad = models.IntegerField(default=0)
    
    CREAR_TITULO_TEMPLATE = 'Vincular trofeo para el equipo' 
    EDITAR_TITULO_TEMPLATE = 'Editar trofeo para el equipo' 
    
    def __str__(self):
        return self.get_trofeo_display()
    
    class Meta:
        ordering = ["trofeo"]
        verbose_name_plural = "trofeo"
        unique_together = ["equipo", "trofeo"]


class Jugador(models.Model):
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE)
    nombre_completo = models.CharField(max_length=64)
    fecha_nacimiento = models.DateField()
    altura = models.FloatField(null=True, blank=True, validators=[CustomValidators.valor_no_negativo])
    pie = models.IntegerField(choices=JugadorPie.choices)
    fichado = models.DateField(null=True, blank=True)
    fin_contrato = models.DateField(null=True, blank=True)
    posicion = models.IntegerField(choices=JugadorPosicion.choices, default=JugadorPosicion.SIN_DEFINIR)

    # sensibles
    salario = models.FloatField(default=0, validators=[CustomValidators.valor_no_negativo])
    valor_mercado = models.FloatField(default=0, validators=[CustomValidators.valor_no_negativo])
    
    CREAR_TITULO_TEMPLATE = 'Crear nuevo jugador para el equipo' 
    EDITAR_TITULO_TEMPLATE = 'Edición de los datos del jugador' 
    
    def activo(self):
        return self.fin_contrado > date.today()
    
    def get_fin_contrato(self):
        return self.fin_contrado
    
    def __str__(self):
        return '{}'.format(self.nombre_completo)
    
    class Meta:
        ordering = ["nombre_completo"]
        verbose_name_plural = "Jugadores"
        permissions = (
            ("ver_salario", "Permite a los dirigentes ver el salario"),
        )

