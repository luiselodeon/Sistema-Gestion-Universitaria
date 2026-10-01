# PLAN INTEGRAL DE PRUEBAS DE CALIDAD DE SOFTWARE
**Sistema:** Sistema de Gestión Universitaria  
**Documento:** Plan de Pruebas de Calidad, Robustez y Seguridad (QA Test Plan)  
**Versión:** 1.0.0  
**Fecha:** Septiembre 2026  
**Rol:** QA Lead & Principal Software Architect  
**Estado:** Propuesta de Diseño de Pruebas (Fase de Definición)

---

## 1. Resumen Ejecutivo y Objetivos de Calidad

### 1.1 Contexto y Alcance
El presente documento establece la estrategia y el diseño exhaustivo del plan de pruebas para el **Sistema de Gestión Universitaria**, una plataforma integral basada en Python 3.9, Flask y MySQL 8.0. La plataforma administra procesos críticos que incluyen la gestión de personas (estudiantes y docentes), control escolar (carreras, planes de estudio, asignaturas, horarios, aulas), inscripciones y evaluaciones, así como finanzas estudiantiles (estados de cuenta, cobros, pagos y becas).

El alcance de este plan cubre prioritariamente toda la lógica de negocio y operaciones de persistencia contenidas en el directorio `utils/`, así como los mecanismos de validación de datos, control de acceso y generación dinámica de esquemas:
*   Mecanismos de Validación y Esquemas: `utils/validators.py`, `utils/form_validation.py`, `utils/schema_generator.py`.
*   Seguridad y Autenticación: `utils/auth.py`, `utils/admin/usuarios_crud.py`.
*   Operación Escolar y Control Académico: `utils/estudiantes/`, `utils/cursos/`, `utils/aulas_horarios/`, `utils/asistencia/`, `utils/calificaciones/`.
*   Operación Docente: `utils/docentes/`.
*   Finanzas y Tesorería: `utils/finanzas_becas/`.
*   Inteligencia de Datos: `utils/reportes_estadísticas/`.

### 1.2 Objetivos de Calidad
1.  **Robustez y Tolerancia a Fallos:** Garantizar que los módulos rechacen de forma predecible y controlada entradas anómalas, nulos inesperados, tipos cruzados y violaciones de restricciones de integridad, evitando excepciones no controladas a nivel de aplicación (errores 500).
2.  **Integridad Transaccional y Consistencia de Datos (ACID):** Evaluar el comportamiento de las operaciones multi-tabla ante desconexiones o fallos en pasos intermedios, asegurando que no se generen registros huérfanos ni desajustes financieros.
3.  **Seguridad y Blindaje de Datos:** Validar que los mecanismos de consulta dinámica no presenten vectores de inyección SQL y que el control de acceso basado en roles (RBAC) impida la ejecución no autorizada de operaciones restringidas.
4.  **Cobertura de Ramas (Branch Coverage):** Establecer una meta mínima de cobertura del **85%** sobre las ramas lógicas de negocio, con un **100%** de cobertura en los módulos críticos de inscripción y pagos.
5.  **Validación de Reglas de Negocio Universitaria:** Certificar que se cumplan las restricciones académicas (capacidades de aulas, prerrequisitos, límites de crédito, empalmes de horarios y coherencia de calificaciones).

---

## 2. Matriz de Casos de Prueba (Lógica Existente)

A continuación se detalla la suite de casos de prueba diseñada para evaluar exhaustivamente cada función y flujo implementado en los módulos de `utils/`.

### 2.1 Módulo: Validadores Base (`utils/validators.py`)

#### `TC-VAL-01: Validación de cadenas de texto dentro del límite permitido`
*   **Archivo/Módulo a Probar:** `tests/test_utils_validators.py`
*   **Tipo de Prueba:** Unitaria
*   **Precondiciones y Datos de Entrada:**
    *   `value = "Ingeniería en Software"`
    *   `rules = {"max": 50}`
*   **Criterio de Aceptación:** Retorna tupla `(True, None)`. No levanta excepciones.
*   **Métricas de Calidad Asociadas:** Cobertura de rama condicional (longitud <= max), tiempo de ejecución < 1ms.

#### `TC-VAL-02: Rechazo de cadenas que superan la longitud máxima`
*   **Archivo/Módulo a Probar:** `tests/test_utils_validators.py`
*   **Tipo de Prueba:** Unitaria / Borde
*   **Precondiciones y Datos de Entrada:**
    *   `value = "TextoExtremadamenteLargoQueSuperaElLimite"`
    *   `rules = {"max": 10}`
*   **Criterio de Aceptación:** Retorna `(False, "El campo excede 10 caracteres.")`.
*   **Métricas de Calidad Asociadas:** Tasa de detección de desbordamiento de buffer/largo VARCHAR.

#### `TC-VAL-03: Validación de números enteros numéricos positivos`
*   **Archivo/Módulo a Probar:** `tests/test_utils_validators.py`
*   **Tipo de Prueba:** Unitaria
*   **Precondiciones y Datos de Entrada:**
    *   `value = "1042"`
    *   `rules = {}`
*   **Criterio de Aceptación:** Retorna tupla `(True, None)`.
*   **Métricas de Calidad Asociadas:** Cobertura de rama `isdigit() == True`.

#### `TC-VAL-04: Rechazo de número entero ante valor no numérico o decimal`
*   **Archivo/Módulo a Probar:** `tests/test_utils_validators.py`
*   **Tipo de Prueba:** Unitaria / Entrada Inválida
*   **Precondiciones y Datos de Entrada:**
    *   `value = "104.5"` (o `"abc"`)
    *   `rules = {}`
*   **Criterio de Aceptación:** Retorna `(False, "Debe ser un número entero.")`.
*   **Métricas de Calidad Asociadas:** Tasa de rechazo de tipos no compatibles con INT.

#### `TC-VAL-05: Validación de números de punto flotante válidos`
*   **Archivo/Módulo a Probar:** `tests/test_utils_validators.py`
*   **Tipo de Prueba:** Unitaria
*   **Precondiciones y Datos de Entrada:**
    *   `value = "9.75"` (y entero en string `"10"`)
    *   `rules = {}`
*   **Criterio de Aceptación:** Retorna `(True, None)`.
*   **Métricas de Calidad Asociadas:** Cobertura de bloque `try/except ValueError`.

#### `TC-VAL-06: Validación de fechas en formato ISO YYYY-MM-DD`
*   **Archivo/Módulo a Probar:** `tests/test_utils_validators.py`
*   **Tipo de Prueba:** Unitaria
*   **Precondiciones y Datos de Entrada:**
    *   `value = "2026-03-15"`
    *   `rules = {}`
*   **Criterio de Aceptación:** Retorna `(True, None)`.
*   **Métricas de Calidad Asociadas:** Cobertura de rama válida en `strptime`.

#### `TC-VAL-07: Rechazo de fechas en formato inválido o fuera de rango`
*   **Archivo/Módulo a Probar:** `tests/test_utils_validators.py`
*   **Tipo de Prueba:** Unitaria / Entrada Inválida
*   **Precondiciones y Datos de Entrada:**
    *   `value = "15/03/2026"` (o `"2026-02-31"`)
    *   `rules = {}`
*   **Criterio de Aceptación:** Retorna `(False, "Fecha inválida. Usa formato YYYY-MM-DD.")`.
*   **Métricas de Calidad Asociadas:** Manejo de excepciones `ValueError`.

#### `TC-VAL-08: Validación de valores restringidos por lista ENUM`
*   **Archivo/Módulo a Probar:** `tests/test_utils_validators.py`
*   **Tipo de Prueba:** Unitaria
*   **Precondiciones y Datos de Entrada:**
    *   Caso A: `value = "ACTIVO"`, `rules = {"values": ["ACTIVO", "BAJA", "EGRESADO"]}`
    *   Caso B: `value = "SUSPENDIDO"`, `rules = {"values": ["ACTIVO", "BAJA", "EGRESADO"]}`
*   **Criterio de Aceptación:**
    *   Caso A: `(True, None)`.
    *   Caso B: `(False, "Valor inválido. Debe ser uno de: ['ACTIVO', 'BAJA', 'EGRESADO']")`.
*   **Métricas de Calidad Asociadas:** Branch coverage (inclusión vs exclusión en lista).

---

### 2.2 Módulo: Generador de Esquemas y Validación Dinámica (`utils/schema_generator.py` y `utils/form_validation.py`)

#### `TC-SCH-01: Generación de esquema a partir de estructura MySQL DESCRIBE`
*   **Archivo/Módulo a Probar:** `tests/test_utils_schema_generator.py`
*   **Tipo de Prueba:** Unitaria con Mock de Cursor
*   **Precondiciones y Datos de Entrada:**
    *   `cursor.fetchall()` retorna metadata simulada de columnas:
        *   `{"Field": "nombre", "Type": "varchar(60)", "Null": "NO"}`
        *   `{"Field": "edad", "Type": "int(11)", "Null": "YES"}`
        *   `{"Field": "costo", "Type": "decimal(10,2)", "Null": "NO"}`
        *   `{"Field": "fecha", "Type": "date", "Null": "YES"}`
        *   `{"Field": "estatus", "Type": "enum('A','B')", "Null": "NO"}`
*   **Criterio de Aceptación:** Diccionario resultante mapea tipos `string` con `max: 60`, `int`, `float`, `date`, y `enum` con `values: ['A', 'B']` y banderas `required` respectivas.
*   **Métricas de Calidad Asociadas:** Cobertura de ramas condicionales para cada tipo SQL (`varchar`, `int`, `decimal`, `date`, `enum`).

#### `TC-SCH-02: Exclusión de campos autogenerados y claves foráneas en esquema`
*   **Archivo/Módulo a Probar:** `tests/test_utils_schema_generator.py`
*   **Tipo de Prueba:** Unitaria
*   **Precondiciones y Datos de Entrada:**
    *   Columnas mockeadas incluyen: `idpersona`, `created_at`, `matricula_alumno`, `idestadodecuenta`.
*   **Criterio de Aceptación:** Ninguno de estos campos debe figurar en el diccionario devuelto por `generate_schema_from_table`.
*   **Métricas de Calidad Asociadas:** Verificación de la cláusula de exclusión.

#### `TC-FRM-01: Detección de campo obligatorio ausente en formulario`
*   **Archivo/Módulo a Probar:** `tests/test_utils_form_validation.py`
*   **Tipo de Prueba:** Integración funcional (Mock de DB)
*   **Precondiciones y Datos de Entrada:**
    *   Esquema simulado: `{"nombre": {"type": "string", "max": 60, "required": True}}`
    *   `form = {"correo": "test@uni.edu"}`
*   **Criterio de Aceptación:** Retorna `(False, "El campo nombre es obligatorio.")`.
*   **Métricas de Calidad Asociadas:** Detección de omisiones de payload antes de persistencia.

#### `TC-FRM-02: Aprobación de formulario con todos los campos válidos`
*   **Archivo/Módulo a Probar:** `tests/test_utils_form_validation.py`
*   **Tipo de Prueba:** Integración funcional
*   **Precondiciones y Datos de Entrada:**
    *   Esquema simulado con campos `nombre` (string) y `capacidad` (int).
    *   `form = {"nombre": "Laboratorio 1", "capacidad": "30"}`
*   **Criterio de Aceptación:** Retorna `(True, None)`.
*   **Métricas de Calidad Asociadas:** Flujo exitoso de validación integral.

---

### 2.3 Módulo: Autenticación y Autorización (`utils/auth.py` y `utils/admin/usuarios_crud.py`)

#### `TC-AUT-01: Bloqueo de acceso en rutas protegidas sin sesión iniciada`
*   **Archivo/Módulo a Probar:** `tests/test_utils_auth.py`
*   **Tipo de Prueba:** Unitaria con contexto de aplicación Flask (`test_request_context`)
*   **Precondiciones y Datos de Entrada:**
    *   `session` vacía (sin clave `"user_id"`).
    *   Llamada a función decorada con `@login_required`.
