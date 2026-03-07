from django.contrib.auth.decorators import login_required
from django.views.generic.base import TemplateView
from django.utils.decorators import method_decorator
from equipo.models import Equipo
from django.contrib.auth.mixins import LoginRequiredMixin
from conf.views import custom_403
# Create your views here.

@method_decorator(login_required, name='dispatch')
class Index(LoginRequiredMixin, TemplateView):
    template_name = 'demo/index.html'
    
    def dispatch(self, request, *args, **kwargs):
        if hasattr(self.request.user, 'persona') and self.request.user.persona:
            return super().dispatch(request, *args, **kwargs)
        else:
            return custom_403(request)
        
    def get_context_data(self, **kwargs):
        context = TemplateView.get_context_data(self, **kwargs)
        equipos = Equipo.objects.filter(pk__in=self.request.user.persona.get_id_equipos())
        context['equipos'] = equipos
        return context
