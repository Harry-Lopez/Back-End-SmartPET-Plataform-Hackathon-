# Cliente MQTT para conectar el Backend de Flask con el Broker
# RESPONSABILIDAD: Crear y mantener la conexión MQTT, y manejar la recepción de datos del Arduino.

import paho.mqtt.client as mqtt
import json
import time

# IMPORTACIÓN DE LA LÓGICA DE BASE DE DATOS (Necesaria para guardar los datos recibidos)
# Asegúrate de que este import funciona correctamente si data_base.py está en el mismo nivel.
from data_base import guardar_new_status 


# =======================================================
#     CONFIGURACIÓN DEL BROKER Y TÓPICOS
# =======================================================

# Broker público de prueba. P2 puede cambiarlo si usa un broker local o uno más robusto.
BROKER_ADDRESS = "broker.hivemq.com" 
BROKER_PORT = 1883
QOS = 1 # Calidad de Servicio (Garantiza que el mensaje llega al menos una vez)

# Tópico para publicar comandos DESDE el Backend HACIA el Arduino (P1 -> P2)
TOPIC_PUB = "proyecto_maquina_p1_p2/comandos" 
# Tópico para suscribirse y recibir estado DESDE el Arduino HACIA el Backend (P2 -> P1)
TOPIC_SUB = "proyecto_maquina_p1_p2/estado" 

# =======================================================
#     CLIENTE MQTT Y CALLBACKS (Toda esta lógica es de P2)
# =======================================================

# Crea el cliente MQTT con un ID único basado en el tiempo
client = mqtt.Client(client_id=f'Backend-P1-{time.time()}')


def on_connect(client, userdata, flags, rc):
    """Callback que se llama al conectar con el broker."""
    if rc == 0:
        print(f"MQTT: Conexión exitosa al broker ({BROKER_ADDRESS}).")
        
        # Suscripción al tópico de estado: Aquí recibimos los datos que P2 manda del Arduino
        client.subscribe(TOPIC_SUB, qos=QOS)
        print(f"MQTT: Suscrito al tópico de recepción: {TOPIC_SUB}")
    else:
        print(f"MQTT: Error en la conexión. Código de retorno: {rc}")
        # Lógica de reconexión puede ir aquí si se requiere mayor robustez


def on_message(client, userdata, msg):
    """
    Callback que se llama cuando se recibe un mensaje. 
    ESTA FUNCIÓN REEMPLAZA AL ENDPOINT '/api/arduino/to/backend'
    """
    try:
        # 1. Decodificar y parsear el JSON
        payload_str = msg.payload.decode('utf-8')
        datos_recibidos = json.loads(payload_str)
        
        print(f"\nMQTT: Mensaje de ESTADO recibido en [{msg.topic}]: {datos_recibidos}")

        # 2. Guardar los datos en la DB (Lógica de P1)
        if guardar_new_status(datos_recibidos):
            print("DB: Estado guardado exitosamente en la base de datos.")
        else:
            print("DB: **ERROR** Al guardar los nuevos datos en la base de datos.")

    except json.JSONDecodeError:
        print(f"MQTT: Error decodificando JSON. Asegúrate de que el Arduino envía un JSON válido.")
    except Exception as e:
        print(f"MQTT: Error inesperado al procesar mensaje: {e}")


# Asignación de Callbacks al cliente
client.on_connect = on_connect
client.on_message = on_message


# =======================================================
#     FUNCIÓN DE PUBLICACIÓN (USADA POR P1 en app.py)
# =======================================================

def publish_command(topic: str, payload: str):
    """
    Publica un comando al broker. Utilizada por el endpoint de Flask (app.py).
    """
    try:
        # Publicación síncrona, espera el resultado antes de continuar
        result = client.publish(topic, payload, qos=QOS)
        # result.rc (return code): 0 es éxito
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
             print(f"MQTT: Publicación exitosa al tópico {topic}")
        else:
             print(f"MQTT: Error al publicar, código: {result.rc}")
        return result
    except Exception as e:
        print(f"MQTT: Excepción al intentar publicar: {e}")
        return None

# =======================================================
#     CONFIGURACIÓN INICIAL Y CONEXIÓN
# =======================================================
try:
    # La conexión debe intentarse una vez al inicio del módulo
    client.connect(BROKER_ADDRESS, BROKER_PORT)
except Exception as e:
    print(f"**ERROR CRÍTICO MQTT:** No se pudo conectar al broker {BROKER_ADDRESS}.")
    print(f"Excepción: {e}")
    
# NOTA: 'client.loop_start()' debe ser llamado en app.py para iniciar el hilo de escucha.