*   **Criterio de Aceptación:** Redirección HTTP 302 hacia endpoint `login` y mensaje flash `"Debes iniciar sesión primero"` con categoría `"danger"`.
*   **Métricas de Calidad Asociadas:** Verificación de barrera de autenticación.

#### `TC-AUT-02: Acceso concedido a ruta protegida con sesión válida`
*   **Archivo/Módulo a Probar:** `tests/test_utils_auth.py`
*   **Tipo de Prueba:** Unitaria
*   **Precondiciones y Datos de Entrada:**
    *   `session = {"user_id": 5, "user_rol": "operacion_academica"}`
*   **Criterio de Aceptación:** Ejecución normal de la función decorada y retorno de su valor nativo.
*   **Métricas de Calidad Asociadas:** Tasa de falso positivo en autenticación (debe ser 0%).

#### `TC-AUT-03: Superusuario administrador elude restricciones de rol específico`
*   **Archivo/Módulo a Probar:** `tests/test_utils_auth.py`
*   **Tipo de Prueba:** Unitaria
*   **Precondiciones y Datos de Entrada:**
    *   Ruta decorada con `@role_required("finanzas_becas")`.
    *   `session = {"user_id": 1, "user_rol": "admin"}`.
*   **Criterio de Aceptación:** La función se ejecuta sin redirección. El rol `"admin"` tiene bypass total.
*   **Métricas de Calidad Asociadas:** Cobertura de rama privilegiada.

#### `TC-AUT-04: Denegación de acceso y redirección por rol insuficiente`
*   **Archivo/Módulo a Probar:** `tests/test_utils_auth.py`
*   **Tipo de Prueba:** Unitaria
*   **Precondiciones y Datos de Entrada:**
    *   Ruta decorada con `@role_required("finanzas_becas")`.
    *   `session = {"user_id": 2, "user_rol": "operacion_academica"}`.
*   **Criterio de Aceptación:** Redirección HTTP hacia `inicio` con mensaje flash `"No tienes permisos para entrar aquí"`.
*   **Métricas de Calidad Asociadas:** Cumplimiento de matriz RBAC.

#### `TC-USR-01: Alta de usuario con hashing unidireccional de contraseña`
*   **Archivo/Módulo a Probar:** `tests/test_utils_usuarios_crud.py`
*   **Tipo de Prueba:** Unitaria con Mock de Cursor
*   **Precondiciones y Datos de Entrada:**
    *   `add_usuario(cursor, "admin@uni.edu", "PasswordPlana123!", "admin")`
*   **Criterio de Aceptación:** La consulta SQL enviada a `cursor.execute` contiene un hash bcrypt/werkzeug en el segundo parámetro; la contraseña en texto plano jamás se envía a la base de datos. `cursor.lastrowid` retorna el identificador numérico.
*   **Métricas de Calidad Asociadas:** Verificación de seguridad de credenciales en tránsito y persistencia.

#### `TC-USR-02: Búsqueda parametrizada de usuarios por correo y rol`
*   **Archivo/Módulo a Probar:** `tests/test_utils_usuarios_crud.py`
*   **Tipo de Prueba:** Unitaria
*   **Precondiciones y Datos de Entrada:**
    *   `search_usuarios(cursor, "finanzas")`
*   **Criterio de Aceptación:** `cursor.execute` recibe tupla `("%finanzas%", "%finanzas%")` asegurando consulta parametrizada contra SQL Injection.
*   **Métricas de Calidad Asociadas:** Prevención de inyección SQL.

---

### 2.4 Módulo: Gestión de Estudiantes y Expediente Académico (`utils/estudiantes/`)

#### `TC-EST-01: Registro integral de nuevo estudiante (Persona + Estado de Cuenta + Estudiante)`
*   **Archivo/Módulo a Probar:** `tests/test_utils_students_crud.py`
*   **Tipo de Prueba:** Integración con Mock de DB
*   **Precondiciones y Datos de Entrada:**
    *   `cursor.fetchone` simula `MAX(idpersona) = 10`, `MAX(idestadodecuenta) = 15`.
    *   Carrera `idcarrera = 2` con costo de inscripción `3500.00` y plan de estudios existente `idplanestudio = 4`.
    *   Payload: `add_student(cursor, "Carlos", "Soto", "Ruiz", "carlos@uni.edu", 2, idbeca=None)`
*   **Criterio de Aceptación:** Se ejecutan ordenadamente:
    1.  `INSERT INTO persona` con `idpersona = 11`.
    2.  `INSERT INTO estadodecuenta` con `idestadodecuenta = 16`, `saldo_inicial = 3500.00`, `saldo_actual = 3500.00`.
    3.  `INSERT INTO estudiante` con `idpersona = 11`, `idcarrera = 2`, `idplanestudio = 4`, `idestadodecuenta = 16`.
*   **Métricas de Calidad Asociadas:** Cobertura de flujo multirregistro integral.

#### `TC-EST-02: Consulta de datos de estudiante existente por matrícula`
*   **Archivo/Módulo a Probar:** `tests/test_utils_students_crud.py`
*   **Tipo de Prueba:** Unitaria
*   **Precondiciones y Datos de Entrada:**
    *   `matricula = 1001`
*   **Criterio de Aceptación:** Retorna registro unificado con nombre, apellidos, correo, carrera, beca y estatus.
*   **Métricas de Calidad Asociadas:** Cobertura de query relacional con `JOIN`.

#### `TC-EST-03: Actualización de estatus académico y beca asignada`
*   **Archivo/Módulo a Probar:** `tests/test_utils_students_crud.py`
*   **Tipo de Prueba:** Unitaria
*   **Precondiciones y Datos de Entrada:**
    *   Modificación de matrícula `1001` a estatus `'EGRESADO'` y `idbeca = 2`.
*   **Criterio de Aceptación:** Retorna `True`; las sentencias `UPDATE persona` y `UPDATE estudiante` son ejecutadas con los parámetros correspondientes.
*   **Métricas de Calidad Asociadas:** Branch coverage de actualización exitosa vs estudiante no encontrado (`False`).

#### `TC-HIS-01: Registro de calificación y estatus final en historial académico`
*   **Archivo/Módulo a Probar:** `tests/test_utils_historialacademico_crud.py`
*   **Tipo de Prueba:** Unitaria
*   **Precondiciones y Datos de Entrada:**
    *   `add_historial(cursor, matricula_alumno=1001, idasignatura=10, idperiodo=1, calificacion_final=9.5, estatus_asignatura='APROBADA')`
*   **Criterio de Aceptación:** Registro exitoso en `historialacademico` retornando `lastrowid`.
*   **Métricas de Calidad Asociadas:** Cobertura de persistencia en historial curricular.

---

### 2.5 Módulo: Inscripciones y Reglas de Negocio Críticas (`utils/estudiantes/inscripcion_crud.py`)

#### `TC-INS-01: Validación de capacidad de aula (Cupo disponible)`
*   **Archivo/Módulo a Probar:** `tests/test_utils_inscripcion_crud.py`
*   **Tipo de Prueba:** Unitaria / Lógica de Negocio
*   **Precondiciones y Datos de Entrada:**
    *   Aula de clase programada `idclaseprogramada = 10` tiene capacidad = 30.
    *   Inscripciones actuales activas (`estatus != 'CANCELADA'`) = 20.
*   **Criterio de Aceptación:** `check_classroom_capacity(cursor, 10)` retorna `(True, None)`.
*   **Métricas de Calidad Asociadas:** Branch coverage (`current_enrollments < capacidad`).

#### `TC-INS-02: Rechazo de inscripción por sobrecupo de aula (Aula llena)`
*   **Archivo/Módulo a Probar:** `tests/test_utils_inscripcion_crud.py`
*   **Tipo de Prueba:** Unitaria / Caso Límite
*   **Precondiciones y Datos de Entrada:**
    *   Aula de `idclaseprogramada = 10` tiene capacidad = 30.
    *   Inscripciones actuales activas = 30.
*   **Criterio de Aceptación:** `check_classroom_capacity(cursor, 10)` retorna `(False, "El aula está llena (30/30)")`.
*   **Métricas de Calidad Asociadas:** Detección de límite superior de aforo.

#### `TC-INS-03: Detección y rechazo de materia duplicada en el mismo periodo`
*   **Archivo/Módulo a Probar:** `tests/test_utils_inscripcion_crud.py`
*   **Tipo de Prueba:** Unitaria / Regla de Negocio
*   **Precondiciones y Datos de Entrada:**
    *   Estudiante `matricula = 1001` ya inscrito en grupo A de "Cálculo I" en periodo 2026-1.
    *   Intenta inscribir grupo B de "Cálculo I" en periodo 2026-1 (`idclaseprogramada = 12`).
*   **Criterio de Aceptación:** `check_duplicate_subject(cursor, 1001, 12)` retorna `(False, "El alumno ya está inscrito en esta materia en este periodo.")`.
*   **Métricas de Calidad Asociadas:** Cobertura de prevención de inscripciones redundantes.

#### `TC-INS-04: Exclusión de la propia inscripción al modificar grupo`
*   **Archivo/Módulo a Probar:** `tests/test_utils_inscripcion_crud.py`
*   **Tipo de Prueba:** Unitaria
*   **Precondiciones y Datos de Entrada:**
    *   `check_duplicate_subject(cursor, 1001, 12, exclude_inscripcion_id=55)`
*   **Criterio de Aceptación:** El query añade la cláusula `AND i.idinscripcion != 55`, permitiendo al estudiante cambiar de horario o grupo sin autobloquearse.
*   **Métricas de Calidad Asociadas:** Branch coverage de actualización con exclusión de ID propio.

#### `TC-INS-05: Rechazo por prerrequisito concurrente directo (Forward Check)`
*   **Archivo/Módulo a Probar:** `tests/test_utils_inscripcion_crud.py`
*   **Tipo de Prueba:** Integración / Lógica Académica
*   **Precondiciones y Datos de Entrada:**
    *   La asignatura "Física II" tiene como prerrequisito "Física I".
    *   El alumno está inscrito actualmente en "Física I" en el periodo 2026-1.
    *   Intenta inscribir "Física II" en el mismo periodo.
*   **Criterio de Aceptación:** `check_concurrent_prerequisites(cursor, matricula, idclase)` retorna `(False, "No se puede inscribir porque depende de: Física I, que también se está cursando.")`.
*   **Métricas de Calidad Asociadas:** Detección de dependencia curricular violada.

#### `TC-INS-06: Rechazo por prerrequisito concurrente inverso (Reverse Check)`
*   **Archivo/Módulo a Probar:** `tests/test_utils_inscripcion_crud.py`
*   **Tipo de Prueba:** Integración / Lógica Académica
*   **Precondiciones y Datos de Entrada:**
    *   El alumno ya está inscrito en "Programación Avanzada" en el periodo actual.
    *   Intenta inscribir en el mismo periodo "Programación Básica" (la cual es prerrequisito de la ya inscrita).
*   **Criterio de Aceptación:** Retorna `(False, "No se puede inscribir porque es prerequisito de: Programación Avanzada, que también se está cursando.")`.
*   **Métricas de Calidad Asociadas:** Cobertura de validación bidireccional de grafos curriculares.

#### `TC-INS-07: Ejecución exitosa de inscripción consolidada`
*   **Archivo/Módulo a Probar:** `tests/test_utils_inscripcion_crud.py`
*   **Tipo de Prueba:** Integración
*   **Precondiciones y Datos de Entrada:**
    *   Capacidad validada, sin duplicados ni prerrequisitos en conflicto.
*   **Criterio de Aceptación:** Inserta registro en `inscripcion` con fecha de hoy (`date.today()`) y estatus predeterminado `'INICIADA'`. Retorna `idinscripcion`.
*   **Métricas de Calidad Asociadas:** Camino feliz (happy path) de alta de inscripción.

---

### 2.6 Módulo: Cursos, Planes y Prerrequisitos (`utils/cursos/`)

