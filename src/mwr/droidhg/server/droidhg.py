from logging import getLogger
from time import time

from mwr.common.twisted import StreamReceiver
from mwr.droidhg.api.frame import Frame
from mwr.droidhg.api.reflection_message import ReflectionRequestForwarder, ReflectionResponseForwarder
from mwr.droidhg.api.system_message import SystemRequestHandler, SystemResponseHandler
from mwr.droidhg.api.protobuf_pb2 import Message

class FrameReceiver(StreamReceiver):
    """
    The FrameReceiver reads streams created by a StreamReceiver, and reads any
    complete Frames from the stream.

    Once a frame is ready, it is passed to the frameReceived() method.
    """

    def connectionMade(self):
        """
        Called when a connection is made to the FrameReceiver, and passes the
        context back to the StreamReceiver.
        """

        StreamReceiver.connectionMade(self)

    def buildFrame(self):
        """
        Attempts to get a frame from the data in the stream.
        """

        frame = Frame.readFrom(self.stream)
        
        return frame

    def streamReceived(self):
        """
        Called whenever the StreamReceiver is updated. Attempts to read a Frame
        from the stream, and passes it to frameReceived if there is.
        """

        frame = self.buildFrame()

        if frame is not None:
            self.frameReceived(frame)


class DroidHG(FrameReceiver):
    """
    Implementation of the Mercury protocol, as a FrameReceiver.
    """
    
    __logger = getLogger(__name__ + '.droidhg')
    
    name = 'droidhg'
    
    def connectionMade(self):
        """
        Called whena a connection is made to the Mercury Server. It initialises
        the FrameReceiver, and then sets up the various message handlers and
        forwarders that we require.
        """

        FrameReceiver.connectionMade(self)

        self.request_forwarder = ReflectionRequestForwarder(self)
        self.request_handler = SystemRequestHandler(self)
        self.response_forwarder = ReflectionResponseForwarder(self)
        self.response_handler = SystemResponseHandler(self)
        
        self.device = None
    
    def close(self):
        """
        Closes the connection.
        """

        self.transport.loseConnection()
    
    def frameReceived(self, frame):
        """
        Called whenever a frame has been received.

        This extracts the message, and routes it appropriately to a callback
        function, or a request handler.

        If something sends a response, this is forwarded back to the client.
        """

        message = frame.message()
        response = None

        if self.device and self.device.hasCallback(message.id):
            response = self.device.callCallback(message.id, message)
        elif message.type == Message.REFLECTION_REQUEST:
            self.request_forwarder.handle(message)
        elif message.type == Message.REFLECTION_RESPONSE:
            self.response_forwarder.handle(message)
        elif message.type == Message.SYSTEM_REQUEST:
            response = self.request_handler.handle(message)
        elif message.type == Message.SYSTEM_RESPONSE:
            response = self.response_handler.handle(message)
        else:
            self.__logger.error("got unexpected message type " + message.type)
        
        if response is not None:
            self.write(response)
        
        if self.device is not None:
            self.device.last_message_at = time()
    
    def write(self, message):
        """
        Writes a message to a client, encapsulating it in a Frame first.
        """

        self.__write(Frame.fromMessage(message))
        
    def __write(self, frame):
        """
        Writes a message to a client.
        """
        
        self.transport.write(str(frame))
        