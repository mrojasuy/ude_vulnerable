from django.contrib import admin
from usuario.models import Hincha, Dirigente, Persona, TokenActivacion


admin.site.register(Persona)
admin.site.register(Hincha)
admin.site.register(Dirigente)
admin.site.register(TokenActivacion)
