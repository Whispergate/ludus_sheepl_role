"""
Output backend interface.

A backend is responsible for taking a built Sheepl object (its assigned
tasks, includes, timing and loop settings) and rendering it into a concrete
automation program for a target platform.

Today there is a single backend, AutoItBackend, which produces the Windows
AutoIT (.au3) output that Sheepl has always generated. The interface exists
so that additional backends (for example a Linux xdotool backend) can be
added without the Sheepl object or the console/profile layers needing to know
how a given platform is driven.
"""

__author__ = "Lavender-exe"
__license__ = "MIT"


class Backend(object):
    """
    Base class for output backends.

    Subclasses set :
        name            > short identifier, e.g. "autoit"
        file_extension  > output file extension including the dot, e.g. ".au3"

    and implement :
        assemble(csh)   > return the full output file content as a string
        escape(text)    > escape a user supplied string for this backend
    """

    name = "base"
    file_extension = ""
    # line ending passed to open(newline=...): None keeps the platform default
    # (CRLF on Windows); a backend whose output must use LF (e.g. a Linux shell
    # script) overrides this with "\n".
    newline = None

    def assemble(self, csh):
        """
        Render the given Sheepl object into the full output program text.
        """
        raise NotImplementedError("backends must implement assemble()")

    def escape(self, text):
        """
        Escape a user supplied string so it is emitted literally by this
        backend's input primitives.
        """
        raise NotImplementedError("backends must implement escape()")

    def comment(self, text):
        """
        Format a source comment for this backend (used by tasks that build
        comment text outside the Comment primitive, e.g. subtask headers).
        """
        raise NotImplementedError("backends must implement comment()")
