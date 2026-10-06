
# #######################################################################
#
#  Task : LibreOfficeWriter Interaction
#
# #######################################################################


"""
 Creates the autoIT stub code to be passed into the master compile
 Takes a supplied text file for the Sheepl to type into a LibreOffice
 Writer document.

 This is the LibreOffice counterpart to the WordDocument task. LibreOffice
 is cross-platform, but as Sheepl emits AutoIT the generated automation
 drives LibreOffice Writer on a Windows endpoint (soffice.exe is launched
 via its App Paths registration).

 Note on escaping:
    The document text and the save path are delivered with Send(), so both
    are passed through escape_autoit_send() to stop characters such as
    ! + ^ # { } being interpreted as modifier keystrokes.

"""

__author__ = "Lavender-exe"
__license__ = "MIT"


import cmd
import sys
import textwrap
from pathlib import Path

from utils.base.base_cmd_class import BaseCMD
from utils import primitives as P


class LibreOfficeWriter(BaseCMD):
    """
    Inherits from BaseCMD
        This parent class contains:
        : do_back               > return to main menu
        : do_discard            > discard current task
        : do_complete           > completes the task and resets trackers
        : check_task_started    > checks to see task status
    """

    def __init__(self, csh, cl):

        # Calling super to inherit from the BaseCMD Class __init__
        super(LibreOfficeWriter, self).__init__(csh, cl)

        # Override the defined task name
        self.taskname = 'LibreOfficeWriter'

        self.csh = csh
        # current colour object
        self.cl = cl

        # Overrides Base Class Prompt Setup
        if csh.creating_subtasks == True:
            print("[^] creating subtasks >>>>>>>>")
            self.baseprompt = cl.yellow('[>] Creating subtask\n{} > libreofficewriter >: '.format(csh.name.lower()))
        else:
            self.baseprompt = cl.yellow('{} > libreofficewriter >: '.format(csh.name.lower()))

        self.prompt = self.baseprompt

        # creating my own
        self.introduction = """
        ----------------------------------
        [!] LibreOfficeWriter Interaction.
        Type help or ? to list commands.
        ----------------------------------
        1: Start a new document using 'new'
        2: Add content with 'input_file'
        3: Complete the document using 'complete'
        """

        self.indent_space = '    '

        # ----------------------------------- >
        #      Task Specific Variables
        # ----------------------------------- >

        self.save_name = ""
        self.input_file = None
        self.typing_block = ''

        # ----------------------------------- >
        # now call the loop if we are in interactive mode by checking
        # if we are parsing JSON

        if not self.csh.json_parsing:
            # call the intro and then start the loop
            print(textwrap.dedent(self.introduction))
            self.cmdloop()

    ########################################################################
    # LibreOfficeWriter Console Commands
    ########################################################################


    def do_new(self, arg):
        """
        This command creates a new LibreOffice Writer document
        """
        # method from parent class BaseCMD
        if self.check_task_started() == False:
            print("[!] Starting : 'LibreOfficeWriter_{}'".format(str(self.csh.counter.current())))

            # init typing block with an empty string when new is first called
            self.typing_block = ""

            print("[?] Enter the name to save the document (include .odt or .doc)")
            file_name = input(self.cl.yellow(">: "))
            print("[?] Enter the Windows path location for document save")
            save_path = input(self.cl.yellow(">: "))
            # need to escape the Windows backslash
            if not save_path.endswith("\\"):
                save_path = save_path + '\\'
            # set the taskname to the document path and name
            self.save_name = save_path + file_name

            print("[!] Saving the file as : {}".format(self.cl.red(self.save_name)))
            # OCD Line break
            print()
            self.prompt = self.cl.blue("[*] Active Document : " + self.save_name) + "\n" + self.baseprompt


    def do_input_file(self, inputf):
        """
        Specify the path to the input text file for typing
        < input_file /path/to/file >
        """
        try:
            if inputf:
                if self.taskstarted:
                    print("[+] Assigning '{}' for typing ".format(inputf))

                    # now open and read this file and append to the typing block
                    with open(inputf) as f:
                        self.typing_block += (f.read().strip())
                else:
                    print(self.cl.red("[!] <ERROR> You need to start a new LibreOfficeWriter Interaction."))
                    print(self.cl.red("[!] <ERROR> Start this with 'new' from the menu."))

            else:
                print(self.cl.red("[!] <ERROR> You need to supply the input file for typing"))
        except (IOError, OSError):
            print(self.cl.red("[!] <ERROR> Accessing input file"))


    def do_complete(self, arg):
        """
        This command assigns the save and close Writer functions
        """
        print("[!] Completing Task : {}".format(self.taskname))

        if self.taskstarted:
            if self.typing_block:
                self.create_autoIT_block()
            else:
                print("{} Nothing has been set to type into the document - set input_file".format(self.cl.red("[!]")))
                return None

        # now reset the tracking values and prompt
        self.complete_task()

        # reset various inputs when new interaction
        self.save_name = ""
        self.typing_block = ""


    #######################################################################
    #  LibreOfficeWriter AutoIT Block Definition
    #######################################################################

    def create_autoIT_block(self):
        """
        Creates the AutoIT Script Block
        """
        current_counter = str(self.csh.counter.current())
        self.csh.add_task('LibreOfficeWriter_' + current_counter, self.create_autoit_function())


    def create_autoit_function(self):
        """
        Builds the ordered primitive list for this task and hands it to the
        backend to render into the target automation language.
        """

        return self.csh.backend.render_task(
            self.taskname,
            self.csh.counter.current(),
            self.build_primitives(),
            emit_call=(not self.csh.creating_subtasks),
        )


    def build_primitives(self):
        """
        Expresses the LibreOffice Writer document as OS-neutral primitives :
        launch Writer, type the content line by line, save via the Save As
        dialog, quit. The typing is neutral (TypeText + Enter per line) so it
        renders on both the AutoIT and Linux backends.
        """

        prims = [
            P.Comment("Creates a LibreOffice Writer Document : {}".format(self.save_name)),
            P.RunDialog("soffice --writer"),
            P.Comment("LibreOffice can be slow to start, so allow a generous wait"),
            P.Sleep(10000),
            P.Comment("LibreOffice windows use the SALFRAME class"),
            P.WaitWindow("[CLASS:SALFRAME]", 30),
            P.FocusWindow("[CLASS:SALFRAME]"),
            P.Comment("type the document, a line at a time"),
        ]
        # type each source line and press Enter (a blank line is just an Enter)
        for line in self.typing_block.splitlines():
            prims.append(P.TypeText(line))
            prims.append(P.SendKeys("{ENTER}"))
        prims += [
            P.Comment("Reset the SendKeep Active before driving the dialogs"),
            P.ReleaseFocus(),
            P.Comment("open the Save As dialog"),
            P.SendKeys("^s"),
            P.WaitWindow("Save", 10),
            P.Comment("type the full save path and confirm"),
            P.TypeLine(self.save_name),
            P.Sleep(2000),
            P.Comment("accept the 'Use <format>' prompt if LibreOffice shows one"),
            P.SendKeys("{ENTER}"),
            P.Sleep(1000),
            P.Comment("close LibreOffice ; the document is already saved"),
            P.SendKeys("^q"),
        ]
        return prims


    def parse_json_profile(self, **kwargs):
        """
        Takes kwargs in and build out task variables when using JSON profiles
        this function sets the various object attributes in the same way
        that the interactive mode does
        """

        print("[%] Setting attributes from JSON Profile")
        # This snippet takes the keys ignoring the first key which is task and then shows
        # what should be set in the kwargs parsing.
        print(f"[-] The following keys are needed for this task : {[x for x in list(kwargs.keys())[1:]]}")

        try:
            self.input_file = kwargs["input_file"]
            self.save_name = kwargs["save_name"]
        except KeyError as missing_key:
            print(self.cl.red("[!] Error Setting JSON Profile attributes : missing key {}".format(missing_key)))
            return

        print(f"[*] Setting the input file attribute : {self.input_file}")
        print(f"[*] Setting the save filename attribute : {self.save_name}")

        # use a Path object so the file is validated before it is opened, rather
        # than crashing the whole run with an unhandled FileNotFoundError
        input_path = Path(self.input_file)
        if not input_path.is_file():
            print(self.cl.red("[!] Input file not found : {}".format(self.input_file)))
            print(self.cl.red("[!] Skipping LibreOfficeWriter task"))
            return

        self.typing_block += input_path.read_text().strip()

        # once these have all been set in here, then self.create_autoIT_block() gets called which pushes the task on the stack
        self.create_autoIT_block()

