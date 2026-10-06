"""
Linux (xdotool) output backend.

Renders the same OS-neutral primitive lists that the AutoIT backend renders,
but emits a bash script driving xdotool / xclip instead of an AutoIT .au3 file.
Selected with `--target linux` or a profile "target": "linux".

The generated script runs on a normal desktop session, or headless on a server:
if no X display is present it starts a virtual one with Xvfb (and a lightweight
window manager if one is installed), so it needs no monitor or logged-in GUI.

Scope and honesty:
    * The genuinely cross-platform tasks — Browser (firefox/chromium),
      LibreOffice Writer/Calc, Thunderbird, VLC, Clipboard, RunCommand — emit
      complete, runnable bash.
    * Windows-only tasks (cmd/powershell shells, mstsc RDP, PuTTY, MS Word,
      Internet Explorer, the KeePass path-launch) express their Windows-specific
      steps through Raw primitives, which this backend renders as skipped
      comments. Launching those binaries on Linux simply no-ops.
    * X11 window matching is approximate : the window specs in the primitives
      are Windows-derived (AutoIT class names), so WaitWindow/FocusWindow are
      best-effort xdotool searches with a sleep fallback.
"""

__author__ = "Lavender-exe"
__license__ = "MIT"


import re

from utils.backends.base_backend import Backend