#### `TC-ASG-01: Generación automatizada de clave de asignatura a partir del departamento`
*   **Archivo/Módulo a Probar:** `tests/test_utils_asignaturas_crud.py`
*   **Tipo de Prueba:** Integración con Mock de DB
*   **Precondiciones y Datos de Entrada:**
    *   Departamento: "Sistemas Computacionales" (`iddepto = 3`).
    *   `cursor.lastrowid` devuelve `145`.
    *   `add_asignatura(cursor, "Bases de Datos", 8, 4.0, 3)`
*   **Criterio de Aceptación:**
    1.  Inserta registro inicial con clave temporal `'TEMP'`.
    2.  Extrae prefijo `'SIST'` (primeros 4 caracteres en mayúscula).
    3.  Actualiza `clave_asignatura = 'SIST145'`.
*   **Métricas de Calidad Asociadas:** Verificación de algoritmo de nombrado de claves.

#### `TC-PLN-01: Validación de fechas de vigencia en plan de estudio (Rechazo de fecha fin anterior)`
*   **Archivo/Módulo a Probar:** `tests/test_utils_planestudio_crud.py`
*   **Tipo de Prueba:** Unitaria / Validación de Dominio
*   **Precondiciones y Datos de Entrada:**
    *   `vigencia_inicio = "2026-08-01"`
    *   `vigencia_fin = "2025-08-01"` (anterior a inicio)
*   **Criterio de Aceptación:** Lanza excepción `ValueError("La fecha de fin no puede ser menor a la fecha de inicio.")`. No ejecuta inserción en DB.
*   **Métricas de Calidad Asociadas:** Detección de incoherencias cronológicas.

#### `TC-PRQ-01: Asociación y desasociación de prerrequisito entre materias`
*   **Archivo/Módulo a Probar:** `tests/test_utils_prerequisito_crud.py`
*   **Tipo de Prueba:** Unitaria
*   **Precondiciones y Datos de Entrada:**
    *   `add_prerequisito(cursor, idasignatura=5, idasignatura_prereq=2)`
    *   `delete_prerequisito(cursor, idasignatura=5, idasignatura_prereq=2)`
*   **Criterio de Aceptación:** Se emite sentencia `INSERT` con clave compuesta y posterior `DELETE` exacto por ambas claves.
*   **Métricas de Calidad Asociadas:** Cobertura de operaciones sobre tabla de unión relacional.

---

### 2.7 Módulo: Aulas y Horarios (`utils/aulas_horarios/`)

#### `TC-AUL-01: Bloqueo de reducción de capacidad de aula por alumnos ya inscritos`
*   **Archivo/Módulo a Probar:** `tests/test_utils_aula_crud.py`
*   **Tipo de Prueba:** Unitaria / Lógica de Negocio
*   **Precondiciones y Datos de Entrada:**
    *   Aula `idaula = 4` tiene actualmente 35 alumnos inscritos en la materia "Estructura de Datos".
    *   Se intenta reducir capacidad a `25`.
*   **Criterio de Aceptación:** `check_aula_capacity_reduction(cursor, 4, 25)` retorna:
    `(False, "No se puede reducir la capacidad a 25. La clase 'Estructura de Datos' (2026-1) tiene 35 estudiantes inscritos.")`.
*   **Métricas de Calidad Asociadas:** Protección de consistencia física de ocupación.

#### `TC-AUL-02: Aprobación de reducción de capacidad si no excede alumnos inscritos`
*   **Archivo/Módulo a Probar:** `tests/test_utils_aula_crud.py`
*   **Tipo de Prueba:** Unitaria
*   **Precondiciones y Datos de Entrada:**
    *   Capacidad actual = 50. Máximo de inscritos en cualquier clase en esa aula = 20.
    *   Nueva capacidad = 30.
*   **Criterio de Aceptación:** Retorna `(True, None)`.
*   **Métricas de Calidad Asociadas:** Branch coverage de reconfiguración física de aulas.

#### `TC-AUL-03: Lanzamiento de excepción en actualización si el aula no existe`
*   **Archivo/Módulo a Probar:** `tests/test_utils_aula_crud.py`
*   **Tipo de Prueba:** Unitaria / Manejo de Errores
*   **Precondiciones y Datos de Entrada:**
    *   `get_aula(cursor, 9999)` devuelve `None`.
    *   `update_aula(cursor, 9999, "Aula Inexistente", "Edificio B", 40)`
*   **Criterio de Aceptación:** Lanza `Exception("Aula no encontrada")`.
*   **Métricas de Calidad Asociadas:** Detección de mutaciones sobre registros inexistentes.

---

### 2.8 Módulo: Docentes y Clases Programadas (`utils/docentes/`)

#### `TC-DOC-01: Alta de docente con creación automática de entidad Persona`
*   **Archivo/Módulo a Probar:** `tests/test_utils_docente_crud.py`
*   **Tipo de Prueba:** Integración con Mock de DB
*   **Precondiciones y Datos de Entrada:**
    *   `add_docente(cursor, "Ana", "Martínez", "López", "ana@uni.edu", fecha_alta=None, estatus='A')`
*   **Criterio de Aceptación:**
    1.  Calcula `next_id_persona`.
    2.  Inserta en `persona`.
    3.  Inserta en `docente` asignando `fecha_alta = date.today()` por defecto.
    4.  Retorna `lastrowid`.
*   **Métricas de Calidad Asociadas:** Cobertura de defaults y creación multi-entidad.

#### `TC-DOC-02: Eliminación en cascada manual de docente y persona asociada`
*   **Archivo/Módulo a Probar:** `tests/test_utils_docente_crud.py`
*   **Tipo de Prueba:** Integración
*   **Precondiciones y Datos de Entrada:**
    *   Docente `iddocente = 12` con `idpersona = 45`.
*   **Criterio de Aceptación:** Se ejecuta `DELETE FROM docente WHERE iddocente = 12` seguido de `DELETE FROM persona WHERE idpersona = 45`. Retorna `True`.
*   **Métricas de Calidad Asociadas:** Limpieza de registros padre e hijo en ausencia de FK ON DELETE CASCADE.

#### `TC-CLS-01: Programación de clase vinculando todas sus entidades dependientes`
*   **Archivo/Módulo a Probar:** `tests/test_utils_claseprogramada_crud.py`
*   **Tipo de Prueba:** Unitaria
*   **Precondiciones y Datos de Entrada:**
    *   `add_clase(cursor, idasignatura=1, modalidad='PRESENCIAL', idhorario=2, iddocente=3, idperiodo=1, idcalendario=1, idaula=4, idioma='ESP')`
*   **Criterio de Aceptación:** Inserta exitosamente en `claseprogramada` con valores provistos e idioma por defecto `'ESP'`.
*   **Métricas de Calidad Asociadas:** Validación de integridad referencial esperada.

---

### 2.9 Módulo: Evaluaciones y Calificaciones (`utils/calificaciones/`)

#### `TC-EVL-01: Alta de actividad evaluativa asociada a clase programada`
*   **Archivo/Módulo a Probar:** `tests/test_utils_evaluacion_crud.py`
*   **Tipo de Prueba:** Unitaria
*   **Precondiciones y Datos de Entrada:**
    *   `add_evaluacion(cursor, idclase=5, tipo='EXAMEN', descripcion='Primer Parcial', fecha='2026-04-10', porcentaje=30.0)`
*   **Criterio de Aceptación:** Inserción exitosa devolviendo `idevaluacion`.
*   **Métricas de Calidad Asociadas:** Cobertura de atributos de ponderación evaluativa.

#### `TC-CAL-01: Registro y actualización de calificación por estudiante y actividad`
*   **Archivo/Módulo a Probar:** `tests/test_utils_calificacion_estudiante_crud.py`
*   **Tipo de Prueba:** Unitaria
*   **Precondiciones y Datos de Entrada:**
    *   `add_calificacion(cursor, idevaluacion=10, idinscripcion=25, calificacion=8.75, observaciones="Buen desempeño")`
    *   `update_calificacion(cursor, idevaluacion=10, idinscripcion=25, calificacion=9.50, observaciones="Revisión aprobada")`
*   **Criterio de Aceptación:** Sentencia `INSERT` y posterior `UPDATE` filtradas por clave primaria compuesta `(idevaluacion, idinscripcion)`.
*   **Métricas de Calidad Asociadas:** Integridad de clave compuesta.

---

### 2.10 Módulo: Finanzas, Estados de Cuenta y Pagos (`utils/finanzas_becas/`)

#### `TC-PAG-01: Registro de pago y deducción inmediata en saldo de estado de cuenta`
*   **Archivo/Módulo a Probar:** `tests/test_utils_pago_crud.py`
*   **Tipo de Prueba:** Integración funcional (Mock de DB)
*   **Precondiciones y Datos de Entrada:**
    *   `idestadodecuenta = 8`, `saldo_actual` inicial = `5000.00`.
    *   Pago: `importe_pago = 2000.00`, `forma_pago = 'TRANSFERENCIA'`, `tipo_movimiento = 'PAGO'`.
*   **Criterio de Aceptación:**
    1.  Inserta registro en tabla `pago` con `CURDATE()` y `CURTIME()`.
    2.  Ejecuta `UPDATE estadodecuenta SET saldo_actual = GREATEST(0, saldo_actual - 2000.00)`.
    3.  El saldo final esperado en DB es `3000.00`.
*   **Métricas de Calidad Asociadas:** Exactitud contable aritmética (Deducción correcta de saldo).

#### `TC-PAG-02: Protección de no negatividad de saldo ante sobrepago (GREATEST)`
*   **Archivo/Módulo a Probar:** `tests/test_utils_pago_crud.py`
*   **Tipo de Prueba:** Unitaria / Caso Límite
*   **Precondiciones y Datos de Entrada:**
    *   `saldo_actual` inicial = `1500.00`.
    *   `importe_pago = 2000.00` (mayor a la deuda).
*   **Criterio de Aceptación:** La cláusula `GREATEST(0, saldo_actual - 2000)` fija el nuevo `saldo_actual` en `0.00` sin arrojar excepción por violación de la restricción de base de datos `saldo_actual >= 0`.
*   **Métricas de Calidad Asociadas:** Adherencia a restricción `chk_estadodecuenta_saldos`.

#### `TC-PAG-03: Modificación de importe de pago y reajuste automático de balance`
*   **Archivo/Módulo a Probar:** `tests/test_utils_pago_crud.py`
*   **Tipo de Prueba:** Integración
*   **Precondiciones y Datos de Entrada:**
    *   Pago original = `1000.00`. Se corrige a nuevo importe = `1200.00` (incremento de $200).
    *   `saldo_actual` actual = `4000.00`.
*   **Criterio de Aceptación:** Se ejecuta `UPDATE estadodecuenta SET saldo_actual = GREATEST(0, saldo_actual + 1000.00 - 1200.00)`. Saldo final = `3800.00`.
*   **Métricas de Calidad Asociadas:** Consistencia de balance tras mutación histórica.

#### `TC-PAG-04: Eliminación de pago y reversión (abono) al saldo de cuenta`
*   **Archivo/Módulo a Probar:** `tests/test_utils_pago_crud.py`
*   **Tipo de Prueba:** Integración
*   **Precondiciones y Datos de Entrada:**
    *   Pago eliminado con importe = `800.00`. Saldo previo = `2200.00`.
*   **Criterio de Aceptación:** `DELETE FROM pago` y `UPDATE estadodecuenta SET saldo_actual = saldo_actual + 800.00`. Saldo resultante = `3000.00`.
*   **Métricas de Calidad Asociadas:** Reversión contable fidedigna.

---

### 2.11 Módulo: Asistencias (`utils/asistencia/`)

