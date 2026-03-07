from django.shortcuts import redirect
from django.views.generic import ListView
from campeonato.models import Partido, Gol
from django.db.models import Count
from equipo.models import Jugador, Equipo
from django.core.exceptions import ValidationError
import random
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.utils import timezone
from datetime import timedelta, date, datetime
from django.db.models.query_utils import Q
from django.db.models import F, Sum, Case, When, IntegerField
from operator import itemgetter
from usuario.models import Hincha
from django.utils.decorators import method_decorator


@method_decorator(login_required, name='dispatch')
class TablaDeGoleadores(ListView):
    template_name = 'campeonato/tabla_de_goleadores.html'

    def get_queryset(self):
        # Consulta la base de datos para contar cuántos goles ha marcado cada jugador
        goleadores = Jugador.objects.annotate(num_goles=Count('goles_jugador')).order_by('-num_goles', 'nombre_completo')

        # Crea una lista de diccionarios con la información de los goleadores
        tabla_goleadores = []
        for jugador in goleadores:
            if jugador.num_goles > 0:
                tabla_goleadores.append({
                    'jugador': jugador,
                    'goles': jugador.num_goles,
                })

        return tabla_goleadores


@method_decorator(login_required, name='dispatch')    
class TablaPosiciones(ListView):
    model = Equipo
    template_name = 'campeonato/tabla_de_posiciones.html'
    context_object_name = 'tabla_posiciones'

    def get_queryset(self):
        equipos = Equipo.objects.all()
        tabla_de_posiciones = []

        for equipo in equipos:
            partidos_jugados = Partido.objects.filter(Q(equipo_local=equipo) | Q(equipo_visitante=equipo), ya_jugado=True)

            puntaje = partidos_jugados.annotate(
                puntaje=Sum(
                    Case(
                        When(Q(equipo_local=equipo) & Q(goles_local__gt=F('goles_visitante')), then=3),
                        When(Q(equipo_local=equipo) & Q(goles_local=F('goles_visitante')), then=1),
                        When(Q(equipo_visitante=equipo) & Q(goles_local__lt=F('goles_visitante')), then=3),
                        default=0,
                        output_field=IntegerField()
                    )
                )
            ).aggregate(puntaje_total=Sum('puntaje'))['puntaje_total']
            
            if not puntaje:
                puntaje = 0
            tabla_de_posiciones.append({'equipo': equipo, 'puntaje': puntaje})

        # Ordenar la tabla de posiciones en función del puntaje (manejar equipos sin puntaje)
        tabla_ordenada = sorted(tabla_de_posiciones, key=lambda x: x['puntaje'], reverse=True)

        return tabla_ordenada

    
@method_decorator(login_required, name='dispatch')  
class Calendario(ListView):
    model = Partido
    template_name = 'campeonato/fixture.html'
    context_object_name = 'partidos'

    def get_queryset(self):
        return Partido.objects.all().order_by('-fecha')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        partidos = Partido.objects.all().order_by('-fecha')
        partidos_agrupados = {}
        fecha_actual = timezone.now()
        
        proxima_fecha = None
        proximos_partidos = []
        
        for partido in partidos:
            fecha = partido.fecha
            
            # Agrupa todos los partidos por fecha
            fecha_sin_hora = fecha.date()
            if fecha_sin_hora not in partidos_agrupados:
                partidos_agrupados[fecha_sin_hora] = []
            partidos_agrupados[fecha_sin_hora].append(partido)
            
            # Encuentra la proxima fecha
            if fecha > fecha_actual and (proxima_fecha is None or fecha < proxima_fecha):
                proxima_fecha = fecha
        
        if proxima_fecha:
            # Obtiene los partidos de la proxima fecha
            proximos_partidos = partidos_agrupados.get(proxima_fecha.date(), [])
        
        context['proxima_fecha'] = proxima_fecha
        context['proximos_partidos'] = proximos_partidos
        context['partidos_agrupados'] = partidos_agrupados
        context['fecha_actual'] = date.today()
        if isinstance(self.request.user.persona, Hincha): 
            equipos = self.request.user.persona.get_id_equipos()
        else:
            equipos = self.request.user.persona.get_id_equipos()
        context['equipos_usuario_logueado'] = equipos

        return context


