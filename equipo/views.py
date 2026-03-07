from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse
from equipo.forms import JugadorForm, EquipoForm, EquipoTrofeoForm
from equipo.models import Jugador, Equipo, EquipoTrofeo
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.decorators import method_decorator
from openpyxl.reader.excel import load_workbook
from equipo.jugadores_desde_archivo import ImportarArchivoClase
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic.base import TemplateView
from django.urls.base import reverse_lazy
from django.contrib import messages
from campeonato.models import Partido, Gol
from django.db.models.query_utils import Q
from vulnerable.settings.base import MAXIMO_PERMITIDO_MB_ARCHIVO
from usuario.models import Hincha
from conf.views import custom_404, custom_403, sin_permiso
from django.http.response import Http404, HttpResponseRedirect
from django.db.models.deletion import ProtectedError


class BaseJugadorView:
    template_name = 'conf/crear_editar_generico_5.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if self.permissions_required and not request.user.has_perm(self.permissions_required):
            return sin_permiso(request)
        
        if isinstance(self.request.user.persona, Hincha): 
            return custom_403(request)
        
        try:
            pk_numero = int(kwargs['pk'])   
            if self.get_object().equipo.pk not in self.request.user.persona.get_id_equipos():
                return custom_403(request)
        except (ValueError, ObjectDoesNotExist, Http404):
            return custom_404(request)
        
        return super().dispatch(request, *args, **kwargs)

    
class CrearJugador(CreateView):
    model = Jugador
    form_class = JugadorForm
    permissions_required = 'equipo.add_jugador'
    template_name = 'conf/crear_editar_generico_5.html'
    
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if self.permissions_required and not request.user.has_perm(self.permissions_required):
            return sin_permiso(request)
        
        # Si el usuario es un hincha, no le permitimos crear jugadores
        if isinstance(self.request.user.persona, Hincha): 
            return custom_403(request)
        else:
            try:
                pk_numero = int(kwargs['pk'])
                if pk_numero not in self.request.user.persona.get_id_equipos():
                    return custom_403(request)
            except (ValueError, ObjectDoesNotExist, Http404):
                return custom_404(request)
       
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        equipo = get_object_or_404(Equipo, pk=self.kwargs['pk'])
        
        if equipo is None:
            messages.error(self.request, 'Error: Debes proporcionar un equipo válido.')
            return self.render_to_response(self.get_context_data(form=form))
        
        form.instance.equipo = equipo
        return super().form_valid(form)
    
    def get_initial(self):
        equipo = get_object_or_404(Equipo, pk=self.kwargs['pk'])
        return {'equipo': equipo}
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        equipo = get_object_or_404(Equipo, pk=self.kwargs['pk'])
        context['titulo_modelo'] = '{0} {1}'.format(Jugador.CREAR_TITULO_TEMPLATE, equipo.__str__())
        return context

    def get_success_url(self):
        equipo = get_object_or_404(Equipo, pk=self.kwargs['pk'])
        return reverse('equipo:equipo-detalle', kwargs={'pk': equipo.pk})


class EditarJugador(BaseJugadorView, UpdateView):
    model = Jugador
    form_class = JugadorForm
    permissions_required = 'equipo.change_jugador'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        jugador = get_object_or_404(Jugador, pk=self.kwargs['pk'])
        context['titulo_modelo'] = '{0} {1}'.format(Jugador.EDITAR_TITULO_TEMPLATE, jugador.__str__())
        return context

    def get_success_url(self):
        return reverse('equipo:equipo-detalle', kwargs={'pk': self.object.equipo.pk})


class EliminarJugador(BaseJugadorView, DeleteView):
    model = Jugador
    template_name = 'conf/confirm_delete.html'
    permissions_required = 'equipo.delete_jugador'

    def dispatch(self, request, *args, **kwargs):
        try:
            self.hay_goles()
            return super().dispatch(request, *args, **kwargs)
        except ProtectedError:
            messages.error(request, "No se puede eliminar el jugador por tener información relacionada.")
            return HttpResponseRedirect(reverse('equipo:equipo-detalle', kwargs={'pk': self.get_object().equipo.pk}))

    def hay_goles(self):
        if Gol.objects.filter(jugador=self.get_object()).exists():
            raise ProtectedError("El jugador tiene goles asociados y no puede ser eliminado.", [])

    def get_success_url(self):
        return reverse('equipo:equipo-detalle', kwargs={'pk': self.object.equipo.pk})

    
