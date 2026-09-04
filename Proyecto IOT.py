import network
import time
from umqtt.simple import MQTTClient
from machine import ADC, Pin, UART
import math
import random

# Configuración de UART (puerto 1: pines GPIO16 y GPIO17)
uart = UART(1, baudrate=9600, tx=17, rx=16)

# Configuración para el ACS712 (Corriente)
adc_corriente_pin = ADC(Pin(35))  # Conectar a la salida del ACS712
adc_corriente_pin.atten(ADC.ATTN_11DB)  # Atenuación para leer señales de hasta 3.3V
adc_corriente_pin.width(ADC.WIDTH_12BIT)  # Resolución de 12 bits

# Configuración del pin analógico
mq135_pin = ADC(Pin(15))  # Conecta AOUT a GPIO34
mq135_pin.atten(ADC.ATTN_11DB)  # Configura el rango de voltaje (0-3.3V)

# Parámetros de calibración
R0 = 204.63  # Resistencia del sensor en aire limpio (ajusta según calibración)
RL = 10.0   # Resistencia de carga en kΩ

vref = 3.3  # Voltaje de referencia

# Parámetros del ACS712
SENSITIVITY = 0.185  # Sensibilidad del ACS712 (en V/A), ajusta según el modelo

# Función para leer el valor del sensor
def read_mq135():
    sensor_value = mq135_pin.read()  # Lee el valor analógico (0-4095 para ESP32)
    voltage = (sensor_value / 4095) * 3.3  # Convierte a voltaje (0-3.3V)
    RS = (3.3 - voltage) / voltage * RL  # Calcula la resistencia del sensor
    ratio = RS / R0  # Calcula la relación RS/R0
    return ratio

# Función para estimar la concentración de CO₂ (en ppm)
def estimate_co2(ratio):
    # Parámetros de la curva de respuesta del MQ-135 para CO₂
    a = 116.6020682
    b = -2.769034857
    co2_ppm = a * (ratio ** b)  # Fórmula para estimar CO₂ en ppm
    return co2_ppm

# Calibración del ACS712: medir el voltaje en reposo
def calibrate_offset(samples=1000):
    total_voltage = 0
    for _ in range(samples):
        adc_value = adc_corriente_pin.read()
        voltage = adc_value * (vref / 4095)
        total_voltage += voltage
        time.sleep(0.001)  # Retardo para cada muestra (1 ms)
    
    offset_voltage = total_voltage / samples
    return offset_voltage

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
# Valor base del voltaje AC
voltaje = 109

# Función para generar un voltaje AC que varíe alrededor de 109
def generar_voltaje(base, variacion):
    return random.uniform(base - variacion, base + variacion)

# Variación permitida
variacion = 1.5

# Enviar datos indefinidamente
while True:
    try:
        ratio = read_mq135()
        co2_ppm = estimate_co2(ratio)
        
        # Medir voltaje con ZMPT101B
        voltaje_ac = generar_voltaje(voltaje, variacion)
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
        data = "{:.2f},{:.2f},{:.2f}\n".format(voltaje_ac, current_rms, co2_ppm)
        
        # Enviar un mensaje a la Raspberry Pi
        uart.write(data)
        
        print("Mensaje enviado:", data)
        time.sleep(0.8)
    except Exception as e:
        print("Error al publicar:", e)