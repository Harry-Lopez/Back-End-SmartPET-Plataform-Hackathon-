import sqlite3 as sql
import time
from typing import Dict, Any

# Definimos el nombre para la base de datos
name_DB = 'historial_estado.db'

def crear_db():
    try:
        connDB = sql.connect(name_DB)
        connDB.row_factory = sql.Row
        return connDB # Retorna como valor a la función que fué correcto y se creó el archivo
    except sql.Error as error:
         print(f"ERROR al intetar conectar la Base de Datos: {error}")
         return None # Retorna como valor a la función que no se creó el archivo

def config_DB():
    # Le damos el valor que se retornó de la función crear_db
    connDB = crear_db()

    if connDB is None:
        print("***ERROR CRÍTICO*** No se logró establecer la conexión con la data base")
        return False
    # Estructura if para manejo de errores (Se ejecuta solo cuando 'connDB' fué retornado)
    if connDB:
        # Manejo de errores si ocurre un error al inicializar la D.B. o la tabla
        try:
            cursor = connDB.cursor()
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS "historial_estado" (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    register_time TEXT NOT NULL,
                    temperatura REAL NOT NULL,
                    nivel_agua TEXT NOT NULL,
                    estado_motor TEXT NOT NULL
                )"""
            )
            print('Base de datos SQLite inicializada, tabla "historial_estado" lista')

            cursor.execute(
                """CREATE TABLE IF NOT EXISTS "usuarios_modo_operador" (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    complet_name TEXT NOT NULL,
                    codigo_institucional TEXT NOT NULL UNIQUE,
                    contacto TEXT NOT NULL,
                    clave_hash TEXT,
                    puesto TEXT DEFAULT 'operador',
                    estado TEXT DEFAULT 'PENDIENTE'
                )"""
            )
            print('Base de datos SQLite inicializada, tabla "usuarios_modo_operador" lista')

            connDB.commit()
            print("**EXITO** Bases de datos inicializadas correctamente")
        except sql.Error as error:
             print(f"***ERROR al inicializar la base de datos SQLite***: {error}")
        finally:
            if connDB:
                connDB.close()

def guardar_new_status(datos : dict[str,any]) ->  bool:
    connDB = crear_db()
     # Comprobamos desde un inicio si hay valores correctos en el JSON enviado por el arduino
    if not connDB:
        print("**ERROR** No se logró conectar con la abse de datos")
        return False
    
    current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

    try:
        temperatura = datos['temperatura']
        nivel_agua = datos['nivel_agua'].upper()
        estado_motor = datos['estado_motor'].upper()
        print("**EXITO AL RECIBIR DATOS**")
    except KeyError as error:
        print(f"**ERROR DE DATOS** {error}")
        connDB.close()
        return False

    try:
        cursor = connDB.cursor()
        cursor.execute(
             """INSERT INTO historial_estado (register_time, temperatura, nivel_agua, estado_motor) 
               VALUES (?, ?, ?, ?)""",
            (current_time, temperatura, nivel_agua, estado_motor)
        )
        connDB.commit()
        print(f"**EXITO** Datos guardados en la base de datos SQLite \n Temperatura={temperatura} \n Agua={nivel_agua} \n Motor={estado_motor}")
        return True
    except sql.Error as error:
         print(f"**ERROR** {error} \n ***No se logró guardar los datos***")
         return False
    finally:
         connDB.close()

def obten_ultim_estado():
    connDB = crear_db()
    if not connDB:
        return None

    try:
        cursor = connDB.cursor()
        cursor.execute("SELECT * FROM historial_estado ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()

        if row:
            return dict(row)
        return None
    except sql.Error as error:
        print(f"**ERROR AL RECUPERAR EL ÚLTIMO ESTADO**: {error}")
        return None
    finally:
        connDB.close()

if __name__ == '__main__':
        config_DB()
        prueba_datos= {
            'temperatura' : 36.6,
            'nivel_agua' : 'medio',
            'estado_motor' : 'encendido'
        }

        guardar_new_status(prueba_datos)
        ultimo_estado = obten_ultim_estado()
        print(f"**ULTIMO ESTADO**: {ultimo_estado}")
