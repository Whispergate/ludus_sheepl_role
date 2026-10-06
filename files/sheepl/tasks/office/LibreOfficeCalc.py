
# #######################################################################
#
#  Task : LibreOfficeCalc Interaction
#
# #######################################################################


"""
 Creates the autoIT stub code to be passed into the master compile

 Drives LibreOffice Calc to enter rows of data into a spreadsheet and save
 it. LibreOffice is cross-platform; as Sheepl emits AutoIT the generated
 automation drives Calc on a Windows endpoint (soffice.exe via App Paths).

 Data entry mirrors how a person fills a sheet : each cell value is typed
 and followed by Tab to move right; at the end of a row Enter returns the
 cursor to the first column of the next row (Calc tracks the Tab origin).

 Note on escaping:
    Cell values and the save path are delivered with Send(), so all are
    passed through escape_autoit_send().

"""

__author__ = "Lavender-exe"
__license__ = "MIT"


import cmd
import sys
import textwrap
from pathlib import Path

from utils.base.base_cmd_class import BaseCMD
from utils import primitives as P


class LibreOfficeCalc(BaseCMD):

    """
    Inherits from BaseCMD
        This parent class contains:
        : do_back               > return to main menu
        : do_discard            > discard current task
        : complete_task()       > completes the task and resets trackers
        : check_task_started    > checks to see task status
    """

    def __init__(self, csh, cl):

        # Calling super to inherit from the BaseCMD Class __init__
        super(LibreOfficeCalc, self).__init__(csh, cl)

        # Override the defined task name
        self.taskname = 'LibreOfficeCalc'

        self.csh = csh
        # current colour object
        self.cl = cl

        # Overrides Base Class Prompt Setup
        if csh.creating_subtasks == True:
            print("[^] creating subtasks >>>>>>>>")
            self.baseprompt = cl.yellow('[>] Creating subtask\n{} > libreofficecalc >: '.format(csh.name.lower()))
        else:
            self.baseprompt = cl.yellow('{} > libreofficecalc >: '.format(csh.name.lower()))

        self.prompt = self.baseprompt

        # creating my own
        self.introduction = """
        ----------------------------------
        [!] LibreOfficeCalc Interaction.
        Type help or ? to list commands.
        ----------------------------------
        1: Start a new spreadsheet using 'new'
        2: Add a row with 'row <comma,separated,values>'
        3: Or load rows from a CSV with 'row_file <path>'
        4: Complete the spreadsheet using 'complete'
        """

        self.indent_space = '    '

        # ----------------------------------- >
        #      Task Specific Variables
        # ----------------------------------- >

        self.save_name = ""
        # list of rows, each row is a list of cell values
        self.rows = []

        # ----------------------------------- >
        # now call the loop if we are in interactive mode by checking
        # if we are parsing JSON

        if not self.csh.json_parsing:
            # call the intro and then start the loop
            print(textwrap.dedent(self.introduction))
            self.cmdloop()


    #######################################################################
    # LibreOfficeCalc Console Commands
    #######################################################################


    def do_new(self, arg):
        """
        This command creates a new LibreOffice Calc spreadsheet
        """
        if self.check_task_started() == False:
            print("[!] Starting : 'LibreOfficeCalc_{}'".format(str(self.csh.counter.current())))
            self.rows = []

            print("[?] Enter the name to save the spreadsheet (include .ods or .xlsx)")
            file_name = input(self.cl.yellow(">: "))
            print("[?] Enter the Windows path location for the save")
            save_path = input(self.cl.yellow(">: "))
            if not save_path.endswith("\\"):
                save_path = save_path + '\\'
            self.save_name = save_path + file_name

            print("[!] Saving the file as : {}".format(self.cl.red(self.save_name)))
            print()
            self.prompt = self.cl.blue("[*] Active Spreadsheet : " + self.save_name) + "\n" + self.baseprompt


    def do_row(self, row):
        """
        Adds a row of comma separated cell values
        <> Example : row Date,Host,Status
        """
        if self.taskstarted == False:
            print(self.cl.red("[!] <ERROR> You need to start a new LibreOfficeCalc Interaction."))
            print(self.cl.red("[!] <ERROR> Start this with 'new' from the menu."))
            return
        if row:
            cells = [cell.strip() for cell in row.split(',')]
            self.rows.append(cells)
            print("[+] Added row : {}".format(self.cl.green(str(cells))))


    def do_row_file(self, input_file):
        """
        Loads rows from a CSV file, one row per line
        """
        if self.taskstarted == False:
            print(self.cl.red("[!] <ERROR> You need to start a new LibreOfficeCalc Interaction."))
            print(self.cl.red("[!] <ERROR> Start this with 'new' from the menu."))
            return
        if input_file:
            try:
                with open(input_file) as f:
                    for line in f.readlines():
                        line = line.rstrip('\n')
                        if line:
                            self.rows.append([cell.strip() for cell in line.split(',')])
                print("[+] Loaded rows from : {}".format(self.cl.green(input_file)))
            except (IOError, OSError):
                print("[!] Error reading file : {}".format(self.cl.red(input_file)))


    def do_assigned(self, arg):
        """
        Shows the currently queued rows
        """
        print(self.cl.green("[?] Currently Queued Rows "))
        if self.rows:
            for index, row in enumerate(self.rows, 1):
                print("[>] {} : {}".format(index, row))
        else:
            print("[>] No rows currently assigned")


    def do_complete(self, arg):
        """
        This command assigns the save and close Calc functions
        """
        print("[!] Completing Task : {}".format(self.taskname))

        if self.taskstarted:
            if self.rows:
                self.create_autoIT_block()
            else:
                print("{} No rows have been added - use 'row <values>'".format(self.cl.red("[!]")))
                return None

        # now reset the tracking values and prompt
        self.complete_task()

        # reset state when new interaction
        self.save_name = ""
        self.rows = []


    #######################################################################
    #  LibreOfficeCalc AutoIT Block Definition
    #######################################################################

    def create_autoIT_block(self):
        """
        Creates the AutoIT Script Block
        """
        current_counter = str(self.csh.counter.current())
        self.csh.add_task('LibreOfficeCalc_' + current_counter, self.create_autoit_function())


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
        Expresses the LibreOffice Calc spreadsheet as OS-neutral primitives :
        launch Calc, enter the rows, save via the Save As dialog, quit. Data
        entry is neutral (type a cell + Tab across, Enter to the next row) so it
        renders on both the AutoIT and Linux backends.
        """

        prims = [
            P.Comment("Creates a LibreOffice Calc Spreadsheet : {}".format(self.save_name)),
            P.RunDialog("soffice --calc"),
            P.Comment("LibreOffice can be slow to start, so allow a generous wait"),
            P.Sleep(10000),
            P.Comment("LibreOffice windows use the SALFRAME class"),
            P.WaitWindow("[CLASS:SALFRAME]", 30),
            P.FocusWindow("[CLASS:SALFRAME]"),
            P.Comment("enter each row : type a cell then Tab, Enter to the next row"),
        ]
        for row in self.rows:
            for cell in row:
                prims.append(P.TypeText(str(cell)))
                prims.append(P.SendKeys("{TAB}"))
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
            P.Comment("close LibreOffice ; the spreadsheet is already saved"),
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
        print(f"[-] The following keys are needed for this task : {[x for x in list(kwargs.keys())[1:]]}")

        try:
            self.rows = kwargs["rows"]
            self.save_name = kwargs["save_name"]
        except KeyError as missing_key:
            print(self.cl.red("[!] Error Setting JSON Profile attributes : missing key {}".format(missing_key)))
            return

        print(f"[*] Setting the rows attribute : {self.rows}")
        print(f"[*] Setting the save filename attribute : {self.save_name}")

        self.create_autoIT_block()

