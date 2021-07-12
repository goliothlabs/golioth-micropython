import network
import uasyncio
import ujson
import machine
import microcoapy
import usocket as socket
import ussl as ssl
from machine import Pin


class GoliothClient:

    observations = {}

    def __init__(self, host, port=5684, identity=None, psk=None):
        self.client = microcoapy.Coap()
        self.client.debug = False
        self.client.responseCallback = self.receivedMessageCallback
        self.host = host
        self.port = port
        self.dtlsSocket = DTLSSocket(
            address=host, port=port, identity=identity, psk=psk)
        self.client.setCustomSocket(self.dtlsSocket)

    def lightdb_set(self, path, value, content_format=microcoapy.COAP_CONTENT_FORMAT.COAP_TEXT_PLAIN):
        messageId = self.client.post(self.host, self.port, '.d/' + path, value,
                                     None, content_format)
        print("[LIGHTDB SET] Message Id: ", messageId)

    def lightdb_get(self, path):
        messageId = self.client.get(self.host, self.port, '.d/' + path)
        print("[LIGHTDB GET] Message Id: ", messageId)

    def lightdb_observe(self, path):
        full_path = '.d/' + path
        messageId = self.client.get(
            self.host, self.port, full_path, observe_option=0)
        print("[LIGHTDB OBSERVE] Message Id: ", messageId)
        self.observations[messageId] = full_path

    async def keepalive_task(self, pingPeriodMs=10_000):
        while True:
            self.client.ping(self.host, self.port)
            await uasyncio.sleep_ms(pingPeriodMs)

    async def poll_task(self, pollPeriodMs=500):
        while True:
            self.client.loop(False)
            await uasyncio.sleep_ms(pollPeriodMs)

    def receivedMessageCallback(self, packet, sender):
        if len(packet.payload) == 0:
            return

        if packet.payload == b'OK':
            return

        payloads = packet.payload.split(b'`')
        for payload in payloads:
            self.onMessage(packet, payload, sender)


################################################################################
# DTLS socket implementation
class DTLSSocket:
    def __init__(self, address, port, identity=None, psk=None):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', port))
        ai = socket.getaddrinfo(address, port)
        addr = ai[0][-1]
        self.addr = addr
        self.identity = identity
        self.psk = psk
        self.connect()

    def connect(self):
        self.sock.connect(self.addr)
        self.ssock = ssl.wrap_socket(
            self.sock, identity=self.identity, pre_shared_key=self.psk)

    def sendto(self, bytes, address):
        return self.ssock.write(bytes)

    def recvfrom(self, bufsize):
        data = self.ssock.read(bufsize)
        return (data, self.addr)

    def setblocking(self, flag):
        self.ssock.setblocking(flag)
################################################################################


wlan = network.WLAN(network.STA_IF)
wlan.active(True)

_MY_SSID = 'FullStackIoT'
_MY_PASS = 'FullStackIoT'
_SERVER_IP = '192.168.86.32'


def connectToWiFi():
    nets = wlan.scan()
    for net in nets:
        ssid = net[0].decode("utf-8")
        if ssid == _MY_SSID:
            print('Network found!')
            wlan.connect(ssid, _MY_PASS)
            while not wlan.isconnected():
                machine.idle()  # save power while waiting
            print('WLAN connection succeeded!')
            break

    return wlan.isconnected()


led0 = Pin(5, Pin.OUT)
led1 = Pin(18, Pin.OUT)
led2 = Pin(23, Pin.OUT)
led3 = Pin(19, Pin.OUT)
leds = [led0, led1, led2, led3]
for led in leds:
    led.on()


async def update_counter(client):
    counter = 0
    while True:
        client.lightdb_set('counter', str(counter))
        counter += 1
        await uasyncio.sleep_ms(5000)


def onMessage(packet, payload, sender):
    print('Message received:', packet.toString(), ', from: ', sender)
    try:
        msg = ujson.loads(payload)
        i = 0
        for index in ['0', '1', '2', '3']:
            if index in msg:
                state = msg[index]
                if state:
                    leds[i].off()
                else:
                    leds[i].on()
            i += 1
    except:
        print("bad msg", payload)


async def main(client):
    print("main running")
    client.lightdb_observe("led")
    uasyncio.create_task(update_counter(client))
    uasyncio.create_task(client.keepalive_task())
    uasyncio.create_task(client.poll_task())
    print("main tasks created")
    while True:
        await uasyncio.sleep_ms(100)


connectToWiFi()

client = GoliothClient(
    host=_SERVER_IP, identity="super-id", psk="anothersecret")
client.onMessage = onMessage

uasyncio.run(main(client))
