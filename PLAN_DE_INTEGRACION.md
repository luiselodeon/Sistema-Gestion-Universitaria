# PLAN TÉCNICO DE INTEGRACIÓN Y AUTOMATIZACIÓN DE PRUEBAS
**Sistema:** Sistema de Gestión Universitaria  
**Documento:** Especificación Técnica de Implementación de Pruebas (Test Integration Plan)  
**Ciclo Crítico:** `TC-EDGE-01`, `TC-EDGE-02`, `TC-PERF-LOAD-01`, `TC-PERF-LOAD-02`  
**Versión:** 1.0.0  
**Fecha:** Septiembre 2026  
**Rol:** Lead QA Automation Engineer & Reliability Architect  
**Estado:** Especificación Técnica Aprobada para Implementación

---

## 1. Objetivo y Alcance del Ciclo de Pruebas

### 1.1 Propósito Técnico
El presente plan establece la arquitectura, diseño de fixtures, simulación de escenarios, criterios de aserción profunda y precondiciones de infraestructura para automatizar un **subconjunto crítico de pruebas de alta prioridad (P0 y P1)** definido en el [`PLAN_DE_PRUEBAS.md`](file:///e:/Github/Sistema-Gestion-Universitaria/PLAN_DE_PRUEBAS.md).

Este ciclo no funcional y de casos borde tiene como objetivo certificar la robustez y resiliencia del sistema ante vectores de falla catastróficos:
1.  **Seguridad de Capa de Datos:** Demostrar y mitigar vectores de inyección SQL en la introspección dinámica de metadatos de tablas.
2.  **Integridad de Contrato de Validación:** Verificar la exhaustividad del motor de validación de formularios, eliminando omisiones silenciosas de campos inválidos.
3.  **Resiliencia y Capacidad de Servicio (Throughput):** Validar la capacidad de respuesta sostenida de la aplicación durante picos masivos de inscripción de materias.
4.  **Consistencia Transaccional Estricta (ACID):** Garantizar la ausencia absoluta de sobrecupos (*overbooking*) en aulas ante contención de concurrencia extrema en ventanas de tiempo de sub-milisegundos.

### 1.2 Matriz de Trazabilidad Técnica

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                            MATRIZ DE TRAZABILIDAD DEL CICLO                                 │
├─────────────────┬──────────┬─────────────────────────────┬───────────────────┬──────────────┤
│ ID Caso         │ Prioridad│ Módulo / Endpoint           │ Tipo de Prueba    │ Objetivo     │
├─────────────────┼──────────┼─────────────────────────────┼───────────────────┼──────────────┤
│ TC-EDGE-01      │ P0       │ utils/schema_generator.py   │ Seguridad (SQLi)  │ DDL Blindado │
│ TC-EDGE-02      │ P0       │ utils/form_validation.py    │ Integridad Lógica │ Bucle Total  │
│ TC-PERF-LOAD-01 │ P1       │ POST /inscripciones/add     │ Carga (50 VUs)    │ SLA p95<1.5s │
│ TC-PERF-LOAD-02 │ P0       │ POST /inscripciones/add     │ Race Condition    │ 0 Sobrecupos │
└─────────────────┴──────────┴─────────────────────────────┴───────────────────┴──────────────┘
```

---

## 2. Desglose Técnico Detallado por Caso de Prueba

```
                                  ARQUITECTURA DEL CICLO CRÍTICO
                                  
      [ Pytest Test Runner ]                       [ Locust / K6 Engine ]
                 │                                            │
        ┌────────┴────────┐                          ┌────────┴────────┐
        ▼                 ▼                          ▼                 ▼
   TC-EDGE-01        TC-EDGE-02               TC-PERF-LOAD-01   TC-PERF-LOAD-02
  (SQLi Schema)     (Form Loop Bug)           (50 VUs Peak)     (Last Seat Race)
        │                 │                          │                 │
        ▼                 ▼                          ▼                 ▼
   [ schema_generator ] [ form_validation ]     [ Flask App / Gunicorn (Port 5002) ]
        │                 │                          │
        └────────┬────────┘                          ▼
                 ▼                            [ MySQL 8.0 Engine ]
        [ Mock / Test DB ]                    (controlescolar_db)
```

---

### 2.1 Caso de Prueba: `TC-EDGE-01` – Inyección SQL en Generador Dinámico de Esquemas

*   **Trazabilidad:** [`PLAN_DE_PRUEBAS.md#TC-EDGE-01`](file:///e:/Github/Sistema-Gestion-Universitaria/PLAN_DE_PRUEBAS.md)
*   **Módulo a Probar:** [`utils/schema_generator.py`](file:///e:/Github/Sistema-Gestion-Universitaria/utils/schema_generator.py) -> `generate_schema_from_table(cursor, table_name)`

#### A. Arquitectura de la Prueba
*   **Componentes Involucrados:**
    *   Módulo evaluado: `generate_schema_from_table`.
    *   Driver de persistencia: `mysql.connector.cursor(dictionary=True)`.
    *   Capa de aislamiento: Mock de cursor (`unittest.mock.MagicMock` / `pytest-mock`) y cursor real conectado a base de datos de pruebas para validar el comportamiento sintáctico del motor MySQL.

#### B. Estrategia de Datos y Fixtures
*   **Fixtures Requeridas:**
    *   `mock_cursor_sqli`: Simula un cursor MySQL donde `execute()` inspecciona la cadena enviada para registrar la instrucción SQL generada.
    *   `real_db_cursor`: Cursor transaccional contra MySQL con permisos restringidos de solo lectura para pruebas de integración reales.
*   **Cleanup Strategy:** No aplica mutación en base de datos al tratarse de sentencias `DESCRIBE`. Si se ejecuta contra base de datos real, se asegura el cierre inmediato del cursor tras la prueba.

#### C. Simulación del Escenario
Se inyectarán cadenas de ataque especialmente diseñadas para explotar la interpolación directa `f"DESCRIBE {table_name}"`:
1.  **Escape de Sentencia DDL con comando múltiple:**  
    `payload_1 = "estudiante; DROP TABLE test_dummy; --"`
2.  **Inyección con Subconsulta y Función de Retardo (Time-based Blind SQLi):**  
    `payload_2 = "estudiante WHERE 1=1 AND SLEEP(3)"`
3.  **Inyección con Caracteres Especiales y Operadores Booleanos:**  
    `payload_3 = "estudiante' OR '1'='1"`
4.  **Inyección de Caracteres Nulos y Comentarios:**  
    `payload_4 = "persona\x00--"`
5.  **Entrada no existente o fuera de lista blanca:**  
    `payload_5 = "informacion_confidencial_db"`

#### D. Aserciones y Verificación Profunda
1.  **Prevención a nivel de Aplicación:**
    *   La función debe verificar el argumento `table_name` contra una lista blanca (*whitelist*) inmutable de tablas del sistema:
        `VALID_TABLES = {"persona", "usuarios", "estudiante", "docente", "carrera", "asignatura", "aula", "horario", "claseprogramada", "inscripcion", "asistencia", "evaluacion", "calificacion_estudiante", "estadodecuenta", "pago", "beca", ...}`
    *   Cualquier valor no contenido en la lista blanca debe disparar de forma inmediata una excepción `ValueError("Tabla no válida o no permitida.")`.
2.  **Verificación de Llamadas SQL:**
    *   El método `cursor.execute` **jamás** debe ser invocado cuando el payload contiene caracteres no alfanuméricos o nombres ajenos a la lista blanca (`assert mock_cursor.execute.call_count == 0`).
3.  **Logs y Manejo de Errores:**
    *   Debe registrarse una entrada en el log de auditoría con severidad `WARNING` indicando un intento de introspección inválido.

---

### 2.2 Caso de Prueba: `TC-EDGE-02` – Omisión Masiva de Validaciones por Retorno Prematuro en Formulario

*   **Trazabilidad:** [`PLAN_DE_PRUEBAS.md#TC-EDGE-02`](file:///e:/Github/Sistema-Gestion-Universitaria/PLAN_DE_PRUEBAS.md)
*   **Módulo a Probar:** [`utils/form_validation.py`](file:///e:/Github/Sistema-Gestion-Universitaria/utils/form_validation.py) -> `validate_form_from_table(cursor, table_name, form)`
*   **Módulos Dependientes:** [`utils/validators.py`](file:///e:/Github/Sistema-Gestion-Universitaria/utils/validators.py), [`utils/schema_generator.py`](file:///e:/Github/Sistema-Gestion-Universitaria/utils/schema_generator.py).

#### A. Arquitectura de la Prueba
*   **Componentes Involucrados:**
    *   `validate_form_from_table`: Orquestador de validación de campos.
    *   Generador de esquemas: `generate_schema_from_table`.
    *   Validadores primitivos: `validate_string`, `validate_int`, `validate_float`, `validate_date`, `validate_enum`.

#### B. Estrategia de Datos y Fixtures
*   **Fixtures Requeridas:**
    *   `mock_schema_multi_field`: Mock que sustituye a `generate_schema_from_table` devolviendo un esquema sintético con 5 campos de tipos dispares ordenados secuencialmente:
        ```python
        {
            "campo_1_nombre": {"type": "string", "max": 20, "required": True},
            "campo_2_edad": {"type": "int", "required": True},
            "campo_3_costo": {"type": "float", "required": True},
            "campo_4_fecha": {"type": "date", "required": True},
            "campo_5_estatus": {"type": "enum", "values": ["A", "B"], "required": True}
        }
        ```
*   **Cleanup Strategy:** Operación pura en memoria sin efectos secundarios en disco ni en base de datos.

#### C. Simulación del Escenario
Se construye un payload donde el **primer campo es 100% válido**, pero uno o varios de los **campos subsiguientes contienen violaciones graves**:
*   **Payload 1 (Fallo en Campo 2 - Entero):**
    *   `"campo_1_nombre"` = `"Carlos"` (Válido, longitud < 20).
    *   `"campo_2_edad"` = `"veinte_anios"` (Inválido: no numérico).
    *   `"campo_3_costo"` = `"150.50"` (Válido).
    *   `"campo_4_fecha"` = `"2026-03-30"` (Válido).
    *   `"campo_5_estatus"` = `"A"` (Válido).
*   **Payload 2 (Fallo en Campo 4 - Fecha Malformada):**
    *   Campos 1 a 3 válidos.
    *   `"campo_4_fecha"` = `"30/03/2026"` (Inválido: formato DD/MM/YYYY en vez de YYYY-MM-DD).
*   **Payload 3 (Fallo en Campo 5 - Valor ENUM ilegal):**
    *   Campos 1 a 4 válidos.
    *   `"campo_5_estatus"` = `"X"` (Inválido: fuera de `["A", "B"]`).
*   **Payload 4 (Desbordamiento de String en Campo 1):**
    *   `"campo_1_nombre"` = `"CadenaExtremadamenteLargaQueSuperaLosVeinte"` (> 20 caracteres).

#### D. Aserciones y Verificación Profunda
1.  **Detección Inequívoca del Error Subsecuente:**
    *   Para el Payload 1, `validate_form_from_table` **no debe retornar `True`**. Debe retornar:
        `assert valid is False`
        `assert "Debe ser un número entero" in error_msg`
2.  **Verificación de Recorrido Completo del Bucle:**
    *   Se instrumentan espías (`mocker.spy`) sobre cada función de `validators.py` (`validate_string`, `validate_int`, etc.).
    *   Se comprueba que ante un formulario completamente válido, todas las funciones de validación correspondientes al esquema sean invocadas exactamente el número de veces requerido por sus campos:
        `assert mock_validate_int.call_count == 1`
        `assert mock_validate_float.call_count == 1`
        `assert mock_validate_date.call_count == 1`
3.  **Comprobación de Regresión:**
    *   Asegurar que corregir el retorno prematuro no cause que errores en campos posteriores sobreescriban silenciosamente errores de campos anteriores si se evalúan en serie (el primer error encontrado debe detener y reportar, o acumular una lista de errores).

---

### 2.3 Caso de Prueba: `TC-PERF-LOAD-01` – Carga Concurrente Sostenida en Picos de Inscripción (50 VUs)

*   **Trazabilidad:** [`PLAN_DE_PRUEBAS.md#TC-PERF-LOAD-01`](file:///e:/Github/Sistema-Gestion-Universitaria/PLAN_DE_PRUEBAS.md)
*   **Endpoints Bajo Carga:**
    *   `GET /estudiantes/inscripciones` (Lectura y renderizado de listado con joins masivos).
    *   `POST /estudiantes/inscripciones/add` (Mutación transaccional con validación de capacidad, duplicados y prerrequisitos).

#### A. Arquitectura de la Prueba
*   **Componentes Involucrados:**
    *   Generador de carga: `Locust` ejecutándose en contenedor o proceso independiente.
    *   Target Application: Flask App expuesta en `http://localhost:5002` (servida vía Gunicorn en entorno de staging o contenedor `proyecto_bases_web`).
    *   Base de datos: MySQL 8.0 (`controlescolar_db`).
    *   Módulos de negocio ejecutados en cada request: `inscripcion_crud.py`, `claseprogramada_crud.py`, `aula_crud.py`, `db.py`.

#### B. Estrategia de Datos y Fixtures
*   **Semillas Requeridas (Data Pre-seeding):**
    1.  Creación de un Periodo de Inscripción dedicado: `idperiodoinscripciones = 999`, estatus `'ABIERTO'`, fechas vigentes.
    2.  Población de 20 Clases Programadas (`idclaseprogramada` 9001 a 9020) con aulas de capacidad = 60 alumnos cada una.
    3.  Población de 100 Estudiantes activos (`matricula_alumno` 80001 a 80100) con estados de cuenta en cero y sin inscripciones previas en el periodo 999.
    4.  Usuarios de prueba autenticados: Sesiones con rol `operacion_academica` o cookies de sesión precalculadas para evitar saturar el endpoint de login durante la prueba de carga.
*   **Cleanup Strategy:**
    *   Script de purga post-ejecución:
        ```sql
        DELETE FROM inscripcion WHERE idclaseprogramada BETWEEN 9001 AND 9020;
        DELETE FROM claseprogramada WHERE idclaseprogramada BETWEEN 9001 AND 9020;
        DELETE FROM estudiante WHERE matricula_alumno BETWEEN 80001 AND 80100;
        DELETE FROM periodoinscripciones WHERE idperiodoinscripciones = 999;
        ```

#### C. Simulación del Escenario (Curva de Carga)
*   **Perfil de Tráfico:**
    *   **Usuarios Virtuales (VUs):** 50 usuarios concurrentes.
    *   **Tasa de Generación (Spawn Rate):** 5 usuarios/segundo (Ramp-up total: 10 segundos).
    *   **Tiempo de Prueba Sostenido (Steady State):** 5 minutos (300 segundos).
    *   **Ramp-down:** 15 segundos.
    *   **Think Time (Pausa de usuario):** Distribución uniforme entre 1.0 y 2.5 segundos.
*   **Comportamiento de los VUs:**
    *   70% de tráfico: `GET /estudiantes/inscripciones` (Consulta de estado).
    *   30% de tráfico: `POST /estudiantes/inscripciones/add` (Intento de inscripción con alumno y clase aleatoria del pool de pruebas).

#### D. Aserciones y Verificación Profunda (SLOs / SLAs)
1.  **Métricas de Latencia (Response Time SLOs):**
    *   Latencia percentil 50 (Mediana): `p50 <= 400 ms`.
    *   Latencia percentil 95: `p95 <= 1,500 ms`.
    *   Latencia percentil 99: `p99 <= 3,000 ms`.
2.  **Tasa de Éxito y Errores:**
    *   Tasa global de errores HTTP (códigos 500, 502, 503, 504 o timeouts): **`Error Rate < 0.5%`**.
    *   Throughput mínimo aceptable: **`>= 25 RPS`** (Requests Per Second).
3.  **Integridad de Recursos de Infraestructura:**
    *   El uso de CPU del contenedor de base de datos no debe exceder el 85% sostenido.
    *   Ninguna conexión debe arrojar `OperationalError: 1040 (Too many connections)`.

---

### 2.4 Caso de Prueba: `TC-PERF-LOAD-02` – Concurrencia Extrema y Detección de Race Condition en Último Cupo

*   **Trazabilidad:** [`PLAN_DE_PRUEBAS.md#TC-PERF-LOAD-02`](file:///e:/Github/Sistema-Gestion-Universitaria/PLAN_DE_PRUEBAS.md)
*   **Módulo a Probar:** [`utils/estudiantes/inscripcion_crud.py`](file:///e:/Github/Sistema-Gestion-Universitaria/utils/estudiantes/inscripcion_crud.py) -> `add_inscripcion`
*   **Ruta HTTP:** `POST /estudiantes/inscripciones/add`

#### A. Arquitectura de la Prueba
*   **Componentes Involucrados:**
    *   Barrera de concurrencia: Script de ejecución paralela multihilo con barrera de sincronización (`threading.Barrier` o `multiprocessing.Barrier`) para garantizar el envío simultáneo en ráfaga.
    *   Servidor Web y Capa de Persistencia MySQL con nivel de aislamiento de transacción (`REPEATABLE READ` por defecto en InnoDB).

#### B. Estrategia de Datos y Fixtures
*   **Estado Inicial Controlado:**
    1.  Aula de prueba: `idaula = 888`, `capacidad = 30`.
    2.  Clase programada: `idclaseprogramada = 7777`, asignada al aula 888.
    3.  Población previa exacta: **29 inscripciones activas** (`estatus = 'INICIADA'`) ligadas a la clase 7777.
    4.  **Disponibilidad real:** Exactamente **1 cupo libre**.
    5.  Estudiantes contendientes: 10 estudiantes distintos (`matricula_alumno` 9001 a 9010), ninguno inscrito previamente en la materia ni con materias en conflicto.
*   **Cleanup Strategy:**
    *   Eliminación de la clase 7777 y sus inscripciones de prueba inmediatamente después de verificar las aserciones.

#### C. Simulación del Escenario (Burst Concurrency)
*   **Mecanismo de Disparo:**
    *   Se configuran 10 hilos/procesos independientes, cada uno asignado a un estudiante diferente (matrículas 9001 a 9010).
    *   Todos los hilos preparan el payload POST: `{"matricula_alumno": matricula, "idclaseprogramada": 7777, "estatus": "INICIADA"}`.
    *   Se utiliza un objeto `Barrier(10)`: los 10 hilos esperan hasta que todos estén listos en el socket TCP.
    *   Al liberarse la barrera, los 10 requests se transmiten simultáneamente hacia el servidor en una ventana temporal **inferior a 50 milisegundos**.

```
Hilo 1 (Matrícula 9001) ──┐
Hilo 2 (Matrícula 9002) ──┤
Hilo 3 (Matrícula 9003) ──┤     [ BARRERA ]
Hilo 4 (Matrícula 9004) ──┼───> [ 10 Hilos ] ──( 50 ms )──> POST /inscripciones/add
...                       │     [ En Espera]
Hilo 10 (Matrícula 9010) ─┘
```

#### D. Aserciones y Verificación Profunda
1.  **Aserción de Respuestas HTTP:**
    *   Exactamente **1 hilo** debe recibir confirmación de éxito (HTTP 200 o redirección 302 con mensaje de éxito).
    *   Exactamente **9 hilos** deben recibir rechazo controlado (mensaje flash `"El aula está llena (30/30)"` o respuesta HTTP con categoría `danger`).
    *   Ningún hilo debe recibir error HTTP 500 (Internal Server Error) ni excepciones no capturadas.
2.  **Aserción de Consistencia en Base de Datos (Zero Overbooking):**
    *   Se ejecuta consulta directa con bloqueo de lectura:
        ```sql
        SELECT COUNT(*) AS total_inscritos 
        FROM inscripcion 
        WHERE idclaseprogramada = 7777 AND estatus != 'CANCELADA';
        ```
    *   **Condición Crítica de Aprobación:**
        `assert total_inscritos == 30`
    *   Si `total_inscritos > 30`, la prueba **FALLA AUTOMÁTICAMENTE**, demostrando la existencia de condición de carrera TOCTOU en `check_classroom_capacity` por falta de bloqueo transaccional (`SELECT ... FOR UPDATE`).
3.  **Auditoría de Integridad del Aula:**
    *   Verificar que la capacidad del aula en la tabla `aula` no se haya alterado y que no existan locks huérfanos en `information_schema.innodb_trx`.

---

## 3. Stack Tecnológico y Herramientas Propuestas

Para la fase inmediata de automatización, se adopta un stack de herramientas homogéneo, robusto y estandarizado en la industria.

```
┌────────────────────────────────────────────────────────────────────────────┐
│                    STACK DE AUTOMATIZACIÓN RECOMENDADO                     │
├──────────────────────────┬──────────────────────┬──────────────────────────┤
│ Categoría de Prueba      │ Herramienta Elegida  │ Justificación Técnica   │
├──────────────────────────┼──────────────────────┼──────────────────────────┤
│ Pruebas Unitarias / Edge │ pytest (>= 7.4.0)    │ Fixtures con yield,      │
│                          │ + pytest-mock        │ parametrización nativa,  │
│                          │                      │ aislamiento por mocks.   │
├──────────────────────────┼──────────────────────┼──────────────────────────┤
│ Concurrencia Extrema     │ Python multiprocessing│ Disparo simultáneo con   │
│ (Race Condition)         │ + requests / aiohttp │ barreras de tiempo en    │
│                          │                      │ sub-milisegundos.        │
├──────────────────────────┼──────────────────────┼──────────────────────────┤
│ Carga y Rendimiento      │ Locust (>= 2.15.0)   │ Escenarios asíncronos en │
│ Sostenido (50 VUs)       │                      │ Python puro (locustfile) │
│                          │                      │ con reportes web en vivo.│
└──────────────────────────┴──────────────────────┴──────────────────────────┘
```

### 3.1 Justificación de Elección
*   **pytest:** Es el estándar *de facto* para Python. Permite modelar los casos `TC-EDGE-01` y `TC-EDGE-02` sin levantar infraestructura externa y verificar excepciones esperadas con `pytest.raises`.
*   **Locust vs. K6:**
    *   Se selecciona **Locust** porque el equipo domina Python, lo que permite reutilizar generadores de datos (`Faker`), modelos de autenticación de Flask y utilidades del proyecto sin fricción de contexto.
    *   Para `TC-PERF-LOAD-02` (Race condition), se complementará con un script en `pytest` utilizando `concurrent.futures` / `multiprocessing.Barrier` para garantizar sincronización sub-milisegundo imposible de garantizar con runners tradicionales.

### 3.2 Estructura de Directorios Propuesta

Se propone crear la siguiente jerarquía de archivos para albergar el ciclo de pruebas:

```
Sistema-Gestion-Universitaria/
├── tests/
│   ├── __init__.py
│   ├── conftest.py                   # Fixtures globales (Conexión BD pruebas, App client)
│   ├── edge/                         # Casos Borde y Seguridad
│   │   ├── __init__.py
│   │   ├── test_tc_edge_01_sqli.py   # Implementación técnica de TC-EDGE-01
│   │   └── test_tc_edge_02_form.py   # Implementación técnica de TC-EDGE-02
│   ├── performance/                  # Carga y Concurrencia
│   │   ├── __init__.py
│   │   ├── conftest_perf.py          # Fixtures de semillas masivas y teardown
│   │   ├── locustfile.py             # Script de carga sostenida para TC-PERF-LOAD-01
│   │   └── test_tc_perf_race_condition.py # Prueba concurrente para TC-PERF-LOAD-02
│   └── fixtures/                     # Payloads sintéticos y esquemas mock
│       └── mock_schemas.py
├── pytest.ini                        # Flags de ejecución (-v, --strict-markers)
├── locust.conf                       # Parámetros de headless run para Locust
├── PLAN_DE_PRUEBAS.md                # Documento rector
└── PLAN_DE_INTEGRACION.md            # Este documento técnico de especificación
```

---

## 4. Riesgos de Ejecución y Precondiciones del Entorno

### 4.1 Aislamiento de Base de Datos y Prevención de Polución
1.  **Prohibición Estricta sobre Base de Datos de Producción/Desarrollo Activo:**
    *   Las pruebas de carga (`TC-PERF-LOAD-01` y `02`) insertan cientos de filas. Si se ejecutan sobre la base de datos de desarrollo habitual, corromperán los estados de cuenta y los cupos de las clases activas.
    *   **Solución:** Las pruebas deben ejecutarse apuntando a una base de datos aislada (`controlescolar_test_db`) o recrear los contenedores mediante `docker compose -f docker-compose.test.yml down -v && docker compose up -d`.
2.  **Garantía de Cleanup (Teardown Idempotente):**
    *   Todas las fixtures de prueba deben implementar el patrón `try ... yield ... finally` para asegurar que, aun cuando la prueba falle o aborte por excepción, los registros insertados con prefijos de prueba (`9000+`, `TEST_`) sean eliminados de las tablas `inscripcion`, `estudiante` y `claseprogramada`.

### 4.2 Advertencia Crítica de Infraestructura Local (Werkzeug vs. WSGI)
*   **Cuello de Botella Detectado en Docker:**
    *   [`docker-compose.yml`](file:///e:/Github/Sistema-Gestion-Universitaria/docker-compose.yml#L40) ejecuta la aplicación con:
        `command: flask run --host=0.0.0.0 --port=5000` con `FLASK_DEBUG: "1"`.
    *   El servidor de desarrollo de Werkzeug es **monoproceso y monohilo** por defecto.
    *   **Impacto en Pruebas de Carga:** Si `TC-PERF-LOAD-01` (50 VUs) o `TC-PERF-LOAD-02` (10 requests en 50ms) se ejecutan contra el servidor de desarrollo `flask run`, las solicitudes se encolarán de manera serial. La prueba de condición de carrera se falseará porque las peticiones no colisionarán en paralelo, y la prueba de carga fallará por timeouts artificiales del servidor web.
    *   **Precondición Obligatoria:** Para las pruebas de rendimiento y concurrencia, el contenedor debe levantarse temporalmente con un servidor WSGI de producción para Python (ej. `gunicorn -w 4 -b 0.0.0.0:5000 app:app` o `waitress`).

### 4.3 Variables de Entorno Requeridas

```bash
# Entorno de Pruebas Automatizadas
TEST_TARGET_URL=http://localhost:5002
TEST_DB_HOST=localhost
TEST_DB_PORT=3306
TEST_DB_NAME=controlescolar_db
TEST_DB_USER=root
TEST_DB_PASSWORD=mypassword
PYTHONPATH=.
```

### 4.4 Checklist Previo a la Implementación de Código
- [x] Matriz de trazabilidad validada con `PLAN_DE_PRUEBAS.md`.
- [x] Payloads de inyección y esquemas de prueba diseñados en especificación.
- [x] Curva de carga y SLOs de latencia definidos (p95 <= 1,500ms, Error rate < 0.5%).
- [x] Estrategia de barrera de concurrencia (< 50ms) documentada para detección de condición de carrera.
- [x] Aislamiento de base de datos y script de limpieza estructurado.
- [x] Precondición de servidor WSGI (Gunicorn) identificada para no falsear concurrencia.

---
*Fin del Plan Técnico de Integración. Especificación lista para proceder a la fase de automatización.*
