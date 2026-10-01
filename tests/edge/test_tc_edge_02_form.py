"""
tests/edge/test_tc_edge_02_form.py
Especificación e Implementación de Prueba: TC-EDGE-02
Objetivo: Demostrar y mitigar el fallo de retorno prematuro en validate_form_from_table,
          el cual causa que solo se valide el primer campo del formulario y se ignoren
          todos los campos subsecuentes con datos inválidos o corruptos.

Módulo evaluado: utils.form_validation.validate_form_from_table
Prioridad: P0 (Must-Have / Crítica)
"""

import pytest
from unittest.mock import patch, MagicMock

from utils.form_validation import validate_form_from_table
from utils.validators import (
    validate_string, validate_int, validate_float,
    validate_date, validate_enum
)
from tests.fixtures.mock_schemas import MOCK_MULTI_FIELD_SCHEMA


# ============================================================================
# IMPLEMENTACIÓN CORREGIDA / BLINDADA (Referencia Arquitectónica)
# ============================================================================

def hardened_validate_form_from_table(cursor, table_name, form, schema_override=None):
    """
    Versión corregida del validador de formularios.
    En lugar de ejecutar 'return' incondicional en el primer campo, evalúa
    la totalidad del esquema y detiene la ejecución solo ante un fallo real
    o acumula todos los errores detectados.
    """
    if schema_override is not None:
        schema = schema_override
    else:
        from utils.schema_generator import generate_schema_from_table
        schema = generate_schema_from_table(cursor, table_name)

    for field, rules in schema.items():
        # 1. Comprobación de campo obligatorio ausente
        if rules.get("required") and (field not in form or str(form.get(field, "")).strip() == ""):
            return False, f"El campo {field} es obligatorio."

        raw_val = form.get(field, "")
        value = str(raw_val).strip() if raw_val is not None else ""

        # Si el campo no es requerido y viene vacío, se permite omitir la validación de tipo
        if not rules.get("required") and value == "":
            continue

        valid = True
        error = None

        # 2. Validación según tipo de dato sin retorno prematuro
        field_type = rules.get("type")
        if field_type == "string":
            valid, error = validate_string(value, rules)
        elif field_type == "int":
            valid, error = validate_int(value, rules)
        elif field_type == "float":
            valid, error = validate_float(value, rules)
        elif field_type == "date":
            valid, error = validate_date(value, rules)
        elif field_type == "enum":
            valid, error = validate_enum(value, rules)

        # Si un campo falla la validación, se retorna de inmediato el error detectado
        if not valid:
            return False, error

    # Si todos los campos del esquema superaron sus respectivas pruebas
    return True, None


# ============================================================================
# CASOS DE PRUEBA: TC-EDGE-02
# ============================================================================

