"""
tests/performance/test_tc_perf_race_condition.py
Especificación e Implementación de Prueba: TC-PERF-LOAD-02
Objetivo: Concurrencia extrema y detección de Race Condition en el último cupo de aula.
          Sincroniza 10 solicitudes concurrentes en una ventana < 50ms para intentar
          ocupar el último lugar disponible de un aula de capacidad = 30 con 29 inscritos.

Criterios de Aceptación:
1. Exactamente 1 solicitud tiene éxito.
2. Exactamente 9 solicitudes son rechazadas limpiamente por aula llena.
3. El conteo final en base de datos debe ser estrictamente 30 (CERO SOBRECUPOS / NO OVERBOOKING).
   Si la base de datos registra 31 o más inscritos, la prueba FALLA revelando la
   condición de carrera TOCTOU (Time Of Check To Time Of Use).

Prioridad: P0 (Must-Have / Crítica)
"""

import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor
import pytest
import requests

from utils.estudiantes import inscripcion_crud


class TestTCRaceConditionLastSeat:
    """
    Suite de prueba para validar la consistencia transaccional y prevención
    de sobrecupos ante colisión simultánea de inscripciones.
    """

    # ¿Por qué @pytest.mark.perf y @pytest.mark.slow?
    # - @pytest.mark.perf: Clasifica la prueba dentro del dominio de rendimiento, concurrencia y sobrecarga
    #   (definido en pytest.ini). Permite ejecutar la suite de rendimiento con `pytest -m perf`.
    # - @pytest.mark.slow: Advierte que la prueba es intensiva en tiempo y recursos (abre 10 conexiones TCP
    #   independientes a MySQL, sincroniza hilos con una barrera threading.Barrier y verifica consistencia
    #   transaccional). Permite omitirla en pipelines de CI rápidos con `pytest -m "not slow"`.
    @pytest.mark.perf
    @pytest.mark.slow
    def test_tc_perf_race_condition_live_db_concurrency(self, db_live_connection, perf_test_scenario_setup):
        """
        Prueba de concurrencia directa en capa de persistencia utilizando múltiples
        conexiones TCP a MySQL sincronizadas mediante una barrera threading.Barrier(10).
        """
        import mysql.connector

        scenario = perf_test_scenario_setup
        id_clase = scenario["idclaseprogramada"]

        # Parámetros de conexión para los 10 hilos
        host = os.getenv("TEST_DB_HOST", os.getenv("DB_HOST", "localhost"))
        port = int(os.getenv("TEST_DB_PORT", "3306"))
        user = os.getenv("TEST_DB_USER", os.getenv("MYSQL_USER", "root"))
        password = os.getenv("TEST_DB_PASSWORD", os.getenv("MYSQL_PASSWORD", "rootpassword"))
        database = os.getenv("TEST_DB_NAME", os.getenv("MYSQL_DATABASE", "controlescolar_db"))

        # Obtenemos 10 estudiantes distintos no inscritos en la materia
        cursor_main = db_live_connection.cursor(dictionary=True)
        cursor_main.execute("""
            SELECT e.matricula_alumno 
            FROM estudiante e 
            WHERE e.matricula_alumno NOT IN (
                SELECT matricula_alumno FROM inscripcion WHERE idclaseprogramada = %s
            )
            LIMIT 10
        """, (id_clase,))
        candidatos = [row["matricula_alumno"] for row in cursor_main.fetchall()]
        cursor_main.close()

        if len(candidatos) < 10:
            pytest.skip(f"Se requieren al menos 10 estudiantes disponibles (encontrados: {len(candidatos)}).")

        num_threads = 10
        barrier = threading.Barrier(num_threads)
        results = []
        errors = []
        results_lock = threading.Lock()

        def worker_enroll(matricula_alumno):
            """Función ejecutada por cada hilo concurrente."""
            conn_worker = None
            try:
                conn_worker = mysql.connector.connect(
                    host=host, port=port, user=user, password=password, database=database
                )
                cursor_worker = conn_worker.cursor(dictionary=True)

                # ESPERA EN LA BARRERA: Todos los hilos se alinean aquí
                barrier.wait()

                # DISPARO SIMULTÁNEO: Ventana de colisión en sub-milisegundos
                inscripcion_id = inscripcion_crud.add_inscripcion(
                    cursor_worker,
                    matricula_alumno=matricula_alumno,
                    idclaseprogramada=id_clase,
                    motivo_inscripcion="Prueba de Concurrencia Extrema TC-PERF-LOAD-02"
                )
                conn_worker.commit()

                with results_lock:
                    results.append((matricula_alumno, inscripcion_id))

            except Exception as exc:
                with results_lock:
                    errors.append((matricula_alumno, str(exc)))
            finally:
                if conn_worker and conn_worker.is_connected():
                    conn_worker.close()

        # Lanzamiento paralelo de los 10 hilos
        threads = []
        for mat in candidatos:
            t = threading.Thread(target=worker_enroll, args=(mat,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # ====================================================================
        # ASERCIONES Y VERIFICACIÓN PROFUNDA
        # ====================================================================

        # 1. Inspeccionar conteo real en Base de Datos
        cursor_verify = db_live_connection.cursor(dictionary=True)
        cursor_verify.execute("""
            SELECT COUNT(*) AS total_inscritos
            FROM inscripcion
            WHERE idclaseprogramada = %s AND estatus != 'CANCELADA'
        """, (id_clase,))
        res = cursor_verify.fetchone()
        total_inscritos = res["total_inscritos"]
        cursor_verify.close()

        print(f"\n[TC-PERF-LOAD-02] Resultados: Exitosos = {len(results)}, Rechazados = {len(errors)}")
        print(f"[TC-PERF-LOAD-02] Total de Alumnos en Aula tras Concurrencia: {total_inscritos}/30")

        # 2. Aserción de Cero Sobrecupo (Zero Overbooking)
        assert total_inscritos <= 30, (
            f"¡FALLO CRÍTICO DE RACE CONDITION / SOBRECUPOS DETECTADO! "
            f"El aula tiene capacidad de 30 pero quedaron inscritos {total_inscritos} alumnos. "
            f"Se requiere implementar bloqueo atómico con 'SELECT ... FOR UPDATE' en check_classroom_capacity."
        )

        # 3. Aserción de que exactamente 1 logró inscribirse si había 1 cupo
        assert len(results) == 1, (
            f"Debe haber exactamente 1 inscripción exitosa para el último cupo. Hubo: {len(results)}"
        )
        assert len(errors) == 9, (
            f"Deben haber exactamente 9 rechazos controlados. Hubo: {len(errors)}"
        )

    # ¿Por qué @pytest.mark.perf?
    # Agrupa la prueba dentro de la suite de concurrencia y estrés sobre la capa web HTTP.
    # Permite evaluar si el servidor Flask tolera ráfagas concurrentes en el endpoint de inscripciones
    # sin arrojar errores 500 bajo ejecución de pruebas de carga (`pytest -m perf`).
    @pytest.mark.perf
    def test_tc_perf_race_condition_http_api(self):
        """
        Prueba equivalente sobre el endpoint HTTP POST /estudiantes/inscripciones/add
        cuando la aplicación Flask está corriendo en el contenedor web (puerto 5002).
        """
        target_url = os.getenv("TEST_TARGET_URL", "http://localhost:5002")
        endpoint = f"{target_url}/estudiantes/inscripciones/add"

        try:
            # Comprobar si el servidor está arriba
            resp = requests.get(target_url, timeout=2)
        except Exception:
            pytest.skip(f"Servidor web local ({target_url}) no está activo. Omitiendo prueba HTTP.")

        # Realizamos 10 peticiones concurrentes mediante ThreadPoolExecutor
        num_requests = 10
        barrier = threading.Barrier(num_requests)
        http_responses = []

        def send_http_request(student_id):
            payload = {
                "matricula_alumno": str(student_id),
                "idclaseprogramada": "7777",
                "motivo_inscripcion": "Prueba HTTP Concurrente",
                "estatus": "INICIADA"
            }
            # Sincronización en barrera
            barrier.wait()
            try:
                r = requests.post(endpoint, data=payload, allow_redirects=False, timeout=5)
                return r.status_code, r.text
            except Exception as e:
                return 500, str(e)

        with ThreadPoolExecutor(max_workers=num_requests) as executor:
            futures = [executor.submit(send_http_request, 9000 + i) for i in range(num_requests)]
            http_responses = [f.result() for f in futures]

        status_codes = [status for status, _ in http_responses]
        # Al menos una petición debe ser procesada y ninguna debe arrojar 500
        assert 500 not in status_codes, "El servidor arrojó errores 500 bajo concurrencia extrema."
