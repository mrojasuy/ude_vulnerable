from django.core.exceptions import ValidationError

class CustomValidators:
    
    @staticmethod
    def valor_no_negativo(value):
        if value < 0:
            raise ValidationError("Este campo no puede ser un valor negativo.")

    # @staticmethod
    # def validate_date_not_in_future(value):
    #     if value and value > timezone.now().date():
    #         raise ValidationError("La fecha no puede estar en el futuro.")
