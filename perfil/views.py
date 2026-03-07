from django.shortcuts import render, redirect
from perfil.forms import RegistroForm
from conf.mail import AutomaticMail
from django.contrib.auth.tokens import default_token_generator
from vulnerable.settings.base import EMAIL_HOST_USER
from django.core.mail.message import EmailMultiAlternatives
from django.template.loader import get_template
from perfil.models import Perfil
from django.contrib import messages
from django.http.response import HttpResponseBadRequest, HttpResponseRedirect
import traceback
from usuario.models import Hincha, TokenActivacion, Persona, Dirigente
from django.contrib.auth import login, logout
from django.urls.base import reverse, reverse_lazy
from django.db import transaction
from perfil.enum import ErrorActivarDesactivar
from equipo.models import Equipo
from django.contrib.auth.decorators import login_required
import os
from django.views.generic.base import TemplateView
from django.contrib.auth.models import Group
from django.utils.decorators import method_decorator
from conf.views import custom_403, custom_404


def enviar_token(self, destinatario, context, asunto, template):
    mail = AutomaticMail(
        recipients=destinatario,
        subject=asunto,
        template_name=template,
        context=context
    )
    mail.send()


def crear_pefil(nombre, apellido, email, username, password):
    """
        Crea un nuevo perfil de usuario.
    
        Esta función recibe información básica del usuario (nombre, apellido, email, nombre de usuario y contraseña),
        crea un nuevo objeto de perfil de usuario, lo guarda en la base de datos y asigna la contraseña proporcionada.

        Parámetros:
            - nombre: Nombre del usuario.
            - apellido: Apellido del usuario.
            - email: Dirección de correo electrónico del usuario.
            - username: Nombre de usuario único.
            - password: Contraseña del usuario.

        Retorna:
            - Perfil: Objeto de perfil de usuario recién creado.
    """
    obj_user = Perfil.objects.create(
            first_name=nombre,
            last_name=apellido,
            email=email,
            username=username,
        )

    obj_user.save()
    obj_user.set_password(password)
    obj_user.save()
    return obj_user

    
def crear_dirigente(equipo, user):
    """
        Crea un nuevo objeto de dirigente asociado a un usuario y equipo específicos.
    
        Esta función toma un objeto de equipo y un objeto de usuario, y crea un nuevo objeto de dirigente
        asociado a ese usuario y equipo. Utiliza la información del usuario para llenar los detalles del dirigente.
    
        Parámetros:
            - equipo: Objeto de equipo al que se asociará el dirigente.
            - user: Objeto de usuario al que se asociará el dirigente.
    
        Retorno:
            - Dirigente: Objeto de dirigente recién creado.
    """
    
    obj_persona = Dirigente(
            usuario=user,
            nombre=user.first_name,
            apellido=user.last_name,
            email=user.email,
            equipo=equipo
        )
    return obj_persona


def crear_hincha(user):
    """
        Crea un nuevo objeto de hincha asociado a un usuario específico.
    
        Esta función toma un objeto de usuario y crea un nuevo objeto de hincha asociado a ese usuario.
        Utiliza la información del usuario para llenar los detalles del hincha.
    
        Parámetros:
            - user: Objeto de usuario al que se asociará el hincha.
    
        Retorno:
            - Hincha: Objeto de hincha recién creado.
    """
    obj_persona = Hincha(
            usuario=user,
            nombre=user.first_name,
            apellido=user.last_name,
            email=user.email,
        )
    return obj_persona


def enviar_mail(asunto, contenido, destino): 
    """
        Envía un correo electrónico con formato HTML.
    
        Esta función utiliza la clase EmailMultiAlternatives de Django para enviar correos electrónicos
        con formato HTML. Se adjunta el contenido HTML al correo y se envía al destino especificado.
    
        Parámetros:
        - asunto : El asunto del correo electrónico.
        - contenido : El contenido HTML del correo electrónico.
        - destino: La dirección de correo electrónico de destino.
    
    """
    message = EmailMultiAlternatives(
        asunto,  # Titulo
        '',
        EMAIL_HOST_USER,  # Remitente
        [destino] 
    ) 

    message.attach_alternative(contenido, 'text/html')
    message.send()

    
def asignar_grupo_de_permiso(user, nombre_grupo):
    try:
        group = Group.objects.get(name=nombre_grupo)
        user.groups.add(group)
    except Group.DoesNotExist:
        raise("El grupo {grupo_nombre} no existe.")

    