class XdotoolBackend(Backend):

    name = "xdotool"
    file_extension = ".sh"
    # a bash script must use LF line endings or it breaks on Linux (the shebang
    # and tokens pick up a stray \r), so force LF even when generating on Windows
    newline = "\n"

    # ------------------------------------------------------------------ >
    #   Assembly
    # ------------------------------------------------------------------ >

    def assemble(self, csh):
        """
        Render the Sheepl object into a complete bash + xdotool script : the
        task functions, a task list with per-task sleeps, and a scheduler loop.
        """

        # reuse the shared timing distribution (milliseconds) and convert to
        # whole seconds for bash's sleep
        sleep_ms = csh.parse_time_values(csh.total_time)
        sleeps = [max(1, int(round(ms / 1000.0))) for ms in sleep_ms]
        print("SLEEP TIMES ARE {}".format(sleeps))

        lines = [
            "#!/usr/bin/env bash",
            "#",
            "# Sheepl behaviour script - xdotool (Linux) backend",
            "# Runs on a desktop session, or headless on a server via Xvfb.",
            "# Requires: xdotool, xclip, and (for headless use) Xvfb. A window",
            "# manager (openbox/fluxbox/jwm/twm) is used automatically if present.",
            "#",
            "# Cross-platform tasks (Browser[firefox], LibreOffice, Thunderbird,",
            "# VLC, Clipboard, RunCommand) run as-is. Windows-only tasks emit their",
            "# app-specific steps as skipped comments.",
            "set -u",
            "",
            'command -v xdotool >/dev/null 2>&1 || { echo "[!] xdotool is required" >&2; exit 1; }',
            "",
            "# --- headless display bootstrap ---",
            "# Use the current X display if one is present; otherwise start a virtual",
            "# display (Xvfb) so the GUI apps and xdotool run on a headless server.",
            "SHEEPL_STARTED_XVFB=0",
            'if [ -z "${DISPLAY:-}" ]; then',
            '    command -v Xvfb >/dev/null 2>&1 || { echo "[!] no DISPLAY and Xvfb not installed (needed for headless use)" >&2; exit 1; }',
            '    export DISPLAY=":99"',
            '    Xvfb "$DISPLAY" -screen 0 1920x1080x24 >/dev/null 2>&1 &',
            "    SHEEPL_XVFB_PID=$!",
            "    SHEEPL_STARTED_XVFB=1",
            "    sleep 2",
            "    # start a lightweight window manager if one is installed (helps focus)",
            "    for sheepl_wm in openbox fluxbox jwm twm; do",
            '        if command -v "$sheepl_wm" >/dev/null 2>&1; then "$sheepl_wm" >/dev/null 2>&1 & break; fi',
            "    done",
            "    sleep 1",
            "fi",
            'cleanup_sheepl() { [ "$SHEEPL_STARTED_XVFB" = "1" ] && kill "${SHEEPL_XVFB_PID:-}" >/dev/null 2>&1; }',
            "trap cleanup_sheepl EXIT",
            "",
        ]

        # task function definitions
        for task_output in csh.tasks.values():
            lines.append(task_output)

        # scheduler
        task_names = list(csh.tasks.keys())
        lines.append("# ----------------------------------- #")
        lines.append("#              scheduler")
        lines.append("# ----------------------------------- #")
        lines.append("tasks=({})".format(" ".join(task_names) if task_names else ""))
        lines.append("sleeptimes=({})".format(" ".join(str(s) for s in sleeps)))
        lines.append("")
        lines.append("run_once() {")
        lines.append("    local i=0")
        lines.append('    for task in "${tasks[@]}"; do')
        lines.append('        sleep "${sleeptimes[$((i % ${#sleeptimes[@]}))]}"')
        lines.append('        "$task"')
        lines.append("        i=$((i + 1))")
        lines.append("    done")
        lines.append("}")
        lines.append("")
        if csh.loop == "True":
            lines.append("while true; do")
            lines.append("    run_once")
            lines.append("done")
        else:
            lines.append("run_once")
        lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------ >
    #   Task + primitive rendering
    # ------------------------------------------------------------------ >

    def render_task(self, task_name, counter, primitives, emit_call=True):
        """
        Render a task's primitive list into a bash function. `emit_call` is
        ignored : bash defines every function up front and the scheduler (or a
        parent task, for subtasks) calls it by name, so no inline call is needed.
        """

        body = []
        has_command = False
        for primitive in primitives:
            rendered = self._render_primitive(primitive)
            for rendered_line in rendered.split("\n"):
                if rendered_line:
                    body.append("    " + rendered_line)
                    stripped = rendered_line.strip()
                    if stripped and not stripped.startswith("#"):
                        has_command = True
                else:
                    body.append("")

        # a bash function needs at least one command; a task whose steps are all
        # skipped on this backend (e.g. a Windows-only task) would otherwise be
        # an empty body, which is a syntax error
        if not has_command:
            body.append("    :")

        lines = [
            "# < {} Interaction >".format(task_name),
            "{}_{}() {{".format(task_name, counter),
        ]
        lines.extend(body)
        lines.append("}")
        lines.append("")

        return "\n".join(lines) + "\n"

    def _render_primitive(self, p):
        op = getattr(p, "op", None)

        if op == "comment":
            return "# " + p.text
        if op == "rundialog":
            return ("# launch: {}\n"
                    "setsid {} >/dev/null 2>&1 &").format(p.command, p.command)
        if op == "type_line":
            return ('xdotool type --clearmodifiers -- "{}"\n'
                    "xdotool key Return").format(self.escape(p.text))
        if op == "type_text":
            return 'xdotool type --clearmodifiers -- "{}"'.format(self.escape(p.text))
        if op == "send_keys":
            return "xdotool key {}".format(" ".join(self._xdotool_keys(p.keys)))
        if op == "sleep":
            return "sleep {:g}".format(p.ms / 1000.0)
        if op == "wait_window":
            name = self._lin_name(p.spec)
            return ('# wait for window: {} (X11 matching is best-effort)\n'
                    'xdotool search --sync --onlyvisible --limit 1 "{}" >/dev/null 2>&1 '
                    "|| sleep {}").format(p.spec, self.escape(name), p.timeout)
        if op == "focus_window":
            name = self._lin_name(p.spec)
            return ('xdotool search --onlyvisible --limit 1 "{}" windowactivate '
                    ">/dev/null 2>&1 || true").format(self.escape(name))
        if op == "release_focus":
            return ": # release focus (no-op on Linux)"
        if op == "close_window":
            name = self._lin_name(p.spec)
            return ('xdotool search --onlyvisible --limit 1 "{}" windowclose '
                    ">/dev/null 2>&1 || xdotool key alt+F4").format(self.escape(name))
        if op == "set_clipboard":
            return 'printf %s "{}" | xclip -selection clipboard'.format(self.escape(p.text))
        if op == "call_function":
            return "{}".format(p.name)
        if op == "raw":
            if getattr(p, "xdotool", None):
                return p.xdotool
            return "# [sheepl] AutoIT-specific step omitted on the linux backend"

        raise ValueError("unknown primitive op: {}".format(op))

    # ------------------------------------------------------------------ >
    #   Helpers
    # ------------------------------------------------------------------ >

    def comment(self, text):
        """ Format a source comment for this backend. """
        return "# " + text

    def escape(self, text):
        """ Escape a string for a bash double-quoted context. """
        if not isinstance(text, str):
            return text
        for find, repl in (("\\", "\\\\"), ('"', '\\"'), ("$", "\\$"), ("`", "\\`")):
            text = text.replace(find, repl)
        return text

    def _xdotool_keys(self, keys):
        """
        Translate an AutoIT Send key string into a list of xdotool key specs.
        Handles the modifier prefixes ^ ! + # and the { } key tokens used by
        the tasks (e.g. '^t' -> 'ctrl+t', '!{F4}' -> 'alt+F4',
        '{TAB}{TAB}' -> ['Tab','Tab'], '{ALT}{HOME}' -> 'alt+Home').
        """
        mods = {'^': 'ctrl', '!': 'alt', '+': 'shift', '#': 'super'}
        special = {
            'ENTER': 'Return', 'TAB': 'Tab', 'F4': 'F4', 'CAPSLOCK': 'Caps_Lock',
            'HOME': 'Home', 'ALT': 'alt', 'SPACE': 'space', 'ESC': 'Escape',
            'DEL': 'Delete', 'BACKSPACE': 'BackSpace',
        }
        presses = []
        cur_mods = []
        i = 0
        n = len(keys)
        while i < n:
            c = keys[i]
            if c in mods:
                cur_mods.append(mods[c])
                i += 1
                continue
            if c == '{':
                j = keys.find('}', i)
                if j == -1:
                    break
                token = keys[i + 1:j].upper()
                name = special.get(token, token)
                # {ALT}/{SHIFT}/... acting as a leading modifier for the next key
                if name in ('alt', 'ctrl', 'shift', 'super') and not cur_mods:
                    cur_mods.append(name)
                    i = j + 1
                    continue
                presses.append('+'.join(cur_mods + [name]) if cur_mods else name)
                cur_mods = []
                i = j + 1
                continue
            # a literal character
            presses.append('+'.join(cur_mods + [c]) if cur_mods else c)
            cur_mods = []
            i += 1
        return presses or ["space"]

    def _lin_name(self, spec):
        """
        Derive a best-effort window-name hint from an AutoIT window spec. The
        specs are Windows-derived, so this is approximate and the user may need
        to adjust it for their window manager.
        """
        if spec.startswith("[CLASS:") and spec.endswith("]"):
            return spec[len("[CLASS:"):-1]
        if spec.startswith("[TITLE:") and spec.endswith("]"):
            return spec[len("[TITLE:"):-1]
        if "REGEXPTITLE:" in spec:
            inner = spec.split("REGEXPTITLE:", 1)[1].rstrip("]")
            words = re.findall(r"[A-Za-z0-9 ]+", inner)
            candidate = max(words, key=len) if words else inner
            return candidate.strip(" .*")
        return spec
