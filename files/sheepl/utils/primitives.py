"""
OS-neutral automation primitives.

A task expresses what the emulated user does as an ordered list of these
primitives instead of hand-writing AutoIT. A backend then renders the list
into its target language (see utils/backends/). This is the layer that lets a
single task definition drive both the AutoIT (Windows) and xdotool (Linux)
backends.

Each primitive carries an `op` string so backends can dispatch on it without
importing these classes. Values held by the primitives are the *semantic*
values (the URL, the command, the text to type); escaping is the backend's
responsibility, because it differs per target (AutoIT's {!} vs shell quoting).

Primitive summary:
    Comment(text)              a source comment
    RunDialog(command)         open the Run dialog and launch `command`
    TypeLine(text)             type `text` then press Enter
    TypeText(text)             type `text` with no trailing Enter
    SendKeys(keys)             send raw key tokens verbatim (e.g. "^t", "{ENTER}")
    Sleep(ms)                  pause for `ms` milliseconds
    WaitWindow(spec, timeout)  wait for a window to be active
    FocusWindow(spec)          keep input directed at a window
    ReleaseFocus()             clear the focus lock
    CloseWindow(spec)          close a window
    SetClipboard(text)         place `text` on the clipboard
    CallFunction(name)         call another defined function by name
    Raw(code)                  backend-specific escape hatch (verbatim code)
"""

__author__ = "Lavender-exe"
__license__ = "MIT"


class Comment(object):
    op = "comment"
    def __init__(self, text):
        self.text = text


class RunDialog(object):
    op = "rundialog"
    def __init__(self, command):
        self.command = command


class TypeLine(object):
    op = "type_line"
    def __init__(self, text):
        self.text = text


class TypeText(object):
    op = "type_text"
    def __init__(self, text):
        self.text = text


class SendKeys(object):
    op = "send_keys"
    def __init__(self, keys):
        self.keys = keys


class Sleep(object):
    op = "sleep"
    def __init__(self, ms):
        self.ms = ms


class WaitWindow(object):
    op = "wait_window"
    def __init__(self, spec, timeout=10):
        self.spec = spec
        self.timeout = timeout


class FocusWindow(object):
    op = "focus_window"
    def __init__(self, spec):
        self.spec = spec


class ReleaseFocus(object):
    op = "release_focus"


class CloseWindow(object):
    op = "close_window"
    def __init__(self, spec):
        self.spec = spec


class SetClipboard(object):
    op = "set_clipboard"
    def __init__(self, text):
        self.text = text


class CallFunction(object):
    op = "call_function"
    def __init__(self, name):
        self.name = name


class Raw(object):
    op = "raw"
    def __init__(self, code):
        self.code = code
