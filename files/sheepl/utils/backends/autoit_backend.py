"""
AutoIT output backend.

Produces the Windows AutoIT (.au3) source that Sheepl generates.

assemble() builds the overall file structure: the optional #NoTrayIcon, the UDF
include headers, the global task and sleep-time arrays, the window watcher, the
task loop, and the task function bodies. render_task() turns a task's
platform-neutral primitive list (see utils/primitives.py) into one AutoIT
function, performing all Send escaping. A few AutoIT helpers used by the file
structure still live on the Sheepl object and are invoked here.
"""

__author__ = "Lavender-exe"
__license__ = "MIT"


import textwrap

from utils.backends.base_backend import Backend


class AutoItBackend(Backend):

    name = "autoit"
    file_extension = ".au3"

    def assemble(self, csh):
        """
        Render the Sheepl object into a complete AutoIT script.

        Mirrors the original write_file() assembly exactly :
            1. #NoTrayIcon when the tray icon is disabled
            2. the UDF #include headers, in order
            3. the global SendKeyDelay (typing speed)
            4. the global task list and sleep-time arrays
            5. the window watcher function
            6. the task loop (looping or single-run)
            7. each task's function body
        """

        # timing distribution is computed first (as before) so the random draw
        # happens at the same point in the run and output stays reproducible
        sleep_time_list = csh.parse_time_values(csh.total_time)
        print("SLEEP TIMES ARE {}".format(sleep_time_list))

        parts = []

        # 1 : suppress the tray icon unless it is enabled
        if csh.icon == "False":
            parts.append("#NoTrayIcon\n")

        # 2 : UDF include headers added by the assigned tasks
        for include_header in csh.autoIT_UDF_includes:
            parts.append(include_header + '\n')

        # 3 : global typing speed
        parts.append(csh.typing_speed)

        # 4 : global task list + sleep-time arrays
        task_list_output, sleep_time_output = csh.autoIT_start(
            len(csh.tasks.keys()),
            csh.tasks.keys(),
            len(sleep_time_list),
            sleep_time_list)
        parts.append(task_list_output)
        parts.append(sleep_time_output)

        # 5 : window watcher cleanup function
        parts.append(textwrap.dedent(csh._window_watcher()))

        # 6 : the task loop (looping or single run)
        parts.append(textwrap.dedent(csh.task_loop()))

        # 7 : each assigned task's function definition
        for task_output in csh.tasks.values():
            parts.append(task_output)

        return "".join(parts)

    def escape(self, text):
        """
        Escape a user supplied string so AutoIT's Send() emits it literally.

        Mirrors BaseCMD.escape_autoit_send. Used when rendering the TypeLine,
        TypeText and RunDialog primitives. Tasks not yet converted to
        primitives still call escape_autoit_send directly.
        """
        if not isinstance(text, str):
            return text

        mapping = {
            '{': '{{}',
            '}': '{}}',
            '!': '{!}',
            '+': '{+}',
            '^': '{^}',
            '#': '{#}',
        }
        escaped = ''.join(mapping.get(char, char) for char in text)
        escaped = escaped.replace('"', '""')
        return escaped

    def comment(self, text):
        """ Format a source comment for this backend. """
        return "; " + text

    @staticmethod
    def _escape_literal(text):
        """
        Escape a string for a literal-string context such as ClipPut(), where
        only the double quote needs doubling. The Send-style brace escaping
        must NOT be applied here or the characters would reach the clipboard
        wrapped in braces.
        """
        if not isinstance(text, str):
            return text
        return text.replace('"', '""')

    # ------------------------------------------------------------------ >
    #   Primitive layer (phase 2)
    # ------------------------------------------------------------------ >

    def render_task(self, task_name, counter, primitives, emit_call=True):
        """
        Render a task, expressed as an ordered list of OS-neutral primitives,
        into an AutoIT function (plus the leading call unless this is a
        subtask, which the parent invokes instead).
        """

        lines = [
            "; < ----------------------------------- >",
            "; <      {} Interaction".format(task_name),
            "; < ----------------------------------- >",
            "",
        ]
        # you cannot nest functions in AutoIT, so only emit the call when this
        # is not being built as a subtask (the parent calls it in that case)
        if emit_call:
            lines.append("{}_{}()".format(task_name, counter))
        lines.append("")
        lines.append("Func {}_{}()".format(task_name, counter))
        lines.append("")

        for primitive in primitives:
            rendered = self._render_primitive(primitive)
            for rendered_line in rendered.split("\n"):
                lines.append(("    " + rendered_line) if rendered_line else "")

        lines.append("")
        lines.append("EndFunc")
        lines.append("")

        return "\n".join(lines) + "\n"

    def _render_primitive(self, p):
        """
        Render a single primitive to one or more lines of AutoIT.
        """
        op = getattr(p, "op", None)

        if op == "comment":
            return "; " + p.text
        if op == "rundialog":
            return ('Send("#r")\n'
                    '; Wait 10 seconds for the Run dialogue window to appear.\n'
                    'WinWaitActive("Run", "", 10)\n'
                    'Send("{}{{ENTER}}")'.format(self.escape(p.command)))
        if op == "type_line":
            return 'Send("{}{{ENTER}}")'.format(self.escape(p.text))
        if op == "type_text":
            return 'Send("{}")'.format(self.escape(p.text))
        if op == "send_keys":
            return 'Send("{}")'.format(p.keys)
        if op == "sleep":
            return "Sleep({})".format(p.ms)
        if op == "wait_window":
            return 'WinWaitActive("{}", "", {})'.format(p.spec, p.timeout)
        if op == "focus_window":
            return 'SendKeepActive("{}")'.format(p.spec)
        if op == "release_focus":
            return 'SendKeepActive("")'
        if op == "close_window":
            return 'WinClose("{}")'.format(p.spec)
        if op == "set_clipboard":
            return 'ClipPut("{}")'.format(self._escape_literal(p.text))
        if op == "call_function":
            return "{}()".format(p.name)
        if op == "raw":
            return p.code

        raise ValueError("unknown primitive op: {}".format(op))
