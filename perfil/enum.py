class ErrorActivarDesactivar:
    TOKEN_NO_EXISTE = 1
    TOKEN_USADO = 2
    
    choices = [
        (TOKEN_NO_EXISTE, 'token recibido no exsite.'),
        (TOKEN_USADO, 'token recibido ya fue usado.'),
    ]
    
    @staticmethod
    def get_descripcion(value):
        for valor, descripcion in ErrorActivarDesactivar.choices:
            if valor == int(value):
                return descripcion
        return "Valor no válido"  # Puedes el