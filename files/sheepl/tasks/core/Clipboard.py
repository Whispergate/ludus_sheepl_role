
# #######################################################################
#
#  Task : Clipboard Interaction
#
# #######################################################################


"""
 Creates the autoIT stub code to be passed into the master compile

 Emulates a user copying a sequence of items (notes, passwords, snippets)
 to the Windows clipboard over the duration of the task using AutoIT's
 native ClipPut() function.

 Note on escaping:
    ClipPut() takes a literal string argument, NOT keystrokes, so only the
    double quote needs escaping (doubled to "") to avoid terminating the
    AutoIT string literal. The Send() style brace escaping of ! + ^ # { }
    must NOT be applied here, otherwise those characters would end up on the
    clipboard wrapped in braces.

"""

__author__ = "Lavender-exe"
__license__ = "MIT"


import cmd
import sys
import random
import textwrap

# Sheepl Class Imports
from utils.base.base_cmd_class import BaseCMD
from utils import primitives as P


class Clipboard(BaseCMD):

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
        super(Clipboard, self).__init__(csh, cl)

        # Override the defined task name
        self.taskname = 'Clipboard'

        # current Sheepl Object
        # which might need to be renamed to Sheepl
        self.csh = csh
        # current colour object
        self.cl = cl

        # Overrides Base Class Prompt Setup
        if csh.creating_subtasks == True:
            print("[^] creating subtasks >>>>>>>>")
            self.baseprompt = cl.yellow('[>] Creating subtask\n{} > clipboard >: '.format(csh.name.lower()))
        else:
            self.baseprompt = cl.yellow('{} > clipboard >: '.format(csh.name.lower()))

        self.prompt = self.baseprompt
        # track subtasks
        self.subtask = False

        # creating my own
        self.introduction = """
        ----------------------------------
        [!] Clipboard Interaction.
        Type help or ? to list commands.
        ----------------------------------
        1: Start a new block using 'new'
        2: Add items with 'clip <text>' (notes, passwords, snippets)
        3: Or load items from a file with 'clip_file <path>'
        4: Optionally wipe the clipboard afterwards with 'clear on'
        5: Complete the interaction using 'complete'
        """

        self.indent_space = '    '

        # ----------------------------------- >
        #      Task Specific Variables
        # ----------------------------------- >

        # List to hold the ordered clipboard items for this interaction
        self.items = []

        # whether to wipe the clipboard at the end so copied secrets do not linger
        self.clear_clipboard = False

        # ----------------------------------- >
        # now call the loop if we are in interactive mode by checking
        # if we are parsing JSON

        if not self.csh.json_parsing:
            # call the intro and then start the loop
            print(textwrap.dedent(self.introduction))
            self.cmdloop()


    #######################################################################
    #  Clipboard Console Commands
    #######################################################################


    def do_new(self, arg):
        """
        This command creates a new Clipboard interaction
        """
        # Init tracking booleans
        # method from parent class BaseCMD
        if self.check_task_started() == False:
            print("[!] Starting : 'Clipboard_{}'".format(str(self.csh.counter.current())))
            # OCD Line break
            print()
            self.prompt = self.cl.blue("[*] Current Task : Clipboard_{}".format(str(self.csh.counter.current()))) + "\n" + self.baseprompt


    def do_clip(self, item):
        """
        Adds an item to the clipboard sequence. This can be a note, a
        password, a snippet of text, anything the user would copy.
        <> Example : clip P@ssw0rd123
        """
        if item:
            if self.taskstarted == True:
                self.items.append(item)
                # avoid echoing the full value in case it is a secret
                print("[+] Stored clipboard item ({} chars)".format(len(item)))
            else:
                if self.taskstarted == False:
                    print(self.cl.red("[!] <ERROR> You need to start a new Clipboard Interaction."))
                    print(self.cl.red("[!] <ERROR> Start this with 'new' from the menu."))
                print("[!] <ERROR> You need to supply the item to store on the clipboard")


    def do_clip_file(self, input_file):
        """
        Takes an input file and stores each line as a separate clipboard item
        expect one item per line
        """
        if input_file:
            if self.taskstarted == True:
                try:
                    with open(input_file) as item_file:
                        for item in item_file.readlines():
                            self.items.append(item.rstrip('\n'))
                    print("[+] Loaded clipboard items from : {}".format(self.cl.green(input_file)))

                except (IOError, OSError):
                    print("[!] Error reading file : {}".format(self.cl.red(input_file)))
            else:
                if self.taskstarted == False:
                    print(self.cl.red("[!] <ERROR> You need to start a new Clipboard Interaction."))
                    print(self.cl.red("[!] <ERROR> Start this with 'new' from the menu."))
                print("[!] <ERROR> You need to supply the item file")


    def do_clear(self, arg):
        """
        Toggles whether the clipboard is wiped (ClipPut("")) at the end of the
        interaction so copied secrets do not linger.
        <> Example : clear on  |  clear off  |  clear (toggles)
        """
        choice = arg.strip().lower()
        if choice in ("on", "yes", "true"):
            self.clear_clipboard = True
        elif choice in ("off", "no", "false"):
            self.clear_clipboard = False
        else:
            # unrecognised / empty argument : just toggle the current state
            self.clear_clipboard = not self.clear_clipboard
        state = "ON" if self.clear_clipboard else "OFF"
        print("[+] Clipboard clearing on exit is : {}".format(self.cl.green(state)))


    def do_assigned(self, arg):
        """
        Get the current list of queued clipboard items
        """
        print(self.cl.green("[?] Currently Queued Clipboard Items "))
        if self.items:
            for index, item in enumerate(self.items, 1):
                print("[>] {} : {}".format(index, item))
        else:
            print("[>] No clipboard items currently assigned")
        print("[>] Clear clipboard on exit : {}".format(self.clear_clipboard))


    def do_complete(self, arg):
        """
        This command calls the constructor on the AutoITBlock
        with all the specific arguments
        >> Check the AutoIT constructor requirements
        """

        if self.taskstarted:
            if self.items:
                self.create_autoIT_block()
            else:
                print("{} There are currently no clipboard items assigned".format(self.cl.red("[!]")))
                print("{} Assign items using 'clip <text>'".format(self.cl.red("[-]")))
                return None

        # now reset the tracking values and prompt
        self.complete_task()

        # reset items list when new interaction
        self.items = []
        self.clear_clipboard = False


    #######################################################################
    #  Clipboard AutoIT Block Definition
    #######################################################################


    def create_autoIT_block(self):
        """
        Creates the AutoIT Script Block
        csh.add_tasks takes two positional arguments
            Clipboard_{counter}, and task
        """
        current_counter = str(self.csh.counter.current())
        self.csh.add_task('Clipboard_' + current_counter, self.create_autoit_function())


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
        Expresses the clipboard interaction as OS-neutral primitives : a
        ClipPut for each stored item with a random dwell between, and an
        optional final empty ClipPut to wipe the clipboard.
        """

        prims = [
            P.Comment("Creates a Clipboard Interaction"),
            P.Comment("copies a sequence of notes, passwords or other items to the"),
            P.Comment("Windows clipboard over the duration of the task"),
        ]

        for item in self.items:
            prims.append(P.SetClipboard(item))
            prims.append(P.Sleep(random.randint(2000, 20000)))

        # optionally wipe the clipboard so copied secrets do not linger
        if self.clear_clipboard:
            prims.append(P.Comment("clear the clipboard so copied items do not linger"))
            prims.append(P.SetClipboard(""))

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
            self.items = kwargs["items"]
        except KeyError as missing_key:
            print(self.cl.red("[!] Error Setting JSON Profile attributes : missing key {}".format(missing_key)))
            return

        print(f"[*] Setting the items attribute : {self.items}")

        # optional : wipe the clipboard at the end so copied secrets do not linger
        self.clear_clipboard = bool(kwargs.get("clear", False))
        print(f"[*] Setting the clear attribute : {self.clear_clipboard}")

        # once these have all been set in here, then self.create_autoIT_block() gets called which pushes the task on the stack
        self.create_autoIT_block()
