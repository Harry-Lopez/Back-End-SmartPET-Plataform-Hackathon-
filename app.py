from data_base import config_DB, guardar_new_status, obten_ultim_estado
from flask import Flask, request, jsonify
import serial

config_DB()

# Flask() es la clase de python que crea el motor del servidor
# __name__ es la variable mágica que python da por defecto a un archivo py que se ejecuta
app = Flask(__name__)

PUERTO_SERIAL = 'COM99'
CANT_BAUTIOS = 9600

@app.route('/')
def pagina_principal():
    return "Prueba 3 de código básico Flask por P1"

@app.route('/api/arduino/to/backend', methods = ['POST'])
def enviarDatosToBackend():
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

@app.route('/api/status/get/backend', methods = ['GET'])
def obtener_status():
    ultimo_estado = obten_ultim_estado()
    if ultimo_estado:
        return jsonify(ultimo_estado), 200
    
    return jsonify({
        "Exito" : False,
        "Mensaje" : "**ERROR** Al obtener los datos"
    }), 204

# /////////////////////////////////////////////////////////////
#   Endpoint para cuando la aplicación nos envía una petición
# /////////////////////////////////////////////////////////////
@app.route('/api/app/to/arduino', methods = ['POST'])
def enviarDatosToArduino():
    comando_arduino = request.json

    if not (comando_arduino and 'accion' in comando_arduino and 'maquina' in comando_arduino):
         # /////--Si al enviar los datos son inválidos/vacíos--\\\\\
        return jsonify({
            "Envío de datos" : False,
            "Mensaje" : "Comando inválido/Comando vacío"
        }), 400

    accion = comando_arduino.get('accion')
    maquina = comando_arduino.get('maquina')

    if accion.upper() == 'START':
        ultimo_estado = obten_ultim_estado()

        if ultimo_estado and ultimo_estado.get('temperatura', 0.0) >= 50.0:
            ultima_temperatura = ultimo_estado.get('temperatura')
            print(f"**ERROR CRITICO** \n La temperatura supera los 50.0°C = {ultima_temperatura}°C")
            return jsonify({
                "EXITO" : False,
                "Mensaje" : '**ERROR CRITICO** La temperatura supera los 50.0°C',
                "Temperatura" : ultima_temperatura,
                "Comando" : accion,
                "Maquina" : maquina
            }), 400
        
    # Mensaje que enviará la app
    mensaje_serial_arduino = f"{accion.upper()} para {maquina.upper()}"

    # <<<<--Manejo de errores en serial-->>>>
    try:
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
        }), 500
    

# //////////////////
#   Ejecutar app
#//////////////////
if __name__ == '__main__':
    app.run(debug=True)