from machine import ADC, Pin
import time
import math

# Configurar el pin ADC de la ESP32
adc_pin = ADC(Pin(34))  # Usa un pin ADC, por ejemplo, GPIO 34
adc_pin.atten(ADC.ATTN_11DB)  # Configurar la atenuación para medir el rango completo (0-3.3V)
adc_pin.width(ADC.WIDTH_12BIT)  # Resolución de 12 bits (0-4095)

# Parámetros del sensor ACS712
VREF = 3.3  # Voltaje de referencia (3.3V para la ESP32)
SENSITIVITY = 0.185  # Sensibilidad del ACS712 (en V/A), puede ser 0.185 para el modelo de 5A

# Calibración: medir el voltaje en reposo
def calibrate_offset(samples=1000):
    total_voltage = 0
    for _ in range(samples):
        adc_value = adc_pin.read()
        voltage = adc_value * (VREF / 4095.0)
        total_voltage += voltage
        time.sleep(0.001)  # Retardo para cada muestra (1 ms)
    
    offset_voltage = total_voltage / samples
    return offset_voltage

# Función para calcular la corriente RMS
def calculate_current_rms(offset_voltage, samples=1000):
    sum_of_squares = 0
    for _ in range(samples):
        adc_value = adc_pin.read()
        voltage = adc_value * (VREF / 4095.0)  # Convertir el valor ADC a voltaje
        current = (voltage - offset_voltage) / SENSITIVITY  # Restar el offset y convertir voltaje a corriente
        sum_of_squares += current ** 2
        time.sleep(0.001)  # Retardo para la lectura de cada muestra (1 ms)
    
    # Calcular RMS
    rms_current = math.sqrt(sum_of_squares / samples)
    return rms_current

# Calibrar el sensor para obtener el voltaje en reposo
offset_voltage = calibrate_offset()
print("Voltaje de offset (reposo): {:.3f} V".format(offset_voltage))

# Crear o abrir archivo CSV para guardar datos
file = open("Datos.csv", "w")
file.write("Amperios\n")  # Encabezado de la tabla

try:
    while True:
        current_rms = calculate_current_rms(offset_voltage)
        print("Corriente RMS: {:.2f} A".format(current_rms))
        
        # Guardar el dato en el archivo CSV
        file.write("{:.2f}\n".format(current_rms))
        
        time.sleep(0.5)  # Leer y guardar cada segundo
finally:
    file.close()