from mwr.droidhg.console.coloured_stream import DecolouredStream

class Tee(object):
    """
    Implementation of the *nix Tee command, to direct an output stream at both
    the console and a file.

    Original Version by Luander <luander.r@samsung.com>
    """

    def __init__(self, console, name, mode='w'):
        self.console = console
        self.file = DecolouredStream(open(name, mode))

    def __del__(self):
        self.file.close()

    def write(self, data):
        """
        Wrapper around the #write command of the stream, that writes the stream
        to both the console and file, before flushing the filestream.
        """

        self.console.write(data)
        self.file.write(data)
        self.file.flush()
