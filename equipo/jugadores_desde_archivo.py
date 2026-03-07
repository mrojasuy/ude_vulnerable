from django.db import transaction
from decimal import Decimal
from django.shortcuts import get_object_or_404
from equipo.models import Equipo, Jugador
import re
from equipo.enum import JugadorPie, JugadorPosicion
import random
import unicodedata
from datetime import date


class ImportarArchivoClase():
    '''
        Clase para importar datos de jugadores desde un archivo Excel a la base de datos.
    '''
    
    TWOPLACES = Decimal(10) ** -2
    COLUMNA_EQUIPO = 1
    COLUMNA_JUGADOR = 2
    COLUMNA_POSICION = 3
    COLUMNA_FECHA_NACIMIENTO = 4
    COLUMNA_ALTURA = 5
    COLUMNA_PIERNA = 6
    COLUMNA_FICHADO = 7
    COLUMNA_CONTRATO = 8
    COLUMNA_VALOR_MERCADO = 9
    
    def __init__(self):
        """
            Inicializa la clase ImportarArchivoClase.
            
            Atributos:
                - listado_errores: Lista para almacenar mensajes de error durante la importación.
                - listado_a_cargar: Lista para almacenar los datos válidos a cargar en la base de datos.
                - cant_cargados: Contador de registros nuevos cargados.
                - cant_actualizados: Contador de registros existentes actualizados.
                - carga_realizada: Indica si la carga se realizó con éxito.
            """
        self.listado_errores = []
        self.listado_a_cargar = []
        self.cant_cargados = 0
        self.cant_actualizados = 0
        self.carga_realizada = False
        
    def validar(self, archivo):
        """
            Valida los datos en el archivo Excel.
    
            Parámetros:
                - archivo: Archivo Excel con los datos a validar.
    
            Retorna:
                - listado_errores: Lista de errores encontrados durante la validación.
                - listado_a_cargar: Lista de datos válidos listos para cargar en la base de datos.
        """
        try:
            hoja = archivo.active
            filas_con_datos = 0
            for row in hoja.iter_rows(values_only=True):
                if any(cell for cell in row if cell is not None):
                    filas_con_datos += 1
                else:
                    break

            linea = 1
            filas = hoja.rows
            for fila in filas:
                if linea > 1:
                    self.validar_fila(linea, fila)
                
                linea += 1
                if linea > filas_con_datos:
                    break

        except Exception as e:
            self.listado_errores.append(str(e))
        return self.listado_errores, self.listado_a_cargar 
    
    def validar_fila(self, linea, fila):
        """
            Valida una fila de datos del archivo Excel.
    
            Parámetros:
            - linea: Número de línea actual.
            - fila: Fila de datos del archivo Excel.
    
            Agrega el errores al listado_errores en caso de problemas y agrega datos válidos a listado_a_cargar.
        """
        id_equipo = None
        jugador_nombre_completo = None
        fecha_nacimiento = None
        posicion = None
        pierna_habil = None
        inicio_contrato = None
        fin_contrato = None
        valor_mercado = None

        for col, columna in enumerate(fila, start=1):
            if col == self.COLUMNA_EQUIPO:
                id_equipo = self.validar_columna_equipo(linea, col, columna)

            elif col == self.COLUMNA_JUGADOR:
                jugador_nombre_completo = self.validar_columna_jugador(linea, col, columna)

            elif col == self.COLUMNA_POSICION:
                posicion = self.validar_columna_posicion(linea, col, columna)

            elif col == self.COLUMNA_FECHA_NACIMIENTO:
                fecha_nacimiento = self.validar_columna_fecha_nacimiento(linea, col, columna)

            elif col == self.COLUMNA_ALTURA:
                altura = self.validar_columna_altura(linea, col, columna)
                if altura is not None:
                    altura = columna.value

            elif col == self.COLUMNA_PIERNA:
                pierna_habil = self.validar_columna_pierna(linea, col, columna)

            elif col == self.COLUMNA_FICHADO:
                inicio_contrato = self.validar_columna_fichado(linea, col, columna)

            elif col == self.COLUMNA_CONTRATO:
                fin_contrato = self.validar_columna_contrato(linea, col, columna, inicio_contrato)

            elif col == self.COLUMNA_VALOR_MERCADO:
                valor_mercado = self.validar_columna_valor_mercado(linea, col, columna)

        if not self.listado_errores:
            detalle = {
                'num_fila': linea,
                'equipo': self.get_equipo(id_equipo),
                'jugador_nombre_completo': jugador_nombre_completo,
                'posicion': posicion,
                'fecha_nacimiento': fecha_nacimiento,
                'altura': altura,
                'pierna_habil': pierna_habil,
                'inicio_contrato': inicio_contrato,
                'fin_contrato': fin_contrato,
                'valor_mercado': valor_mercado,
            }
            self.listado_a_cargar.append(detalle)

    def validar_columna_equipo(self, linea, col, columna):
        if not columna.value:
            self.listado_errores.append(self.error_detectado(linea, col, 'El campo equipo no puede ser vacío.'))
        elif not self.equipo_valido(columna.value):
            self.listado_errores.append(self.error_detectado(linea, col, 'Equipo no válido.'))
        else:
            return columna.value

    def validar_columna_jugador(self, linea, col, columna):
        if not columna.value:
            self.listado_errores.append(self.error_detectado(linea, col, 'El campo nombre no puede ser vacío.'))
        elif not self.contenido_es_texto(columna.value):
            self.listado_errores.append(self.error_detectado(linea, col, 'El nombre y el apellido solo deben contener letras.'))
        else:
            return columna.value

    def validar_columna_posicion(self, linea, col, columna):
        if not columna.value:
            self.listado_errores.append(self.error_detectado(linea, col, 'El campo posición no puede ser vacío.'))
        elif not self.contenido_es_texto(columna.value):
            self.listado_errores.append(self.error_detectado(linea, col, 'El nombre de la posición solo puede contener letras.'))
        else:
            posicion = self.get_posicion(columna.value.rstrip()) 
            if not posicion:
                self.listado_errores.append(self.error_detectado(linea, col, 'La posición recibida no es válida'))
            
            return posicion

    def validar_columna_fecha_nacimiento(self, linea, col, columna):
        if not columna.value:
            self.listado_errores.append(self.error_detectado(linea, col, 'El campo fecha de nacimiento no puede ser vacío.'))
        elif not self.fecha_formato_valido(columna.value):
            self.listado_errores.append(self.error_detectado(linea, col, 'El formato de la fecha no es correcto.'))
        elif columna.value.date() >= date.today():
            self.listado_errores.append(self.error_detectado(linea, col, 'La fecha de nacimiento no puede ser mayor a la fecha actual.'))
        else:
            return columna.value

    def validar_columna_altura(self, linea, col, columna):
        if columna.value:
            if not self.es_numero(columna.value):
                self.listado_errores.append(self.error_detectado(linea, col, 'La altura solo puede contener números.'))
            elif not self.altura_valida(columna.value):
                self.listado_errores.append(self.error_detectado(linea, col, 'La altura debe estar entre 1 y 2.5 metros.'))
            else:
                return columna.value

    def validar_columna_pierna(self, linea, col, columna):
        if columna.value and not self.validar_pierna_habil(columna.value):
            self.listado_errores.append(self.error_detectado(linea, col, 'Valor incorrecto de pierna hábil.'))
        else:
            return self.get_pierna_habil(columna.value)

    def validar_columna_fichado(self, linea, col, columna):
        if columna.value and not self.fecha_formato_valido(columna.value):
            self.listado_errores.append(self.error_detectado(linea, col, 'El formato de la fecha en la que se fichó no es correcto.'))
        else:
            return columna.value

    def validar_columna_contrato(self, linea, col, columna, inicio_contrato):
        if columna.value and not self.fecha_formato_valido(columna.value):
            self.listado_errores.append(self.error_detectado(linea, col, 'El formato de la fecha de contrato no es correcto.'))
        else:
            if columna.value and inicio_contrato:
                if columna.value < inicio_contrato:
                    self.listado_errores.append(self.error_detectado(linea, col, 'La fecha de inicio del contrato no puede ser superior a la de fin del contrato.'))
                else:
                    return columna.value

    def validar_columna_valor_mercado(self, linea, col, columna):
        valor_mercado = 0
        if columna.value:
            if not self.es_numero(columna.value):
                self.listado_errores.append(self.error_detectado(linea, col, 'El valor del mercado solo puede contener números.'))
            elif columna.value < 0:
                self.listado_errores.append(self.error_detectado(linea, col, 'El valor del mercado no puede ser negativo.'))
            else:
                return columna.value
            
    def pre_cargar(self, listado_a_cargar):
        """
            Realiza pre-carga de datos y actualiza los contadores de registros cargados y actualizados.
        
            Parámetros:
                - listado_a_cargar: Lista de datos válidos.
        
            Retorna:
                - carga_realizada: Indica si la carga se realizó con éxito.
                - mensaje_carga: Mensaje informativo sobre la carga.
                - listado_errores: Lista de errores encontrados durante la carga.
        """
        try:
            self.cargar_jugadores(listado_a_cargar)
    
            if self.hay_errores():
                self.cant_cargados = 0
                self.cant_actualizados = 0
    
            if self.cant_cargados > 0:
                mensaje_carga = 'Carga finalizada con éxito. Se cargaron {0} registros'.format(self.cant_cargados)
                self.carga_realizada = True
            elif self.cant_actualizados > 0:
                mensaje_carga = 'Carga finalizada con éxito. Se actualizaron {0} registros'.format(self.cant_actualizados)
                self.carga_realizada = True
            else:
                mensaje_carga = 'No se pudieron cargar los registros. Verifique el archivo e intente de nuevo.'
        except Exception as e:
            mensaje_carga = 'Error durante la carga: {0}'.format(str(e))

        return self.carga_realizada, mensaje_carga, self.listado_errores
    
    @transaction.atomic
    def cargar_jugadores(self, listado_a_cargar):
        try:
            for item in listado_a_cargar:
                self._cargar_jugadores(item)
        except Exception as e:
            self.listado_errores.append('Error durante la carga de jugadores: {0}'.format(str(e)))
    
    def _cargar_jugadores(self, item):
        """
            Método para cargar un jugador en la base de datos.
    
            Parámetros:
            - item: Diccionario con datos del jugador.
    
        """
        equipo = item['equipo']
        nombre_completo = item['jugador_nombre_completo']
        posicion = item['posicion'] 
        fecha_nacimiento = item['fecha_nacimiento']  
        altura = item['altura']
        pierna_habil = item['pierna_habil']
        inicio_contrato = item['inicio_contrato']
        fin_contrato = item['fin_contrato']
        valor_mercado = item['valor_mercado']
        salario = 0
        porcentaje_aleatorio = random.randint(1, 10)
        if valor_mercado:
            salario = (porcentaje_aleatorio / 100) * valor_mercado
        else:
            valor_mercado = 0
        if not Jugador.objects.filter(nombre_completo=nombre_completo,
                                      equipo=equipo,
                                      fin_contrato=fin_contrato,
                                      fichado=inicio_contrato).exists():
            obj_jugadro = Jugador(
                equipo=equipo,
                nombre_completo=nombre_completo,
                fecha_nacimiento=fecha_nacimiento,
                altura=altura,
                pie=pierna_habil,
                fichado=inicio_contrato,
                fin_contrato=fin_contrato,
                valor_mercado=valor_mercado,
                salario=salario,
                posicion=posicion
                )
            obj_jugadro.save()
            self.cant_cargados += 1
        else:
            jugador = Jugador.objects.get(nombre_completo=nombre_completo,
                                          equipo=equipo,
                                          fin_contrato=fin_contrato,
                                           fichado=inicio_contrato)
            jugador.equipo = equipo
            jugador.nombre_completo = nombre_completo
            jugador.fecha_nacimiento = fecha_nacimiento
            jugador.altura = altura
            jugador.pie = pierna_habil
            jugador.fichado = inicio_contrato
            jugador.fin_contrato = fin_contrato
            jugador.valor_mercado = valor_mercado
            jugador.salario = salario
            jugador.posicion = posicion
            jugador.save()
            self.cant_actualizados += 1
    
    def hay_errores(self):
        return len(self.listado_errores) > 0

    def error_detectado(self, linea, columna=None, error=None):
        if not error: 
            campo_nombre = self.get_campo_nombre(columna)
            error = 'Falta informacion en el campo {}'.format(campo_nombre)
        
        if columna:
            mensaje = '(Fila: {0} | Columna: {1}) - {2}'.format(linea, columna, error)
        else:
            mensaje = '(Fila: {0}) - {1}'.format(linea, error)
            
        return mensaje

    def fecha_formato_valido(self, valor):
        return isinstance(valor, date)
        
    def get_equipo(self, id_equipo):
        try:
            equipo = get_object_or_404(Equipo, pk=id_equipo)
        except Equipo.DoesNotExist:
            self.listado_errores.append('Equipo con ID {0} no encontrado.'.format(id_equipo))
            equipo = None
        return equipo

    def get_posicion(self, posicion):
        mapeo_posiciones = {
            'Portero': JugadorPosicion.ARQUERO,
            'Defensa central': JugadorPosicion.DEFENSA_CENTRAL,
            'Defensa': JugadorPosicion.DEFENSA_CENTRAL,
            'Lateral izquierdo': JugadorPosicion.LATERAL_IZQUIERDO,
            'Interior izquierdo': JugadorPosicion.LATERAL_IZQUIERDO,
            'Interior derecho': JugadorPosicion.LATERAL_DERECHO,
            'Lateral derecho': JugadorPosicion.LATERAL_DERECHO,
            'Centrocampista': JugadorPosicion.MEDIOCAMPO,
            'Mediocentro ofensivo': JugadorPosicion.MEDIOCAMPO,
            'Mediapunta': JugadorPosicion.MEDIOCAMPO,
            'Mediocentro': JugadorPosicion.MEDIOCAMPO,
            'Delantero centro': JugadorPosicion.DELANTERO,
            'Delantero derecho': JugadorPosicion.DELANTERO,
            'Delantero izquierdo': JugadorPosicion.DELANTERO,
            'Delantero': JugadorPosicion.DELANTERO,
            'Pivote': JugadorPosicion.DELANTERO,
            'Extremo izquierdo': JugadorPosicion.DELANTERO,
            'Extremo derecho': JugadorPosicion.DELANTERO,
        }
        
        return mapeo_posiciones.get(posicion)
        
    def equipo_valido(self, id_equipo):
        return Equipo.objects.filter(pk=id_equipo).exists()
    
    def es_numero(self, valor):
        return isinstance(valor, float) or isinstance(valor, int) 
        
    def es_str(self, valor):
        return isinstance(valor, str)
   
    def elimina_tildes(self, cadena):
        s = ''.join((c for c in unicodedata.normalize('NFD', cadena) if unicodedata.category(c) != 'Mn'))
        return s

    def contenido_es_texto(self, valor):
        if self.es_str(valor):
            sin_tilde = self.elimina_tildes(valor)
            return re.match("^[a-zA-ZñÑ ]+$", sin_tilde)
        else:
            return False
    
    def altura_valida(self, altura):
        valida = True
        if altura < 1 or altura > 2.5:
            valida = False
        return valida
    
    def get_pierna_habil(self, valor):
        if valor == 'derecho':
            return JugadorPie.DERECHO
        elif valor == 'izquierdo':
            return JugadorPie.IZQUIERDO
        else:
            return JugadorPie.SIN_DEFINIR
        
    def validar_pierna_habil(self, valor):
        return valor == 'derecho' or valor == 'izquierdo'
