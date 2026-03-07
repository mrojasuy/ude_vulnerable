from django import forms
from .models import Persona
from usuario.models import Hincha, Dirigente
from equipo.models import Equipo

class PersonaForm(forms.ModelForm):
    class Meta:
        model = Persona
        fields = ['nombre', 'apellido', 'email',  'password']

    password = forms.CharField(widget=forms.PasswordInput())
    
class HinchaForm(forms.ModelForm):
    class Meta:
        model = Hincha
        fields = ['nombre', 'apellido', 'email', 'equipos']
        
    equipos = forms.ModelMultipleChoiceField(
        queryset=Equipo.objects.all(),
    )

class DirigenteForm(forms.ModelForm):
    class Meta:
        model = Dirigente
        fields = ['nombre', 'apellido', 'email']