#### `TC-ASI-01: Registro de asistencia de estudiante con validación de tipo`
*   **Archivo/Módulo a Probar:** `tests/test_utils_asistencia_crud.py`
*   **Tipo de Prueba:** Unitaria
*   **Precondiciones y Datos de Entrada:**
    *   `add_asistencia(cursor, idclase=3, fecha="2026-03-20", tipo="ESTUDIANTE", matricula=1001, iddocente=None, estatus="ASISTIO", observaciones="A tiempo")`
*   **Criterio de Aceptación:** Inserta fila con `matricula_alumno` poblada y `iddocente` en `NULL`.
*   **Métricas de Calidad Asociadas:** Separación de dominios de asistencia (estudiante vs docente).

#### `TC-ASI-02: Registro de asistencia de docente con estatus justificado`
*   **Archivo/Módulo a Probar:** `tests/test_utils_asistencia_crud.py`
*   **Tipo de Prueba:** Unitaria
*   **Precondiciones y Datos de Entrada:**
    *   `add_asistencia(cursor, idclase=3, fecha="2026-03-20", tipo="DOCENTE", matricula=None, iddocente=15, estatus="JUSTIFICADO", observaciones="Comisión académica")`
*   **Criterio de Aceptación:** Inserta fila con `iddocente` poblado y `matricula_alumno` en `NULL`.
*   **Métricas de Calidad Asociadas:** Cobertura de ENUM (`JUSTIFICADO`).

---

### 2.12 Módulo: Reportes y Estadísticas (`utils/reportes_estadísticas/`)

#### `TC-REP-01: Reporte de mejores promedios generales ponderados`
*   **Archivo/Módulo a Probar:** `tests/test_utils_reportes_crud.py`
*   **Tipo de Prueba:** Integración analítica
*   **Precondiciones y Datos de Entrada:**
    *   Datos en `historialacademico` para múltiples estudiantes con diversas calificaciones.
    *   `get_top_students(cursor, limit=10)`
*   **Criterio de Aceptación:** Devuelve listado ordenado descendente por `promedio_general = ROUND(AVG(calificacion_final), 2)`. Respeta límite superior de 10 filas.
*   **Métricas de Calidad Asociadas:** Precisión de cálculo agregativo (`ROUND`, `AVG`).

#### `TC-REP-02: Reporte de saturación de horarios escolares`
*   **Archivo/Módulo a Probar:** `tests/test_utils_reportes_crud.py`
*   **Tipo de Prueba:** Integración analítica
*   **Precondiciones y Datos de Entrada:**
    *   `get_busy_schedules(cursor, limit=5)`
*   **Criterio de Aceptación:** Agrupa por horario y día de semana, contabilizando `total_clases` mediante `COUNT(cp.idclaseprogramada)` de forma descendente.
*   **Métricas de Calidad Asociadas:** Cobertura de query analítica con `GROUP BY`.

---

## 3. Casos No Considerados y Análisis de Casos Borde (Edge Cases & Failure Modes)