class TestTCEdge02FormValidationLoop:
    """
    Suite de pruebas para certificar la exhaustividad del motor de validación
    de formularios frente al bug de retorno prematuro.
    """

    # ¿Por qué @pytest.mark.edge y @patch?
    # - @pytest.mark.edge: Categoriza este caso como prueba de frontera y fallo arquitectónico (retorno prematuro
    #   en el bucle de validación), permitiendo ejecutarla con `pytest -m edge`.
    # - @patch("utils.form_validation.generate_schema_from_table"): Intercepta dinámicamente la generación del esquema
    #   para desacoplar la prueba de una base de datos real. Inyecta de forma controlada el esquema sintético multicampo
    #   ('MOCK_MULTI_FIELD_SCHEMA') asegurando que la prueba evalúe estrictamente la lógica de iteración de campos.
    @pytest.mark.edge
    @patch("utils.form_validation.generate_schema_from_table")
    def test_current_flaw_demonstration_premature_return_ignores_subsequent_invalid_fields(
        self, mock_gen_schema, mock_cursor
    ):
        """
        Demuestra la vulnerabilidad en el código actual:
        El formulario tiene el campo 1 válido (string), pero el campo 2 ('campo_2_edad')
        es una cadena alfanumérica que NO es un número entero.
        En el código actual, la función retorna inmediatamente en el campo 1 con (True, None),
        ignorando por completo que el campo 2 está corrupto.
        """
        mock_gen_schema.return_value = MOCK_MULTI_FIELD_SCHEMA

        # Payload donde campo 1 es válido pero campo 2 es completamente inválido
        flawed_payload = {
            "campo_1_nombre": "Carlos Soto",           # Válido (< 20 caracteres)
            "campo_2_edad": "esta_edad_no_es_entero", # ¡INVÁLIDO!
            "campo_3_costo": "150.00",
            "campo_4_fecha": "2026-03-30",
            "campo_5_estatus": "ACTIVO"
        }

        # Ejecutamos la función original de utils/form_validation.py
        is_valid, error = validate_form_from_table(mock_cursor, "tabla_test", flawed_payload)

        # ASERCIÓN DEL BUG ACTUAL:
        # En el código no corregido, is_valid es TRUE porque salió en la línea 20
        assert is_valid is True, (
            "Fallo de arquitectura confirmado: El código actual retorna True prematuramente "
            "e ignora campos corruptos posteriores."
        )
        assert error is None

    # ¿Por qué @pytest.mark.edge?
    # Marca la prueba dentro de la suite de validación defensiva para verificar que el bucle
    # inspeccione y rechace errores de tipo entero en campos posteriores al primero.
    @pytest.mark.edge
    def test_hardened_validation_detects_invalid_integer_in_second_field(self, mock_cursor):
        """
        Verifica que la versión corregida inspeccione el segundo campo y rechace
        el formulario cuando contiene una entrada no numérica en campo entero.
        """
        payload = {
            "campo_1_nombre": "Carlos Soto",
            "campo_2_edad": "veinte_anios",  # Inválido
            "campo_3_costo": "150.00",
            "campo_4_fecha": "2026-03-30",
            "campo_5_estatus": "A"
        }

        is_valid, error = hardened_validate_form_from_table(
            mock_cursor, "test", payload, schema_override=MOCK_MULTI_FIELD_SCHEMA
        )

        assert is_valid is False, "Debe rechazar el formulario con edad inválida."
        assert "número entero" in error

    # ¿Por qué @pytest.mark.edge?
    # Clasifica la prueba de caso límite para comprobar el análisis de formatos complejos (fechas YYYY-MM-DD)
    # situados en posiciones intermedias/avanzadas del esquema.
    @pytest.mark.edge
    def test_hardened_validation_detects_malformed_date_in_fourth_field(self, mock_cursor):
        """
        Verifica que campos avanzados en el esquema (ej. campo 4: fecha)
        sean validados con rigor cuando los 3 primeros campos son válidos.
        """
        payload = {
            "campo_1_nombre": "Carlos Soto",
            "campo_2_edad": "25",
            "campo_3_costo": "99.90",
            "campo_4_fecha": "30/03/2026",  # Inválido: Formato incorrecto DD/MM/YYYY
            "campo_5_estatus": "A"
        }

        is_valid, error = hardened_validate_form_from_table(
            mock_cursor, "test", payload, schema_override=MOCK_MULTI_FIELD_SCHEMA
        )

        assert is_valid is False
        assert "Fecha inválida" in error

    # ¿Por qué @pytest.mark.edge?
    # Asegura que el validador examine los límites finales del formulario, comprobando la validación
    # de campos tipo enum en la quinta posición del esquema.
    @pytest.mark.edge
    def test_hardened_validation_detects_illegal_enum_in_fifth_field(self, mock_cursor):
        """
        Verifica que el último campo del esquema sea evaluado adecuadamente.
        """
        payload = {
            "campo_1_nombre": "Carlos Soto",
            "campo_2_edad": "25",
            "campo_3_costo": "99.90",
            "campo_4_fecha": "2026-03-30",
            "campo_5_estatus": "VALOR_INVENTADO_NO_PERMITIDO"  # Inválido
        }

        is_valid, error = hardened_validate_form_from_table(
            mock_cursor, "test", payload, schema_override=MOCK_MULTI_FIELD_SCHEMA
        )

        assert is_valid is False
        assert "Valor inválido" in error

    # ¿Por qué @pytest.mark.edge?
    # Caso de control dentro de la suite edge: confirma que un formulario con todos los campos
    # válidos no sea rechazado erróneamente (evita falsos positivos en el bucle corregido).
    @pytest.mark.edge
    def test_hardened_validation_approves_completely_valid_payload(self, mock_cursor):
        """
        Verifica que cuando los 5 campos cumplen con sus reglas,
        el formulario sea aceptado con (True, None).
        """
        valid_payload = {
            "campo_1_nombre": "Ingeniería Software",
            "campo_2_edad": "30",
            "campo_3_costo": "3500.50",
            "campo_4_fecha": "2026-08-15",
            "campo_5_estatus": "ACTIVO"
        }

        is_valid, error = hardened_validate_form_from_table(
            mock_cursor, "test", valid_payload, schema_override=MOCK_MULTI_FIELD_SCHEMA
        )

        assert is_valid is True
        assert error is None

    # ¿Por qué @pytest.mark.edge?
    # Evalúa la condición de borde donde un campo obligatorio faltante se encuentra al final
    # del formulario, asegurando que la iteración no se detenga antes de inspeccionarlo.
    @pytest.mark.edge
    def test_hardened_validation_detects_missing_required_field_at_end(self, mock_cursor):
        """
        Verifica que la omisión de un campo obligatorio ubicado al final del esquema
        sea detectada sin importar que los campos previos estén poblados.
        """
        missing_last_field_payload = {
            "campo_1_nombre": "Carlos Soto",
            "campo_2_edad": "25",
            "campo_3_costo": "100.0",
            "campo_4_fecha": "2026-03-30"
            # Falta 'campo_5_estatus'
        }

        is_valid, error = hardened_validate_form_from_table(
            mock_cursor, "test", missing_last_field_payload, schema_override=MOCK_MULTI_FIELD_SCHEMA
        )

        assert is_valid is False
        assert "El campo campo_5_estatus es obligatorio" in error
