"""
tests/edge/test_tc_edge_01_sqli.py
Especificación e Implementación de Prueba: TC-EDGE-01
Objetivo: Demostrar vector de inyección SQL en la introspección dinámica de tablas
          y verificar los mecanismos de remediación defensiva (Whitelist de tablas).

Módulo evaluado: utils.schema_generator.generate_schema_from_table
"""

import re
import pytest
from unittest.mock import MagicMock

from utils.schema_generator import generate_schema_from_table
from tests.fixtures.mock_schemas import (
    VALID_DATABASE_TABLES,
    MOCK_DESCRIBE_ESTUDIANTE_COLUMNS
)


# ============================================================================
# FUNCIONES DE REMEDIACIÓN Y VALIDACIÓN DEFENSIVA (Propuestas en Arquitectura)
# ============================================================================

def validate_table_name_whitelist(table_name: str) -> str:
    """
    Función de remediación recomendada: Valida el nombre de tabla contra
    la lista blanca inmutable del sistema antes de pasarlo al motor SQL.
    """
    if not isinstance(table_name, str):
        raise ValueError("El nombre de la tabla debe ser una cadena de texto.")
    
    clean_name = table_name.strip().lower()
    if clean_name not in VALID_DATABASE_TABLES:
        raise ValueError(f"Tabla no válida o no permitida: '{table_name}'. Acceso DDL denegado.")
    
    # Verificación estricta de caracteres alfanuméricos seguros
    if not re.match(r"^[a-z0-9_]+$", clean_name):
        raise ValueError(f"Caracteres ilegales detectados en nombre de tabla: '{table_name}'.")
    
    return clean_name


def hardened_generate_schema_from_table(cursor, table_name: str):
    """
    Versión blindada de generate_schema_from_table con protección anti-SQLi.
    """
    validated_table = validate_table_name_whitelist(table_name)
    return generate_schema_from_table(cursor, validated_table)


# ============================================================================
# CASOS DE PRUEBA: TC-EDGE-01
# ============================================================================

