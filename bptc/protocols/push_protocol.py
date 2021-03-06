from datetime import datetime
import zlib
from math import ceil
from twisted.internet import protocol
import bptc

"""The push protocol is used between two clients for pushing events."""


class PushServerFactory(protocol.ServerFactory):

    def __init__(self, receive_data_string_callback, allow_reset_signal=False, network=None):
        self.receive_data_string_callback = receive_data_string_callback
        self.allow_reset_signal = allow_reset_signal
        self.protocol = PushServer
        self.received_data = b""
        self.network = network


class PushServer(protocol.Protocol):
    """The push server handles the pushes of a push client."""

    def connectionMade(self):
        # Don't call transport.write at this point - all received data might be gone
        pass

    def dataReceived(self, data):
        if data[:3] == b'GET':
            if self.factory.allow_reset_signal and data[4:11] == b'/?reset':
                self.transport.write('Resetting the local hashgraph!'.encode('UTF-8'))
                bptc.logger.warn('Deleting local database containing the hashgraph')
                self.network.reset()
            else:
                self.transport.write('I\'m alive!'.encode('UTF-8'))
            self.transport.loseConnection()
            return
        self.factory.received_data += data

    def connectionLost(self, reason):
        if len(self.factory.received_data) == 0:
            bptc.logger.warn('No data received!')
            return
        try:
            # data = zlib.decompress(self.factory.received_data)
            data = self.factory.received_data
            self.factory.receive_data_string_callback(data.decode('UTF-8'), self.transport.getPeer())
        except zlib.error as err:
            bptc.logger.error(
                'Failed parsing input: {}... [length={}] \n\n Error message: {}'.format(
                    self.factory.received_data[:100], len(self.factory.received_data), err))
        finally:
            self.factory.received_data = b""


class PushClientFactory(protocol.ClientFactory):

    def __init__(self, string_to_send, network=None, receiver=None):
        self.string_to_send = string_to_send
        self.protocol = PushClient
        self.network = network
        self.receiver = receiver

    def clientConnectionLost(self, connector, reason):
        # Ignore failed connections because we expect this to happen
        if reason.getErrorMessage() != 'Connection was closed cleanly.':
            bptc.logger.error("Connection lost: {}".format(reason.getErrorMessage()))
        pass

    def clientConnectionFailed(self, connector, reason):
        # Count how often a connection to someone failed
        if self.receiver:
            self.receiver.push_fail_count += 1
            if self.receiver.push_fail_count >= 3:
                self.receiver.address = None
                bptc.logger.debug("Forgot address of {} after three failed attempts".format(self.receiver))


class PushClient(protocol.Protocol):
    """The push client pushes to a push server."""

    def connectionMade(self):
        # data_to_send = zlib.compress(self.factory.string_to_send)
        data_to_send = self.factory.string_to_send
        for i in range(1, (ceil(len(data_to_send) / 65536)) + 1):
            self.transport.write(data_to_send[(i-1) * 65536:min(i*65536, len(data_to_send))])
        self.transport.loseConnection()

        if self.factory.network:
            self.factory.network.last_push_sent = datetime.now().isoformat()

    def connectionLost(self, reason):
        pass