En esta sección se detallan las deficiencias, huecos arquitectónicos y supuestos no validados detectados durante el análisis profundo del código fuente actual, acompañados de los casos de prueba requeridos para su demostración y las recomendaciones de remediación.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MAPA DE VULNERABILIDADES Y RIESGOS                        │
├───────────────────────────────┬─────────────────────────────────────────────┤
│ 1. Inyección SQL Dinámica     │ cursor.execute(f"DESCRIBE {table_name}")    │
│ 2. Bug Lógico en Validación   │ form_validation.py retorna en 1er campo     │
│ 3. Corrupción en Desempaque   │ students_crud.py: id_p, id_e = dict         │
│ 4. Condición de Carrera       │ SELECT MAX(id) + 1 sin transaccionalidad    │
│ 5. Gaps de Reglas de Negocio  │ No valida prerrequisitos pasados aprobados   │
│ 6. Inconsistencia Contable    │ Pagos negativos y truncamiento a 0 sin saldo│
│ 7. Strings Nulos en MySQL     │ CONCAT(..., p.apellido_materno) -> NULL     │
└───────────────────────────────┴─────────────────────────────────────────────┘
```

### 3.1 Pruebas de Casos Borde Críticos y Modos de Falla

#### `TC-EDGE-01: Inyección SQL a través de nombre de tabla en generador de esquemas`
*   **Módulo:** `utils/schema_generator.py` -> `generate_schema_from_table`
*   **Descripción del Escenario:** El código concatena directamente la variable `table_name` en la sentencia SQL: `cursor.execute(f"DESCRIBE {table_name}")`.
*   **Vector de Entrada:** `table_name = "estudiante; DROP TABLE logs; --"`
*   **Comportamiento Actual (Falla):** Ejecución directa o error de sintaxis SQL; vulnerable a inyección de comandos DDL/DML si el parámetro proviniera de una fuente manipulable.
*   **Criterio de Aceptación Esperado tras Remediación:** Validación estricta mediante lista blanca (whitelist) de nombres de tablas permitidas. Si no pertenece a la lista blanca, debe lanzar `ValueError("Tabla inválida o no permitida")` sin consultar la base de datos.
*   **Riesgo:** Crítico (Integridad y Confidencialidad de la Base de Datos).

#### `TC-EDGE-02: Omisión masiva de validaciones por retorno prematuro en bucle de formulario`
*   **Módulo:** `utils/form_validation.py` -> `validate_form_from_table`
*   **Descripción del Escenario:** En las líneas 19 a 32, el bucle `for field, rules in schema.items():` tiene instrucciones `return validate_string(...)`. Como consecuencia, la función finaliza en la primera columna evaluada. Si el primer campo es válido pero los campos 2 al 10 contienen tipos erróneos o desbordamientos, el formulario se declara como válido.
*   **Vector de Entrada:**
    *   Campo 1 (`nombre`): `"Juan"` (Válido).
    *   Campo 2 (`edad`): `"no_es_un_numero"` (Inválido).
    *   Campo 3 (`correo`): `"string_de_mas_de_150_caracteres..."` (Inválido).
*   **Comportamiento Actual (Falla):** Retorna `(True, None)` permitiendo que datos corruptos avancen a la capa CRUD y colapsen en la base de datos con excepción 500.
*   **Criterio de Aceptación Esperado tras Remediación:** La función debe iterar sobre **todos** los campos del esquema, acumulando errores o deteniéndose únicamente ante el primer fallo, evaluando exhaustivamente cada clave.
*   **Riesgo:** Crítico (Integridad de Datos y Ruptura de Contrato de Validación).

#### `TC-EDGE-03: Corrupción en desempaquetado de diccionario al eliminar estudiante`
*   **Módulo:** `utils/estudiantes/students_crud.py` -> `delete_student`
*   **Descripción del Escenario:** En la línea 112: `id_persona, id_estado_cuenta = result`. Cuando `cursor(dictionary=True)` está activo, `result` es un diccionario `{"idpersona": 10, "idestadodecuenta": 15}`. En Python, desempaquetar un diccionario desempaqueta sus **claves**, no sus valores.
*   **Vector de Entrada:** Invocación a `delete_student(cursor, matricula=1001)`.
*   **Comportamiento Actual (Falla):** `id_persona` recibe el string `'idpersona'` y `id_estado_cuenta` recibe `'idestadodecuenta'`. La sentencia subsiguiente ejecuta `DELETE FROM persona WHERE idpersona = 'idpersona'`, lo cual no borra al individuo o falla con `DataTruncated / Incorrect integer value`.
*   **Criterio de Aceptación Esperado tras Remediación:** Extracción correcta por clave: `id_persona = result['idpersona']` y `id_estado_cuenta = result['idestadodecuenta']`.
*   **Riesgo:** Alto (Falla de Borrado e Inconsistencia de Registros Huérfanos).

#### `TC-EDGE-04: Condición de carrera por cálculo manual de ID en concurrencia`
*   **Módulo:** `utils/docentes/docente_crud.py` y `utils/estudiantes/students_crud.py`
*   **Descripción del Escenario:** Ambos módulos ejecutan `SELECT MAX(idpersona) FROM persona` y calculan `next_id = MAX + 1` en memoria de aplicación antes del `INSERT`.
*   **Vector de Entrada:** 10 peticiones simultáneas de registro de alumnos/docentes en hilos concurrentes.
*   **Comportamiento Actual (Falla):** Múltiples hilos leen el mismo valor máximo e intentan insertar con el mismo `idpersona`, disparando `mysql.connector.IntegrityError: Duplicate entry for key 'PRIMARY'`.
*   **Criterio de Aceptación Esperado tras Remediación:** Delegar la generación de identificadores a la propiedad `AUTO_INCREMENT` nativa de MySQL de la tabla `persona` (`cursor.lastrowid`).
*   **Riesgo:** Alto (Inestabilidad en Entornos Concurrentes).

#### `TC-EDGE-05: Omisión de prerrequisitos históricos aprobados en inscripción`
*   **Módulo:** `utils/estudiantes/inscripcion_crud.py`
*   **Descripción del Escenario:** `check_concurrent_prerequisites` únicamente verifica si el alumno está cursando el prerrequisito en el **mismo** periodo. Si el alumno jamás cursó la materia previa en periodos pasados, el sistema no lo detecta y permite la inscripción.
*   **Vector de Entrada:** Alumno de nuevo ingreso intenta inscribir "Cálculo Integral" sin tener cursada ni aprobada "Cálculo Diferencial" en `historialacademico`.
*   **Comportamiento Actual (Falla):** Permite la inscripción porque no hay materias concurrentes en el periodo activo.
*   **Criterio de Aceptación Esperado tras Remediación:** Validar en `historialacademico` que todas las asignaturas requeridas tengan registro con `estatus_asignatura = 'APROBADA'` (o calificación >= 6.0/7.0).
*   **Riesgo:** Alto (Violación de Reglamentación Académica Universitaria).

#### `TC-EDGE-06: Traslape de horarios (Schedule Clash) no detectado para estudiantes`
*   **Módulo:** `utils/estudiantes/inscripcion_crud.py`
*   **Descripción del Escenario:** No existe validación alguna que impida a un alumno inscribir dos clases programadas en el mismo día y rango horario.
*   **Vector de Entrada:** Alumno inscribe Clase A (Lunes 08:00 - 10:00) y Clase B (Lunes 08:00 - 10:00).
*   **Comportamiento Actual (Falla):** Se aceptan ambas inscripciones.
*   **Criterio de Aceptación Esperado tras Remediación:** Rechazo con mensaje: `"Conflicto de horario: La clase seleccionada se empalma con [Materia X] los días [Día] de [Hora Inicio] a [Hora Fin]"`.
*   **Riesgo:** Alto (Inviabilidad Operativa del Estudiante).

#### `TC-EDGE-07: Doble asignación horaria para el mismo docente`
*   **Módulo:** `utils/docentes/claseprogramada_crud.py`
*   **Descripción del Escenario:** `add_clase` y `update_clase` no validan si el docente asignado ya tiene una clase programada en el mismo horario en otra aula.
*   **Vector de Entrada:** Asignar al docente `iddocente = 5` a Clase 1 (Martes 10:00-12:00, Aula 1) y Clase 2 (Martes 10:00-12:00, Aula 2).
*   **Comportamiento Actual (Falla):** Permite la inserción ya que la restricción UNIQUE solo existe para `(idaula, idhorario)`.
*   **Criterio de Aceptación Esperado tras Remediación:** Validación preventiva que retorne error si el docente ya tiene clase en ese `idhorario` y periodo.
*   **Riesgo:** Alto (Imposibilidad de Impartición de Cátedra).

#### `TC-EDGE-08: Inyección de pagos negativos y alteración artificial de balance`
*   **Módulo:** `utils/finanzas_becas/pago_crud.py` -> `add_pago`
*   **Descripción del Escenario:** `add_pago` no verifica que `importe_pago > 0`. Aunque la base de datos tiene una restricción `chk_pago_importe`, a nivel de aplicación no se captura de forma amigable.
*   **Vector de Entrada:** `add_pago(cursor, idestadodecuenta=1, ..., importe_pago=-500.00)`
*   **Comportamiento Actual (Falla):** Si la base de datos no tuviera check o fallara en modo no estricto, `saldo_actual - (-500)` incrementaría la deuda del estudiante. Al estar el check activo, colapsa con excepción `IntegrityError` no controlada.
*   **Criterio de Aceptación Esperado tras Remediación:** Validación en Python: `if importe_pago <= 0: raise ValueError("El importe del pago debe ser mayor a cero.")`.
*   **Riesgo:** Medio-Alto (Vulnerabilidad Contable / Fallo 500 no controlado).

#### `TC-EDGE-09: Pérdida de excedentes financieros por truncamiento ciego a cero`
*   **Módulo:** `utils/finanzas_becas/pago_crud.py` -> `add_pago`
*   **Descripción del Escenario:** La sentencia `saldo_actual = GREATEST(0, saldo_actual - importe)` borra cualquier saldo a favor.
*   **Vector de Entrada:** Deuda de `$100.00`, pago recibido de `$500.00`.
*   **Comportamiento Actual (Falla):** El saldo queda en `$0.00`, desapareciendo `$400.00` del haber del estudiante sin quedar asentado como saldo crediticio a favor.
*   **Criterio de Aceptación Esperado tras Remediación:** Manejo explícito de saldo a favor o rechazo de pagos mayores a la deuda pendiente si no se admiten saldos crediticios.
*   **Riesgo:** Alto (Riesgo Legal y Contable).

#### `TC-EDGE-10: Ponderación evaluativa acumulada superior al 100%`
*   **Módulo:** `utils/calificaciones/evaluacion_crud.py` -> `add_evaluacion`
*   **Descripción del Escenario:** No existe verificación de suma agregada de porcentajes para una misma clase.
*   **Vector de Entrada:** 4 evaluaciones de 30% cada una para la misma `idclaseprogramada` (Suma = 120%).
*   **Comportamiento Actual (Falla):** Inserción exitosa de las 4 evaluaciones.
*   **Criterio de Aceptación Esperado tras Remediación:** Verificar que `SUM(porcentaje) + nuevo_porcentaje <= 100.00`.
*   **Riesgo:** Medio (Inconsistencia en Cálculo de Calificaciones Finales).

#### `TC-EDGE-11: Calificaciones numéricas fuera del rango permitido (0 a 10)`
*   **Módulo:** `utils/calificaciones/calificacion_estudiante_crud.py`
*   **Descripción del Escenario:** La función `add_calificacion` no valida el rango numérico antes del INSERT.
*   **Vector de Entrada:** `calificacion = 15.00` o `calificacion = -2.00`.
*   **Comportamiento Actual (Falla):** Error no controlado de integridad de base de datos (`chk_calificacion_rango`).
*   **Criterio de Aceptación Esperado tras Remediación:** Validación en capa de negocio que retorne `(False, "La calificación debe estar entre 0.0 y 10.0")`.
*   **Riesgo:** Medio (Fallo no controlado).

#### `TC-EDGE-12: Prerrequisitos autorreferenciales y ciclos infinitos en planes de estudio`
*   **Módulo:** `utils/cursos/prerequisito_crud.py`
*   **Descripción del Escenario:** `add_prerequisito` no valida si `idasignatura == idasignatura_prereq`, ni verifica ciclos (A requiere B, B requiere A).
*   **Vector de Entrada:** Asignatura 4 como prerrequisito de la misma Asignatura 4.
*   **Comportamiento Actual (Falla):** Se inserta la relación autorreferencial, haciendo imposible que ningún alumno pueda inscribir jamás la materia.
*   **Criterio de Aceptación Esperado tras Remediación:** Rechazo inmediato si ambas claves coinciden y detección de ciclos en el grafo de prerrequisitos.
*   **Riesgo:** Medio-Alto (Bloqueo permanente de avance curricular).

#### `TC-EDGE-13: Creación de horarios con hora de inicio posterior o igual a la hora de fin`
*   **Módulo:** `utils/aulas_horarios/horario_crud.py` -> `add_horario`
*   **Descripción del Escenario:** No se valida en Python que `hora_fin > hora_inicio`.
*   **Vector de Entrada:** `hora_inicio = "18:00:00"`, `hora_fin = "14:00:00"`.
*   **Comportamiento Actual (Falla):** Excepción no controlada por el CHECK `chk_horario_horas` de MySQL.
*   **Criterio de Aceptación Esperado tras Remediación:** Validación preventiva de tiempo en capa Python.
*   **Riesgo:** Medio.

#### `TC-EDGE-14: Pérdida total de nombres por concatenación con NULL en MySQL`
*   **Módulo:** `utils/docentes/docente_capacitacion_crud.py`
*   **Descripción del Escenario:** Línea 9 y 29: `CONCAT(p.nombre, ' ', p.apellido_paterno, ' ', p.apellido_materno) AS nombre_docente`. En SQL estándar, cualquier concatenación con `NULL` resulta en `NULL`.
*   **Vector de Entrada:** Docente sin apellido materno registrado (`apellido_materno IS NULL`).
*   **Comportamiento Actual (Falla):** La consulta devuelve `nombre_docente = NULL`, ocultando el nombre del profesor en la interfaz.
*   **Criterio de Aceptación Esperado tras Remediación:** Uso estandarizado de `IFNULL(p.apellido_materno, '')`.
*   **Riesgo:** Medio (Falla de Presentación y UI).

#### `TC-EDGE-15: Falla parcial en operaciones multi-tabla sin manejo transaccional`
*   **Módulo:** `utils/estudiantes/students_crud.py` (`add_student`)
*   **Descripción del Escenario:** Se ejecutan inserciones en `persona`, `estadodecuenta` y `estudiante`. Si el paso 3 falla (ej. error de foreign key o violación de regla), los registros en `persona` y `estadodecuenta` ya fueron emitidos y no se hace `ROLLBACK`.
*   **Vector de Entrada:** Simulación de fallo en `INSERT INTO estudiante`.
*   **Comportamiento Actual (Falla):** Persistencia de registros huérfanos sin estudiante asociado.
*   **Criterio de Aceptación Esperado tras Remediación:** Encapsulamiento en bloque transaccional explícito `try ... conn.commit() except ... conn.rollback()`.
*   **Riesgo:** Alto (Corrupción Silenciosa de Integridad Referencial).

#### `TC-EDGE-16: Excepciones por tipos no primitivos o nulos en validadores base`
*   **Módulo:** `utils/validators.py`
*   **Descripción del Escenario:**
    *   `validate_int(123, ...)` -> Falla con `AttributeError: 'int' object has no attribute 'isdigit'`.
    *   `validate_string(None, ...)` -> Falla con `TypeError: object of type 'NoneType' has no len()`.
    *   `validate_float(None, ...)` -> Falla con `TypeError: float() argument must be a string or a real number, not 'NoneType'`.
*   **Vector de Entrada:** Invocación con valores `None` o tipos numéricos nativos en lugar de strings.
*   **Comportamiento Actual (Falla):** Colapso de la función con excepciones de tipo de Python en lugar de retornar `(False, "...")`.
*   **Criterio de Aceptación Esperado tras Remediación:** Sanitización previa: verificar si el valor es nulo o realizar cast seguro antes de invocar métodos de cadena.
*   **Riesgo:** Medio-Alto (Fragilidad de Validadores).

---

### 3.2 Tabla Resumen de Riesgos y Recomendaciones de Remediación

| ID Riesgo | Severidad | Módulo(s) Afectado(s) | Descripción Breve | Acción de Remediación Previa a Pruebas |
|---|---|---|---|---|
| **RSK-01** | Crítica | `utils/form_validation.py` | Bucle de validación retorna en primer campo | Eliminar el `return` prematuro; acumular validaciones o retornar sólo en fallo. |
| **RSK-02** | Crítica | `utils/schema_generator.py` | Concatenación f-string en `DESCRIBE` | Validar `table_name` contra una lista blanca fija de tablas del sistema. |
| **RSK-03** | Alta | `utils/estudiantes/students_crud.py` | Desempaque de dict `a, b = result` | Indexar por clave de diccionario (`result['idpersona']`). |
| **RSK-04** | Alta | `docente_crud.py`, `students_crud.py` | `SELECT MAX(idpersona) + 1` en concurrencia | Usar `AUTO_INCREMENT` nativo en tabla `persona` y obtener `cursor.lastrowid`. |
| **RSK-05** | Alta | `utils/estudiantes/inscripcion_crud.py` | Prerrequisitos históricos no validados | Agregar consulta a `historialacademico` para verificar materias aprobadas previas. |
| **RSK-06** | Alta | `utils/estudiantes/inscripcion_crud.py` | Empalmes de horario para estudiantes | Cruzar días y horas de clases ya inscritas en el periodo activo. |
| **RSK-07** | Alta | `utils/docentes/claseprogramada_crud.py` | Empalmes de horario para docentes | Validar que el docente no tenga otra clase asignada en el mismo horario. |
| **RSK-08** | Alta | Todos los CRUDs multi-tabla | Ausencia de transacciones atómicas | Implementar bloques `conn.start_transaction()`, `conn.commit()` y `conn.rollback()`. |
| **RSK-09** | Media | `utils/finanzas_becas/pago_crud.py` | Pagos negativos y truncamiento | Validar `importe_pago > 0` y rechazar pagos que superen el saldo actual. |
| **RSK-10** | Media | `utils/calificaciones/evaluacion_crud.py` | Suma de ponderaciones > 100% | Validar que el acumulado de porcentajes de la clase no exceda 100.0%. |
| **RSK-11** | Media | `utils/cursos/prerequisito_crud.py` | Prerrequisitos autorreferenciales/cíclicos | Validar que `origen != destino` y verificar que el destino no tenga al origen como prerrequisito. |
| **RSK-12** | Media | `utils/validators.py` | Fallos de tipo `AttributeError`/`TypeError` | Validar tipos y nulos antes de invocar `.isdigit()`, `.strip()` o `len()`. |---

## 4. Matriz de Casos de Prueba de Frontend, UI/UX y Rendimiento

Para garantizar la calidad end-to-end de la plataforma, se diseñan las siguientes pruebas cubriendo la interacción del usuario en la capa de presentación (`templates/`), el desempeño de renderizado del lado del cliente y la estabilidad del servidor ante picos de demanda y concurrencia.

### 4.1 Pruebas UI e Interacción de Usuario (`templates/`)

#### `TC-UI-01: Validación visual de formulario de estudiantes y retención de estado`
*   **Archivo/Ruta a Probar:** `templates/estudiantes/student_form.html` (`/gestion_estudiantes/registro_consulta/add`)
*   **Tipo de Prueba:** UI / Validación Funcional
*   **Precondiciones y Datos de Entrada:**
    *   Usuario autenticado con rol `admin` o `operacion_academica`.
    *   Navegación al formulario de alta de estudiante.
    *   Envío con campo `correo` malformado (ej. `"usuario@dominio_invalido"`) o campo `nombre` en blanco.
*   **Criterio de Aceptación:**
    1.  El navegador o backend rechaza el envío mostrando el mensaje flash o validación nativa.
    2.  Los campos válidos ya capturados no deben borrarse (preservación de estado de formulario en inputs).
    3.  El botón de envío no debe permitir doble clic accidental (prevención de envíos múltiples concurrentes).
*   **Métricas de Calidad Asociadas:** Tasa de retención de datos en formulario, tiempo de retroalimentación de error < 500ms.

#### `TC-UI-02: Renderizado condicional dinámico de tipo de asistente en asistencia`
*   **Archivo/Ruta a Probar:** `templates/asistencia/asistencia_form.html` (`/asistencia/add`)
*   **Tipo de Prueba:** UI / Lógica de Interfaz (DOM dinámico)
*   **Precondiciones y Datos de Entrada:**
    *   Usuario accede al formulario de asistencia.
    *   Cambio interactivo del selector `#tipo`:
        *   Selección `"ESTUDIANTE"`: `#estudiante_div` cambia a visible (`display: block`) y `#docente_div` a oculto (`display: none`).
        *   Selección `"DOCENTE"`: `#docente_div` visible y `#estudiante_div` oculto.
