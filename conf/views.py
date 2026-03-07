from django.shortcuts import render

# Create your views here.

def custom_404(request, exception=None):
    context = {'exception': exception}
    return render(request, 'conf/error/404.html', context, status=404)

def custom_403(request, exception=None):
    context = {'exception': exception}
    return render(request, 'conf/error/403.html', context ,status=403)

def sin_permiso(request, mensaje=None):
    context = {'mensaje': mensaje}
    return render(request, 'conf/error/error_permisos.html', context )
