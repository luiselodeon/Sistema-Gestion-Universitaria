# Scratchpad: Mapeo Técnico, Arquitectura y Análisis de Puntos de Falla
**Proyecto:** Sistema de Gestión Universitaria
**Rol:** QA Lead & Software Architect
**Fecha de Análisis:** Septiembre 2026

---

## 1. Mapeo de Arquitectura y Dependencias entre Módulos

```
                   ┌──────────────────────────────────────────────┐
                   │             app.py (Flask Web App)           │
                   └──────────────────────┬───────────────────────┘
                                          │
       ┌──────────────────┬───────────────┼───────────────┬──────────────────┐
       ▼                  ▼               ▼               ▼                  ▼
┌──────────────┐   ┌──────────────┐ ┌───────────┐  ┌─────────────┐   ┌──────────────┐
│  Estudiantes │   │   Docentes   │ │  Cursos   │  │   Aulas y   │   │  Finanzas y  │
│              │   │              │ │           │  │  Horarios   │   │    Becas     │
└──────┬───────┘   └──────┬───────┘ └─────┬─────┘  └──────┬──────┘   └──────┬───────┘
       │                  │               │               │                 │
       ▼                  ▼               ▼               ▼                 ▼
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                         Tablas Base y Relacionales                         │
 │ persona, usuario, estudiante, docente, carrera, planestudio, asignatura,   │
 │ aula, horario, claseprogramada, inscripcion, asistencia, evaluacion,       │
 │ calificacion_estudiante, estadodecuenta, pago, beca                        │
 └─────────────────────────────────────────────────────────────────────────────┘
```

### 1.1 Cadena de Dependencias Críticas
1. **Flujo de Creación de Estudiante (`students_crud.py`):**
   - Requiere `persona` -> `carrera` -> `planestudio` -> `estadodecuenta` -> `beca` (opcional).
   - Genera registro en `persona`, registro en `estadodecuenta` con `saldo_inicial = carrera.costo_inscripcion`, y registro en `estudiante`.
   - **Dependencia implícita no transaccional:** Si falla el INSERT en `estudiante`, quedan registros huérfanos en `persona` y `estadodecuenta`.

2. **Flujo de Inscripción (`inscripcion_crud.py`):**
   - Requiere `estudiante` (activo) + `claseprogramada` (con cupo en `aula`, en periodo `ABIERTO`).
   - Valida:
     a) Capacidad de aula (`check_classroom_capacity`).
     b) Duplicidad de materia en el mismo periodo (`check_duplicate_subject`).
     c) Prerrequisitos concurrentes en el mismo periodo (`check_concurrent_prerequisites`).
   - **Gaps críticos:**
     - NO valida prerrequisitos históricos aprobados en `historialacademico`.
     - NO valida empalmes de horario (schedule clash) para el alumno.
     - NO valida estatus financiero (adeudos o límite de crédito).

3. **Flujo de Pagos y Finanzas (`pago_crud.py` & `estadodecuenta_crud.py`):**
   - `pago` depende de `estadodecuenta`.
   - Al registrar pago: inserta en `pago` y modifica `estadodecuenta.saldo_actual`.
   - **Gaps críticos:**
     - Sin transacción atómica: si se interrumpe, se crea el pago sin descontar saldo.
     - No valida importes negativos (podría aumentar la deuda).
     - `GREATEST(0, saldo_actual - importe)` descarta saldos a favor (overpayments silenciosos).

4. **Flujo de Evaluación y Calificación (`calificaciones`):**
   - `evaluacion` depende de `claseprogramada`.
   - `calificacion_estudiante` depende de `evaluacion` + `inscripcion`.
   - **Gaps críticos:**
     - Permite porcentajes de evaluación acumulados mayores al 100%.
     - No valida rangos numéricos de calificación (0.0 a 10.0) en código.
     - Permite calificar inscripciones que no pertenecen a la clase evaluada.

---

## 2. Puntos de Entrada y Salida de Datos

