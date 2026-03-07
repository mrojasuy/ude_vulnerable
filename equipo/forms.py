from equipo.models import Jugador, Equipo, EquipoTrofeo
from django import forms
from datetime import date, timedelta
import re
from django.core.exceptions import ValidationError    
from django.contrib.admin.widgets import AdminDateWidget


class JugadorForm(forms.ModelForm):

    class Meta:
        model = Jugador
        exclude = ('equipo', )
        widgets = {
            'fecha_nacimiento': AdminDateWidget(),
            'fichado': AdminDateWidget(),
            'fin_contrato': AdminDateWidget(),
        }
        
    field_order  = ['nombre_completo', 'posicion' ,'altura','fecha_nacimiento',
                    'fichado','fin_contrato', 'salario','valor_mercado', 'pie']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['posicion'].label = 'Posición'
    
    def clean_nombre_completo(self):
        nombre = self.cleaned_data.get('nombre_completo')
        if not re.match("^[a-zA-ZñÑáéíóúÁÉÍÓÚ ]+$", nombre) or len(nombre) < 1:
            raise ValidationError("El nombre ingresado no es valido.")
        return nombre
    
    def clean_altura(self):
        altura = self.cleaned_data.get('altura')
        # Verifica que la altura sea un número no vacío
        if altura is None:
            raise forms.ValidationError("La altura es requerida.")
        # Verifica que la altura esté en el rango específico
        if altura < 1 or altura > 2.5:
            raise ValidationError("La altura debe estar entre 1 y 2.5 metros.")
        return altura

    def clean_fecha_nacimiento(self):
        fecha_nacimiento = self.cleaned_data.get('fecha_nacimiento')
        # Calcula la fecha hace 14 años desde hoy
        fecha_minima = date.today() - timedelta(days=14 * 365)
        # Calcula la fecha hace 50 años desde hoy
        fecha_maxima = date.today() - timedelta(days=60 * 365)
        
        # Verifica que la persona tenga al menos 14 años y no más de 60 años
        if fecha_nacimiento:
            if fecha_nacimiento > fecha_minima:
                raise ValidationError("El jugador debe tener al menos 14 años de edad.")
            elif fecha_nacimiento < fecha_maxima:
                raise ValidationError("El jugador no puede tener más de 60 años de edad.")
        
        return fecha_nacimiento
    
    def clean_fin_contrato(self):
        fichado = self.cleaned_data.get('fichado')
        fin_contrato = self.cleaned_data.get('fin_contrato')
        # Verifica que la fecha de fin de contrato sea posterior a la fecha de fichado
        if fin_contrato and fichado: 
            if fichado > fin_contrato:
                raise ValidationError("La fecha de inicio del contrato no puede ser superior a la de fin del contrato.") 
        return fin_contrato


class EquipoForm(forms.ModelForm):

    class Meta:
        model = Equipo
        fields = '__all__'
        widgets = {
            'fecha_fundado': AdminDateWidget(),
        }
    
    historia = forms.CharField(widget=forms.Textarea(attrs={
            'style': 'width:250px;',
            'rows': 10,
        }),
        required=False
    )
    
    field_order  = ['nombre', 'fecha_fundado',  'escudo', 'pais',
                    'historia']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:  
            self.fields['fecha_fundado'].label = 'Fundado el'


    def clean_fecha_fundado(self):
        fecha_fundado = self.cleaned_data.get('fecha_fundado')
        if fecha_fundado and fecha_fundado > date.today():
            self.add_error('fecha_fundado', "La fecha de fundación no puede ser mayor que la fecha actual.")
        return fecha_fundado


class EquipoTrofeoForm(forms.ModelForm):

    class Meta:
        model = EquipoTrofeo
        fields = '__all__'
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['equipo'].disabled = True  
        
    def clean(self):
        cleaned_data = super().clean()
        equipo = cleaned_data.get('equipo')
        trofeo = cleaned_data.get('trofeo')
        
        # Verificar si ya existe un registro con la misma combinación de equipo y trofeo
        if EquipoTrofeo.objects.filter(equipo=equipo, trofeo=trofeo).exclude(pk=self.instance.pk).exists():
            self.add_error('trofeo', "Ya existe un registro con la misma combinación de equipo y trofeo.")
        
    def clean_cantidad(self):
        cantidad = self.cleaned_data.get('cantidad')
        if cantidad < 0:
            self.add_error('cantidad', "La cantidad ingresada no puede ser negativa.")
        return cantidad