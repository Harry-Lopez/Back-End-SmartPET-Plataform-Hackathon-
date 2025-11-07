import sqlite3 as sql
import time
from typing import Dict, Any
import hashlib
import os
import secrets

# Definimos el nombre para la base de datos
name_DB = 'historial_estado.db'

# ////////////////////////////
#   Crear la data base
# ////////////////////////////
def crear_db():
    try:
        connDB = sql.connect(name_DB)
        connDB.row_factory = sql.Row
        return connDB # Retorna como valor a la función que fué correcto y se creó el archivo
    except sql.Error as error:
         print(f"ERROR al intetar conectar la Base de Datos: {error}")
         return None # Retorna como valor a la función que no se creó el archivo

# //////////////////////////////////
#   Crear tablas en la data base
# /////////////////////////////////
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

            cursor.execute(
                """CREATE TABLE IF NOT EXISTS "usuarios_modo_general" (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    complet_name TEXT NOT NULL,
                    contacto TEXT NOT NULL,
                    clave_hash TEXT,
                    puesto TEXT DEFAULT 'usuario',
                    estado TEXT DEFAULT 'PENDIENTE'
                )"""
            )
            print('Base de datos SQLite inicializada, tabla "usuarios_modo_general" lista')

            connDB.commit()
            print("**EXITO** Bases de datos inicializadas correctamente")
        except sql.Error as error:
             print(f"***ERROR al inicializar la base de datos SQLite***: {error}")
        finally:
            if connDB:
                connDB.close()

# ///////////////////////////////////////////////////////////////////////
#   Extraer los datos y guardarlos como último estado de la máquina
# //////////////////////////////////////////////////////////////////////
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

# /////////////////////////////////////////////
#   Obtener ultimo estado de la data base
# ////////////////////////////////////////////
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

# Iteraciones para el hash
ITERACIONES = 100000

# //////////////////////////////////////////////////////////////
#   Proceso para crear el salt+hash y guardar en data base
# /////////////////////////////////////////////////////////////
def crear_contraseña_hash(contraseña : str, salt : bytes = None) -> str:

    if salt == None:
        salt = os.urandom(16)

    contraseña_hash = hashlib.pbkdf2_hmac(
        'sha256',
        contraseña.encode('utf-8'),
        salt,
        ITERACIONES
    )
    print("**EXITO** Proceso hash completado")
    return salt.hex() + contraseña_hash.hex()

# //////////////////////////////////////////////////////////////////
#   Crear la clave segura para el usuario y actualizarlo en db
# ////////////////////////////////////////////////////////////////
def crear_token_operador(codigo_institucional : str):

    connDB = crear_db()
    if connDB  == None:
        print("No se logró conectar con la data base ")
        return {
            "EXITO" : False,
            "MENSAJE" : 'No se pudo conectar con la data base'
        }

    try:
        cursor = connDB.cursor()
        cursor.execute('SELECT clave_hash, estado FROM usuarios_modo_operador WHERE codigo_institucional = ?',
                        (codigo_institucional,)
                    )

        operador_existente = cursor.fetchone()

        if not operador_existente:
            print("**ERROR** Código institucional no encontrado **USUARIO NO AUTORIZADO MODO OPERADOR**")
            return {
                "EXITO" : False,
                "MENSAJE" : '**ERROR** El código institucional no es de un usuario autorisado'
            }

        if operador_existente and operador_existente['estado'] == 'ACTIVO':
            print("**MENSAJE** Este código institucional ya había sido activado antes")
            return {
                "EXITO" : False,
                "MENSAJE" : 'Este código institucional ya había sido activado antes'
            }
        
        nueva_clave_texto = secrets.token_urlsafe(6)

        clave_hash_to_db = crear_contraseña_hash(nueva_clave_texto)

        cursor.execute(
            """UPDATE usuarios_modo_operador SET clave_hash = ?, estado = 'ACTIVO' WHERE codigo_institucional = ?""",
            (clave_hash_to_db, codigo_institucional)
        )
        connDB.commit()
        print("**EXITO** Usuario ACTIVADO y CLAVE HASH GUARDADA en la data base")
        print(f"**COMPLETADO** Bienvenido \n Clave de usuario única : {nueva_clave_texto}")
        return {
            "EXITO" : True,
            "MENSAJE" : 'Usuario ACTIVADO y Clave Hash Guardada',
            "Clave Única del Usuario" : nueva_clave_texto
        }
    except sql.Error as error:
        print(f"**ERROR** No se pudo registrar al operador en la Data Base: {error}")
        return {
                "EXITO": False,
                "MENSAJE": f"Error interno al acceder a la base de datos: {error}"
                }
    finally:
        connDB.close()