| Módulo / Función | Datos de Entrada (Inputs) | Transformación / Lógica Interna | Salidas / Efectos Colaterales (Outputs) |
|---|---|---|---|
| `validators.validate_string` | `value: any`, `rules: dict` | Chequeo de `rules['max']` contra `len(value)` | `(bool, Optional[str])` |
| `validators.validate_int` | `value: str`, `rules: dict` | `value.isdigit()` | `(bool, Optional[str])` |
| `validators.validate_float` | `value: any`, `rules: dict` | `float(value)` en `try/except ValueError` | `(bool, Optional[str])` |
| `validators.validate_date` | `value: str`, `rules: dict` | `datetime.strptime(value, "%Y-%m-%d")` | `(bool, Optional[str])` |
| `validators.validate_enum` | `value: any`, `rules: dict` | `value not in rules['values']` | `(bool, Optional[str])` |
| `form_validation.validate_form_from_table` | `cursor`, `table_name: str`, `form: dict` | Genera esquema vía `DESCRIBE`, itera campos y ejecuta validador | `(bool, Optional[str])` |
| `schema_generator.generate_schema_from_table` | `cursor`, `table_name: str` | Ejecuta `DESCRIBE {table_name}`, parsea tipos SQL | `dict` con esquema generado |
| `auth.login_required` | Decorador sobre vista Flask | Revisa `"user_id" in session` | Función envuelta o redirección a `login` |
| `auth.role_required` | `*roles`, decorador | Revisa `"user_rol" in session` y `rol == 'admin'` | Función envuelta o redirección a `inicio` |
| `usuarios_crud.add_usuario` | `cursor`, `email`, `password`, `rol` | Hash con `werkzeug.security.generate_password_hash` | `int (idusuario)` |
| `usuarios_crud.update_usuario` | `cursor`, `idusuario`, `email`, `rol`, `password` | Solo actualiza campo `rol` | Mutación DB |
| `aula_crud.check_aula_capacity_reduction` | `cursor`, `idaula`, `new_capacity` | Consulta `HAVING COUNT(i.idinscripcion) > new_capacity` | `(bool, Optional[str])` |
| `aula_crud.update_aula` | `cursor`, `idaula`, `descripcion`, `lugar`, `capacidad` | Chequea reducción de cupo; lanza `Exception` si no procede | Mutación DB |
| `horario_crud.add_horario` | `cursor`, `dia_semana`, `hora_inicio`, `hora_fin`, `descripcion` | `INSERT INTO horario` | `int (idhorario)` |
| `asignaturas_crud.add_asignatura` | `cursor`, `nombre`, `creditos`, `horas`, `iddepto` | Inserta con clave 'TEMP', consulta depto y actualiza clave | Mutación DB |
| `prerequisito_crud.add_prerequisito` | `cursor`, `idasignatura`, `idasignatura_prereq` | `INSERT INTO prerequisito_asignatura` | Mutación DB |
| `planestudio_crud.add_planestudio` | `cursor`, `nombre`, `vigencia_inicio`, `vigencia_fin`, `idcarrera` | Compara `str(vigencia_fin) < str(vigencia_inicio)` | Mutación DB o `ValueError` |
| `docente_crud.add_docente` | `cursor`, `nombre`, `paterno`, `materno`, `correo`, `fecha_alta`, `estatus` | `MAX(idpersona) + 1`, `INSERT persona`, `INSERT docente` | `int (iddocente)` |
| `docente_crud.delete_docente` | `cursor`, `iddocente` | Obtiene `idpersona`, borra de `docente`, borra de `persona` | `bool` |
| `students_crud.add_student` | `cursor`, `nombre`, `paterno`, `materno`, `correo`, `idcarrera`, `idbeca` | `MAX(idpersona)`, `MAX(idestadodecuenta)`, inserta 3 tablas | Mutación DB |
| `students_crud.delete_student` | `cursor`, `matricula` | `id_persona, id_estado_cuenta = result` -> borra en 3 tablas | `bool` |
| `inscripcion_crud.check_classroom_capacity` | `cursor`, `idclaseprogramada` | Cuenta inscripciones activas vs capacidad de aula | `(bool, Optional[str])` |
| `inscripcion_crud.check_duplicate_subject` | `cursor`, `matricula`, `idclase`, `exclude_id` | Consulta misma materia y periodo | `(bool, Optional[str])` |
| `inscripcion_crud.check_concurrent_prerequisites` | `cursor`, `matricula`, `idclase`, `exclude_id` | Doble verificación hacia adelante y reversa | `(bool, Optional[str])` |
| `inscripcion_crud.add_inscripcion` | `cursor`, `matricula`, `idclase`, `motivo`, `estatus` | Ejecuta 3 validaciones, inserta con `date.today()` | `int (idinscripcion)` |
| `pago_crud.add_pago` | `cursor`, `idestadodecuenta`, `forma`, `tipo`, `importe`, `referencia` | Inserta en `pago` y `UPDATE estadodecuenta (GREATEST(0, saldo - importe))` | Mutación DB |
| `pago_crud.update_pago` | `cursor`, `idpago`, `forma`, `tipo`, `new_importe`, `referencia` | Obtiene `old_importe`, actualiza `pago`, reajusta saldo | `bool` |
| `pago_crud.delete_pago` | `cursor`, `idpago` | Borra pago y suma importe a saldo | `bool` |
| `evaluacion_crud.add_evaluacion` | `cursor`, `idclase`, `tipo`, `descripcion`, `fecha`, `porcentaje` | `INSERT INTO evaluacion` | `int (idevaluacion)` |
| `calificacion_estudiante_crud.add_calificacion` | `cursor`, `idevaluacion`, `idinscripcion`, `calificacion`, `obs` | `INSERT INTO calificacion_estudiante` | Mutación DB |

