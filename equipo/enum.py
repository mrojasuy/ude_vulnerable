class EquipoPais:
    URUGUAY = 1
    ARGENTINA = 2
    CHILE = 3
    
    choices = [
        (URUGUAY, 'URUGUAY'),
        (ARGENTINA, 'ARGENTINA'),
        (CHILE, 'CHILE'),
    ]
    
class JugadorPie:
    DERECHO = 1
    IZQUIERDO = 2
    SIN_DEFINIR = 3

    
    choices = [
        (DERECHO, 'DERECHO'),
        (IZQUIERDO, 'IZQUIERDO'),
        (SIN_DEFINIR, 'SIN DEFINIR'),

    ]
    
class JugadorPosicion:
    ARQUERO = 1
    LATERAL_IZQUIERDO = 2
    LATERAL_DERECHO = 3
    MEDIOCAMPO = 4
    VOLANTE_IZQUIERDA = 5
    VOLANTE_DERECHA = 6
    DELANTERO = 7
    DEFENSA_CENTRAL = 8
    SIN_DEFINIR = 9
    
    choices = [
        (ARQUERO, 'Arquero'),
        (LATERAL_IZQUIERDO, 'Lateral izquierdo'),
        (LATERAL_DERECHO, 'Lateral derecho'),
        (LATERAL_IZQUIERDO, 'Lateral izquierdo'),
        (MEDIOCAMPO, 'Mediocampo'),
        (VOLANTE_IZQUIERDA, 'Volante izquierdo'),
        (VOLANTE_DERECHA, 'Volante derecho'),
        (DELANTERO, 'Delantero'),
        (DEFENSA_CENTRAL, 'Defensa central'),
        (SIN_DEFINIR, 'Sin definir'),
    ]
    
class EquipoTrofeoOpcion:
    PROGDS = 1
    INTERMEDIO = 2
    COPA_LIBERTADORES = 3
    COPA_INTERCONTINENTAL = 4  
    choices = [
        (PROGDS, 'Trofeo PROGDS'),
        (COPA_LIBERTADORES, 'Copa Libertadores'),
        (INTERMEDIO, 'Intermedio'),
        (COPA_INTERCONTINENTAL, 'Copa Intercontinental'),
    ]