# //////////////////////////////////////////////////////////////////
#   Crear la clave segura para el usuario y actualizarlo en db
# ////////////////////////////////////////////////////////////////
def crear_token_usuario(correo_electronico : str, complete_name : str):

    connDB = crear_db()
    if connDB  == None:
        print("No se logró conectar con la data base ")
        return {
            "EXITO" : False,
            "MENSAJE" : 'No se pudo conectar con la data base'
        }

    try:
        cursor = connDB.cursor()
        cursor.execute('SELECT clave_hash, estado FROM usuarios_modo_general WHERE contacto = ?',
                        (correo_electronico,)
                    )

        usuario_existente = cursor.fetchone()

        if not usuario_existente:
            print("**USUARIO NO REGISTRADO** Insertando nuevo usuario y generando clave")
            nueva_clave_texto = secrets.token_urlsafe(6)

            clave_hash_to_db = crear_contraseña_hash(nueva_clave_texto)

            cursor.execute(
                """INSERT INTO usuarios_modo_general (complet_name, contacto, clave_hash, puesto, estado) VALUES(?, ?, ?, ?, ?)""",
                (complete_name, correo_electronico, clave_hash_to_db, 'usuario', 'ACTIVO')
            )
            connDB.commit()
            print("**EXITO** Usuario ACTIVADO, GUARDADO y CLAVE HASH GUARDADA en la data base")
            print(f"**COMPLETADO** Bienvenido \n Clave de usuario única : {nueva_clave_texto}")
            return {
                "EXITO" : True,
                "MENSAJE" : 'Usuario ACTIVADO, GUARDADO y Clave Hash Guardada',
                "Clave Única del Usuario" : nueva_clave_texto
            }

        if usuario_existente and usuario_existente['estado'] == 'ACTIVO':
            print("**MENSAJE** Este correo electrónico ya había sido activado antes")
            return {
                "EXITO" : False,
                "MENSAJE" : 'Este correo electrónico ya había sido activado antes'
            }
        
    except sql.Error as error:
        print(f"**ERROR** No se pudo registrar al usuario en la Data Base: {error}")
        return {
                "EXITO": False,
                "MENSAJE": f"Error interno al acceder a la base de datos: {error}"
                }
    finally:
        connDB.close()

SALT_SIZE_HEX = 32
# /////////////////////////////////////////////////////////////
#   Verificar solo la clave del usuario con la de el en db
# ////////////////////////////////////////////////////////////
def verificar_clave_solo_logica(clave_ingresada : str, clave_hash_to_db : str) -> bool:

    # <--Extraer de la clave en la db el salt(32 dig) y el hash(clave guardada(resto de dig))-->>
    salt_hexadecimal = clave_hash_to_db[:SALT_SIZE_HEX]
    hash_almacenado_hex_db = clave_hash_to_db[SALT_SIZE_HEX:]

    try:
        salt_bytes = bytes.fromhex(salt_hexadecimal)
    except ValueError:
        print("**ERROR** Salt en data base inválido (DB corrupta)")
        return False

    # <<--Convertir la clave escrita por el usuario a hash-->>
    hash_usuario_bytes = hashlib.pbkdf2_hmac(
        'sha256',
        clave_ingresada.encode('utf-8'),
        salt_bytes,
        ITERACIONES
    )

    hash_generado_user_hex = hash_usuario_bytes.hex()

    # <<--Comprobar qu ela clave es correcta-->>
    if hash_generado_user_hex != hash_almacenado_hex_db:
        print("**ERROR** Clave incorrecta")
        return False
    # <<--En este punto la clave resulta ser correcta-->>
    print("**EXITO** Clave correcta y comprobada")
    return True

