from machine import SoftI2C, Pin
import machine
import time

#Pines de botones
ping = machine.Pin(33, machine.Pin.IN, machine.Pin.PULL_DOWN)
pinr = machine.Pin(32, machine.Pin.IN, machine.Pin.PULL_DOWN)
pinf = machine.Pin(14, machine.Pin.IN, machine.Pin.PULL_DOWN)
# Configura el bus I2C
i2c = SoftI2C(scl=machine.Pin(22), sda=machine.Pin(21))
addr = 0x51  # Dirección I2C de la EEPROM
addr_rtc = 0x68 # Dirección I2C de la RTC

address = None
posision = 0x00
x=0

i2c.readfrom(addr, 1)  # Intentar leer un byte
address = addr

if address is None:
    print("No se pudo encontrar el dispositivo 24LC256 en ninguna de las direcciones.")
else:
    print("Dispositivo 24LC256 esta conectado")

def lecturartc(timer):
    global datos, cantidad
    time_data = i2c.readfrom_mem(addr_rtc, 0, 7)
    second = ((time_data[0] >> 4) * 10 + (time_data[0] & 0x0F))
    minute = ((time_data[1] >> 4) * 10 + (time_data[1] & 0x0F))
    hour = ((time_data[2] >> 4) * 10 + (time_data[2] & 0x0F))
    day = time_data[3]  # Elimina esta línea para quitar la parte del día
    date = ((time_data[4] >> 4) * 10 + (time_data[4] & 0x0F))
    month = ((time_data[5] >> 4) * 10 + (time_data[5] & 0x0F))
    year = ((time_data[6] >> 4) * 10 + (time_data[6] & 0x0F)) + 2000
    if day==1:
        d="L"
    elif day==2:
        d="M"
    elif day==3:
        d="W"
    elif day==4:
        d="J"
    elif day==5:
        d="V"
    elif day==6:
        d="S"
    elif day==7:
        d="D"
    datas=("{}/{}/{} {}:{}:{} {}".format(date, month, year, hour, minute, second,d))
    datos=datas
    cantidad= len(datas)
    #print(data)
tim=machine.Timer(-1)
tim.init(period=1000,mode=machine.Timer.PERIODIC, callback=lecturartc)

def guardado(ping):
    global datos, addr, cantidad,posision,x
    if x==0:
        i2c.writeto_mem(addr, posision, datos,addrsize=16)
        print("Escrito")
        x=1
        if x==1:
            posision += cantidad
            x=0
# Configura la interrupción en el pin y asocia la función de interrupción
ping.irq(trigger=machine.Pin.IRQ_RISING, handler=guardado)

def read_until_ff():
    eeprom_data = bytearray()  # Crear un arreglo para almacenar los datos de la EEPROM

    # Leer datos hasta encontrar 0xFF (255)
    for address in range(256):
        data = i2c.readfrom_mem(addr, address, 1,addrsize=16)[0]
        if data == 0xFF:
              # Si encuentra 0xFF, detener la lectura
            break
        eeprom_data.append(data)
    if not eeprom_data:
       print("No hay datos")
    return eeprom_data

def lectura(pinr):
    data_ff = read_until_ff()

    # Convertir bytearray a cadena de texto
    data_string = data_ff.decode('utf-8')

    # Dividir los datos en una lista usando 'M' como separador
    data_list = data_string.split('M')

    # Filtrar los elementos vacíos de la lista
    data_list = list(filter(None, data_list))

    # Ordenar la lista de fechas y horas
    data_list.sort()

    # Iterar sobre los datos y mostrarlos en dos líneas con 'M'
    dia = 'M'
    for i in range(0, len(data_list), 2):
        print(data_list[i] + (dia if i < len(data_list) - 1 else ''))
        if i + 1 < len(data_list):
            print(data_list[i + 1] + (dia if i + 2 < len(data_list) else '')

# Configura la interrupción en el pin y asocia la función de interrupción
pinr.irq(trigger=machine.Pin.IRQ_RISING, handler=lectura)

def formateo(pinf):
    for i in range(640):
        addr = hex(i)
        i2c.writeto_mem(0x51, i, b'\xff', addrsize=16)

    data_memory = i2c.readfrom_mem(0x51, 0x00, 32, addrsize=16)
    print("\nDatos I2C después de la escritura:")
    for byte in data_memory:
        print(hex(byte), end=" ")
    print("Formateo")
pinf.irq(trigger=machine.Pin.IRQ_RISING, handler=formateo)
while True:
    pass