*   **Criterio de Aceptación:** La visibilidad conmuta instantáneamente sin parpadeos visuales ni desconfiguración de layouts; el select oculto debe deshabilitarse para evitar el envío de datos fantasmas en el payload POST.
*   **Métricas de Calidad Asociadas:** Consistencia de visualización en DOM, ausencia de errores en consola de JavaScript.

#### `TC-UI-03: Bloqueo de selección y resistencia a manipulación de clases llenas (Select2)`
*   **Archivo/Ruta a Probar:** `templates/estudiantes/inscripcion_form.html` (`/estudiantes/inscripciones/add`)
*   **Tipo de Prueba:** UI / Seguridad del Cliente
*   **Precondiciones y Datos de Entrada:**
    *   Existe una clase programada con cupo lleno (`inscritos >= capacidad`).
    *   El usuario interactúa con el selector `#idclaseprogramada` mejorado con Select2.
    *   Intento de manipulación: Remoción del atributo `disabled` vía DevTools del navegador e intento de envío del formulario.
*   **Criterio de Aceptación:**
    1.  La opción en Select2 se renderiza visiblemente deshabilitada con el texto `[LLENO]`.
    2.  Si se remueve `disabled` en el cliente y se fuerza el POST, el backend rechaza la petición con flash alert `"El aula está llena..."`.
*   **Métricas de Calidad Asociadas:** Detección de evasión de controles de cliente (Bypass prevention).

#### `TC-UI-04: Renderizado accesible y descarte de mensajes flash de notificación`
*   **Archivo/Ruta a Probar:** `templates/base.html` (Contenedor de Alertas Flash)
*   **Tipo de Prueba:** UI / Accesibilidad (A11y) y Notificaciones
*   **Precondiciones y Datos de Entrada:**
    *   Disparo de mensajes flash en categorías `success`, `danger`, `warning`.
*   **Criterio de Aceptación:**
    1.  Las alertas se renderizan con los estilos Bootstrap correspondientes (`alert-success`, `alert-danger`, etc.).
    2.  El botón de cierre (`btn-close`) descarta la alerta suavemente (`fade show`).
    3.  El contenedor cuenta con atributo accesible `role="alert"` para lectores de pantalla.
*   **Métricas de Calidad Asociadas:** Cumplimiento de contraste WCAG AA, animación de descarte < 200ms.

#### `TC-UI-05: Filtrado reactivo de opciones de navegación según rol RBAC en Navbar`
*   **Archivo/Ruta a Probar:** `templates/base.html` (`Navbar`)
*   **Tipo de Prueba:** UI / Control de Acceso Visual
*   **Precondiciones y Datos de Entrada:**
    *   Sesión A: Rol `operacion_academica`.
    *   Sesión B: Rol `finanzas_becas`.
    *   Sesión C: Rol `admin`.
*   **Criterio de Aceptación:**
    *   Sesión A: Solo visualiza menús "Estudiantes", "Docentes", "Cursos y Planes", "Calificaciones", "Asistencia", "Aulas y Horarios". No ve "Finanzas y Becas" ni "Más" (Usuarios/Reportes).
    *   Sesión B: Solo visualiza "Finanzas y Becas".
    *   Sesión C: Visualiza todos los menús incluyendo "Más" (Usuarios y Reportes).
*   **Métricas de Calidad Asociadas:** 0% de filtración visual de rutas no autorizadas en el árbol de navegación.

#### `TC-UI-06: Retroalimentación y flujo de error en pantalla de autenticación`
*   **Archivo/Ruta a Probar:** `templates/login.html` (`/login`)
*   **Tipo de Prueba:** UI / Flujo de Usuario
*   **Precondiciones y Datos de Entrada:**
    *   Intento de login con credenciales erróneas (`correo="invalido@uni.edu"`, `password="incorrecta"`).
*   **Criterio de Aceptación:**
    1.  Se renderiza alerta visual de error clara sin filtrar si el fallo fue por usuario inexistente o contraseña incorrecta (prevención de enumeración de usuarios).
    2.  El campo `email` conserva el valor introducido; el campo `password` se limpia por seguridad.
    3.  El foco del cursor se posiciona automáticamente en el campo de contraseña.
*   **Métricas de Calidad Asociadas:** Tiempo de respuesta visual < 1s, seguridad anti-enumeración.

#### `TC-UI-07: Validación visual de fortaleza de contraseña en registro de usuarios`
*   **Archivo/Ruta a Probar:** `templates/register.html` (`/register`)
*   **Tipo de Prueba:** UI / Robustez de Entrada
*   **Precondiciones y Datos de Entrada:**
    *   Captura de contraseña débil (ej. `"123"` o `"admin"`).
*   **Criterio de Aceptación:** Indicador visual de fortaleza de contraseña advierte al usuario; el botón de creación permanece deshabilitado hasta cumplir criterios mínimos (mínimo 8 caracteres, alfanumérico).
*   **Métricas de Calidad Asociadas:** Prevención de registro de credenciales vulnerables en frontend.

#### `TC-UI-08: Responsividad de tablas y adaptación visual en dispositivos móviles`
*   **Archivo/Ruta a Probar:** `templates/estudiantes/registro_consulta.html` e `inscripcion_list.html`
*   **Tipo de Prueba:** UI / Responsividad y Cross-device
*   **Precondiciones y Datos de Entrada:**
    *   Simulación de viewport móvil (375x667 px y 768x1024 px).
*   **Criterio de Aceptación:**
    1.  Las tablas cuentan con envoltorio responsive (`table-responsive`) que habilita scroll horizontal sin romper el viewport general de la pantalla ni provocar desbordamiento del navbar.
    2.  Los botones de acción ("Editar", "Eliminar") mantienen separación mínima táctil de 44x44 px.
*   **Métricas de Calidad Asociadas:** 0 errores de desbordamiento horizontal en Google Lighthouse Mobile.

---

### 4.2 Pruebas de Rendimiento Web (Client-Side & Core Web Vitals)

#### `TC-PERF-WEB-01: Largest Contentful Paint (LCP) en Directorio de Estudiantes`
*   **Ruta a Probar:** `/gestion_estudiantes/registro_consulta` (`templates/estudiantes/registro_consulta.html`)
*   **Tipo de Prueba:** Client-side Performance / Core Web Vitals
*   **Precondiciones y Datos de Entrada:**
    *   Base de datos poblada con 100 estudiantes representativos (seeding estándar).
    *   Condiciones de red simuladas: Fast 4G / Desktop Cable.
*   **Criterio de Aceptación:**
    *   **LCP <= 2.0 segundos** (Umbral Bueno de Google: <= 2.5s).
    *   El elemento más grande (la tabla de estudiantes o encabezado principal) debe renderizarse completamente en el viewport inicial antes del umbral.
*   **Métricas de Calidad Asociadas:** LCP (ms), First Contentful Paint (FCP <= 1.0s), Speed Index <= 2.0s.

#### `TC-PERF-WEB-02: Interaction to Next Paint (INP) con inicialización de Select2 en formularios masivos`
*   **Ruta a Probar:** `/estudiantes/inscripciones/add` (`templates/estudiantes/inscripcion_form.html`)
*   **Tipo de Prueba:** Client-side Performance / Responsividad de Entrada
*   **Precondiciones y Datos de Entrada:**
    *   500 estudiantes y 150 clases programadas cargadas en los elementos `<select>`.
    *   El usuario hace clic y escribe en el input de búsqueda de Select2.
*   **Criterio de Aceptación:**
    *   **INP <= 150 ms** (Umbral Bueno: <= 200ms).
    *   La apertura del menú desplegable y el filtrado por caracteres no debe congelar el hilo principal de JavaScript ni producir jank perceptible (> 16ms por frame).
*   **Métricas de Calidad Asociadas:** INP (ms), Total Blocking Time (TBT <= 200ms).

#### `TC-PERF-WEB-03: Cumulative Layout Shift (CLS) por inyección tardía de CSS y Select2`
*   **Ruta a Probar:** `/estudiantes/inscripciones/add`
*   **Tipo de Prueba:** Client-side Performance / Estabilidad Visual
*   **Precondiciones y Datos de Entrada:**
    *   Carga de página con enlace `<link>` de Select2 CSS ubicado en el cuerpo (`<body>`) del template.
*   **Criterio de Aceptación:**
    *   **CLS <= 0.05** (Umbral Bueno: <= 0.1).
    *   El paso de select nativo a select estilizado por Select2 no debe provocar brincos de maquetación en los botones inferiores ("Guardar" / "Cancelar").
*   **Métricas de Calidad Asociadas:** Puntuación CLS (adimensional).

#### `TC-PERF-WEB-04: Sobrecarga del árbol DOM y tiempo de parseo HTML en listados sin paginación`
*   **Ruta a Probar:** `/gestion_estudiantes/registro_consulta`
*   **Tipo de Prueba:** DOM Bloat / Client Memory Footprint
*   **Precondiciones y Datos de Entrada:**
    *   Base de datos con 1,000 registros de estudiantes sin paginación activa.
*   **Criterio de Aceptación:**
    1.  El peso del HTML transferido no debe superar los **800 KB**.
    2.  La cantidad total de nodos en el DOM no debe superar los **2,000 nodos** (recomendación de Lighthouse: < 1,400 nodos).
    3.  Consumo de memoria de la pestaña del navegador no debe exceder los **80 MB**.
*   **Métricas de Calidad Asociadas:** Total DOM Nodes, HTML Transfer Size (KB), Heap Memory Usage (MB).

#### `TC-PERF-WEB-05: Auditoría de peso de assets, bloqueo de renderizado y caché HTTP`
*   **Ruta a Probar:** Todas las vistas maestras (`templates/base.html`)
*   **Tipo de Prueba:** Optimización de Recursos de Red
*   **Precondiciones y Datos de Entrada:**
    *   Inspección de peticiones de red para Bootstrap CSS/JS, Inter Font, `styles.css`.
*   **Criterio de Aceptación:**
    1.  Cero scripts bloqueantes de renderizado sin atributos `defer` o `async`.
    2.  Uso de encabezados de caché `Cache-Control` en assets estáticos locales (`static/css/styles.css`).
    3.  Inclusión de atributos `crossorigin` y `integrity` (SRI) en recursos CDN para prevenir manipulación externa.
*   **Métricas de Calidad Asociadas:** Total Page Weight < 1.5 MB en carga inicial sin caché; < 100 KB en visitas repetidas con caché activa.

---

### 4.3 Pruebas de Rendimiento del Sistema, Carga y Concurrencia (Load & Stress)

#### `TC-PERF-LOAD-01: Prueba de carga concurrente en pico de inscripciones (Simulación de 50 VUs)`
*   **Módulo/Ruta a Probar:** POST `/estudiantes/inscripciones/add` y GET `/estudiantes/inscripciones`
*   **Tipo de Prueba:** Carga Concurrente (Load Testing)
*   **Precondiciones y Perfil de Carga:**
    *   Rampa de subida (Ramp-up): 10 VUs a 50 VUs en 2 minutos.
    *   Sostenimiento: 50 Usuarios Virtuales (VUs) concurrentes realizando el flujo de inscripción durante 5 minutos.
    *   Rampa de bajada: 1 minuto.
*   **Criterio de Aceptación:**
    1.  **Latencia HTTP p95 <= 1,500 ms**; p50 <= 400 ms.
    2.  **Tasa de Errores HTTP (5xx) < 0.5%**.
    3.  Rendimiento sostenido de al menos **25 solicitudes por segundo (RPS)** sin degradación progresiva.
*   **Métricas de Calidad Asociadas:** Latencia p90/p95/p99 (ms), Throughput (RPS), Error Rate (%), CPU y Memoria del Contenedor Web.