# ///////////////////////////////////////////////////////
#   Comprobar su estado, cobtraseña e iniciar sesión
# ///////////////////////////////////////////////////////
def iniciar_sesion_operador_db(codigo_institucional : str, clave_usuario : str):
    connDB = None
    connDB = sql.connect(name_DB)

    # <<--Recuperar los datos de la data base-->>
    try:
        cursor = connDB.cursor()
        cursor.execute(
            'SELECT clave_hash, estado, puesto, complet_name FROM usuarios_modo_operador WHERE codigo_institucional = ?', 
            (codigo_institucional, )
        )

        row = cursor.fetchone()

        # <--Salida temprana si no está el código institucional(usuario)-->>
        if row == None:
            print("**ERROR** Código Institucional no encontrado")
            return {
                "EXITO" : False, 
                "MENSAJE" : 'Codigo institucional no registrado en la data base'
            }
        
        # <<--Extraer datos de la fila del usuario-->>
        clave_hash, estado_db, puesto_db, complet_name_db = row

        # <<--Salida temprana si no se ha registrado antes el usuario (PENDIENTE)-->>
        if estado_db != 'ACTIVO':
            print("**ERROR** No se ha iniciado sesión antes, primero registrese con sus datos")
            return{
                "EXITO" : False, 
                "MENSAJE" : 'No se ha registrado el usuario, intente "Registrarse"'
            }

        # <<--Comprobar con la función si la clave del usuario coinside con la de la db-->>
        if verificar_clave_solo_logica(clave_usuario, clave_hash):
            # Guardamos los datos del usuario extraídos de la fila de db
            datos_usuario_login = {
                "Nombre" : complet_name_db,
                "Codigo Institucional" : codigo_institucional,
                "Puesto" : puesto_db
            }
            print(f"**EXITO** Inicio de sesión exitoso\n{datos_usuario_login}")
            return{
                "EXITO" : True,
                "MENSAJE" : f'Inicio de sesión exitoso\n{datos_usuario_login}'
            }
        # <<--Si no es correcta la clave-->>
        else:
            print("**ERROR** Clave incorrecta, inténtelo de nuevo...ahorita")
            return{
                "EXITO" : False,
                "MENSAJE" : 'Contraseña incorrecta, inténtelo de nuevo...ahorita'
            }
    # <<--Comando except si no  se conectó a la data base-->>
    except sql.Error as error:
        print("**ERROR** No se logró conectar con la data base en Log-in")
        return{
            "EXITO" : False,
            "ERROR in Log-in" : f'Error: {error}',
            "MENSAJE" : 'No se logró conectar con la data base en Log-in'
        }
    # <<--Cerra la data base-->>
    finally:
        if connDB:
            connDB.close()

