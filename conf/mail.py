from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _
from django.template.loader import get_template
import os
from django.core import mail



class AutomaticMail:
    '''
    Arma mail utilizando html.

    class NuevaClase(AutomaticMail):
        recipients = ['usuario@algo.com']
        subject = 'Asunto'
        template_name = 'app/template_name.html'
        context = {'personas': Persona.objects.all()}

    template_name: debe extender de "base_mail.html"


    Instanciar Mail
        mail = AutomaticMail(subject='hola', message='sdf')
        mail.send()
    '''

    sender = None
    recipients = None
    subject = None
    template_name = None
    context = None
    message = None

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod
    def run(cls):
        instance = cls()
        instance.send()

    def send(self):
        if self.message:
            return self.send_message_mail()
        else:
            return self.send_template_mail()

    def send_message_mail(self):
        return self.send_mail(
            self.get_subject(),
            self.message,
            self.get_sender(),
            self.get_recipients(),
        )

    def send_template_mail(self):
        if self.can_send():
            return self.send_mail(
                self.get_subject(),
                '',
                self.get_sender(),
                self.get_recipients(),
                html_message=self.render_template()
            )

    def can_send(self):
        '''Override to set send condition'''
        return True

    def get_subject(self):
        if not self.subject:
            raise ImproperlyConfigured(_('Falta asunto del mail'))
        return self.subject

    def get_sender(self):
        if not self.sender:
            self.sender = 'no-reply@prodie.com.uy'
        return self.sender

    def get_recipients(self):
        if 'test' in os.environ['DJANGO_SETTINGS_MODULE']:
            return self.sender
        if not self.recipients:
            return list(map(lambda admin: admin[1], 'rodrigoperera@outlook.com'))
        return self.recipients

    def render_template(self):
        template = self.get_template()
        return template.render(self.get_context())

    def get_template(self):
        template_name = self.get_template_name()
        template = get_template(template_name)
        return template

    def get_template_name(self):
        if not self.template_name:
            raise ImproperlyConfigured(_('template_name no definido.'))
        return self.template_name

    def get_context(self):
        if not self.context:
            return dict()
        return self.context
    
    def send_mail(self, subject, message, from_email, recipient_list,
              fail_silently=False, auth_user=None, auth_password=None,
              connection=None, html_message=None):
        #if 'produccion' in os.environ['DJANGO_SETTINGS_MODULE']:
        return mail.send_mail(subject, message, from_email, recipient_list, fail_silently, auth_user, auth_password, connection, html_message)
        # if 'local' in os.environ['DJANGO_SETTINGS_MODULE']:
        #     return mail.send_mail(subject, message, from_email, recipient_list, fail_silently, auth_user, auth_password, connection, html_message)
        # if 'test' in os.environ['DJANGO_SETTINGS_MODULE']:
        #     # el que envia es el que recive en testing
        #     # se desactiva el envio de mails en testing hasta que busque una solucion definitiva.
        #     return True