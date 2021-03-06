import cmd
import os
import shlex
import sys
import textwrap

from mwr.common import system
from mwr.common.text import wrap

class Cmd(cmd.Cmd):
    """
    An extension to cmd.Cmd to provide some advanced functionality. Including:

    - aliases for commands;
    - bash-style special variables;
    - history file support;
    - output redirection to file; and
    - separate output and error streams.

    Also overwrite some of the default prompts, to make a more user-friendly
    output.
    """

    def __init__(self):
        cmd.Cmd.__init__(self)

        self.__output_redirected = None

        self.aliases = {}
        self.doc_header = "Commands:"
        self.doc_leader = wrap(textwrap.dedent(self.__class__.__doc__))
        self.history_file = None
        self.ruler = " "
        self.stdout = self.stdout
        self.stderr = sys.stderr

    def cmdloop(self, intro=None):
        """
        Repeatedly issue a prompt, accept input, parse an initial prefix
        off the received input, and dispatch to action methods, passing them
        the remainder of the line as argument.
        """

        self.preloop()
        if self.use_rawinput and self.completekey:
            try:
                import readline
                self.old_completer = readline.get_completer()
                readline.set_completer(self.complete)
                readline.set_completer_delims(readline.get_completer_delims().replace("/", ""))
                if self.history_file != None and os.path.exists(self.history_file):
                    readline.read_history_file(self.history_file)
                readline.parse_and_bind(self.completekey + ": complete")
            except ImportError:
                pass
        try:
            if intro is not None:
                self.intro = intro
            if self.intro:
                self.stdout.write(str(self.intro)+"\n")
            stop = None
            while not stop:
                if self.cmdqueue:
                    line = self.cmdqueue.pop(0)
                else:
                    if self.use_rawinput:
                        try:
                            line = raw_input(self.prompt)
                        except EOFError:
                            line = 'EOF'
                    else:
                        self.stdout.write(self.prompt)
                        self.stdout.flush()
                        line = self.stdin.readline()
                        if not len(line):
                            line = 'EOF'
                        else:
                            line = line.rstrip('\r\n')
                line = self.precmd(line)
                stop = self.onecmd(line)
                stop = self.postcmd(stop, line)
            self.postloop()
        finally:
            if self.use_rawinput and self.completekey:
                try:
                    import readline
                    if self.history_file != None:
                        readline.write_history_file(self.history_file)
                    readline.set_completer(self.old_completer)
                except ImportError:
                    pass

    def complete(self, text, state):
        """
        Return the next possible completion for 'text'.

        If a command has not been entered, then complete against command list.
        Otherwise try to call complete_<command> to get list of completions.
        """

        if state == 0:
            import readline
            origline = readline.get_line_buffer()
            line = origline.lstrip()
            stripped = len(origline) - len(line)
            begidx = readline.get_begidx() - stripped
            endidx = readline.get_endidx() - stripped

            if begidx > 0:
                if ">" in line and begidx > line.index(">"):
                    self.completion_matches = self.completefilename(text, line, begidx, endidx)

                    return self.completion_matches[0]
                    
                command = self.parseline(line)[0]
                if command == '':
                    compfunc = self.completedefault
                else:
                    try:
                        compfunc = getattr(self, 'complete_' + command)
                    except AttributeError:
                        compfunc = self.completedefault
            else:
                compfunc = self.completenames
            self.completion_matches = compfunc(text, line, begidx, endidx)

        try:
            return self.completion_matches[state]
        except IndexError:
            return None

    def completefilename(self, text, line, begidx, endidx):
        """
        Placeholder for a filename autocompletion method, that is invoked by
        the runtime when providing an argument for output redirection.
        """

        pass

    def default(self, line):
        """
        Override the default handler (i.e., no command matched) so we can add
        support for aliases.
        """

        argv = shlex.split(line)

        if argv[0] in self.aliases:
            getattr(self, "do_" + self.aliases[argv[0]])(" ".join(argv[1:]))
        else:
            cmd.Cmd.default(self, line)

    def emptyline(self):
        """
        Replace the default emptyline handler, it makes more sense to do nothing
        than to repeat the last command.
        """

        pass

    def handleException(self, e):
        """
        Default exception handler, writes the message to stderr.
        """

        self.stderr.write("%s\n" % str(e))

    def postcmd(self, stop, line):
        """
        Remove output redirection when a command has finished executing.
        """

        if self.__output_redirected != None:
            tee = self.stdout
            self.stdout = self.__output_redirected

            self.__output_redirected = None

            del(tee)

        return stop

    def precmd(self, line):
        """
        Process a command before it executes: perform variable substitutions and
        set up any output redirection.
        """

        # perform Bash-style substitutions
        if line.find("!!") >= 0 or line.find("!$") >= 0 or line.find("!^") >= 0 or line.find("!*") >= 0:
            line = self.__do_substitutions(line)

        # perform output stream redirection (as in the `tee` command)
        if line.find(">") >= 0:
            line = self.__redirect_output(line)

        return line

    def __build_tee(self, console, destination):
        """
        Create a mwr.system.Tee object to be used by output redirection.
        """

        if destination[0] == ">":
            destination = destination[1:]
            mode = 'a'
        else:
            mode = 'w'

        return system.Tee(console, destination.strip(), mode)

    def __do_substitutions(self, line):
        """
        Perform substitution of Bash-style variables.
        """

        if self.lastcmd != "":
            argv = shlex.split(self.lastcmd)
                
            line = line.replace("!!", self.lastcmd)
            line = line.replace("!$", argv[-1])
            line = line.replace("!^", argv[1])
            line = line.replace("!*", " ".join(argv[1:]))

            return line
        else:
            self.stderr.write("no previous command\n")

            return ""

    def __redirect_output(self, line):
        """
        Set up output redirection, by building a Tee between stdout and the
        specified file.
        """

        (line, destination) = line.split(">", 1)

        if len(destination) > 0:
            self.__output_redirected = self.stdout
            self.stdout = self.__build_tee(self.stdout, destination)
        else:
            self.stderr.write("no redirection target specified\n")
            return ""

        return line
