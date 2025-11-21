from data_base import config_DB, guardar_new_status, guardar_new_status_calentador, obten_ultim_estado, obten_ultim_estado_calentador, crear_contraseña_hash, crear_token_operador, crear_token_usuario, verificar_clave_solo_logica, iniciar_sesion_operador_db, iniciar_sesion_usuario_db, obtener_clave_hash_por_codigo
from flask import Flask, request, jsonify
import serial

config_DB()

# Flask() es la clase de python que crea el motor del servidor
# __name__ es la variable mágica que python da por defecto a un archivo py que se ejecuta
app = Flask(__name__)


@app.route('/')
def pagina_principal():
    return "Prueba 3 de código básico Flask por P1"

@app.route('/api/arduino/backend/m1', methods = ['POST'])
def enviarDatosToBackend_m1():
    datos_recibidos = request.json

    if datos_recibidos:
        if guardar_new_status(datos_recibidos):
            return jsonify({
                "Exito" : True,
                "Mensaje" : 'Estado guardado exitosamente en la data base'
            }), 200
        else:
            return jsonify({
                "Exito" : False,
                "Mensaje" : '**ERROR** Al guardar los nuevos datos'
            }), 500
    return jsonify({
        "Exito" : False,
        "Mensaje" : '**ERROR** datos no recibidos o nulos'
    })

@app.route('/api/arduino/backend/m2', methods = ['POST'])
def enviarDatosToBackend_m2():
    datos_recibidos = request.json

    if datos_recibidos:
        if guardar_new_status_calentador(datos_recibidos):
            return jsonify({
                "Exito" : True,
                "Mensaje" : 'Estado guardado exitosamente en la data base'
            }), 200
        else:
            return jsonify({
                "Exito" : False,
                "Mensaje" : '**ERROR** Al guardar los nuevos datos'
            }), 500
    return jsonify({
        "Exito" : False,
        "Mensaje" : '**ERROR** datos no recibidos o nulos'
    })

@app.route('/api/status/backend/m1', methods = ['GET'])
def obtener_status_m1():
    ultimo_estado = obten_ultim_estado()
    if ultimo_estado:
        return jsonify(ultimo_estado), 200
    
    return jsonify({
        "Exito" : False,
        "Mensaje" : "**ERROR** Al obtener los datos"
    }), 204

@app.route('/api/status/backend/m2', methods = ['GET'])
def obtener_status_m2():
    ultimo_estado = obten_ultim_estado_calentador()
    if ultimo_estado:
        return jsonify(ultimo_estado), 200
    
    return jsonify({
        "Exito" : False,
        "Mensaje" : "**ERROR** Al obtener los datos"
    }), 204

# ////////////////////////////////////////////////////////
#   verificar si es un operador y darle la clave hash
# ///////////////////////////////////////////////////////
@app.route('/api/autenticar/operador', methods = ['POST'])
def autenticacion_operador_dar_clave():
    datos_usuario = request.json
    if not datos_usuario:
        print("**ERROR** No se encontraron datos/datos inválidos")
        return jsonify({
            "EXITO" : False,
            "MENSAJE" : 'No se encontraron datos/datos inválidos'
        }), 400
    if 'codigo_institucional' not in datos_usuario:
        print("**ERROR** No se encuentra el código institucional")
        return jsonify({
            "EXITO" : False,
            "MENSAJE" : 'No se encuentra el código institucional del ususario'
        }), 400
    
    codigo_institucional = datos_usuario.get('codigo_institucional')
    comprobacion_usuario = crear_token_operador(codigo_institucional)

    if comprobacion_usuario['EXITO']:
        return jsonify(comprobacion_usuario), 200
    else:
        codigo_http = 500 if 'Error interno' in comprobacion_usuario['MENSAJE'] else 400
        return jsonify(comprobacion_usuario), codigo_http
    