def sign_up(request):
    """
        Maneja el proceso de registro de un nuevo usuario.
    
        Esta función se encarga de procesar la solicitud de registro de un nuevo usuario.
        Utiliza un formulario de registro, valida la información proporcionada y, si es válida,
        crea un nuevo perfil de usuario (con un token de activación), un objeto de hincha asociado
        y envía un correo electrónico de activación.

        Retorno:
            - Render: Renderiza la página de registro o la página de registro completo.
    """
    form = RegistroForm()
    hay_error = False
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            nombre = form.cleaned_data['nombre']
            apellido = form.cleaned_data['apellido']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password1']
            
            if Perfil.objects.filter(username=username).exists():
                hay_error = True
                messages.error(request, "Nombre de usuario no disponible.")
            if Perfil.objects.filter(email=email).exists():
                hay_error = True
                messages.error(request, "La cuenta de correo ingresada ya existe.")
            
            if not hay_error: 
                with transaction.atomic():
                    # Crear un usuario
                    obj_user = crear_pefil(nombre, apellido, email, username, password)
                    token = default_token_generator.make_token(obj_user)
                    obj_persona = crear_hincha(obj_user)
                    obj_persona.save()
                    obj_persona.crear_token(token)
                    
                    asignar_grupo_de_permiso(obj_user, Persona.GRUPO_HINCHA)
                    
                    obj_user.is_active = False
                    obj_user.save()
                    
                    # logica para envio de mail
                    asunto = 'Bienvenido al prototipo de vulnerable - Confirme su cuenta paar ingresar'            
                    template = get_template('registration/activar_registro.html')
                    if 'production' in os.environ['DJANGO_SETTINGS_MODULE']:
                        activation_url = "http://vulnerable.proyectoprogsd.com/perfil/activar/{0}".format(token)
                    else:
                        activation_url = "http://127.0.0.1:8020/perfil/activar/{0}".format(token)

                    variables = template.render({
                        'nombre': nombre,
                        'apellido': apellido,
                        'activation_url': activation_url
                    })
                    enviar_mail(asunto, variables, obj_user.email)      
                return render(request, 'registration/registro_completo.html')
    
    context = {
        'form': form
    }
    return render(request, 'registration/registro.html', context)


@login_required
def sign_up_directivo(request, equipo):
    """
        Maneja el proceso de registro de un nuevo directivo asociado a un equipo.
    
        Esta función procesa la solicitud de registro de un nuevo directivo asociado a un equipo específico.
        Verifica los permisos del usuario actual, valida la información proporcionada a través de un formulario de registro,
        crea un nuevo perfil de usuario (directivo), y envía un correo electrónico de activación.

        Parámetros:
            - equipo: El identificador del equipo al que se asociará el nuevo directivo.
    
        Retorno:
            - Renderiza la página de registro para directivos o redirige a la página de detalles del equipo después del registro.
    """
    form = RegistroForm()
    
    if not request.user.is_superuser:
        if request.user.persona.es_hincha():
            return custom_403(request)
        else:
            try:
                pk_equipo = int(equipo)
                equipos = request.user.persona.get_id_equipos()
                if int(equipo) not in equipos:
                    return custom_403(request)
            except ValueError:
                return custom_404(request)
        
    hay_error = False    
    if equipo:
        obj_equipo = Equipo.objects.get(pk=equipo)
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            nombre = form.cleaned_data['nombre']
            apellido = form.cleaned_data['apellido']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password1']
            
            if Perfil.objects.filter(username=username).exists():
                hay_error = True
                messages.error(request, "Nombre de usuario no disponible.")
            if Perfil.objects.filter(email=email).exists():
                hay_error = True
                messages.error(request, "La cuenta de correo ingresada ya existe.")
            
            if not hay_error: 
                with transaction.atomic():
                    # Crear un usuario
                    obj_user = crear_pefil(nombre, apellido, email, username, password)
                    obj_user.is_active = False
                    obj_user.save()
                    
                    asignar_grupo_de_permiso(obj_user, Persona.GRUPO_DIRIGENTE)

                    token = default_token_generator.make_token(obj_user)
                    
                    obj_persona = crear_dirigente(obj_equipo, obj_user)
                    obj_persona.save()
                    obj_persona.crear_token(token)
                    
                    # logica para envio de mail
                    asunto = 'Bienvenido al prototipo de vulnerable - Confirme su cuenta paar ingresar'            
                    template = get_template('registration/activar_registro.html')
                    if 'production' in os.environ['DJANGO_SETTINGS_MODULE']:
                        activation_url = "http://vulnerable.proyectoprogsd.com/perfil/activar/{0}".format(token)
                    else:
                        activation_url = "http://127.0.0.1:8020/perfil/activar/{0}".format(token)
                    
                    content = template.render({
                        'nombre': nombre,
                        'apellido': apellido,
                        'activation_url': activation_url
                    })
                    enviar_mail(asunto, content, obj_user.email)   
                    messages.success(request, "Se envio un aviso por correo para notificar a {0} que fue dado de alta como dirigente de {1}".format
                                     (obj_persona.get_nombre_apellido(), obj_equipo))   
                    return HttpResponseRedirect(reverse('equipo:equipo-detalle', kwargs={'pk': obj_equipo.pk}))
    
    context = {
        'form': form,
        'equipo': obj_equipo
    }
    return render(request, 'equipo/registro.html', context)