#### `TC-PERF-LOAD-02: Concurrencia extrema y detección de Race Condition en último cupo de aula`
*   **Módulo/Ruta a Probar:** POST `/estudiantes/inscripciones/add`
*   **Tipo de Prueba:** Concurrencia Transaccional / Race Condition Testing
*   **Precondiciones y Perfil de Carga:**
    *   Una clase programada con capacidad para 30 alumnos tiene exactamente 29 alumnos inscritos (queda **1 solo cupo**).
    *   10 usuarios virtuales envían una solicitud de inscripción simultánea para esa misma clase en una ventana de **50 milisegundos**.
*   **Criterio de Aceptación:**
    1.  Exactamente **1 solicitud** es aceptada con éxito (HTTP 200/302).
    2.  Exactamente **9 solicitudes** son rechazadas de manera limpia y controlada informando aula llena.
    3.  La base de datos debe contener exactamente **30 inscritos** (0 sobrecupos en `inscripcion`).
*   **Métricas de Calidad Asociadas:** Consistencia transaccional de aforo (Sobrecupos permitidos = 0).

#### `TC-PERF-LOAD-03: Prueba de estrés y saturación de conexiones MySQL sin pool`
*   **Módulo/Ruta a Probar:** `utils/db.py` (`get_db_connection()`) bajo carga incremental
*   **Tipo de Prueba:** Prueba de Estrés (Stress & Breakpoint Testing)
*   **Precondiciones y Perfil de Carga:**
    *   Incrementar VUs de 10 en 10 hasta alcanzar 150 VUs o el punto de quiebre.
    *   Monitoreo del parámetro `Threads_connected` y `Max_used_connections` en MySQL.
*   **Criterio de Aceptación:**
    1.  Identificar con precisión el umbral máximo de concurrencia que soporta la arquitectura actual antes de arrojar `mysql.connector.Error: 1040 (08004): Too many connections`.
    2.  El sistema debe registrar la falla en logs sin corromper transacciones en vuelo ni colapsar el contenedor de MySQL.
*   **Métricas de Calidad Asociadas:** Punto de saturación de conexiones (VUs máximas estables), tiempo de recuperación tras caída (MTTR < 10s).

#### `TC-PERF-LOAD-04: Prueba de carga en búsquedas intensivas con LIKE %query% masivo`
*   **Módulo/Ruta a Probar:** GET `/gestion_estudiantes/registro_consulta/search?query=garcia`
*   **Tipo de Prueba:** Carga en Capa de Persistencia y Base de Datos
*   **Precondiciones y Perfil de Carga:**
    *   Base de datos con 5,000 registros en `persona` y `estudiante`.
    *   30 VUs ejecutando búsquedas continuas con términos comunes (`query=a`, `query=mar`).
*   **Criterio de Aceptación:**
    1.  La latencia p95 no debe superar los **2,000 ms**.
    2.  El uso de CPU del contenedor de MySQL no debe mantenerse al 100% por más de 15 segundos consecutivos.
    3.  Ninguna consulta debe ser terminada por deadlock o timeout de conexión.
*   **Métricas de Calidad Asociadas:** Tiempo de ejecución de consulta en base de datos (Query Execution Time), CPU Utilization (%).

#### `TC-PERF-LOAD-05: Prueba de resistencia prolongada (Endurance / Soak Testing)`
*   **Módulo/Ruta a Probar:** Flujos mixtos (Lecturas de listas, búsquedas, altas de asistencia)
*   **Tipo de Prueba:** Resistencia y Detección de Fugas de Memoria (Soak Testing)
*   **Precondiciones y Perfil de Carga:**
    *   Carga moderada constante de 15 VUs a una tasa de 10 peticiones/segundo durante **2 horas continuas**.
*   **Criterio de Aceptación:**
    1.  El consumo de memoria del proceso Python (`proyecto_bases_web`) debe mantenerse estable (variación < 10% tras los primeros 15 minutos de rampa).
    2.  Cero fugas de descriptores de sockets o conexiones de base de datos abiertas sin cerrar en bloques `finally`.
*   **Métricas de Calidad Asociadas:** Consumo de memoria RAM (RSS MB), Conexiones activas residuales en MySQL tras finalizar la prueba (debe retornar al baseline inicial).

---

## 5. Matriz de Priorización Global (MoSCoW / Niveles P0 a P3)

Para optimizar el esfuerzo de aseguramiento de calidad y mitigar los riesgos de mayor impacto en la operación universitaria, se establece la siguiente matriz de priorización integral para la totalidad de los casos de prueba del sistema.

### 5.1 Definición de Niveles de Prioridad

*   **P0 / Crítica (Must-Have):** Funcionalidades de integridad absoluta, transacciones financieras, seguridad contra inyecciones y consistencia de datos sin las cuales el sistema colapsa o genera pérdidas irreversibles.
*   **P1 / Alta (Should-Have):** Flujos operativos primarios (inscripción, control de cupos, asignación docente, autenticación RBAC) y pruebas de carga concurrentes bajo condiciones de pico.
*   **P2 / Media (Could-Have):** Validaciones secundarias de interfaz, métricas de Core Web Vitals en clientes de escritorio, filtros y reportes estadísticos.
*   **P3 / Baja (Nice-to-Have):** Optimizaciones estéticas, íconos de interfaz, escenarios atípicos o casos límite de bajísima frecuencia de ocurrencia.

### 5.2 Tabla Consolidada de Priorización

| ID Caso de Prueba | Módulo / Componente | Capa / Tipo de Prueba | Prioridad (MoSCoW) | Justificación de Negocio / Riesgo Técnico |
|---|---|---|---|---|
| **TC-EDGE-01** | `utils/schema_generator.py` | Seguridad / Inyección SQL | **P0 (Must-Have)** | Riesgo de compromiso total de la base de datos por interpolación dinámica en DDL. |
| **TC-EDGE-02** | `utils/form_validation.py` | Arquitectura / Validación | **P0 (Must-Have)** | El retorno prematuro invalida toda la suite de validación, permitiendo datos corruptos. |
| **TC-EDGE-03** | `utils/estudiantes/students_crud.py` | Persistencia / Integridad | **P0 (Must-Have)** | Desempaquetado erróneo de dict impide la eliminación de alumnos o corrompe datos. |
| **TC-EDGE-04** | `docente_crud.py`, `students_crud.py` | Concurrencia / ACID | **P0 (Must-Have)** | `MAX(id) + 1` colapsa con Duplicate Entry ante registros concurrentes. |
| **TC-EDGE-08** | `utils/finanzas_becas/pago_crud.py` | Finanzas / Contabilidad | **P0 (Must-Have)** | Pagos negativos pueden alterar artificialmente deudas e incurrir en fraude o error contable. |
| **TC-EDGE-09** | `utils/finanzas_becas/pago_crud.py` | Finanzas / Contabilidad | **P0 (Must-Have)** | Truncamiento ciego a cero descarta dinero real del estudiante (riesgo legal). |
| **TC-EDGE-15** | `utils/estudiantes/students_crud.py` | Persistencia / ACID | **P0 (Must-Have)** | Inserciones multi-tabla sin transacción generan registros huérfanos irreparables. |
| **TC-PAG-01** | `utils/finanzas_becas/pago_crud.py` | Finanzas / Integración | **P0 (Must-Have)** | Descuento exacto de saldo tras registro de pago es el core financiero de la institución. |
| **TC-PAG-03** | `utils/finanzas_becas/pago_crud.py` | Finanzas / Integración | **P0 (Must-Have)** | Reajuste aritmético de saldo ante mutación de pagos garantiza la cuadratura de caja. |
| **TC-PERF-LOAD-02** | `utils/estudiantes/inscripcion_crud.py` | Concurrencia / Carga | **P0 (Must-Have)** | Un sobrecupo en inscripciones concurrentes supera la capacidad física legal de las aulas. |
| **TC-AUT-01** | `utils/auth.py` | Seguridad / Autenticación | **P0 (Must-Have)** | Bloqueo estricto de rutas a usuarios no autenticados evita accesos no autorizados. |
| **TC-AUT-03** | `utils/auth.py` | Seguridad / Autorización | **P0 (Must-Have)** | Bypass seguro de superusuario admin garantiza operatividad y gobierno del sistema. |
| **TC-AUT-04** | `utils/auth.py` | Seguridad / RBAC | **P0 (Must-Have)** | Impedir que un rol acceda a módulos de otro (ej. académico entrando a finanzas). |
| **TC-USR-01** | `utils/admin/usuarios_crud.py` | Seguridad / Criptografía | **P0 (Must-Have)** | Almacenamiento obligatorio de contraseñas con hash seguro (cumplimiento normativo). |
| **TC-INS-01** | `utils/estudiantes/inscripcion_crud.py` | Regla de Negocio | **P1 (Should-Have)** | Validación de aforo disponible previo a inscripción evita saturación escolar. |
| **TC-INS-02** | `utils/estudiantes/inscripcion_crud.py` | Regla de Negocio / Borde | **P1 (Should-Have)** | Rechazo inequívoco de inscripción ante aula en capacidad máxima (30/30). |
| **TC-INS-03** | `utils/estudiantes/inscripcion_crud.py` | Regla de Negocio | **P1 (Should-Have)** | Evita que un estudiante duplique materias en el mismo periodo lectivo. |
| **TC-INS-05** | `utils/estudiantes/inscripcion_crud.py` | Lógica Académica | **P1 (Should-Have)** | Rechazo de prerrequisitos concurrentes hacia adelante asegura secuencia curricular. |
| **TC-INS-06** | `utils/estudiantes/inscripcion_crud.py` | Lógica Académica | **P1 (Should-Have)** | Rechazo de prerrequisitos inversos evita enrolamiento en materias predecesoras simultáneas. |
| **TC-EDGE-05** | `utils/estudiantes/inscripcion_crud.py` | Lógica Académica | **P1 (Should-Have)** | Validar materias previas aprobadas en historial es indispensable para el avance escolar. |
| **TC-EDGE-06** | `utils/estudiantes/inscripcion_crud.py` | Lógica de Horarios | **P1 (Should-Have)** | Empalmes de horario impiden al estudiante asistir físicamente a sus clases. |
| **TC-EDGE-07** | `utils/docentes/claseprogramada_crud.py` | Lógica de Horarios | **P1 (Should-Have)** | Evita que un profesor sea asignado a dos materias en diferentes aulas al mismo tiempo. |
| **TC-AUL-01** | `utils/aulas_horarios/aula_crud.py` | Regla de Negocio | **P1 (Should-Have)** | Impide reducir capacidad de aulas si hay más alumnos ya inscritos que el nuevo cupo. |
| **TC-EST-01** | `utils/estudiantes/students_crud.py` | Operación Core | **P1 (Should-Have)** | Alta integral de alumno (persona + saldo de inscripción + matrícula). |
| **TC-DOC-01** | `utils/docentes/docente_crud.py` | Operación Core | **P1 (Should-Have)** | Alta integral de docente y generación de expediente personal. |
| **TC-DOC-02** | `utils/docentes/docente_crud.py` | Integridad Referencial | **P1 (Should-Have)** | Borrado limpio de docente y persona asociada para evitar datos huérfanos. |
| **TC-PERF-LOAD-01**| Capa Web / API | Rendimiento / Carga | **P1 (Should-Have)** | El sistema debe sostener 50 usuarios concurrentes en periodos de inscripción escolar. |
| **TC-PERF-LOAD-03**| Base de Datos / Conexiones | Rendimiento / Estrés | **P1 (Should-Have)** | Conocer y blindar el agotamiento de sockets TCP de MySQL bajo tráfico pico. |
| **TC-UI-03** | `templates/estudiantes/inscripcion_form.html` | Frontend / Seguridad | **P1 (Should-Have)** | Blindaje visual e interactivo contra selección de clases saturadas. |
| **TC-UI-05** | `templates/base.html` | Frontend / RBAC | **P1 (Should-Have)** | Asegura que la interfaz oculte módulos prohibidos según el rol del usuario. |
| **TC-FRM-01** | `utils/form_validation.py` | Validación Funcional | **P1 (Should-Have)** | Rechazo de peticiones con campos obligatorios faltantes antes de invocar la BD. |
| **TC-VAL-03** | `utils/validators.py` | Validación Unitaria | **P1 (Should-Have)** | Comprobación de números enteros en IDs y claves numéricas. |
| **TC-VAL-06** | `utils/validators.py` | Validación Unitaria | **P1 (Should-Have)** | Formato cronológico ISO indispensable para calendarios y fechas de pago. |
| **TC-VAL-08** | `utils/validators.py` | Validación Unitaria | **P1 (Should-Have)** | Restricción de estatus de alumnos y modalidades a catálogos controlados. |
| **TC-EDGE-10** | `utils/calificaciones/evaluacion_crud.py` | Lógica Académica | **P2 (Could-Have)** | Asegurar que la suma de evaluaciones de una materia no sobrepase el 100%. |
| **TC-EDGE-11** | `calificacion_estudiante_crud.py` | Validación de Dominio | **P2 (Could-Have)** | Validación preventiva en código de rango de calificaciones (0.0 a 10.0). |
| **TC-EDGE-12** | `utils/cursos/prerequisito_crud.py` | Validación de Dominio | **P2 (Could-Have)** | Detección de ciclos y autorreferencias en la malla de materias. |
| **TC-EDGE-13** | `utils/aulas_horarios/horario_crud.py` | Validación de Dominio | **P2 (Could-Have)** | Validación de coherencia temporal (`hora_fin > hora_inicio`). |
| **TC-EDGE-16** | `utils/validators.py` | Robustez de Código | **P2 (Could-Have)** | Manejo defensivo ante valores `None` o tipos cruzados en validadores primitivos. |
| **TC-PERF-WEB-01** | Frontend / Web Vitals | Rendimiento Web | **P2 (Could-Have)** | LCP <= 2.5s en vistas de alta frecuencia de consulta como directorio de alumnos. |
| **TC-PERF-WEB-02** | Frontend / Select2 | Rendimiento Web | **P2 (Could-Have)** | INP <= 200ms para evitar congelamientos en selectores con cientos de opciones. |
| **TC-PERF-WEB-04** | Frontend / DOM Size | Rendimiento Web | **P2 (Could-Have)** | Evitar el colapso del navegador por árboles DOM de miles de nodos sin paginación. |
| **TC-PERF-LOAD-04**| Base de Datos / Consultas | Rendimiento / Carga | **P2 (Could-Have)** | Optimizar latencia de búsquedas `LIKE %term%` para no degradar el servidor. |
| **TC-UI-01** | `templates/estudiantes/student_form.html` | Frontend / UX | **P2 (Could-Have)** | Mejorar retención de datos en inputs ante errores para evitar frustración de captura. |
| **TC-UI-02** | `templates/asistencia/asistencia_form.html`| Frontend / UX | **P2 (Could-Have)** | Conmutación limpia de tipo de asistente sin enviar campos vacíos residuales. |
| **TC-UI-04** | `templates/base.html` | Frontend / Accesibilidad | **P2 (Could-Have)** | Visualización accesible y descarte fluido de mensajes flash. |
| **TC-UI-08** | Frontend / Responsive | Frontend / UX | **P2 (Could-Have)** | Adaptabilidad en pantallas móviles para directivos y docentes en tabletas. |
| **TC-REP-01** | `reportes_crud.py` | Inteligencia de Negocio | **P2 (Could-Have)** | Generación precisa de reportes de mejores promedios para becas y distinciones. |
| **TC-REP-02** | `reportes_crud.py` | Inteligencia de Negocio | **P2 (Could-Have)** | Análisis de saturación de horarios para optimización de aulas institucionales. |
| **TC-PAG-04** | `utils/finanzas_becas/pago_crud.py` | Finanzas / Reversión | **P2 (Could-Have)** | Reversión de pago ante cancelaciones o cheques rebotados. |
| **TC-EDGE-14** | `docente_capacitacion_crud.py` | Presentación de Datos | **P3 (Nice-to-Have)** | Evitar que docentes sin apellido materno muestren nombre `NULL` usando `IFNULL`. |
| **TC-UI-06** | `templates/login.html` | Frontend / UX | **P3 (Nice-to-Have)** | Autoenfoque en campo password tras error y ergonomía visual de acceso. |
| **TC-UI-07** | `templates/register.html` | Frontend / UX | **P3 (Nice-to-Have)** | Medidor estético de fortaleza de contraseña en formulario de registro. |
| **TC-PERF-WEB-03** | Frontend / CSS Layout | Rendimiento Web | **P3 (Nice-to-Have)** | Reducción de CLS por carga de estilos en el pie o cuerpo del documento. |
| **TC-PERF-WEB-05** | Frontend / Assets | Optimización de Red | **P3 (Nice-to-Have)** | Caché de assets locales y atributos SRI en librerías de CDN. |
| **TC-PERF-LOAD-05**| Servidor / Estabilidad | Pruebas de Resistencia | **P3 (Nice-to-Have)** | Prueba de resistencia prolongada de 2 horas para descartar fugas menores. |

