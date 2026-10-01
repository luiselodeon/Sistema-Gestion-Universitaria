"""
tests/conftest.py
Configuración global de Pytest y fixtures compartidas para la suite de pruebas.
Provee cursores mock, cliente de pruebas Flask y gestión de sesiones simuladas.
"""

import sys
import os
from unittest.mock import MagicMock
import pytest

# Asegurar que el directorio raíz del proyecto esté en el PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app as flask_app
from tests.fixtures.mock_schemas import MOCK_DESCRIBE_ESTUDIANTE_COLUMNS


@pytest.fixture
def mock_cursor():
    """
    Cursor simulado compatible con mysql.connector (dictionary=True).
    Registra llamadas a execute() y devuelve estructuras de datos preconfiguradas.
    """
    cursor = MagicMock()
    cursor.fetchall.return_value = MOCK_DESCRIBE_ESTUDIANTE_COLUMNS
    cursor.fetchone.return_value = MOCK_DESCRIBE_ESTUDIANTE_COLUMNS[0]
    cursor.lastrowid = 1001
    cursor.rowcount = 1
    return cursor


@pytest.fixture
def mock_db_connection(mock_cursor):
    """
    Conexión de base de datos simulada con métodos ACID (commit, rollback, cursor).
    """
    conn = MagicMock()
    conn.cursor.return_value = mock_cursor
    conn.commit = MagicMock()
    conn.rollback = MagicMock()
    conn.close = MagicMock()
    return conn


@pytest.fixture
def app():
    """
    Instancia de la aplicación Flask configurada en modo TESTING.
    """
    flask_app.config.update({
        "TESTING": True,
        "SECRET_KEY": "test-secret-key-automation",
        "WTF_CSRF_ENABLED": False  # Facilitar pruebas de API/rutas
    })
    return flask_app


@pytest.fixture
def client(app):
    """
    Cliente de pruebas HTTP de Flask (app.test_client).
    """
    return app.test_client()


@pytest.fixture
def auth_client(client):
    """
    Factory fixture para generar clientes de prueba autenticados con distintos roles.
    Uso: auth_client(rol="admin", email="admin@universidad.edu")
    """
    def _create_authenticated_client(rol="operacion_academica", email="test@universidad.edu", user_id=1):
        with client.session_transaction() as sess:
            sess["user_id"] = user_id
            sess["user_rol"] = rol
            sess["user_email"] = email
        return client
    return _create_authenticated_client


@pytest.fixture(scope="session")
def db_live_connection():
    """
    Fixture opcional para pruebas de integración reales contra MySQL.
    Si la base de datos no está disponible en el host configurado, omite la prueba limpiamente.
    """
    try:
        import mysql.connector
        host = os.getenv("TEST_DB_HOST", os.getenv("DB_HOST", "localhost"))
        port = int(os.getenv("TEST_DB_PORT", "3306"))
        user = os.getenv("TEST_DB_USER", os.getenv("MYSQL_USER", "root"))
        password = os.getenv("TEST_DB_PASSWORD", os.getenv("MYSQL_PASSWORD", "rootpassword"))
        database = os.getenv("TEST_DB_NAME", os.getenv("MYSQL_DATABASE", "controlescolar_db"))

        conn = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        yield conn
        conn.close()
    except Exception as exc:
        pytest.skip(f"Base de datos de prueba no disponible ({exc}). Omitiendo pruebas live.")
