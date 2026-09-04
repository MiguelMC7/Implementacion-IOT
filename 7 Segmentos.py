import machine as mc
import time

segmentos = [
    mc.Pin(4, mc.Pin.OUT),
    mc.Pin(16, mc.Pin.OUT),
    mc.Pin(17, mc.Pin.OUT),
    mc.Pin(18, mc.Pin.OUT),
    mc.Pin(19, mc.Pin.OUT),
    mc.Pin(21, mc.Pin.OUT),
    mc.Pin(22, mc.Pin.OUT)]
led = mc.Pin(23, mc.Pin.OUT)
led1 = mc.Pin(32, mc.Pin.OUT)
bot_interrupt = mc.Pin(33, mc.Pin.IN, mc.Pin.PULL_UP)

def interrupcion(pin):
    global start, stop
    if stop:
        stop=False
        start=True
    else:
        stop=True
        start=False

bot_interrupt.irq(trigger=mc.Pin.IRQ_RISING, handler=interrupcion)
stop=False
start=True

def lectura(v):
    for i in range(7):
        segmentos[i].value((v >> i) & 0b0000001)

def datos():
    lectura(64)
    input()
    r = input("Digite a si es ascendente o d si es desendente: ")
    t=0
    if r=="a":
        led.on()
        led1.off()
        t=1
    elif r=="d":
        led1.on()
        led.off()
        t=2
    else:
        print ("Valor Incorrecto")
        return datos()

    x = input("Ingrese dato: " )
    d=0
    u=0
    z=0
    contador=0
    c=len(x)

    for i in x:
        if c==2:
            if z==0:
                d=int(i)
                z=z+1
            elif z==1:
                u=int(i)
        elif c==1:
            u=int(i)
        elif c>=3:
            print ("Error")
            return datos()

    contador = d*10+u

    while True:
        mc.idle()
        if not stop:
            if t==1:
                contador = contador+1
            elif t==2:
                contador = contador-1

        if contador>99:
            contador=0
            led.off()
            led1.off()
            return datos()
        elif contador<0:
            contador=0
            led.off()
            led1.off()
            return datos()
        if start:
            time.sleep(0.5)
            print(contador)
            dec = int(contador / 10)
            m = 0
        if dec == 0:
            m = 64
            lectura(m)
        elif dec == 1:
            m = 121
            lectura(m)
        elif dec == 2:
            m = 36
            lectura(m)
        elif dec == 3:
            m = 48
            lectura(m)
        elif dec == 4:
            m = 25
            lectura(m)
        elif dec == 5:
            m = 18
            lectura(m)
        elif dec == 6:
            m = 2
            lectura(m)
        elif dec == 7:
            m = 120
            lectura(m)
        elif dec == 8:
            m = 0
            lectura(m)
        elif dec == 9:
            m = 16
            lectura(m)
datos()