class PreEliminarJugadores(TemplateView):
    template_name = 'equipo/pre_eliminacion_masiva.html'
    permissions_required = 'perfil.eliminar_jugadores_de_forma_masiva'
    
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if self.permissions_required and not request.user.has_perm(self.permissions_required):
            return custom_403(request)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_confirmar'] = reverse_lazy('equipo:jugador-eliminar-masivo')  
        context['url_cancelar'] = reverse_lazy('demo:index') 
        return context

    
@login_required
def eliminar_jugadores_masivo(request):
    ''' Elimina todos los datos de partidos, goles y jugadores'''
    Jugador.objects.all().delete()
    Partido.objects.all().delete()
    Gol.objects.all().delete()
    messages.info(request, "Se eliminaron todos los registros de partido, goles y jugadores")
    return redirect('demo:index')


class BaseEquipoView:
    template_name = 'conf/crear_editar_generico_3.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if self.permissions_required and not request.user.has_perm(self.permissions_required):
            return sin_permiso(request)
        try:
            pk_numero = int(kwargs['pk'])
            
        except (ValueError, ObjectDoesNotExist, Http404):
            return custom_404(request)
        
        equipo_id = pk_numero    
        if isinstance(self.request.user.persona, Hincha): 
            equipos = self.request.user.persona.get_id_equipos()
        else:
            equipos = self.request.user.persona.get_id_equipos()
            
        if equipo_id not in equipos:
            return sin_permiso(request) 
        return super().dispatch(request, *args, **kwargs)

    
class CrearEquipo(CreateView):
    model = Equipo
    form_class = EquipoForm
    permissions_required = 'equipo.add_equipo'
    template_name = 'conf/crear_editar_generico_3.html'
    
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if self.permissions_required and not request.user.has_perm(self.permissions_required):
            return sin_permiso(request)
        
        return super().dispatch(request, *args, **kwargs)   
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_modelo'] = '{0}'.format(Equipo.CREAR_TITULO_TEMPLATE)
        return context

    def get_success_url(self):
        return reverse('equipo:equipo-detalle', kwargs={'pk': self.object.pk})


class EditarEquipo(BaseEquipoView, UpdateView):
    model = Equipo
    form_class = EquipoForm
    permissions_required = 'equipo.change_equipo'
    template_name = 'conf/crear_editar_generico_3.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        equipo = get_object_or_404(Equipo, pk=self.kwargs['pk'])
        context['titulo_modelo'] = '{0} {1}'.format(Equipo.EDITAR_TITULO_TEMPLATE, equipo.__str__())
        return context

    def get_success_url(self):
        return reverse('equipo:equipo-detalle', kwargs={'pk': self.object.pk})


class EliminarEquipo(BaseEquipoView, DeleteView):
    model = Equipo
    template_name = 'conf/confirm_delete.html'
    permissions_required = 'equipo.delete_equipo'
    
    def get_success_url(self):
        return reverse('demo:index')


class DetalleEquipo(BaseEquipoView, DetailView):
    model = Equipo
    template_name = 'equipo/detalle.html'
    permissions_required = 'equipo.view_equipo'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['es_dirigente'] = self.request.user.persona.es_dirigente()
        jugadores = self.get_object().get_jugadores()
        filtro_nombre = self.request.GET.get('filtro_nombre', '')  
        if filtro_nombre:
            query = "SELECT * FROM equipo_jugador where equipo_id = '%s' and LOWER(nombre_completo) LIKE  '%s';" % (
                self.kwargs['pk'], filtro_nombre)
            jugadores = Jugador.objects.raw(query)
        context['jugadores'] = jugadores
        return context


class BaseEquipoTrofeoView:
    template_name = 'conf/crear_editar_generico.html'
    
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if self.permissions_required and not request.user.has_perm(self.permissions_required):
            return sin_permiso(request)
        
        if isinstance(self.request.user.persona, Hincha): 
            return custom_403(request)
        
        try:
            pk_numero = int(kwargs['pk'])
            if self.get_object().equipo.pk not in self.request.user.persona.get_id_equipos():
                return custom_403(request)
        except (ValueError, ObjectDoesNotExist, Http404):
            return custom_404(request)
        
        return super().dispatch(request, *args, **kwargs)

    
