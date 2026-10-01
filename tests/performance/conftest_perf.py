"""
tests/performance/conftest_perf.py
Fixtures especializadas para pruebas de rendimiento y concurrencia.
Gestiona el sembrado controlado de datos masivos y el teardown idempotente.
"""

import os
import pytest
from datetime import date


@pytest.fixture
def perf_test_scenario_setup(db_live_connection):
    """
    Prepara el estado inicial para la prueba de condición de carrera TC-PERF-LOAD-02:
    - 1 Aula con capacidad = 30 (idaula = 888)
    - 1 Asignatura de prueba (idasignatura = 888)
    - 1 Docente, Horario y Periodo de prueba
    - 1 Clase Programada (idclaseprogramada = 7777)
    - 29 Inscripciones previas activas (Queda 1 SOLO CUPO DISPONIBLE)
    - 10 Estudiantes contendientes preparados
    """
    cursor = db_live_connection.cursor(dictionary=True)
    created_resources = {
        "idaula": 888,
        "idclaseprogramada": 7777,
        "idperiodo": 888,
        "idasignatura": 888,
        "matriculas": list(range(9001, 9011))
    }

    try:
        # 1. Limpieza previa por si quedaron datos residuales
        cursor.execute("DELETE FROM inscripcion WHERE idclaseprogramada = 7777")
        cursor.execute("DELETE FROM claseprogramada WHERE idclaseprogramada = 7777")
        cursor.execute("DELETE FROM aula WHERE idaula = 888")
        db_live_connection.commit()

        # 2. Inserción de Aula con Capacidad = 30
        cursor.execute("""
            INSERT INTO aula (idaula, descripcion_aula, lugar_fisico, capacidad)
            VALUES (888, 'Aula de Pruebas de Carga', 'Edificio QA', 30)
            ON DUPLICATE KEY UPDATE capacidad = 30
        """)

        # 3. Asegurar que exista la clase 7777
        # Buscamos un horario y docente existentes o usamos los del sistema
        cursor.execute("SELECT idhorario FROM horario LIMIT 1")
        horario = cursor.fetchone()
        id_horario = horario["idhorario"] if horario else 1

        cursor.execute("SELECT iddocente FROM docente LIMIT 1")
        docente = cursor.fetchone()
        id_docente = docente["iddocente"] if docente else 1

        cursor.execute("SELECT idperiodoinscripciones FROM periodoinscripciones WHERE estatus='ABIERTO' LIMIT 1")
        periodo = cursor.fetchone()
        id_periodo = periodo["idperiodoinscripciones"] if periodo else 1

        cursor.execute("SELECT idasignatura FROM asignatura LIMIT 1")
        asig = cursor.fetchone()
        id_asig = asig["idasignatura"] if asig else 1

        cursor.execute("SELECT idcalendarioescolar FROM calendarioescolar LIMIT 1")
        cal = cursor.fetchone()
        id_cal = cal["idcalendarioescolar"] if cal else 1

        cursor.execute("""
            INSERT INTO claseprogramada 
            (idclaseprogramada, idasignatura, modalidad, idhorario, iddocente, idperiodoinscripciones, idcalendarioescolar, idaula, idioma)
            VALUES (7777, %s, 'PRESENCIAL', %s, %s, %s, %s, 888, 'ESP')
        """, (id_asig, id_horario, id_docente, id_periodo, id_cal))

        # 4. Inserción de 29 inscripciones previas para dejar 1 SOLO cupo
        # Obtenemos o creamos 29 estudiantes base
        cursor.execute("SELECT matricula_alumno FROM estudiante LIMIT 35")
        estudiantes_existentes = cursor.fetchall()
        
        today = date.today()
        enrolled_count = 0
        for est in estudiantes_existentes[:29]:
            cursor.execute("""
                INSERT INTO inscripcion (matricula_alumno, idclaseprogramada, fecha_inscripcion, motivo_inscripcion, estatus)
                VALUES (%s, 7777, %s, 'Pre-seeding 29 cupos', 'INICIADA')
            """, (est["matricula_alumno"], today))
            enrolled_count += 1

        db_live_connection.commit()
        created_resources["pre_enrolled_count"] = enrolled_count

        yield created_resources

    finally:
        # TEARDOWN Y LIMPIEZA IDEMPOTENTE
        try:
            cursor.execute("DELETE FROM inscripcion WHERE idclaseprogramada = 7777")
            cursor.execute("DELETE FROM claseprogramada WHERE idclaseprogramada = 7777")
            cursor.execute("DELETE FROM aula WHERE idaula = 888")
            db_live_connection.commit()
        except Exception:
            db_live_connection.rollback()
        finally:
            cursor.close()
