from django.contrib.auth.models import AbstractUser

class Perfil(AbstractUser):
    pass

    class Meta:
        abstract = False
        permissions = (
            ("ver_menu_admin", "Permite ver menu de admin"),
            ("crear_jugadores_desde_archivo", "Permite cargar archivo de jugadores"),
            ("generar_fixtur", "Permite generar el fixture de partidos"),
            ("eliminar_jugadores_de_forma_masiva", "Permite eliminar todos los jugadores cargados"),
        )