class EditarTrofeo(BaseEquipoTrofeoView, UpdateView):
    model = EquipoTrofeo
    form_class = EquipoTrofeoForm
    permissions_required = 'equipo.change_equipotrofeo'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        equipo = get_object_or_404(Equipo, pk=self.kwargs['pk'])
        context['titulo_modelo'] = '{0} {1}'.format(EquipoTrofeo.EDITAR_TITULO_TEMPLATE, equipo.__str__())
        return context

    def get_success_url(self):
        return reverse('equipo:equipo-detalle', kwargs={'pk': self.object.equipo.pk})


class EliminarTrofeo(BaseEquipoTrofeoView, DeleteView):
    model = EquipoTrofeo
    template_name = 'conf/confirm_delete.html'
    permissions_required = 'equipo.delete_equipotrofeo'
    
    def get_success_url(self):
        return reverse('equipo:equipo-detalle', kwargs={'pk': self.object.equipo.pk})


class VincularTrofeo(CreateView):
    model = EquipoTrofeo
    form_class = EquipoTrofeoForm
    permissions_required = 'equipo.change_equipotrofeo'
    template_name = 'conf/crear_editar_generico.html'
    
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if self.permissions_required and not request.user.has_perm(self.permissions_required):
            return sin_permiso(request)
        
        if isinstance(self.request.user.persona, Hincha): 
            return custom_403(request)
        else:
            try:
                pk_numero = int(kwargs['pk'])
                if pk_numero not in self.request.user.persona.get_id_equipos():
                    return custom_403(request)
            except (ValueError, ObjectDoesNotExist, Http404):
                return custom_404(request)        
            
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        equipo = get_object_or_404(Equipo, pk=self.kwargs['pk'])
        return {'equipo': equipo}
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        equipo = get_object_or_404(Equipo, pk=self.kwargs['pk'])
        context['titulo_modelo'] = '{0} {1}'.format(EquipoTrofeo.CREAR_TITULO_TEMPLATE, equipo.__str__())
        return context

    def get_success_url(self):
        return reverse('equipo:equipo-detalle', kwargs={'pk': self.object.equipo.pk})


@login_required
@permission_required('perfil.crear_jugadores_desde_archivo', raise_exception=True)  
def cargar_desde_archivo(request):
    """
        Vista que maneja la carga de datos de jugadores desde un archivo Excel (.xlsx).

        Esta función procesa la carga de datos desde un archivo enviado mediante un formulario POST.
        Se valida y analiza el archivo, y se muestra un informe de errores o se realiza la carga
        dependiendo de los resultados.

    """
    template = 'equipo/crear_jugdores_desde_archivo.html'
    listado_errores = []
    listado_a_cargar = []
    mensaje_carga = None
    carga_realizada = False
    
    if request.method == 'POST':
        if 'archivo' in request.FILES:
            archivo = request.FILES['archivo']
            if archivo and str(archivo.name).find('.xlsx') > -1:
                if archivo.size < MAXIMO_PERMITIDO_MB_ARCHIVO:
                    book = load_workbook(archivo, read_only=True)
                    archivo_clase = ImportarArchivoClase()
                    if 'validar_y_cargar' in request.POST:
                        listado_errores, listado_a_cargar = archivo_clase.validar(book)
                        if not listado_errores:
                            carga_realizada, mensaje_carga, listado_errores = archivo_clase.pre_cargar(listado_a_cargar)
                else:
                    listado_errores.append('El peso del archivo no puede superar los 5 mb')            
    
            else:
                listado_errores.append('la extensión del archivo seleccionado no es válida para la carga del parte diario.')            
    
        else:
            listado_errores.append('Para poder comenzar la validación y carga es necesario seleccionar un archivo.')            
    variables = {
        'entorno': '',
        'listado_errores': listado_errores,
        'mensaje_carga': mensaje_carga,
        'carga_realizada': carga_realizada 
    }
    return render(request, template, variables)
    
