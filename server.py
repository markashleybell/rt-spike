import sys
import json

from twisted.python import log
from twisted.internet import reactor
from autobahn.twisted.websocket import WebSocketServerProtocol, \
                                       WebSocketServerFactory


class BroadcastServerFactory(WebSocketServerFactory):
    """
    Simple broadcast server broadcasting any message it receives to all
    currently connected clients.
    """

    def __init__(self, url, debug = False, debugCodePaths = False):
        WebSocketServerFactory.__init__(self, url, debug = debug, debugCodePaths = debugCodePaths)
        self.clients = []

    def register(self, client):
        if not client in self.clients:
            print("Registered client {0}".format(client.peer))
            self.clients.append(client)

    def unregister(self, client):
        if client in self.clients:
            print("Unregistered client {0}".format(client.peer))
            self.clients.remove(client)

    def broadcast(self, msg):
        for client in self.clients:
            client.sendMessage(msg.encode('utf8'))
            print("Message sent to {0}".format(client.peer))


class MyServerProtocol(WebSocketServerProtocol):

    def onConnect(self, request):
        print("Client connecting: {0}".format(request.peer))

    def onOpen(self):
        print("WebSocket connection open")
        self.factory.register(self)

    def onMessage(self, payload, isBinary):
        if isBinary:
            print("Binary message received: {0} bytes".format(len(payload)))
            self.factory.broadcast(json.dumps({ "message": "Received binary message: {0} bytes".format(len(payload)) }))
        else:
            print("Text message received: {0}".format(payload.decode('utf8')))
            # Parse the JSON we were sent
            message = json.loads(payload.decode('utf8'));
            ## Send the JSON back to the clients
            ## self.sendMessage(json.dumps(response), isBinary)
            self.factory.broadcast(json.dumps(message))

    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))
        self.factory.unregister(self)

    def connectionLost(self, reason):
        print("WebSocket connection lost: {0}".format(reason))
        WebSocketServerProtocol.connectionLost(self, reason)
        self.factory.unregister(self)


if __name__ == '__main__':

    log.startLogging(sys.stdout)

    host = "localhost"
    port = 8001

    factory = BroadcastServerFactory("ws://{0}:{1}".format(host, port), debug=False)
    factory.protocol = MyServerProtocol

    reactor.listenTCP(port, factory)
    reactor.run()
