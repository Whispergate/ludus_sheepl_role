
# #######################################################################
#
#  Task : KeePass Interaction
#
# #######################################################################


"""
 Creates the autoIT stub code to be passed into the master compile

 : Takes a supplied text file for the Sheepl to type
 : the master script will already define the typing speed as part of the master declarations

"""

__author__ = "Matt Lorentzen @lorentzenman"
__license__ = "MIT"

import cmd
import sys
import random
import textwrap

from utils.base.base_cmd_class import BaseCMD
from utils import primitives as P
#from utils.typing import TypeWriter


class KeePass(BaseCMD):

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
        super(KeePass, self).__init__(csh, cl)

        # Override the defined task name
        self.taskname = 'KeePass'
        
        # which might need to be renamed to Sheepl
        self.csh = csh
        # current colour object
        self.cl = cl

        #  Overrides Base Class Prompt Setup
        if csh.creating_subtasks == True:
            print("[^] creating subtasks >>>>>>>>")
            self.baseprompt = cl.yellow('[>] Creating subtask\n{} > command >: '.format(csh.name.lower()))
        else:
            self.baseprompt = cl.yellow('{} > keepass >: '.format(csh.name.lower()))

        self.prompt = self.baseprompt
         
         # track subtasks
        self.subtask = False  

        # creating my own
        self.introduction = """
        ----------------------------------
        [!] KeePass Interaction.
        Type help or ? to list commands.
        ----------------------------------
        1: Start a new block using 'new'
        2: This task takes in 'database_location' and 'masterpassword'
        3: You can also supply the title to kill any open windows on loop
        4: Complete the interaction using 'complete'
        """

        self.indent_space = '    '

        # ----------------------------------- >
        #      Task Specific Variables
        # ----------------------------------- >

        self.database_location = ''
        self.masterpassword = ''

        # ----------------------------------- >
        # now call the loop if we are in interactive mode by checking 
        # if we are parsing JSON

        if not self.csh.json_parsing:
            # call the intro and then start the loop
            print(textwrap.dedent(self.introduction))
            self.cmdloop()


    ########################################################################
    # KeePass Class Definition
    ########################################################################
    

    def do_new(self, arg):
        """
        This command creates a new Word document
        """
        # Init tracking booleans
        # method from parent class BaseCMD
        # Inverse check to see if task has already started
        # Booleans are set in parent method

        # method from parent class BaseCMD
        if self.check_task_started() == False:
            print("[!] Starting : 'KeePass_{}'".format(str(self.csh.counter.current())))
            # OCD Line break
            print()
            self.prompt = self.cl.blue("[*] KeePass_{}".format(str(self.csh.counter.current()))) + "\n" + self.baseprompt


    def do_database_location(self, location):
        r"""
        Specifies the keepass location > database_location c:\path.to.keepass.db
        """
        if location:
            if self.taskstarted == True:
                print("[!] Database Location : {}".format(location))
                self.database_location = location
            else:
                if self.taskstarted == False:
                    print(self.cl.red("[!] <ERROR> You need to start a new KeePass Interaction."))
                    print(self.cl.red("[!] <ERROR> Start this with 'new' from the menu."))
                print("[!] <ERROR> You need to supply the command for typing")


    def do_masterpassword(self, masterpassword):
        """
        Specifies the keepass masterpassword credential
        """
        if masterpassword:
            if self.taskstarted == True:
                self.masterpassword = masterpassword
            else:
                if self.taskstarted == False:
                    print(self.cl.red("[!] <ERROR> You need to start a new KeePass Interaction."))
                    print(self.cl.red("[!] <ERROR> Start this with 'new' from the menu."))
                print("[!] <ERROR> You need to supply the command for typing")


    def do_show(self, arg):
        """
        Shows the current configured credentials
        """

        current_setup = """
        > Database Location : {}
        > MasterPassword : {}

        """.format(self.database_location, self.masterpassword)

        print(textwrap.dedent(current_setup))


    def do_complete(self, arg):
        """
        This command calls the constructor on the AutoITBlock
        with all the specific arguments
        >> Check the AutoIT constructor requirements
        """
        # setup create_keepass for ease and clarity
        # pass in unique contructor arguments for AutoITBlock

        # Call the static method in the task object
        if self.taskstarted:
            # check to see if required stuff is here
            if (self.database_location and self.masterpassword):
                self.create_autoIT_block()
            
                # now reset the tracking values and prompt
                self.complete_task()
        
            else:
                print("[!] You need to supply a database location and MasterPassword")
                return None
        else:
            print("{} There are currently no command assigned".format(self.cl.red("[!]")))
            print("{} Assign some commands using 'cmd <command>'".format(self.cl.red("[-]")))
            return None


    ########################################################################
    # KeePass AutoIT Block Definition
    ########################################################################


    def create_autoIT_block(self):
        """
        Creates the AutoIT Script Block
        """
        current_counter = str(self.csh.counter.current())
        self.csh.add_task('KeePass_' + current_counter, self.create_autoit_function())


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
        Expresses the KeePass interaction as OS-neutral primitives : launch the
        database, wait for the open prompt, type the master password, then quit.
        """

        return [
            P.Comment("Creates a KeePass Interaction"),
            P.Comment("Sends path to the KeePass database on the local box"),
            P.RunDialog(self.database_location),
            P.Raw(self.rdp_focus_check("[CLASS:ConsoleWindowClass]")),
            P.Comment("Keep Window Infocus - longer wait delay to let program catchup"),
            P.WaitWindow("Open Database", 40),
            P.FocusWindow("Open Database"),
            P.Comment("open the database using the masterpassword"),
            P.TypeText(self.masterpassword),
            P.Sleep(15677),
            P.FocusWindow("KeePass"),
            P.Comment("exit via CTRL + q"),
            P.SendKeys("^q"),
            P.Comment("Reset Focus"),
            P.ReleaseFocus(),
        ]


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
            self.database_location  = kwargs["database_location"]
            self.masterpassword     = kwargs["masterpassword"]
 
            print(f"[*] Setting the command attribute : {self.database_location}")
            print(f"[*] Setting the command attribute : {self.masterpassword}")


        except KeyError as missing_key:
            print(self.cl.red("[!] Error Setting JSON Profile attributes : missing key {}".format(missing_key)))

        # once these have all been set in here, then self.create_autoIT_block() gets called which pushes the task on the stack
        self.create_autoIT_block()



   