---

## 3. Matriz de Supuestos No Validados, Riesgos y Casos Borde Críticos

### 3.1 Vulnerabilidades de Seguridad y Estabilidad Críticas
1. **Inyección SQL en Generación de Esquemas (`schema_generator.py`):**
   - `cursor.execute(f"DESCRIBE {table_name}")`: Si `table_name` es manipulado, existe riesgo de inyección directa.
2. **Error Arquitectónico en Validación de Formularios (`form_validation.py`):**
   - El bucle `for field, rules in schema.items():` tiene un `return` directo en el primer tipo evaluado (`return validate_string(...)`). Esto provoca que **únicamente se valide el primer campo de la tabla** y se ignoren todos los demás campos del formulario.
3. **Desempaquetado Erróneo en Eliminación de Alumno (`students_crud.delete_student`):**
   - `id_persona, id_estado_cuenta = result` cuando `result` es un diccionario (`dict`) asigna las cadenas literales de las claves: `id_persona = 'idpersona'`, `id_estado_cuenta = 'idestadodecuenta'`. Esto rompe la eliminación o intenta borrar con strings no enteros.
4. **Condición de Carrera en Generación Manual de IDs (`docente_crud.py` y `students_crud.py`):**
   - Ambos usan `SELECT MAX(idpersona) FROM persona` seguido de `INSERT persona (idpersona, ...)`. En entornos multiusuario o concurrentes, dos peticiones simultáneas calculan el mismo ID y una colisiona con `Duplicate entry`.
5. **Transaccionalidad Ausente (ACID Violation):**
   - Ninguno de los CRUDs multi-tabla (`students_crud.add_student`, `docente_crud.delete_docente`, `pago_crud.add_pago`, `asignaturas_crud.add_asignatura`) gestiona bloques `BEGIN / COMMIT / ROLLBACK`. Fallos a mitad de ejecución dejan la base de datos en estado inconsistente.

### 3.2 Lógica de Negocio Ignorada (Reglas Académicas y Financieras)
1. **Falta de Validación de Prerrequisitos Históricos:**
   - `inscripcion_crud.py` únicamente valida si el prerrequisito se está cursando en el mismo semestre. No valida si el alumno cursó y aprobó la materia previa en periodos anteriores con estatus `APROBADA`.
2. **Ausencia de Validación de Empalme de Horarios:**
   - Un alumno puede inscribir dos materias diferentes que se imparten en el mismo día y la misma hora. El sistema no realiza validación de cruce de horarios para estudiantes.
3. **Cruces de Horario en Asignación de Docentes:**
   - `claseprogramada_crud.py` no verifica si el docente ya tiene otra clase asignada en el mismo día y horario.
4. **Pagos Negativos y Alteración de Saldo:**
   - `pago_crud.py` no valida `importe_pago > 0`. Un pago negativo incrementa la deuda del alumno de forma ilegítima.
5. **Suma de Porcentajes de Evaluación Excedida:**
   - Se pueden dar de alta evaluaciones para una clase cuya suma de porcentajes exceda el 100% (ej. 4 exámenes del 30% = 120%).
6. **Autoreferencias y Ciclos en Prerrequisitos:**
   - `prerequisito_crud.py` permite que una materia sea su propio prerrequisito (`idasignatura == idasignatura_prereq`) o generar ciclos directos (A requiere B, B requiere A).
7. **Inconsistencia de Nombres NULL en MySQL:**
   - En `docente_capacitacion_crud.py`, `CONCAT(p.nombre, ' ', p.apellido_paterno, ' ', p.apellido_materno)` sin `IFNULL` devuelve `NULL` para docentes sin apellido materno.

---

## 4. Hallazgos de Frontend & UI/UX

### 4.1 Rutas y Vistas con Mayor Complejidad de Renderizado
1. **`templates/estudiantes/inscripcion_form.html` (Sobrecarga de Payload y Assets en Body):**
   - Carga masiva en memoria de todos los estudiantes y de todas las clases programadas con descripciones extensas concatenadas en `<option>`. En una institución mediana (ej. 3,000 estudiantes y 400 clases), el HTML generado supera los 3.5 MB para un único formulario.
   - Inyección anómala de dependencias: Carga Select2 CSS, jQuery 3.7.1 y Select2 JS en el cuerpo (`<body>`) del documento en lugar de `<head>` o pie de página. Esto genera bloqueo de renderizado, FOUC (Flash of Unstyled Content) y riesgo de colisión de scripts.