### 5.3 Resumen Estadístico de la Matriz de Priorización

```
┌─────────────────────────────────────────────────────────────┐
│               DISTRIBUCIÓN DE CASOS DE PRUEBA                │
├───────────────────┬──────────────┬──────────────────────────┤
│ Nivel de Prioridad│ Cantidad TCs │ Porcentaje del Total     │
├───────────────────┼──────────────┼──────────────────────────┤
│ P0 / Crítica      │      14      │ 25.0%                    │
│ P1 / Alta         │      20      │ 35.7%                    │
│ P2 / Media        │      16      │ 28.6%                    │
│ P3 / Baja         │       6      │ 10.7%                    │
├───────────────────┼──────────────┼──────────────────────────┤
│ TOTAL CONSOLIDADO │      56      │ 100.0%                   │
└───────────────────┴──────────────┴──────────────────────────┘
```

---

## 6. Estrategia y Herramientas Recomendadas (Actualizada)

Para ejecutar de manera coordinada las pruebas en las capas de Backend, Base de Datos, Frontend y Rendimiento, se define la siguiente arquitectura de testing modular:

### 6.1 Ecosistema de Herramientas Especializadas

```
┌────────────────────────────────────────────────────────────────────────────┐
│                        SUITE DE HERRAMIENTAS DE QA                         │
├──────────────────────────┬─────────────────────────────────────────────────┤
│ Backend & Mocking DB     │ pytest + pytest-mock + pytest-cov               │
│ Pruebas E2E & Frontend   │ Playwright (Python API) + pytest-playwright     │
│ Core Web Vitals          │ Lighthouse CI / Google PageSpeed API            │
│ Carga y Concurrencia     │ Locust (Load Testing nativo en Python)          │
│ Monitoreo de Recursos    │ Docker stats / cAdvisor + Prometheus            │
└──────────────────────────┴─────────────────────────────────────────────────┘
```

1.  **Backend & DB Layer (`pytest` >= 7.4.0):**
    *   `pytest-mock` para aislar llamadas al cursor de MySQL.
    *   `pytest-cov` para auditoría de branch coverage en `utils/`.
    *   `Faker` para generación de datasets realistas.
2.  **Frontend & UI Layer (`Playwright` para Python):**
    *   Permite ejecutar navegadores reales (Chromium, Firefox, WebKit) en modo headless.
    *   Automatiza interacciones complejas con Select2, formularios dinámicos y validación de atributos accesibles sin depender de Selenium.
3.  **Client-side Performance (`Lighthouse CI`):**
    *   Auditorías automatizadas de Core Web Vitals (LCP, CLS, INP) integrables en pipelines de CI/CD.
4.  **Carga y Concurrencia (`Locust` >= 2.15.0):**
    *   Framework de carga basado en Python (`locustfile.py`), ideal para simular usuarios concurrentes ejecutando tareas complejas de inscripción y consulta mediante peticiones HTTP asíncronas con gevent.

### 6.2 Estructura del Directorio de Pruebas Propuesta

```
Sistema-Gestion-Universitaria/
├── tests/
│   ├── conftest.py                   # Fixtures globales (Mock DB, App Context, Auth Sessions)
│   ├── unit/                         # Pruebas Unitarias Aisladas
│   │   ├── test_validators.py        # Validadores primitivos
│   │   ├── test_schema_generator.py  # Generador de esquemas SQL
│   │   ├── test_form_validation.py   # Validación de formularios
│   │   └── test_auth.py              # Decoradores RBAC y login
│   ├── integration/                  # Pruebas de Integración con Base de Datos
│   │   ├── test_students_crud.py     # Estudiantes y estados de cuenta
│   │   ├── test_inscripcion_crud.py  # Aforo, duplicidad y prerrequisitos
│   │   ├── test_pago_crud.py         # Pagos, descuentos y reversiones
│   │   ├── test_docentes_crud.py     # Docentes y asignación
│   │   ├── test_cursos_crud.py       # Carreras, planes y materias
│   │   └── test_aulas_horarios.py    # Aulas y restricciones horarias
│   ├── ui/                           # Pruebas End-to-End de Frontend (Playwright)
│   │   ├── test_ui_student_form.py   # Formularios de captura y validaciones
│   │   ├── test_ui_inscripcion.py    # Interacción con Select2 y aforo visual
│   │   ├── test_ui_rbac_navbar.py    # Visibilidad de menús por rol
│   │   └── test_ui_responsive.py     # Adaptabilidad móvil y tablas
│   ├── performance/                  # Pruebas no funcionales
│   │   ├── test_web_vitals.py        # Métricas LCP, CLS, INP con Lighthouse
│   │   └── locustfile.py             # Escenarios de carga, estrés y concurrencia
│   └── edge_cases/                   # Pruebas de Modos de Falla y Vulnerabilidades
│       ├── test_security_injection.py# Blindaje contra SQLi y CSRF
│       ├── test_race_conditions.py   # Concurrencia por último cupo e IDs
│       └── test_financial_sanity.py  # Pagos negativos y truncamiento
├── pytest.ini                        # Configuración general de ejecución
├── locust.conf                       # Configuración de workers y headless load test
└── PLAN_DE_PRUEBAS.md                # Documento rector de aseguramiento de calidad
```

### 6.3 Configuración de Ejecución (`pytest.ini`)

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v 
    --strict-markers 
    --tb=short
    --cov=utils 
    --cov-report=term-missing 
    --cov-report=html:tests/coverage_report
markers =
    unit: Pruebas unitarias sin dependencias externas
    integration: Pruebas con interacción de base de datos
    ui: Pruebas de navegador y frontend con Playwright
    perf: Pruebas de rendimiento web y client-side
    edge: Modos de falla, seguridad y concurrencia
    slow: Pruebas de carga o de larga duración
```

### 6.4 Quality Gateways para Aprobación de Releases

Para que una versión del software sea promovida a producción, debe superar de forma obligatoria los siguientes umbrales:

1.  **Cero Fallos en Pruebas P0 y P1:** Tasa de éxito del **100%** en todos los casos P0 y P1.
2.  **Cobertura de Ramas (Backend):** Mínimo **85%** en `utils/` y **95%** en `inscripcion_crud.py` y `pago_crud.py`.
3.  **Umbrales de Rendimiento Web:**
    *   LCP <= 2.5 segundos en 75% de las vistas auditadas.
    *   CLS <= 0.1 en todas las páginas.
    *   INP <= 200 ms.
4.  **Criterios de Carga del Sistema:**
    *   Latencia p95 <= 1,500 ms con 50 VUs concurrentes.
    *   Tasa de error HTTP < 0.5% bajo carga pico.
    *   0 sobrecupos registrados ante pruebas de condición de carrera.
5.  **Cero Vulnerabilidades Críticas:** Ausencia total de inyecciones SQL y formularios mutadores sin token CSRF.

---
*Fin del Plan de Pruebas Integral. Documento maestro actualizado para revisión ejecutiva.*

