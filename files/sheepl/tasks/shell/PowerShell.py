
# #######################################################################
#
#  Task : PowerShell Interaction
#
# #######################################################################


"""
 Creates the autoIT stub code to be passed into the master compile

 Takes a supplied text file for the Sheepl to type
 the master script will already define the typing speed as part of the master declarations

"""
__author__ = "Matt Lorentzen @lorentzenman"
__license__ = "MIT"


import cmd
import sys
import random
import textwrap

# Sheepl Class Imports
from utils.base.base_cmd_class import BaseCMD
from utils import primitives as P



class PowerShell(BaseCMD):

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
        super(PowerShell, self).__init__(csh, cl)

        # Override the defined task name
        self.taskname = 'PowerShell'

        # current Sheepl Object
        # which might need to be renamed to Sheepl
        self.csh = csh
        # current colour object
        self.cl = cl
        
        # Overrides Base Class Prompt Setup
        if csh.creating_subtasks == True:
            print("[^] creating subtasks >>>>>>>>")
            self.baseprompt = cl.yellow('[>] Creating subtask\n{} > command >: '.format(csh.name.lower()))
        else:
            self.baseprompt = cl.yellow('{} > powershell >: '.format(csh.name.lower()))

        self.prompt = self.baseprompt
        # list to hold commands
        self.commands = []
        # track subtasks
        self.subtask = False    
        
        # creating my own 
        self.introduction = """
        ----------------------------------
        [!] PowerShell Interaction.
        Type help or ? to list commands.
        ----------------------------------
        1: Start a new block using 'new'
        2: Add in PowerShell commands using cmd
        3: Complete the interaction using 'complete'
        """
        
        self.indent_space = '    '

        # ----------------------------------- >
        #      Task Specific Variables
        # ----------------------------------- >
        
        
        # ----------------------------------- >
        # now call the loop if we are in interactive mode by checking 
        # if we are parsing JSON
        
        if not self.csh.json_parsing:
            # call the intro and then start the loop
            print(textwrap.dedent(self.introduction))
            self.cmdloop()


    ########################################################################
    # PowerShell Console Commands
    ########################################################################


    def do_new(self, arg):
        """ 
        This command creates a new Powershell interaction
        """
        # Init tracking booleans
        # method from parent class BaseCMD
        # Inverse check to see if task has already started
        # Booleans are set in parent method

        # method from parent class BaseCMD
        if self.check_task_started() == False:
            print("[!] Starting : 'PowerShell_{}'".format(str(self.csh.counter.current())))
            # OCD Line break
            print()
            self.prompt = "[*] Current Task : PowerShell_{}".format(str(self.csh.counter.current())) + "\n" + self.baseprompt


    def do_cmd(self, command):
        """
        First checks to see if a new PowerShell BLock has been started
        if so allows the command to be issued and then runs some checks
        or prompts to start a new interaction using 'new'
        Specify the command to run in the shell
        <> Example : gwmi win32_service | ? {S_.Status -eq 'Running'}
        """
        if command:
            if self.taskstarted == True:   
                print(command)
                self.commands.append(command)
            else:
                if self.taskstarted == False:
                    print(self.cl.red("[!] <ERROR> You need to start a new PowerShell Interaction."))
                    print(self.cl.red("[!] <ERROR> Start this with 'new' from the menu."))
                print("[!] <ERROR> You need to supply the command for typing")


    def do_command_file(self, input_file):
        """
        Takes an input command file and parses
        expect one per line
        """
        if input_file:
            if self.taskstarted == True:
                try:
                    with open(input_file) as command_file:
                        for command in command_file.readlines():  
                            self.commands.append(command.rstrip('\n'))

                except:
                    print("[!] Error reading file : {}".format(self.cl.red(input_file)))
            else:
                if self.taskstarted == False:
                    print(self.cl.red("[!] <ERROR> You need to start a new PowerShell Interaction."))
                    print(self.cl.red("[!] <ERROR> Start this with 'new' from the menu."))
                print("[!] <ERROR> You need to supply the command for typing")


    def do_assigned(self, arg):
        """ 
        Get the current list of assigned PowerShell commands
        """
        print(self.cl.green("[?] Currently Assigned Commands "))
        for command in self.commands:
            print("[>] {}".format(command))


    def do_complete(self, arg):
        """
        This command calls the constructor on the AutoITBlock
        with all the specific arguments
        >> Check the AutoIT constructor requirements      
        """

        if self.taskstarted:
            if self.commands:
                self.create_autoIT_block()
            else:
                print("{} There are currently no commands assigned".format(self.cl.red("[!]")))
                print("{} Assign some commands using 'cmd <command>'".format(self.cl.red("[-]")))
                return None

        # now reset the tracking values and prompt
        self.complete_task()

        # reset commands list when new interaction
        self.commands = []


    ######################################################################
    #  PowerShell AutoIT Block Definition
    #######################################################################
    
    def create_autoIT_block(self):
        """
        Creates the AutoIT Script Block
        csh.add_tasks takes two positional arguments
            commandname_{counter}, and task
        """
        current_counter = str(self.csh.counter.current())
        self.csh.add_task('PowerShell_' + current_counter, self.create_autoit_function())


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
        Expresses the PowerShell interaction as OS-neutral primitives : open a
        PowerShell prompt (keeping focus, handling the RDP case), type each
        command with a random dwell, then exit.
        """

        prims = [
            P.Comment("Creates a PowerShell Interaction"),
            P.RunDialog("powershell"),
            P.Raw(self.rdp_focus_check("Windows PowerShell")),
        ]
        for command in self.commands:
            prims.append(P.TypeLine(command))
            prims.append(P.Sleep(random.randint(2000, 20000)))
        prims.append(P.TypeLine("exit"))
        prims.append(P.Comment("Reset Focus"))
        prims.append(P.ReleaseFocus())
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
        self.commands = kwargs["cmd"]
        print(f"[*] Setting the commands attribute : {self.commands}")

        # once these have all been set in here, then self.create_autoIT_block() gets called which pushes the task on the stack
        self.create_autoIT_block()   


