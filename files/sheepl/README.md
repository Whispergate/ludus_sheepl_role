# Sheepl

Creating realistic user behaviour for supporting tradecraft development within
lab environments.

## Introduction

A network is not a collection of static endpoints. It is a platform for
communication between people. Most lab environments miss that: the hosts sit
idle while you practise against them.

Sheepl emulates the ordinary things people do on a network so that a lab looks
and behaves like a working one. You describe what a user does over a day, such
as opening a shell, browsing to a few sites, writing a document, copying a
password out of a vault, and Sheepl emits a script that performs those actions
on an endpoint, in a randomised order, across a time window you choose.

For red teamers, that benign activity creates moments to practise tradecraft
inside. For blue teamers, it is realistic noise to practise detecting malicious
activity within.

## How it works

You give Sheepl a profile (or build one interactively). Sheepl turns each task
into a sequence of platform-neutral steps, then renders those steps for a target:

- **Windows**: an AutoIT (`.au3`) script you compile to a standalone `.exe` with
  Aut2EXE, then run on the endpoint.
- **Linux (X11)**: a bash script that drives `xdotool` and `xclip`.

One profile can produce either, selected with `--target`.

## Requirements

- Python 3.6 or newer. The tool uses only the standard library.
- For Windows output: the AutoIT3 runtime and the Aut2EXE compiler,
  from https://www.autoitscript.com/site/autoit/downloads/
- For Linux output: `xdotool` and `xclip`. To run on a headless server, also
  `Xvfb` (the script starts a virtual display by itself); a window manager such
  as `openbox` is used automatically if it is installed.

## Usage

Interactive console:

```bash
python3 sheepl.py --interactive
```

Build from a JSON profile:

```bash
python3 sheepl.py --profile profiles/analyst.json
```

Produce a Linux bash script instead of AutoIT:

```bash
python3 sheepl.py --profile profiles/crossplatform.json --target linux
```

Output is written to `output/<name>.au3` for Windows or `output/<name>.sh` for
Linux.

### Options

| Flag | Effect |
| --- | --- |
| `--interactive` | Launch the interactive console. |
| `--profile <path>` | Build a Sheepl from a JSON profile. |
| `--target windows\|linux` | Select the output backend. Default is `windows`. |
| `--no_loop` | Run the task list once instead of looping over the time window. |
| `--no_tray` | Suppress the compiled script's system-tray icon (Windows). |
| `--no_colour` | Plain terminal output, no ANSI colour. |

### Interactive console

Create a Sheepl, assign tasks, then write the file:

```
create <name>      start a new Sheepl and set its time window and typing speed
list               show the available tasks
task <TaskName>    assign a task (drops into that task's own prompt)
loop               toggle whether the task list repeats
icon               toggle the compiled tray icon
finished           write the output file
quit               exit
```

Each task opens a short sub-console. Type `help` there for its commands.

## Tasks

| Task | Category | Windows | Linux | Notes |
| --- | --- | --- | --- | --- |
| Browser | browsing | yes | yes | edge, chrome, firefox or default; opens each URL in a tab. On Linux use `firefox`. |
| Clipboard | core | yes | yes | Copies a sequence of notes or passwords. Optional wipe on exit. |
| RunCommand | core | yes | yes | Runs a single command through the launcher. |
| LibreOfficeWriter | office | yes | yes | Types a text file into a Writer document and saves it. |
| LibreOfficeCalc | office | yes | yes | Enters rows of data into a Calc spreadsheet and saves it. |
| Thunderbird | mail | yes | yes | Composes an email. Saves a draft by default, or set `send`. |
| VLC | media | yes | yes | Plays a local file or a stream URL. |
| CommandShell | shell | yes | partial | cmd.exe. On Linux the typed commands render, but it launches `cmd`. |
| PowerShell | shell | yes | partial | As CommandShell, with `powershell`. |
| WordDocument | office | yes | no | MS Word via COM. Use LibreOfficeWriter on Linux. |
| RemoteDesktop | network | yes | no | mstsc. Runs assigned subtasks inside the session. |
| PuttyConnection | network | yes | no | SSH through PuTTY. Use a terminal and `ssh` on Linux. |
| KeePass | credentials | yes | no | Opens a database with a master password. |
| InternetExplorer | browsing | legacy | no | Removed on Windows 11. Use Browser. |

