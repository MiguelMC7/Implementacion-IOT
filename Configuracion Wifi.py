import network
import time
from umqtt.simple import MQTTClient
from machine import ADC, Pin, UART
import math

# Configuración para el ZMPT101B (Voltaje)
adc_voltaje_pin = ADC(Pin(34))  # Conectar a la salida del ZMPT101B
adc_voltaje_pin.atten(ADC.ATTN_11DB)  # Atenuación para leer señales de hasta 3.3V
adc_voltaje_pin.width(ADC.WIDTH_12BIT)  # Resolución de 12 bits

# Configuración para el ACS712 (Corriente)
adc_corriente_pin = ADC(Pin(35))  # Conectar a la salida del ACS712
adc_corriente_pin.atten(ADC.ATTN_11DB)  # Atenuación para leer señales de hasta 3.3V
adc_corriente_pin.width(ADC.WIDTH_12BIT)  # Resolución de 12 bits

# Parámetros del ZMPT101B
num_muestras = 1000  # Número de muestras a tomar
vref = 3.3  # Voltaje de referencia
conversion_factor_voltaje = vref / 4095  # Factor de conversión a voltaje

# Parámetros del ACS712
SENSITIVITY = 0.185  # Sensibilidad del ACS712 (en V/A), ajusta según el modelo

def conectar_wifi():
    ssid = "FAMI MORENO"
    password = "23071714"
    
    wifi = network.WLAN(network.STA_IF)
    wifi.active(True)
    wifi.connect(ssid, password)
    
    print("Conectando a Wi-Fi...")
    while not wifi.isconnected():
        time.sleep(1)
    print("Conectado a Wi-Fi. IP:", wifi.ifconfig()[0])

def conectar_mqtt():
    broker_ip = "broker.hivemq.com"
    broker_port = 1883
    topic_pub = "datos/esp32"
    cliente = MQTTClient("ESP32", broker_ip, port=broker_port)

    while True:
        try:
            cliente.connect()
            print("Conectado al broker MQTT")
            return cliente  # Conexión exitosa, retornar el cliente
        except Exception as e:
            print("No se pudo conectar al broker:", e)
            time.sleep(2)  # Espera 5 segundos antes de intentar nuevamente

# Configurar Wi-Fi y conectar al broker
conectar_wifi()
cliente = conectar_mqtt()

# Calibración del ACS712: medir el voltaje en reposo
def calibrate_offset(samples=1000):
    total_voltage = 0
    for _ in range(samples):
        adc_value = adc_corriente_pin.read()
        voltage = adc_value * (vref / 4095.0)
        total_voltage += voltage
        time.sleep(0.001)  # Retardo para cada muestra (1 ms)
    
    offset_voltage = total_voltage / samples
    return offset_voltage

# Función para calcular el voltaje RMS utilizando ZMPT101B
def leer_zmpt101b():
    muestras = []
   
    for _ in range(num_muestras):
        valor = adc_voltaje_pin.read()
        muestras.append(valor)
        time.sleep(0.001)  # Esperar 1 ms entre cada muestra
   
    promedio = sum(muestras) / num_muestras
    suma_cuadrados = 0
    for muestra in muestras:
        valor_ac = muestra - promedio  # Restar el offset DC
        suma_cuadrados += valor_ac ** 2
   
    rms = math.sqrt(suma_cuadrados / num_muestras)
    voltaje_ac = rms * conversion_factor_voltaje
    return voltaje_ac

# Función para calcular la corriente RMS utilizando ACS712
def calculate_current_rms(offset_voltage, samples=1000):
    sum_of_squares = 0
    for _ in range(samples):
        adc_value = adc_corriente_pin.read()
        voltage = adc_value * (vref / 4095.0)  # Convertir el valor ADC a voltaje
        current = (voltage - offset_voltage) / SENSITIVITY  # Restar el offset y convertir voltaje a corriente
        sum_of_squares += current ** 2
        time.sleep(0.001)  # Retardo para la lectura de cada muestra (1 ms)
    
    rms_current = math.sqrt(sum_of_squares / samples)
    return rms_current
# Calibrar el sensor ACS712
offset_voltage = calibrate_offset()
# Enviar datos indefinidamente
while True:
    try:
        # Medir voltaje con ZMPT101B
        #voltaje_ac = (leer_zmpt101b() * 1000) / 2  # Convertir a voltaje (mV)
        voltaje_ac = 109
        if voltaje_ac < 25:
            voltaje_ac = 0
        else:
            voltaje_ac += 11  # Ajuste según el cálculo previo

        # Medir corriente con ACS712
        current_rms = (calculate_current_rms(offset_voltage)*1000)
        #current_rms = 450
        if current_rms < 150:
            current_rms -= 90
            if current_rms < 0:
                current_rms = 0
        elif current_rms > 250:
            current_rms += 300

        # Enviar los datos por serial
        data = "{:.2f},{:.2f}\n".format(voltaje_ac, current_rms)
        
        mensaje = data
        cliente.publish("datos/esp32", mensaje)
        print("Mensaje enviado:", mensaje)
        time.sleep(1)
    except Exception as e:
        print("Error al publicar:", e)
        client.disconnect()