2. **`templates/estudiantes/registro_consulta.html` y Vistas de Lista (Cero Paginación y Bloqueo de DOM):**
   - Ninguna de las vistas de listado (`estudiantes`, `inscripciones`, `docentes`, `asistencias`, `pagos`) implementa paginación (`LIMIT / OFFSET`).
   - Renderizan colecciones completas (`for student in students`) en el DOM. Más de 500 filas generan miles de nodos en el árbol DOM, provocando degradación severa en el tiempo de interacción (INP / TBT) y congelamiento de scroll en dispositivos móviles.
3. **`templates/asistencia/asistencia_form.html` (Duplicación Oculta en el DOM):**
   - Renderiza listas completas de estudiantes y docentes en divs ocultos (`display: none`), manipulados mediante JavaScript en línea (`togglePersona()`). El navegador procesa y mantiene en memoria cientos de nodos inútiles según el tipo seleccionado.
4. **`templates/reportes/reportes.html` (Assets Rotos):**
   - Referencia clases de FontAwesome (`<i class="fas fa-...">`) para los íconos de tarjetas y descargas, pero la biblioteca FontAwesome **no está enlazada** en `base.html` ni en `reportes.html`, generando íconos invisibles o fallos visuales.

### 4.2 Formas y Campos Vulnerables a Entradas Malformadas o Falta de Sanitización
1. **Ausencia Universal de Protección CSRF (Cross-Site Request Forgery):**
   - Ningún formulario de la aplicación (`<form method="POST">`) incluye tokens CSRF. Operaciones críticas como eliminación de alumnos (`delete_student`), eliminación de inscripciones (`delete_inscripcion`), y registro de pagos (`add_pago`) son ejecutables mediante ataques de falsificación de petición en sitios cruzados.
2. **Dependencia Exclusiva de Validaciones Nativas HTML5:**
   - La interfaz carece de validación dinámica en JavaScript con retroalimentación en tiempo real (regex para correos universitarios, máscaras de teléfono, límites de fecha válidos).
   - Manipulación de elementos `disabled`: En `inscripcion_form.html`, las clases con cupo lleno tienen el atributo `disabled`. Cualquier usuario puede abrir las herramientas de desarrollador, remover el atributo `disabled` y enviar el formulario, aprovechando la falta de sincronización reactiva en frontend.
3. **Pérdida Catastrófica del Estado del Formulario en Errores:**
   - Ante fallos de validación en backend (por ejemplo en `add_student` o `add_pago`), los controladores ejecutan `return redirect(request.referrer)`. Al tratarse de una redirección HTTP 302, los datos que el usuario ingresó se pierden por completo, obligándolo a capturar todo de nuevo.
4. **Inconsistencias en Formularios de Autenticación (`register.html` y `login.html`):**
   - `register.html` no hereda de `base.html`, utiliza campo `name="username"` en vez de `email`, carece de medidor de fortaleza de contraseña y no previene el autoregistro masivo por bots (ausencia de rate limiting o CAPTCHA).
   - `login.html` filtra arbitrariamente el mensaje flash `"Sesión cerrada"`, ocultando confirmaciones de logout al usuario.

### 4.3 Puntos Susceptibles a Degradación de Rendimiento ante Múltiples Usuarios
1. **Cuello de Botella en el Servidor de Aplicación (Werkzeug Development Server):**
   - `docker-compose.yml` inicia Flask mediante `command: flask run --host=0.0.0.0 --port=5000` con `FLASK_DEBUG: "1"`. El servidor de desarrollo de Flask es estrictamente monohilo o con concurrencia muy limitada. Durante periodos de inscripción concurrente, las solicitudes se encolan linealmente, disparando la latencia a más de 15 segundos o causando caídas por timeout.
2. **Agotamiento Inmediato del Pool de Conexiones a Base de Datos:**
   - `utils/db.py` abre una conexión TCP nueva por cada petición sin pooling reutilizable. Con 50 usuarios simultáneos, MySQL agota las conexiones permitidas (`Too many connections`) y el sistema colapsa con error 500.
3. **Búsquedas Masivas no Paginadas con LIKE %term%:**
   - Las barras de búsqueda envían consultas con comodines bilaterales (`%query%`) directamente por GET sin debounce (`setTimeout` o entrada retardada). Múltiples usuarios escribiendo en la barra de búsqueda saturan el motor InnoDB con escaneos secuenciales de tablas completas.
4. **Métricas Core Web Vitals Comprometidas:**
   - **LCP (Largest Contentful Paint):** Afectado negativamente por fuentes de Google Fonts (Inter) y CSS de Bootstrap cargados desde CDN externos sin optimización de pre-carga local.
   - **CLS (Cumulative Layout Shift):** Generado por hojas de estilo insertadas tardíamente en `<body>` (`Select2`) y alertas flash sin reserva de espacio.
   - **INP (Interaction to Next Paint):** Afectado por la inicialización pesada de Select2 sobre elementos `<select>` con miles de nodos hijos.

---
*Scratchpad completado y actualizado con hallazgos de Frontend & UI/UX.*
