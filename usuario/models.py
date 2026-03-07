from django.db import models
from polymorphic.models import PolymorphicModel
from vulnerable.settings.base import AUTH_USER_MODEL
from equipo.models import Equipo
# Create your models here.

class Persona(PolymorphicModel):
    usuario = models.OneToOneField(AUTH_USER_MODEL, 
                                   on_delete=models.CASCADE,
                                   null=True, 
                                   blank=True
                                   )
    nombre = models.CharField(max_length=64)
    apellido = models.CharField(max_length=64)
    email = models.EmailField()
    
    GRUPO_HINCHA = 'Hincha'
    GRUPO_DIRIGENTE = 'Dirigente'
    
    def es_hincha(self):
        return isinstance(self, Hincha)
    
    def get_nombre_apellido(self):
        return self.nombre + ' ' + self.apellido
    
    def crear_token(self, nuevo_token):
        nuevo = TokenActivacion(
                token=nuevo_token,
                user=self.usuario,
            )
        nuevo.save()
    
    def __str__(self):
        return '%s %s' % (self.nombre, self.apellido)
    
    
    
class Hincha(Persona):
    equipos = models.ManyToManyField(Equipo)
    
    def es_dirigente(self):
        return False
    
    def es_hincha(self):
        return True
    
    def get_id_equipos(self):
        return list(self.equipos.all().values_list('pk', flat=True))
    
    def get_equipos(self):
        return self.equipos.all()

class Dirigente(Persona):
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE)
    
    def es_dirigente(self):
        return True
    
    def es_hincha(self):
        return False

    def get_id_equipos(self):
        if self.equipo:
            return [self.equipo.pk]
        else:
            return []
        
    def get_equipos(self):
        return self.equipo
        
class TokenActivacion(models.Model):
    user = models.OneToOneField(AUTH_USER_MODEL, on_delete=models.CASCADE)
    token = models.CharField(max_length=100)
    usado = models.BooleanField(default=False)