# //////////////////////////////////////////////////////////
#   Comprobar, estado, contraseña y sesion modo ggeneral
# /////////////////////////////////////////////////////////
def iniciar_sesion_usuario_db(correo_electronico : str, clave_usuario : str):
    connDB = None
    connDB = sql.connect(name_DB)

    # <<--Recuperar los datos de la data base-->>
    try:
        cursor = connDB.cursor()
        cursor.execute(
            'SELECT clave_hash, estado, puesto, complet_name FROM usuarios_modo_general WHERE contacto = ?', 
            (correo_electronico, )
        )

        row = cursor.fetchone()

        # <--Salida temprana si no está el código institucional(usuario)-->>
        if row == None:
            print("**ERROR** Medio de contacto no encontrado")
            return {
                "EXITO" : False, 
                "MENSAJE" : 'Medio de contacto no registrado en la data base'
            }
        
        # <<--Extraer datos de la fila del usuario-->>
        clave_hash, estado_db, puesto_db, complet_name_db = row

        # <<--Salida temprana si no se ha registrado antes el usuario (PENDIENTE)-->>
        if estado_db != 'ACTIVO':
            print("**ERROR** No se ha iniciado sesión antes, primero registrese con sus datos")
            return{
                "EXITO" : False, 
                "MENSAJE" : 'No se ha registrado el usuario, intente "Registrarse"'
            }

        # <<--Comprobar con la función si la clave del usuario coinside con la de la db-->>
        if verificar_clave_solo_logica(clave_usuario, clave_hash):
            # Guardamos los datos del usuario extraídos de la fila de db
            datos_usuario_login = {
                "Nombre" : complet_name_db,
                "Contacto" : correo_electronico,
                "Puesto" : puesto_db
            }
            print(f"**EXITO** Inicio de sesión exitoso\n{datos_usuario_login}")
            return{
                "EXITO" : True,
                "MENSAJE" : f'Inicio de sesión exitoso\n{datos_usuario_login}'
            }
        # <<--Si no es correcta la clave-->>
        else:
            print("**ERROR** Clave incorrecta, inténtelo de nuevo...ahorita")
            return{
                "EXITO" : False,
                "MENSAJE" : 'Contraseña incorrecta, inténtelo de nuevo...ahorita'
            }
    # <<--Comando except si no  se conectó a la data base-->>
    except sql.Error as error:
        print("**ERROR** No se logró conectar con la data base en Log-in")
        return{
            "EXITO" : False,
            "ERROR in Log-in" : f'Error: {error}',
            "MENSAJE" : 'No se logró conectar con la data base en Log-in'
        }
    # <<--Cerra la data base-->>
    finally:
        if connDB:
            connDB.close()

# ////////////////////////////
#   Pre-logica START seguro
# ////////////////////////////

# <<--Retorna la clave hash de la db si fué exitoso-->>
def obtener_clave_hash_por_codigo(codigo_institucional: str) -> dict:
    # <<--Conectar  a la data  base-->>
    connDB = crear_db()
    # <<--Salida temprana-->>
    if connDB is None:
        return{
            "EXITO": False, 
            "MENSAJE": "No se pudo conectar con la base de datos"
        }

    try:
        cursor = connDB.cursor()
        cursor.execute(
            'SELECT clave_hash, estado FROM usuarios_modo_operador WHERE codigo_institucional = ?',
            (codigo_institucional,)
        )
        row = cursor.fetchone()

        # <<--Salida temprana si no hay ninguna fila con el código institucional-->>
        if row is None:
            return{
                "EXITO": False, 
                "MENSAJE": "Código institucional no encontrado"
            }
        # <<--Salida temprana si el usuario no se ha registrado antes-->>
        if row['estado'] != 'ACTIVO':
             return{
                "EXITO": False, 
                "MENSAJE": "Usuario no activo, requiere registro/activación"
            }
        # <<--En este punto fué exitoso el log-in-->>
        return{
            "EXITO": True, 
            # Muestra lo que se extrajo de la fila (salt + hash)
            "clave_hash": row['clave_hash'] 
        }

    except sql.Error as error:
        print(f"**ERROR** SQL en obtener_clave_hash_por_codigo: {error}")
        return{
            "EXITO": False,
            "MENSAJE": "Error interno del servidor"
        }
    finally:
        if connDB:
            connDB.close()


# //////////////////////
#   Ejecutar archivo
# /////////////////////
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