# ////////////////////////////////////////////////////////
#   verificar al usuario general y darle la clave hash
# ///////////////////////////////////////////////////////
@app.route('/api/autenticar/usuario/general', methods = ['POST'])
def autenticacion_usuario_dar_clave():
    datos_usuario = request.json
    if not datos_usuario:
        print("**ERROR** No se encontraron datos/datos inválidos")
        return jsonify({
            "EXITO" : False,
            "MENSAJE" : 'No se encontraron datos/datos inválidos'
        }), 400
    if 'correo_electronico' not in datos_usuario:
        print("**ERROR** No se encuentra el correo electrónico para contacto")
        return jsonify({
            "EXITO" : False,
            "MENSAJE" : 'No se encuentra el correo electrónico para contacto'
        }), 400
    
    correo_electronico = datos_usuario.get('correo_electronico')
    nombre_usuario = datos_usuario.get('complete_name')
    comprobacion_usuario = crear_token_usuario(correo_electronico, nombre_usuario)

    if comprobacion_usuario['EXITO']:
        return jsonify(comprobacion_usuario), 200
    else:
        codigo_http = 500 if 'Error interno' in comprobacion_usuario['MENSAJE'] else 400
        return jsonify(comprobacion_usuario), codigo_http

# //////////////////////////////////////////////////////
#   Iniciar sesion comprobando en la db de operadores
# /////////////////////////////////////////////////////
@app.route('/api/iniciar/sesion/operador', methods = ['POST'])
def iniciar_sesion_operador():
    datos_login_usuario = request.json
    if not datos_login_usuario:
        print("**ERROR** No se encontraron datos/datos inválidos")
        return jsonify({
            "EXITO" : False,
            "MENSAJE" : 'No se encontraron datos/datos inválidos'
        }), 400
    if 'codigo_institucional' and 'clave_ingresada' not in datos_login_usuario:
        print("**ERROR** No se ingresó el código institucional ni la clave")
        return jsonify({
            "EXITO" : False,
            "MENSAJE" : 'No se ingresó el código institucional y clave, favor de ingresarlo'
        }), 400
    
    codigo_institucional = datos_login_usuario.get('codigo_institucional')
    clave_usuario_app = datos_login_usuario.get('clave_ingresada')

    comprobacion_login = iniciar_sesion_operador_db(codigo_institucional, clave_usuario_app)

    if comprobacion_login['EXITO']:
        return jsonify(comprobacion_login), 200
    else:
        codigo_http = 401 if 'Clave incorrecta' in comprobacion_login['MENSAJE'] else 400
        return jsonify(comprobacion_login), codigo_http

# //////////////////////////////////////////////////////
#   Iniciar sesion comprobando en la db de usuarios
# /////////////////////////////////////////////////////
@app.route('/api/iniciar/sesion/usuario', methods = ['POST'])
def iniciar_sesion_usuario_general():
    datos_login_usuario = request.json
    if not datos_login_usuario:
        print("**ERROR** No se encontraron datos/datos inválidos")
        return jsonify({
            "EXITO" : False,
            "MENSAJE" : 'No se encontraron datos/datos inválidos'
        }), 400
    if 'correo_electronico' and 'clave_ingresada' not in datos_login_usuario:
        print("**ERROR** No se ingresó el correo electrónico ni la clave")
        return jsonify({
            "EXITO" : False,
            "MENSAJE" : 'No se ingresó el correo electrónico y la clave, favor de ingresarlo'
        }), 400
    
    correo_electronico = datos_login_usuario.get('correo_electronico')
    clave_usuario_app = datos_login_usuario.get('clave_ingresada')

    comprobacion_login = iniciar_sesion_usuario_db(correo_electronico, clave_usuario_app)

    if comprobacion_login['EXITO']:
        return jsonify(comprobacion_login), 200
    else:
        codigo_http = 401 if 'Clave incorrecta' in comprobacion_login['MENSAJE'] else 400
        return jsonify(comprobacion_login), codigo_http

#  //////////////////////////////////
#   Mapeo de la máquina solicitada
# //////////////////////////////////
MACHINES_STATUS_FUNCTION = {
    'TRITURADORA': obten_ultim_estado,
    'CALENTADORA': obten_ultim_estado_calentador
}