def activar_cuenta(request, token):
    """
        Activa la cuenta de usuario utilizando el token de activación proporcionado.
    
        Esta función intenta activar la cuenta de usuario asociada al token de activación proporcionado.
        Verifica la existencia y el estado del token, y activa la cuenta del usuario si el token no ha sido utilizado previamente.
    
        Parámetros:
            - token: El token de activación proporcionado.
    
        Retorno:
            - Redirige a la página de éxito después de activar la cuenta o muestra un mensaje de error si hay problemas.
    """
    try:
        if TokenActivacion.objects.filter(token=token).exists():
            obj_token = TokenActivacion.objects.get(token=token)
            if not obj_token.usado:
                # Activar la cuenta del usuario
                obj_token.user.is_active = True
                obj_token.usado = True
                obj_token.user.save()
                obj_token.save()
                login(request, obj_token.user)
    
                # Redirigir a una página de éxito o mostrar un mensaje de éxito
                messages.success(request, 'Tu cuenta ha sido activada con éxito.')
                return redirect('demo:index')
            else:
                return HttpResponseRedirect(reverse('perfil:error-activar-desactivar', kwargs={'codigo': ErrorActivarDesactivar.TOKEN_USADO}))
        else:
            return HttpResponseRedirect(reverse('perfil:error-activar-desactivar', kwargs={'codigo': ErrorActivarDesactivar.TOKEN_NO_EXISTE}))

    except:  # (ValueError, get_user_model().DoesNotExist):
        return HttpResponseBadRequest('Token no válido o usuario no encontrado.')


class PreDesactivarCuenta(TemplateView):
    template_name = 'usuario/pre_desactivar_cuenta.html'
    
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        try:
            cuenta_a_desactivar_id = int(self.kwargs['pk'])
        except ValueError:
            return custom_404(request)
        if self.request.user.persona.id == cuenta_a_desactivar_id:
            return super().dispatch(request, *args, **kwargs)
        else:
            return custom_403(request)         
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_confirmar'] = reverse_lazy('perfil:desactivar', kwargs={'id': self.kwargs['pk']})  # Reemplaza 'url_confirmar' con la URL de confirmación
        context['url_cancelar'] = reverse_lazy('usuario:detalle', kwargs={'pk': self.kwargs['pk']})  # Reemplaza 'url_cancelar' con la URL de cancelación
        context['usuario_logueado'] = self.request.user.persona
        return context

    
@login_required  
def desactivar_cuenta(request, id):
    """
        Desactiva la cuenta de usuario identificada por el ID proporcionado.
    
        Esta función intenta desactivar la cuenta de usuario correspondiente al ID proporcionado.
        Verifica si el usuario tiene permisos para desactivar la cuenta y realiza la desactivación.
        Después de desactivar la cuenta, el usuario se desconecta del sistema.
    
        Parametros:
            - id: El ID de la cuenta de usuario a desactivar.
    
        Retorno:
            - Redirige a la página de inicio de sesión después de desactivar la cuenta o muestra un mensaje de error si hay problemas.
    """
    try:
        if request.user.persona.pk == int(id):
            if Persona.objects.filter(pk=id).exists():
                
                user = Persona.objects.get(pk=id).usuario
                user.is_active = False
                user.save()        
                # lo saca del sistema
                logout(request)
                messages.info(request, 'Tu cuenta ha sido desactivada con éxito.')
                return redirect('perfil:login')
        else:
            # Caso donde el ID que recibe el view no es el del usuario logueado
            messages.error(request, "Cuenta no desactivada. ID incorrecto.")
    except Exception as e:
        messages.error(request, "Error al desactivar la cuenta.") 
           
    return HttpResponseRedirect(reverse('usuario:detalle', kwargs={'pk': id}))

def error_activar_desactivar(request, codigo):
    """
        Muestra una página de error relacionada con la activación o desactivación de cuentas.
    
        Esta función recibe un código de error y utiliza la clase ErrorActivarDesactivar para obtener
        la descripción asociada al código de error. Luego, renderiza una página de error con la descripción.
    
        Parámetros:
            - codigo: El código de error asociado al tipo de error ocurrido.
    
        Retorno:
    """
    context = {'error': ErrorActivarDesactivar.get_descripcion(codigo)}
    return render(request, 'registration/error_activacion_registro.html', context)
    
