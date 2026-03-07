from django.urls import path
from django.contrib.auth import views as auth_views
from perfil.views import sign_up, activar_cuenta, desactivar_cuenta,\
    error_activar_desactivar, sign_up_directivo, PreDesactivarCuenta
from perfil.forms import PasswordResetForm
#from prodieweb.perfil.forms import PasswordResetForm

app_name = 'perfil'
urlpatterns = [
    #path('login/', CustomLoginView.as_view(), name='login'),
    path('', auth_views.LoginView.as_view(), name='login'),
    path('logout', auth_views.LogoutView.as_view(), name='logout'),
    path('registro/', sign_up, name='registro'),
    path('registro/directivo/<equipo>/', sign_up_directivo, name='registro-directivo'),

    path('activar/<token>/', activar_cuenta, name='activar'),
    path('pre-desactivar/<pk>/', PreDesactivarCuenta.as_view(), name='pre-desactivar'),
    path('desactivar/<id>/', desactivar_cuenta, name='desactivar'),
    path('error/activar/desactivar/<codigo>/', error_activar_desactivar, name='error-activar-desactivar'),

    
    path('password_reset', auth_views.PasswordResetView.as_view(), {'password_reset_form': PasswordResetForm}, name='password_reset'),
    path('password_reset/done', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('password_change', auth_views.PasswordChangeView.as_view(), name='password_change'),
    path('password_change_done', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),
]