@login_required
@permission_required('perfil.generar_fixtur', raise_exception=True)  
def generar_fixture(request):
    """
        Vista que genera un fixture de partidos entre equipos.
    
        Esta función crea enfrentamientos entre equipos, asegurándose de que cada equipo juegue
        contra todos los demás exactamente una vez. Los partidos se programan semanalmente a partir
        de la fecha actual. Se requieren al menos 2 equipos registrados para generar un fixture.
    
    """
    equipos = Equipo.objects.all()
    
    total_partidos = equipos.count() - 1
    # Asegurarse de que haya al menos 2 equipos registrados
    if len(equipos) < 2:
        raise ValidationError("Deben registrarse al menos 2 equipos para generar un fixture.")
    
    fecha_actual = datetime(2024, 2, 16, 17, 0)  
    enfrentamientos_anteriores = set()
    for semana in range(total_partidos):
        equipos_disponibles = list(equipos)  
        while equipos_disponibles:
            equipo_local = equipos_disponibles.pop(0)
            
            # Buscar un equipo visitante que no haya jugado contra el equipo local previamente
            equipo_visitante = None
            for candidato in equipos_disponibles:
                enfrentamiento = (equipo_local, candidato)
                inverso_enfrentamiento = (candidato, equipo_local)
                
                if (enfrentamiento not in enfrentamientos_anteriores) and (inverso_enfrentamiento not in enfrentamientos_anteriores):
                    equipo_visitante = candidato
                    break
            
            if equipo_visitante:
                partido = Partido(
                    equipo_local=equipo_local,
                    equipo_visitante=equipo_visitante,
                    fecha=fecha_actual,
                )
                partido.save()
                
                enfrentamientos_anteriores.add((equipo_local, equipo_visitante))
                # Se saca el equipo visitante de la lista
                equipos_disponibles.remove(equipo_visitante)  

        # Incrementar la fecha actual para la próxima semana
        fecha_actual += timedelta(weeks=1)  
        
    return redirect('campeonato:fixture')


@login_required
@permission_required('campeonato.simular_partido', raise_exception=True)
def cargar_goles_al_azar(request, id_partido):
    """
        Vista que carga goles al azar para un partido y actualiza las estadísticas.
    
        Esta función simula la carga de goles al azar para un partido, generando un número aleatorio
        de goles para cada equipo. Luego, crea instancias de Gol para los jugadores que anotaron en
        el partido y actualiza las estadísticas del partido y los jugadores involucrados.
    
        Parámetros:
        - id_partido: Identificador del partido.

    """
    obj_partido = Partido.objects.get(pk=id_partido)
    if not obj_partido.ya_jugado:
        # Generar un número aleatorio para los goles de cada equipo. El maximo 
        # de 5 es un numero sin justificacion seleccionado por el equipo. 
        goles_local = random.randint(0, 5)  
        goles_visitante = random.randint(0, 5)  
        
        # Actualizar los campos 'goles_local' y 'goles_visitantes' en el modelo 'Partido'
        obj_partido.goles_local = goles_local
        obj_partido.goles_visitante = goles_visitante
        obj_partido.save()
        
        # Crear instancias de Gol para los goles anotados por el equipo local
        for _ in range(goles_local):
            jugador = random.choice(obj_partido.equipo_local.get_jugadores())
            minuto = random.randint(1, 90)  # Minuto aleatorio entre 1 y 90
            Gol.objects.create(jugador=jugador, partido=obj_partido, minuto=minuto)
        
        # Crear instancias de Gol para los goles anotados por el equipo visitante
        for _ in range(goles_visitante):
            jugador = random.choice(obj_partido.equipo_visitante.get_jugadores())
            # Se busca un minutos aleatorio entre 1 y 90 para decir que ahi se hizo el gol
            minuto = random.randint(1, 90)  
            Gol.objects.create(jugador=jugador, partido=obj_partido, minuto=minuto)
            
        obj_partido.ya_jugado = True    
        obj_partido.save()
        
        obj_partido.actualizar_jugadores_goles()
    else:
        messages.info(request, "Partido ya jugado.")
    return redirect('campeonato:fixture')
