
# #######################################################################
#
#  Task : Browser Interaction
#
# #######################################################################


"""
 Creates the autoIT stub code to be passed into the master compile

 Opens a modern web browser (Edge, Chrome, Firefox, or the system default)
 and visits a sequence of URLs, dwelling on each page for a random period.
 Each additional URL after the first is opened in a new tab, like a real
 user browsing through several pages in one session.

 This replaces the legacy InternetExplorer task for Windows 10/11 where
 Internet Explorer and the _IE* UDFs are no longer available.

 Note on escaping:
    URLs are delivered with Send(), so they are passed through
    escape_autoit_send(). A '#' fragment or a '+' in a query string would
    otherwise be interpreted by AutoIT as a modifier keystroke.

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


# Maps the supported browsers to the Run-dialog launch keyword and the
# window class used to keep the window in focus. The 'default' browser is
# launched by typing the URL straight into the Run dialog (Windows opens it
# in whatever browser is configured as default) and uses no class pinning.
BROWSER_CONFIG = {
    "edge":    {"launch": "msedge",  "winclass": "Chrome_WidgetWin_1"},
    "chrome":  {"launch": "chrome",  "winclass": "Chrome_WidgetWin_1"},
    "firefox": {"launch": "firefox", "winclass": "MozillaWindowClass"},
    "default": {"launch": "",        "winclass": ""},
}


class Browser(BaseCMD):

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
        super(Browser, self).__init__(csh, cl)

        # Override the defined task name
        self.taskname = 'Browser'

        # current Sheepl Object
        self.csh = csh
        # current colour object
        self.cl = cl

        # Overrides Base Class Prompt Setup
        if csh.creating_subtasks == True:
            print("[^] creating subtasks >>>>>>>>")
            self.baseprompt = cl.yellow('[>] Creating subtask\n{} > browser >: '.format(csh.name.lower()))
        else:
            self.baseprompt = cl.yellow('{} > browser >: '.format(csh.name.lower()))

        self.prompt = self.baseprompt
        # track subtasks
        self.subtask = False

        # creating my own
        self.introduction = """
        ----------------------------------
        [!] Browser Interaction.
        Type help or ? to list commands.
        ----------------------------------
        1: Start a new block using 'new'
        2: Choose a browser with 'browser <edge|chrome|firefox|default>'
        3: Add pages with 'url <address>' or 'url_file <path>'
        4: Complete the interaction using 'complete'
        """

        self.indent_space = '    '

        # ----------------------------------- >
        #      Task Specific Variables
        # ----------------------------------- >

        # the browser to drive : defaults to Edge which ships with Windows 10/11
        self.browser = 'edge'
        # ordered list of URLs to visit
        self.urls = []

        # ----------------------------------- >
        # now call the loop if we are in interactive mode by checking
        # if we are parsing JSON

        if not self.csh.json_parsing:
            # call the intro and then start the loop
            print(textwrap.dedent(self.introduction))
            self.cmdloop()


    #######################################################################
    #  Browser Console Commands
    #######################################################################


    def do_new(self, arg):
        """
        This command creates a new Browser interaction
        """
        # method from parent class BaseCMD
        if self.check_task_started() == False:
            print("[!] Starting : 'Browser_{}'".format(str(self.csh.counter.current())))
            # OCD Line break
            print()
            self.prompt = self.cl.blue("[*] Current Task : Browser_{}".format(str(self.csh.counter.current()))) + "\n" + self.baseprompt


    def do_browser(self, choice):
        """
        Sets which browser to drive : edge, chrome, firefox or default
        <> Example : browser chrome
        """
        if self.taskstarted == False:
            print(self.cl.red("[!] <ERROR> You need to start a new Browser Interaction."))
            print(self.cl.red("[!] <ERROR> Start this with 'new' from the menu."))
            return

        choice = choice.strip().lower()
        if choice in BROWSER_CONFIG:
            self.browser = choice
            print("[+] Browser set to : {}".format(self.cl.green(choice)))
        else:
            print(self.cl.red("[!] <ERROR> Unknown browser '{}'".format(choice)))
            print("[?] Choose one of : {}".format(", ".join(BROWSER_CONFIG.keys())))


    def do_url(self, url):
        """
        Adds a URL to the browsing sequence
        <> Example : url https://www.google.com
        """
        if url:
            if self.taskstarted == True:
                self.urls.append(url.strip())
                print("[+] Added URL : {}".format(self.cl.green(url.strip())))
            else:
                if self.taskstarted == False:
                    print(self.cl.red("[!] <ERROR> You need to start a new Browser Interaction."))
                    print(self.cl.red("[!] <ERROR> Start this with 'new' from the menu."))
                print("[!] <ERROR> You need to supply the URL to visit")


    def do_url_file(self, input_file):
        """
        Takes an input file and adds each line as a URL to visit
        expect one URL per line
        """
        if input_file:
            if self.taskstarted == True:
                try:
                    with open(input_file) as url_file:
                        for url in url_file.readlines():
                            cleaned = url.rstrip('\n').strip()
                            if cleaned:
                                self.urls.append(cleaned)
                    print("[+] Loaded URLs from : {}".format(self.cl.green(input_file)))

                except (IOError, OSError):
                    print("[!] Error reading file : {}".format(self.cl.red(input_file)))
            else:
                if self.taskstarted == False:
                    print(self.cl.red("[!] <ERROR> You need to start a new Browser Interaction."))
                    print(self.cl.red("[!] <ERROR> Start this with 'new' from the menu."))
                print("[!] <ERROR> You need to supply the URL file")


    def do_assigned(self, arg):
        """
        Get the current browser and list of queued URLs
        """
        print(self.cl.green("[?] Current Browser Configuration "))
        print("[>] Browser : {}".format(self.browser))
        if self.urls:
            for index, url in enumerate(self.urls, 1):
                print("[>] {} : {}".format(index, url))
        else:
            print("[>] No URLs currently assigned")


    def do_complete(self, arg):
        """
        This command calls the constructor on the AutoITBlock
        with all the specific arguments
        >> Check the AutoIT constructor requirements
        """

        if self.taskstarted:
            if self.urls:
                self.create_autoIT_block()
            else:
                print("{} There are currently no URLs assigned".format(self.cl.red("[!]")))
                print("{} Add URLs using 'url <address>'".format(self.cl.red("[-]")))
                return None

        # now reset the tracking values and prompt
        self.complete_task()

        # reset state when new interaction
        self.urls = []
        self.browser = 'edge'


    #######################################################################
    #  Browser AutoIT Block Definition
    #######################################################################


    def create_autoIT_block(self):
        """
        Creates the AutoIT Script Block
        csh.add_tasks takes two positional arguments
            Browser_{counter}, and task
        """
        current_counter = str(self.csh.counter.current())
        self.csh.add_task('Browser_' + current_counter, self.create_autoit_function())


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
        Expresses the browsing session as OS-neutral primitives : launch the
        browser on the first URL, dwell, then open each further URL in a new
        tab, and finally close the window.
        """

        config = BROWSER_CONFIG.get(self.browser, BROWSER_CONFIG["edge"])
        launch = config["launch"]
        winclass = config["winclass"]

        # a named browser is launched as '<launch> <url>'; the default browser
        # is reached by typing the URL straight into the Run dialog. The URL is
        # left unescaped here : the backend escapes it when rendering the primitive
        run_target = "{} {}".format(launch, self.urls[0]) if launch else self.urls[0]

        prims = [
            P.Comment("Creates a Browser Interaction : {}".format(self.browser)),
            P.RunDialog(run_target),
            P.Comment("give the browser time to start"),
            P.Sleep(8000),
        ]
        if winclass:
            prims.append(P.WaitWindow("[CLASS:{}]".format(winclass), 15))
            prims.append(P.FocusWindow("[CLASS:{}]".format(winclass)))
        prims.append(P.Comment("dwell on the first page"))
        prims.append(P.Sleep(random.randint(8000, 30000)))

        for url in self.urls[1:]:
            prims.append(P.Comment("open the next page in a new tab"))
            prims.append(P.SendKeys("^t"))
            prims.append(P.Sleep(1500))
            prims.append(P.TypeLine(url))
            prims.append(P.Sleep(random.randint(8000, 30000)))

        prims.append(P.ReleaseFocus())
        if winclass:
            prims.append(P.CloseWindow("[CLASS:{}]".format(winclass)))
        else:
            # default browser : class unknown, fall back to Alt+F4
            prims.append(P.SendKeys("!{F4}"))

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
            self.urls = kwargs["urls"]
        except KeyError as missing_key:
            print(self.cl.red("[!] Error Setting JSON Profile attributes : missing key {}".format(missing_key)))
            return

        # browser is optional : default to edge and validate the choice
        self.browser = str(kwargs.get("browser", "edge")).lower()
        if self.browser not in BROWSER_CONFIG:
            print(self.cl.red("[!] Unknown browser '{}' - defaulting to edge".format(self.browser)))
            self.browser = "edge"

        print(f"[*] Setting the browser attribute : {self.browser}")
        print(f"[*] Setting the urls attribute : {self.urls}")

        # once these have all been set in here, then self.create_autoIT_block() gets called which pushes the task on the stack
        self.create_autoIT_block()