class TestTCEdge01SQLInjection:
    """
    Suite de pruebas para validar y blindar la función generate_schema_from_table
    contra inyecciones SQL directas y basadas en tiempo/booleanas.
    """

    # Clasifica este caso dentro de la suite de casos borde, límites y fallos de seguridad
    # (registrado en pytest.ini). Permite ejecutar selectivamente la suite defensiva usando
    # `pytest -m edge` sin tener que correr pruebas unitarias estándar o pruebas de carga.
    @pytest.mark.edge
    def test_current_implementation_vulnerability_flaw_detection(self, mock_cursor):
        """
        Demuestra la vulnerabilidad actual en el código fuente:
        La instrucción f"DESCRIBE {table_name}" concatena directamente el argumento,
        enviando el payload sin sanitizar al cursor de base de datos.
        """
        malicious_payload = "estudiante; DROP TABLE logs; --"

        # Ejecutamos la función original con el payload malicioso
        generate_schema_from_table(mock_cursor, malicious_payload)

        # Aserción: Comprobar que el cursor recibió la cadena concatenada sin filtrar
        mock_cursor.execute.assert_called_once_with(f"DESCRIBE {malicious_payload}")
        executed_query = mock_cursor.execute.call_args[0][0]

        # Verificación crítica: La consulta enviada contiene la sentencia inyectada
        assert "DROP TABLE" in executed_query, (
            "Vulnerabilidad confirmada: La consulta SQL contiene comandos arbitrarios inyectados."
        )

    # - @pytest.mark.edge: Mantiene el etiquetado para auditorías de seguridad y casos límite.
    # - @pytest.mark.parametrize: Permite inyectar múltiples vectores de ataque SQL maliciosos
    #   (consultas apiladas, inyecciones booleanas/basadas en tiempo, bypass con bytes nulos y path traversal)
    #   reutilizando la misma lógica de prueba sin duplicar código. Cada payload se ejecuta como un
    #   caso de prueba independiente, facilitando aislar con precisión qué patrón específico falla o pasa.
    @pytest.mark.edge
    @pytest.mark.parametrize("malicious_table_input", [
        "estudiante; DROP TABLE logs; --",
        "estudiante' OR '1'='1",
        "estudiante WHERE 1=1 AND SLEEP(3)",
        "persona\x00--",
        "usuarios' UNION SELECT 1, 'v', 'NO' --",
        "catalogo_oculto_privado",
        "../../etc/passwd",
        "estudiante/*comentario*/"
    ])
    def test_sqli_defense_whitelist_blocks_malicious_inputs(self, mock_cursor, malicious_table_input):
        """
        Verifica que el mecanismo de remediación basado en lista blanca (Whitelist)
        rechace de forma inmediata con ValueError cualquier entrada sospechosa,
        garantizando que el cursor de MySQL NUNCA sea invocado con código malicioso.
        """
        mock_cursor.reset_mock()

        # Debe lanzar ValueError antes de tocar la base de datos
        with pytest.raises(ValueError) as exc_info:
            hardened_generate_schema_from_table(mock_cursor, malicious_table_input)

        # Criterio de Aceptación: Mensaje de error controlado y descriptivo
        assert "Tabla no válida o no permitida" in str(exc_info.value) or "Caracteres ilegales" in str(exc_info.value)

        # Verificación profunda: El cursor no debe haberse ejecutado jamás
        assert mock_cursor.execute.call_count == 0, (
            "Fallo de seguridad: cursor.execute fue llamado a pesar de entrada maliciosa."
        )

    # - @pytest.mark.edge: Certifica la robustez de la frontera de validación del sistema.
    # - @pytest.mark.parametrize: Evalúa de forma iterativa y exhaustiva toda la lista blanca de tablas legítimas
    #   del sistema, asegurando que la remediación defensiva no produzca falsos positivos durante la introspección.
    @pytest.mark.edge
    @pytest.mark.parametrize("valid_table", [
        "estudiante",
        "persona",
        "aula",
        "horario",
        "claseprogramada",
        "inscripcion",
        "pago"
    ])
    def test_sqli_defense_allows_legitimate_tables(self, mock_cursor, valid_table):
        """
        Verifica que la protección por lista blanca no genere falsos positivos
        y permita la introspección fluida de tablas válidas del sistema.
        """
        mock_cursor.reset_mock()
        mock_cursor.fetchall.return_value = MOCK_DESCRIBE_ESTUDIANTE_COLUMNS

        # Invocación con tabla legítima
        schema = hardened_generate_schema_from_table(mock_cursor, valid_table)

        # Criterio de Aceptación: Se consulta la tabla limpia y se genera el esquema
        mock_cursor.execute.assert_called_once_with(f"DESCRIBE {valid_table}")
        assert isinstance(schema, dict), "El resultado debe ser un diccionario de esquema."

    # Categoriza la verificación de tipos incompatibles (None, enteros, listas) en la frontera de entrada,
    # garantizando que la función defensiva rechace tipos anómalos antes de interactuar con la base de datos.
    @pytest.mark.edge
    def test_non_string_type_payload_rejection(self, mock_cursor):
        """
        Prueba de robustez ante tipos cruzados (None, int, listas o diccionarios).
        """
        mock_cursor.reset_mock()

        with pytest.raises(ValueError):
            validate_table_name_whitelist(None)

        with pytest.raises(ValueError):
            validate_table_name_whitelist(12345)

        with pytest.raises(ValueError):
            validate_table_name_whitelist(["estudiante"])

        assert mock_cursor.execute.call_count == 0

    # Clasifica esta prueba como una verificación que interactúa con un servidor real de MySQL (requiere conexión viva).
    # Permite aislar pruebas que dependen de infraestructura externa (`pytest -m integration`) y excluirlas
    # en ejecuciones rápidas o en entornos de CI sin base de datos activa (`pytest -m "not integration"`).
    @pytest.mark.integration
    def test_sqli_live_database_syntax_rejection(self, db_live_connection):
        """
        Prueba de integración real (opcional): Verifica que si se envía una consulta
        maliciosa a MySQL, el motor relacional no ejecute inyecciones ciegas.
        """
        cursor = db_live_connection.cursor(dictionary=True)
        try:
            # Entrada con comillas o sentencias múltiples
            with pytest.raises(Exception):
                cursor.execute("DESCRIBE estudiante; DROP TABLE non_existent_test_table;")
        finally:
            cursor.close()
