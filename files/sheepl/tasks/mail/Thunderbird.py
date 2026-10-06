
# #######################################################################
#
#  Task : Thunderbird Interaction
#
# #######################################################################


"""
 Creates the autoIT stub code to be passed into the master compile

 Drives Mozilla Thunderbird to compose an email. Thunderbird is
 cross-platform; as Sheepl emits AutoIT the generated automation drives
 Thunderbird on a Windows endpoint.

 By default the composed message is saved as a draft (Ctrl+S) rather than
 sent, so the task produces believable activity even on a box without a
 fully configured outgoing account. Set "send": true to actually send it
 (Ctrl+Enter).

 Note on escaping:
    Recipient, subject and body are delivered with Send(), so all are passed
    through escape_autoit_send() to stop characters such as ! + ^ # { } being
    interpreted as modifier keystrokes.

 Note on compose navigation:
    Moving between the To, Subject and body fields is done with Tab. The exact
    number of tabs can vary slightly between Thunderbird versions, so treat
    this as a best-effort sequence (consistent with the rest of Sheepl).

"""

__author__ = "Lavender-exe"
__license__ = "MIT"


import cmd
import sys
import random
import textwrap

from utils.base.base_cmd_class import BaseCMD
from utils import primitives as P


class Thunderbird(BaseCMD):

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
        super(Thunderbird, self).__init__(csh, cl)

        # Override the defined task name
        self.taskname = 'Thunderbird'

        self.csh = csh
        # current colour object
        self.cl = cl

        # Overrides Base Class Prompt Setup
        if csh.creating_subtasks == True:
            print("[^] creating subtasks >>>>>>>>")
            self.baseprompt = cl.yellow('[>] Creating subtask\n{} > thunderbird >: '.format(csh.name.lower()))
        else:
            self.baseprompt = cl.yellow('{} > thunderbird >: '.format(csh.name.lower()))

        self.prompt = self.baseprompt
        self.subtask = False

        # creating my own
        self.introduction = """
        ----------------------------------
        [!] Thunderbird Interaction.
        Type help or ? to list commands.
        ----------------------------------
        1: Start a new block using 'new'
        2: Set the recipient with 'to <address>'
        3: Set the subject with 'subject <text>'
        4: Add body lines with 'body <text>' or 'body_file <path>'
        5: Optionally 'send on' to send instead of saving a draft
        6: Complete the interaction using 'complete'
        """

        self.indent_space = '    '

        # ----------------------------------- >
        #      Task Specific Variables
        # ----------------------------------- >

        self.to = ''
        self.subject = ''
        self.body = ''
        # default to saving a draft rather than actually sending
        self.send_email = False

        # ----------------------------------- >
        # now call the loop if we are in interactive mode by checking
        # if we are parsing JSON

        if not self.csh.json_parsing:
            # call the intro and then start the loop
            print(textwrap.dedent(self.introduction))
            self.cmdloop()


    #######################################################################
    #  Thunderbird Console Commands
    #######################################################################


    def do_new(self, arg):
        """
        This command creates a new Thunderbird interaction
        """
        if self.check_task_started() == False:
            print("[!] Starting : 'Thunderbird_{}'".format(str(self.csh.counter.current())))
            print()
            self.prompt = self.cl.blue("[*] Current Task : Thunderbird_{}".format(str(self.csh.counter.current()))) + "\n" + self.baseprompt


    def do_to(self, address):
        """
        Sets the recipient address
        <> Example : to colleague@lab.local
        """
        if self.taskstarted == False:
            print(self.cl.red("[!] <ERROR> You need to start a new Thunderbird Interaction."))
            print(self.cl.red("[!] <ERROR> Start this with 'new' from the menu."))
            return
        if address:
            self.to = address.strip()
            print("[+] Recipient set to : {}".format(self.cl.green(self.to)))


    def do_subject(self, subject):
        """
        Sets the subject line
        <> Example : subject Weekly sync notes
        """
        if self.taskstarted == False:
            print(self.cl.red("[!] <ERROR> You need to start a new Thunderbird Interaction."))
            print(self.cl.red("[!] <ERROR> Start this with 'new' from the menu."))
            return
        if subject:
            self.subject = subject
            print("[+] Subject set to : {}".format(self.cl.green(self.subject)))


    def do_body(self, line):
        """
        Appends a line to the email body
        <> Example : body Hi team, here are the notes from today.
        """
        if self.taskstarted == False:
            print(self.cl.red("[!] <ERROR> You need to start a new Thunderbird Interaction."))
            print(self.cl.red("[!] <ERROR> Start this with 'new' from the menu."))
            return
        # append as its own line
        self.body += (line + "\n")


    def do_body_file(self, input_file):
        """
        Loads the email body from a text file
        """
        if self.taskstarted == False:
            print(self.cl.red("[!] <ERROR> You need to start a new Thunderbird Interaction."))
            print(self.cl.red("[!] <ERROR> Start this with 'new' from the menu."))
            return
        if input_file:
            try:
                with open(input_file) as f:
                    self.body += f.read().strip()
                print("[+] Loaded body from : {}".format(self.cl.green(input_file)))
            except (IOError, OSError):
                print("[!] Error reading file : {}".format(self.cl.red(input_file)))


    def do_send(self, arg):
        """
        Toggles whether the email is sent (Ctrl+Enter) or saved as a draft.
        <> Example : send on  |  send off
        """
        choice = arg.strip().lower()
        if choice in ("on", "yes", "true"):
            self.send_email = True
        elif choice in ("off", "no", "false"):
            self.send_email = False
        else:
            self.send_email = not self.send_email
        state = "SEND" if self.send_email else "SAVE DRAFT"
        print("[+] Message will : {}".format(self.cl.green(state)))


    def do_assigned(self, arg):
        """
        Shows the currently configured email
        """
        print(self.cl.green("[?] Current Email Configuration "))
        print("[>] To      : {}".format(self.to or "None"))
        print("[>] Subject : {}".format(self.subject or "None"))
        print("[>] Action  : {}".format("send" if self.send_email else "save draft"))
        print("[>] Body    :")
        for l in self.body.splitlines():
            print("    {}".format(l))


    def do_complete(self, arg):
        """
        This command calls the constructor on the AutoITBlock
        with all the specific arguments
        """
        if self.taskstarted:
            if self.to and self.subject:
                self.create_autoIT_block()
            else:
                print("{} A recipient ('to') and 'subject' are required".format(self.cl.red("[!]")))
                return None

        # now reset the tracking values and prompt
        self.complete_task()

        # reset state when new interaction
        self.to = ''
        self.subject = ''
        self.body = ''
        self.send_email = False


    #######################################################################
    #  Thunderbird AutoIT Block Definition
    #######################################################################


    def create_autoIT_block(self):
        """
        Creates the AutoIT Script Block
        """
        current_counter = str(self.csh.counter.current())
        self.csh.add_task('Thunderbird_' + current_counter, self.create_autoit_function())


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
        Expresses composing an email as OS-neutral primitives : launch
        Thunderbird, open a compose window, fill the recipient/subject/body,
        then send or save a draft. The body is emitted via Raw because it is a
        single Send with embedded {ENTER} line breaks.
        """

        prims = [
            P.Comment("Creates a Thunderbird Interaction"),
            P.RunDialog("thunderbird"),
            P.Comment("Thunderbird can be slow to start"),
            P.Sleep(10000),
            P.Comment("Thunderbird windows use the Mozilla window class"),
            P.WaitWindow("[CLASS:MozillaWindowClass]", 30),
            P.FocusWindow("[CLASS:MozillaWindowClass]"),
            P.Comment("dwell as if reading mail before composing"),
            P.Sleep(random.randint(8000, 20000)),
            P.Comment("open a new compose window"),
            P.SendKeys("^n"),
            P.Sleep(4000),
            P.Comment("recipient"),
            P.TypeText(self.to),
            P.Sleep(800),
            P.Comment("Tab twice : past the recipient row to the Subject field"),
            P.SendKeys("{TAB}{TAB}"),
            P.Comment("subject"),
            P.TypeText(self.subject),
            P.Sleep(800),
            P.Comment("Tab once more into the message body"),
            P.SendKeys("{TAB}"),
        ]

        # body : type each line with an Enter between lines (neutral primitives
        # so the body renders on both the AutoIT and Linux backends)
        body_lines = self.body.splitlines()
        if body_lines:
            prims.append(P.Comment("body"))
            for idx, line in enumerate(body_lines):
                if idx > 0:
                    prims.append(P.SendKeys("{ENTER}"))
                prims.append(P.TypeText(line))

        prims.append(P.Comment("dwell while composing"))
        prims.append(P.Sleep(random.randint(5000, 15000)))

        if self.send_email:
            prims.append(P.Comment("send the message"))
            prims.append(P.SendKeys("^{ENTER}"))
            prims.append(P.Sleep(3000))
        else:
            prims.append(P.Comment("save the message as a draft"))
            prims.append(P.SendKeys("^s"))
            prims.append(P.Sleep(2000))
            prims.append(P.Comment("close the compose window"))
            prims.append(P.SendKeys("^w"))
            prims.append(P.Sleep(1500))

        prims.append(P.ReleaseFocus())
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
            self.to = kwargs["to"]
            self.subject = kwargs["subject"]
        except KeyError as missing_key:
            print(self.cl.red("[!] Error Setting JSON Profile attributes : missing key {}".format(missing_key)))
            return

        # body and send are optional
        self.body = str(kwargs.get("body", ""))
        self.send_email = bool(kwargs.get("send", False))

        print(f"[*] Setting the to attribute : {self.to}")
        print(f"[*] Setting the subject attribute : {self.subject}")
        print(f"[*] Setting the send attribute : {self.send_email}")

        self.create_autoIT_block()


