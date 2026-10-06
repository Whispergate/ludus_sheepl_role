
# #######################################################################
#
#  Task : VLC Interaction
#
# #######################################################################


"""
 Creates the autoIT stub code to be passed into the master compile

 Drives the VLC media player to open and play a media file or stream URL,
 dwell for a period as if watching/listening, then quit. VLC is
 cross-platform; as Sheepl emits AutoIT the generated automation drives VLC
 on a Windows endpoint (vlc is launched via the Run dialog).

 Note on escaping:
    The media path/URL is delivered with Send(), so it is passed through
    escape_autoit_send() : a '#' fragment or other special character would
    otherwise be interpreted by AutoIT as a modifier keystroke.

"""

__author__ = "Lavender-exe"
__license__ = "MIT"


import cmd
import sys
import random
import textwrap

from utils.base.base_cmd_class import BaseCMD
from utils import primitives as P


class VLC(BaseCMD):

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
        super(VLC, self).__init__(csh, cl)

        # Override the defined task name
        self.taskname = 'VLC'

        self.csh = csh
        # current colour object
        self.cl = cl

        # Overrides Base Class Prompt Setup
        if csh.creating_subtasks == True:
            print("[^] creating subtasks >>>>>>>>")
            self.baseprompt = cl.yellow('[>] Creating subtask\n{} > vlc >: '.format(csh.name.lower()))
        else:
            self.baseprompt = cl.yellow('{} > vlc >: '.format(csh.name.lower()))

        self.prompt = self.baseprompt
        self.subtask = False

        # creating my own
        self.introduction = """
        ----------------------------------
        [!] VLC Interaction.
        Type help or ? to list commands.
        ----------------------------------
        1: Start a new block using 'new'
        2: Set what to play with 'media <path or URL>'
        3: Complete the interaction using 'complete'
        """

        self.indent_space = '    '

        # ----------------------------------- >
        #      Task Specific Variables
        # ----------------------------------- >

        # local file path or stream URL to play
        self.media = ''

        # ----------------------------------- >
        # now call the loop if we are in interactive mode by checking
        # if we are parsing JSON

        if not self.csh.json_parsing:
            # call the intro and then start the loop
            print(textwrap.dedent(self.introduction))
            self.cmdloop()


    #######################################################################
    #  VLC Console Commands
    #######################################################################


    def do_new(self, arg):
        """
        This command creates a new VLC interaction
        """
        if self.check_task_started() == False:
            print("[!] Starting : 'VLC_{}'".format(str(self.csh.counter.current())))
            print()
            self.prompt = self.cl.blue("[*] Current Task : VLC_{}".format(str(self.csh.counter.current()))) + "\n" + self.baseprompt


    def do_media(self, media):
        """
        Sets the media file path or stream URL to play
        <> Example : media https://example.com/stream.mp4
        """
        if self.taskstarted == False:
            print(self.cl.red("[!] <ERROR> You need to start a new VLC Interaction."))
            print(self.cl.red("[!] <ERROR> Start this with 'new' from the menu."))
            return
        if media:
            self.media = media.strip()
            print("[+] Media set to : {}".format(self.cl.green(self.media)))


    def do_assigned(self, arg):
        """
        Shows the currently configured media
        """
        print(self.cl.green("[?] Current VLC Configuration "))
        print("[>] Media : {}".format(self.media or "None"))


    def do_complete(self, arg):
        """
        This command calls the constructor on the AutoITBlock
        with all the specific arguments
        """
        if self.taskstarted:
            if self.media:
                self.create_autoIT_block()
            else:
                print("{} No media set - use 'media <path or URL>'".format(self.cl.red("[!]")))
                return None

        # now reset the tracking values and prompt
        self.complete_task()

        # reset state when new interaction
        self.media = ''


    #######################################################################
    #  VLC AutoIT Block Definition
    #######################################################################


    def create_autoIT_block(self):
        """
        Creates the AutoIT Script Block
        """
        current_counter = str(self.csh.counter.current())
        self.csh.add_task('VLC_' + current_counter, self.create_autoit_function())


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
        Expresses the media session as OS-neutral primitives : launch VLC on
        the media, wait for its window, dwell as if watching, then quit.
        """

        return [
            P.Comment("Creates a VLC Interaction"),
            P.RunDialog("vlc " + self.media),
            P.Comment("allow VLC to start and begin playback"),
            P.Sleep(8000),
            P.Comment("match the VLC window by title regardless of the media name"),
            P.WaitWindow("[REGEXPTITLE:(?i).*VLC.*]", 20),
            P.FocusWindow("[REGEXPTITLE:(?i).*VLC.*]"),
            P.Comment("dwell as if watching / listening"),
            P.Sleep(random.randint(15000, 60000)),
            P.Comment("quit VLC"),
            P.SendKeys("^q"),
            P.Sleep(1000),
            P.ReleaseFocus(),
        ]


    def parse_json_profile(self, **kwargs):
        """
        Takes kwargs in and build out task variables when using JSON profiles
        this function sets the various object attributes in the same way
        that the interactive mode does
        """

        print("[%] Setting attributes from JSON Profile")
        print(f"[-] The following keys are needed for this task : {[x for x in list(kwargs.keys())[1:]]}")

        try:
            self.media = kwargs["media"]
        except KeyError as missing_key:
            print(self.cl.red("[!] Error Setting JSON Profile attributes : missing key {}".format(missing_key)))
            return

        print(f"[*] Setting the media attribute : {self.media}")

        self.create_autoIT_block()

