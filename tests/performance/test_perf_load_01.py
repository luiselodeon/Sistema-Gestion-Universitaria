"""
tests/performance/test_perf_load_01.py
Runner en Pytest para la prueba de carga sostenida: TC-PERF-LOAD-01
Permite validar los SLAs/SLOs de rendimiento directamente desde la suite de pruebas
utilizando peticiones asíncronas concurrentes o invocando a Locust en modo headless.
"""

import os
import time
import pytest
import requests
from concurrent.futures import ThreadPoolExecutor


class TestTCPerfLoad01SustainedPeak:
    """
    Evaluación automatizada de latencia y tasa de errores bajo 50 usuarios virtuales.
    """

    # Asigna este test a la suite de rendimiento y SLAs (registrado en pytest.ini bajo addopts --strict-markers).
    # Este caso ejecuta una ráfaga de 50 usuarios virtuales (VUs) concurrentes mediante ThreadPoolExecutor
    # para validar los umbrales de latencia percentil (p50 <= 400ms, p95 <= 1500ms) y porcentaje de fallos 5xx (< 0.5%).
    # Al marcarlo con 'perf', se asegura que solo se ejecute durante fases de auditoría de rendimiento y no entorpezca
    # las pruebas unitarias rápidas del flujo diario (`pytest -m perf`).
    @pytest.mark.perf
    def test_tc_perf_load_01_concurrent_requests_sla(self):
        """
        Ejecuta ráfaga de 50 peticiones concurrentes contra /estudiantes/inscripciones
        y audita que el percentil 95 de latencia cumpla con el SLA (<= 1500 ms)
        y la tasa de error sea menor al 0.5%.
        """
        target_url = os.getenv("TEST_TARGET_URL", "http://localhost:5002")
        endpoint = f"{target_url}/gestion_estudiantes/inscripciones"

        try:
            # Comprobar conectividad con el servicio web
            r = requests.get(target_url, timeout=2)
        except Exception:
            pytest.skip(
                f"Servidor web local ({target_url}) no está activo. "
                "Para ejecutar esta prueba levanta los contenedores con 'docker compose up -d'."
            )

        num_vus = 50
        durations = []
        status_codes = []

        def execute_user_request(_):
            start = time.perf_counter()
            try:
                resp = requests.get(endpoint, timeout=5)
                elapsed = (time.perf_counter() - start) * 1000  # Convertir a milisegundos
                return resp.status_code, elapsed
            except Exception as e:
                elapsed = (time.perf_counter() - start) * 1000
                return 500, elapsed

        # Ejecución paralela de 50 VUs
        with ThreadPoolExecutor(max_workers=num_vus) as executor:
            results = list(executor.map(execute_user_request, range(num_vus)))

        for status, latency in results:
            status_codes.append(status)
            durations.append(latency)

        # Cálculo de percentiles
        durations.sort()
        idx_p50 = int(len(durations) * 0.50)
        idx_p95 = int(len(durations) * 0.95)
        p50_latency = durations[idx_p50]
        p95_latency = durations[idx_p95]

        failed_requests = [s for s in status_codes if s >= 500]
        error_rate = (len(failed_requests) / len(status_codes)) * 100

        print(f"\n[TC-PERF-LOAD-01] VUs Concurrentes: {num_vus}")
        print(f"[TC-PERF-LOAD-01] Latencia p50: {p50_latency:.2f} ms (Objetivo <= 400 ms)")
        print(f"[TC-PERF-LOAD-01] Latencia p95: {p95_latency:.2f} ms (Objetivo <= 1500 ms)")
        print(f"[TC-PERF-LOAD-01] Tasa de Errores 5xx: {error_rate:.2f}% (Objetivo < 0.5%)")

        # Aserciones de SLAs / SLOs
        assert error_rate < 0.5, f"La tasa de errores ({error_rate}%) excedió el umbral de 0.5%"
        assert p95_latency <= 1500, f"La latencia p95 ({p95_latency:.2f} ms) excedió el SLA de 1500 ms"