Under `--target linux`, the cross-platform tasks produce complete scripts. The
Windows-specific tasks emit their application steps as skipped comments, so the
script stays valid and you can see where a Linux-native equivalent would go.

## Profiles

A profile is a JSON file describing one Sheepl and the tasks it runs.

```json
{
  "sheepl": {
    "name": "Harper",
    "total_time": "25m",
    "typing_speed": 60,
    "loop": "True",
    "icon": "False",
    "tasks": [
      { "task": "Browser", "browser": "edge", "urls": ["https://www.virustotal.com"] },
      { "task": "PowerShell", "cmd": ["Get-Process", "$psversiontable"] },
      { "task": "Clipboard", "clear": true, "items": ["IOC: 185.220.101.4 suspected C2"] }
    ]
  }
}
```

Top-level keys:

- `name`: the Sheepl's name, also the output file name.
- `total_time`: the window the tasks are spread across. Suffix with `m`, `h` or
  `d`, for example `45m`, `6h`, `2d`.
- `typing_speed`: milliseconds between keystrokes.
- `loop`: `"True"` to repeat the task list, `"False"` to run it once.
- `icon`: `"False"` to suppress the Windows tray icon.
- `target` (optional): `"windows"` or `"linux"`. Overrides `--target` for this
  profile.
- `tasks`: a list of task objects.

Each task object has a `task` key naming the module, plus the keys that module
needs. Common ones:

| Task | Keys |
| --- | --- |
| Browser | `browser`, `urls` |
| Clipboard | `items`, `clear` (optional) |
| CommandShell / PowerShell | `cmd` (list) |
| RunCommand | `cmd` (list; the first is used) |
| LibreOfficeWriter / WordDocument | `input_file`, `save_name` |
| LibreOfficeCalc | `rows` (list of lists), `save_name` |
| Thunderbird | `to`, `subject`, `body` (optional), `send` (optional) |
| VLC | `media` |
| RemoteDesktop | `computer`, `username`, `password`, `subtasks` (optional) |
| PuttyConnection | `computer`, `username`, `password`, `cmd` |
| KeePass | `database_location`, `masterpassword` |

The `profiles/` directory ships several personas (analyst, developer, helpdesk,
executive, sysadmin and others). `crossplatform.json` uses only cross-platform
tasks and runs with `--target linux`.

WordDocument and LibreOffice tasks read their text from a file. `content/if.txt`
is a sample so the shipped profiles run as delivered; replace it with your own.

## Running the output

Windows: compile `output/<name>.au3` with Aut2EXE (or run it with the AutoIT3
runtime), then execute the result on the endpoint.

Linux: make the script executable and run it.

```bash
chmod +x output/<name>.sh
./output/<name>.sh
```

On a desktop session it uses the current display. On a headless server with no
`DISPLAY`, it starts a virtual display with Xvfb (install `Xvfb`, and optionally
a window manager such as `openbox`), runs the activity there, and shuts the
display down on exit. Window matching is best-effort: the window hints come from
the Windows definition, so you may need to adjust a name for your window
manager.

## Adding a task

A task lives in `tasks/<category>/<Name>.py` and is discovered automatically, so
dropping a file into a category directory is enough to register it. A task
collects its inputs, from the interactive console or a profile, and returns an
ordered list of platform-neutral primitives from `build_primitives()`. A backend
renders that list to AutoIT or bash.

The primitives are defined in `utils/primitives.py` (launch, type, send keys,
sleep, window waits, focus, clipboard, call a function, and a `Raw` escape hatch
for a step that only one platform has). The backends are in `utils/backends/`.
Use `RunCommand` or `Clipboard` as a short example to copy from.

## Credits

Sheepl was created by Matt Lorentzen (@lorentzenman).

- The AutoIT language: https://www.autoitscript.com, by Jonathan Bennett.
- The Python language: https://www.python.org, by Guido van Rossum.

## Videos

Sheepl 2.0 demo: https://www.youtube.com/watch?v=S4Zvw-IG1Pc

44Con workshop: https://www.youtube.com/watch?v=ZErvmrP4UCg