# /////////////////////////////////////////////////////////////
#   Endpoint para cuando la aplicación nos envía una petición
# /////////////////////////////////////////////////////////////
@app.route('/api/app/to/arduino', methods = ['POST'])
def enviarDatosToArduino():
    comando_arduino = request.json

    if not (comando_arduino and 'accion' in comando_arduino and 'maquina' in comando_arduino and 'codigo_institucional' in comando_arduino):
         # /////--Si al enviar los datos son inválidos/vacíos--\\\\\
        return jsonify({
            "Envío de datos" : False,
            "Mensaje" : "Comando inválido/Comando vacío"
        }), 400

    accion = comando_arduino.get('accion').upper()
    maquina = comando_arduino.get('maquina').upper()
    codigo_institucional = comando_arduino.get('codigo_institucional')

    # <<--SELECCIÓN DE LA FUNCIÓN DE ESTADO-->>
    obtener_estado_funcion = MACHINES_STATUS_FUNCTION.get(maquina)
    # <<--MANEJO DE ERRORES SI NO RECONOCE LA MAQUINA-->>
    if not obtener_estado_funcion:
        return jsonify({
            "EXITO": False,
            "Mensaje": f"**ERROR** Máquina '{maquina}' no reconocida. Máquinas válidas: {list(MACHINES_STATUS_FUNCTION.keys())}"
        }), 400

    if accion.upper() == 'START':

        # <<--Salida temprana si no hay usuario identificado-->>
        obtener_usuario_db = obtener_clave_hash_por_codigo(codigo_institucional)
        if not obtener_usuario_db['EXITO']:
            print(f"**ERROR** No se encontró algún usuario \n {obtener_usuario_db['MENSAJE']}")
            return jsonify({
                "EXITO": False, 
                "MENSAJE": obtener_usuario_db['MENSAJE']
            }), 401
        
        # <<--Salida temprana si el usuario no escribió una clave-->>
        clave_usuario = comando_arduino.get('clave_escrita')
        if not clave_usuario:
            print(f"**ERROR** No se escribió ninguna clave \n El comando 'START' necesita una clave escrita")
            return jsonify({
                "EXITO": False, 
                "MENSAJE": '**ERROR** No se escribió ninguna clave \n El comando "START" necesita una clave escrita'
            }), 401

        clave_hash_db = obtener_usuario_db.get('clave_hash')

        comprobar_operador = verificar_clave_solo_logica(clave_usuario, clave_hash_db)

        # <<--Salida temprana si no se encontró al operador-->>
        if not comprobar_operador:
            print(f"**ERROR** Operador no identificado, inténtelo de nuevo")
            return jsonify ({
                "EXITO" : False,
                "Mensaje" : '**ERROR** Operador no identificado, inténntelo de nuevo'
            })

        ultimo_estado = obtener_estado_funcion()
        # <<--Comprobar el estado de la máquina-->>
        if ultimo_estado and ultimo_estado.get('temperatura', 0.0) >= 50.0:
            ultima_temperatura = ultimo_estado.get('temperatura')
            print(f"**ERROR CRITICO** \n La temperatura supera los 50.0°C = {ultima_temperatura}°C")
            return jsonify({
                "EXITO" : False,
                "Mensaje" : '**ERROR CRITICO** La temperatura supera los 50.0°C',
                "Temperatura" : ultima_temperatura,
                "Comando" : f"{accion} INVALIDO",
                "Maquina" : maquina
            }), 400
            
        return jsonify({
            "EXITO" : True,
            "Mensaje" : '**EXITO** Operador identificado y comando enviado a la máquina',
            "Maquina" : maquina,
            "Comando" : accion
        })
        
    # Mensaje que enviará la app
    mensaje_serial_arduino = f"{accion.upper()} para {maquina.upper()}"

    # <<<<--Manejo de errores en serial-->>>>
    """try:
        with serial.Serial(PUERTO_SERIAL, CANT_BAUTIOS, timeout=2) as ser: # ser: palabra clave para serial
            ser.write(mensaje_serial_arduino.encode('utf-8')) # .write : función de envío
            # .encode('utf-8'): convertir el mensaje string a byte para enviarlos
            print(f"***ENVÍO DE DATOS EXITOSO*** {mensaje_serial_arduino.strip}")

            return jsonify({
                    "Recepción de datos" : True,
                    "Comando"  : accion,
                    "Maquina" : maquina
            }), 200
            
        # <<<<--Manejo de errores-->>>>
    except serial.SerialException as error:
        #Mensaje del error
        print(f"***ERROR CRÍTICO*** {error} **FALLA PUERTO** : {PUERTO_SERIAL}")

        return jsonify({
            "Recepción de datos" : False,
            "Error" : f"{error}",
            "Mensaje" : f"No se logró enviar datos a la máquina. ***ERROR PUERTO*** : {PUERTO_SERIAL}"
        }), 500"""
    

# //////////////////
#   Ejecutar app
#//////////////////
if __name__ == '__main__':
    app.run(debug=True)