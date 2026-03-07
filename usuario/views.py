from django.shortcuts import render
from django.views.generic.detail import DetailView
from usuario.models import Persona, Dirigente, Hincha
from django.views.generic.edit import UpdateView
from usuario.forms import DirigenteForm, HinchaForm
from django.urls.base import reverse
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from conf.views import sin_permiso, custom_404
from django.http.response import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import TemplateView


class VerificarPermisosPersonaMixin:
    def dispatch(self, request, *args, **kwargs):
        user = request.user
        try:
            pk_numero = int(kwargs['pk'])
            persona = self.model.objects.get(pk=pk_numero)
        except (ValueError, ObjectDoesNotExist):
            return custom_404(request)
        
        if user == persona.usuario:
            return super().dispatch(request, *args, **kwargs)
        else:
            return sin_permiso(request)


@method_decorator(csrf_exempt, name='dispatch')
class EditarPersonaView(UpdateView):
    '''
        Se excluye control de csrf para poder acceder desde Postman para actualizar
        datos
    '''
    template_name = 'usuario/crear_editar_usuario.html'
    model = None  
    
    def dispatch(self, request, *args, **kwargs):
        try:
            pk_numero = int(kwargs['pk'])
            persona = self.model.objects.get(pk=pk_numero)
        except (ValueError, ObjectDoesNotExist):
            return custom_404(request)
        
        return super().dispatch(request, *args, **kwargs)
  
    def get_model(self):
        if self.model == Hincha:
            return 'hincha'
        elif self.model == Dirigente:
            return 'dirigente'
        return None
    
    def get_titulo_para_template(self):
        persona = self.model.objects.get(pk=self.kwargs['pk'])
        if self.model == Hincha:
            titulo = 'Datos del hincha {0}'.format(persona)
        else:
            titulo = 'Datos del dirigente {0}'.format(persona)
        return titulo

    def get_context_data(self, **kwargs):
        context =  UpdateView.get_context_data(self, **kwargs)
        context['titulo_modelo'] = self.get_titulo_para_template() 
        return context
    
    def post(self, request, *args, **kwargs):        
        persona = self.model.objects.get(pk=kwargs['pk'])
        form = self.get_form_class()(request.POST, instance=persona)
        if form.is_valid():
            if self.mail_valido(persona.usuario.email, form.cleaned_data['email']):
                form.save()
                self.actualizar_user(persona, form)
                messages.success(request, "Datos actualizados con exito.")
                return HttpResponseRedirect(reverse('usuario:detalle', kwargs={'pk': persona.pk}))
            else:
                messages.error(request, "El correo ingresado no es válido o ya está registrado.")
        titulo_modelo = self.get_titulo_para_template() 
        return render(request, self.template_name, {'form': form, 
                                                    'object': persona,
                                                    'titulo_modelo': titulo_modelo})

    def get_form_class(self):
        # Devuelve la clase del formulario según el modelo (Hincha o Dirigente)
        if self.model == Hincha:
            return HinchaForm
        elif self.model == Dirigente:
            return DirigenteForm
        return None
    
    def mail_valido(self, mail_actual, nuevo_email):
        exito = True
        if mail_actual != nuevo_email:
            if Persona.objects.filter(email=nuevo_email).exists():
                exito = False
        return exito
        
    def actualizar_user(self, persona, form):
        persona.usuario.nombre = form.cleaned_data['nombre']
        persona.usuario.apellido = form.cleaned_data['apellido']
        persona.usuario.email = form.cleaned_data['email']
        persona.usuario.save()
    
class EditarHinchaView(EditarPersonaView):
    model = Hincha

class EditarDirigenteView(EditarPersonaView):
    model = Dirigente

@method_decorator(login_required, name='dispatch')
class Detalle(VerificarPermisosPersonaMixin, DetailView):
    model = Persona
    template_name = 'usuario/detalle.html'
    
@method_decorator(login_required, name='dispatch')
class Ayuda(TemplateView):
    template_name = 'usuario/ayuda.html'
