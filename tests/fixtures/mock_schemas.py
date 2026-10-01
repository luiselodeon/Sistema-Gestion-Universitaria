"""
tests/fixtures/mock_schemas.py
Fixtures de esquemas de datos y esquemas de tablas para pruebas unitarias y de integración.
"""

# Esquema sintético con tipos de datos heterogéneos para evaluar el recorrido exhaustivo del bucle
MOCK_MULTI_FIELD_SCHEMA = {
    "campo_1_nombre": {
        "type": "string",
        "max": 20,
        "required": True
    },
    "campo_2_edad": {
        "type": "int",
        "required": True
    },
    "campo_3_costo": {
        "type": "float",
        "required": True
    },
    "campo_4_fecha": {
        "type": "date",
        "required": True
    },
    "campo_5_estatus": {
        "type": "enum",
        "values": ["A", "B", "ACTIVO"],
        "required": True
    }
}

# Esquema para simular tabla estudiante
MOCK_ESTUDIANTE_SCHEMA = {
    "nombre": {
        "type": "string",
        "max": 60,
        "required": True
    },
    "apellido_paterno": {
        "type": "string",
        "max": 60,
        "required": True
    },
    "correo": {
        "type": "string",
        "max": 80,
        "required": True
    },
    "idcarrera": {
        "type": "int",
        "required": True
    }
}

# Columnas simuladas devueltas por MySQL 'DESCRIBE estudiante'
MOCK_DESCRIBE_ESTUDIANTE_COLUMNS = [
    {"Field": "matricula_alumno", "Type": "int(11)", "Null": "NO", "Key": "PRI", "Default": None, "Extra": "auto_increment"},
    {"Field": "idpersona", "Type": "int(11)", "Null": "NO", "Key": "UNI", "Default": None, "Extra": ""},
    {"Field": "idcarrera", "Type": "int(11)", "Null": "NO", "Key": "MUL", "Default": None, "Extra": ""},
    {"Field": "idplanestudio", "Type": "int(11)", "Null": "NO", "Key": "MUL", "Default": None, "Extra": ""},
    {"Field": "idbeca", "Type": "int(11)", "Null": "YES", "Key": "MUL", "Default": None, "Extra": ""},
    {"Field": "idestadodecuenta", "Type": "int(11)", "Null": "NO", "Key": "MUL", "Default": None, "Extra": ""},
    {"Field": "fecha_ingreso", "Type": "date", "Null": "NO", "Key": "", "Default": None, "Extra": ""},
    {"Field": "estatus", "Type": "enum('ACTIVO','BAJA','EGRESADO')", "Null": "NO", "Key": "", "Default": "ACTIVO", "Extra": ""},
]

# Lista blanca oficial de tablas válidas en el modelo de base de datos
VALID_DATABASE_TABLES = {
    "persona",
    "usuarios",
    "departamentoacademico",
    "departamentoasignatura",
    "carrera",
    "planestudio",
    "asignatura",
    "plan_asignatura",
    "prerequisito_asignatura",
    "docente",
    "certificacion",
    "capacitacion",
    "docente_certificacion",
    "docente_capacitacion",
    "tipo_beca",
    "beca",
    "estadodecuenta",
    "estudiante",
    "historialacademico",
    "periodoinscripciones",
    "calendarioescolar",
    "aula",
    "horario",
    "claseprogramada",
    "inscripcion",
    "inscripcion_carrera",
    "inscripcion_claseprogramada",
    "asistencia",
    "evaluacion",
    "calificacion_estudiante",
    "pago"
}
