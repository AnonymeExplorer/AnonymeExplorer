"""RacOS - terminal + GUI operating system simulation for Pythonista 3 (iOS)."""

from __future__ import annotations

import datetime as _dt
import platform
import random
import shlex
import textwrap
from dataclasses import dataclass, field
from typing import Dict, List, Optional

try:
    import ui  # Pythonista specific
except Exception:  # pragma: no cover - optional outside Pythonista
    ui = None


@dataclass
class FakeFile:
    name: str
    content: str = ""
    is_dir: bool = False
    children: Dict[str, "FakeFile"] = field(default_factory=dict)


class FileSystem:
    def __init__(self) -> None:
        self.root = FakeFile("/", is_dir=True)
        self.cwd: List[str] = ["home", "user"]
        self._bootstrap()

    def _bootstrap(self) -> None:
        self.mkdir("/home")
        self.mkdir("/home/user")
        self.mkdir("/home/user/docs")
        self.mkdir("/home/user/bin")
        self.write_file("/home/user/docs/welcome.txt", "Witaj w RacOS!\nUżyj 'help' aby zobaczyć komendy.")
        self.write_file("/home/user/docs/changelog.txt", "RacOS 1.0\n- terminal\n- GUI\n- wirtualny system plików")

    def _split(self, path: str) -> List[str]:
        if path.startswith("/"):
            parts = [p for p in path.split("/") if p]
        else:
            parts = self.cwd + [p for p in path.split("/") if p]
        out: List[str] = []
        for part in parts:
            if part == ".":
                continue
            if part == "..":
                if out:
                    out.pop()
            else:
                out.append(part)
        return out

    def _get_node(self, path: str) -> Optional[FakeFile]:
        node = self.root
        for part in self._split(path):
            if not node.is_dir or part not in node.children:
                return None
            node = node.children[part]
        return node

    def _get_parent(self, path: str) -> tuple[Optional[FakeFile], str]:
        parts = self._split(path)
        if not parts:
            return None, ""
        parent_path = "/" + "/".join(parts[:-1]) if parts[:-1] else "/"
        return self._get_node(parent_path), parts[-1]

    def pwd(self) -> str:
        return "/" + "/".join(self.cwd)

    def cd(self, path: str) -> str:
        target = self._get_node(path)
        if not target:
            return f"cd: nie znaleziono: {path}"
        if not target.is_dir:
            return f"cd: to nie katalog: {path}"
        self.cwd = self._split(path)
        return ""

    def ls(self, path: str = ".") -> str:
        target = self._get_node(path)
        if not target:
            return f"ls: nie znaleziono: {path}"
        if not target.is_dir:
            return target.name
        names = sorted(target.children.keys())
        return "  ".join(names) if names else "(pusto)"

    def mkdir(self, path: str) -> str:
        parent, name = self._get_parent(path)
        if not parent or not parent.is_dir:
            return f"mkdir: nieprawidłowa ścieżka: {path}"
        if name in parent.children:
            return f"mkdir: już istnieje: {name}"
        parent.children[name] = FakeFile(name=name, is_dir=True)
        return ""

    def write_file(self, path: str, content: str) -> str:
        parent, name = self._get_parent(path)
        if not parent or not parent.is_dir:
            return f"write: nieprawidłowa ścieżka: {path}"
        parent.children[name] = FakeFile(name=name, content=content, is_dir=False)
        return ""

    def cat(self, path: str) -> str:
        node = self._get_node(path)
        if not node:
            return f"cat: nie znaleziono: {path}"
        if node.is_dir:
            return f"cat: {path} to katalog"
        return node.content

    def rm(self, path: str) -> str:
        parent, name = self._get_parent(path)
        if not parent or name not in parent.children:
            return f"rm: nie znaleziono: {path}"
        del parent.children[name]
        return ""


@dataclass
class Process:
    pid: int
    name: str
    cpu: float
    memory: int
    status: str = "RUNNING"


class ProcessManager:
    def __init__(self) -> None:
        self._next_pid = 100
        self.processes: Dict[int, Process] = {}
        for base in ("kernel", "shell", "netd", "uid"):
            self.spawn(base)

    def spawn(self, name: str) -> Process:
        p = Process(
            pid=self._next_pid,
            name=name,
            cpu=round(random.uniform(0.2, 9.7), 2),
            memory=random.randint(8, 120),
        )
        self.processes[p.pid] = p
        self._next_pid += 1
        return p

    def kill(self, pid: int) -> str:
        if pid not in self.processes:
            return f"kill: nie znaleziono PID {pid}"
        if self.processes[pid].name == "kernel":
            return "kill: nie można zakończyć procesu kernel"
        del self.processes[pid]
        return ""

    def table(self) -> str:
        lines = ["PID   NAME      CPU%   MEM(MB)  STATUS"]
        for pid in sorted(self.processes):
            p = self.processes[pid]
            lines.append(f"{p.pid:<5} {p.name:<9} {p.cpu:<6} {p.memory:<8} {p.status}")
        return "\n".join(lines)


class RacOS:
    VERSION = "1.0"

    def __init__(self) -> None:
        self.fs = FileSystem()
        self.pm = ProcessManager()
        self.boot_time = _dt.datetime.now()
        self.net_connected = True

    @property
    def prompt(self) -> str:
        return f"racos:{self.fs.pwd()}$ "

    def execute(self, command_line: str) -> str:
        if not command_line.strip():
            return ""
        try:
            parts = shlex.split(command_line)
        except ValueError as exc:
            return f"Błąd parsera: {exc}"
        cmd, *args = parts

        handlers = {
            "help": self._cmd_help,
            "pwd": lambda *_: self.fs.pwd(),
            "cd": self._cmd_cd,
            "ls": self._cmd_ls,
            "mkdir": self._cmd_mkdir,
            "touch": self._cmd_touch,
            "write": self._cmd_write,
            "cat": self._cmd_cat,
            "rm": self._cmd_rm,
            "date": lambda *_: _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "uptime": self._cmd_uptime,
            "sysinfo": self._cmd_sysinfo,
            "ps": lambda *_: self.pm.table(),
            "run": self._cmd_run,
            "kill": self._cmd_kill,
            "net": self._cmd_net,
            "gui": lambda *_: self.launch_gui(),
            "clear": lambda *_: "__CLEAR__",
            "exit": lambda *_: "__EXIT__",
        }

        if cmd not in handlers:
            return f"Nieznane polecenie: {cmd}. Użyj 'help'."
        return handlers[cmd](args)

    def _cmd_help(self, _args: List[str]) -> str:
        return textwrap.dedent(
            """
            Dostępne komendy:
              help                 - lista poleceń
              pwd                  - aktualny katalog
              cd <path>            - zmiana katalogu
              ls [path]            - listowanie plików
              mkdir <path>         - tworzenie katalogu
              touch <file>         - tworzenie pustego pliku
              write <file> <tekst> - zapis tekstu do pliku
              cat <file>           - odczyt pliku
              rm <path>            - usunięcie pliku/katalogu
              date                 - aktualna data i czas
              uptime               - czas działania RacOS
              sysinfo              - informacje o systemie
              ps                   - lista procesów
              run <name>           - start procesu użytkownika
              kill <pid>           - zakończenie procesu
              net [up|down|scan]   - stan i symulacja sieci
              gui                  - uruchomienie GUI
              clear                - wyczyszczenie terminala
              exit                 - wyjście z aplikacji
            """
        ).strip()

    def _cmd_cd(self, args: List[str]) -> str:
        if not args:
            return "cd: podaj ścieżkę"
        return self.fs.cd(args[0])

    def _cmd_ls(self, args: List[str]) -> str:
        return self.fs.ls(args[0] if args else ".")

    def _cmd_mkdir(self, args: List[str]) -> str:
        if not args:
            return "mkdir: podaj ścieżkę"
        return self.fs.mkdir(args[0])

    def _cmd_touch(self, args: List[str]) -> str:
        if not args:
            return "touch: podaj nazwę pliku"
        return self.fs.write_file(args[0], "")

    def _cmd_write(self, args: List[str]) -> str:
        if len(args) < 2:
            return "write: użycie write <plik> <tekst>"
        path = args[0]
        content = " ".join(args[1:])
        return self.fs.write_file(path, content)

    def _cmd_cat(self, args: List[str]) -> str:
        if not args:
            return "cat: podaj nazwę pliku"
        return self.fs.cat(args[0])

    def _cmd_rm(self, args: List[str]) -> str:
        if not args:
            return "rm: podaj ścieżkę"
        return self.fs.rm(args[0])

    def _cmd_uptime(self, _args: List[str]) -> str:
        delta = _dt.datetime.now() - self.boot_time
        secs = int(delta.total_seconds())
        return f"RacOS działa od {secs} sekund"

    def _cmd_sysinfo(self, _args: List[str]) -> str:
        return textwrap.dedent(
            f"""
            RacOS {self.VERSION}
            Host Python: {platform.python_version()}
            Platforma: {platform.platform()}
            Aktywnych procesów: {len(self.pm.processes)}
            Sieć: {'ONLINE' if self.net_connected else 'OFFLINE'}
            """
        ).strip()

    def _cmd_run(self, args: List[str]) -> str:
        if not args:
            return "run: podaj nazwę procesu"
        p = self.pm.spawn(args[0])
        return f"Uruchomiono {p.name} (PID={p.pid})"

    def _cmd_kill(self, args: List[str]) -> str:
        if not args:
            return "kill: podaj PID"
        try:
            pid = int(args[0])
        except ValueError:
            return "kill: PID musi być liczbą"
        return self.pm.kill(pid)

    def _cmd_net(self, args: List[str]) -> str:
        mode = args[0] if args else "status"
        if mode == "up":
            self.net_connected = True
            return "Interfejs sieciowy aktywny"
        if mode == "down":
            self.net_connected = False
            return "Interfejs sieciowy wyłączony"
        if mode == "scan":
            nets = ["RacNet-Office", "RacNet-Home", "Public-5G", "IoT-Lab"]
            random.shuffle(nets)
            return "Dostępne sieci:\n- " + "\n- ".join(nets[: random.randint(2, 4)])
        return "ONLINE" if self.net_connected else "OFFLINE"

    def launch_gui(self) -> str:
        if ui is None:
            return "GUI niedostępne poza Pythonista 3 (brak modułu 'ui')."

        os_ref = self

        class RacOSView(ui.View):
            def __init__(self):
                self.name = "RacOS GUI"
                self.background_color = "#101725"
                self.frame = (0, 0, 900, 620)
                self._build()

            def _build(self):
                title = ui.Label(frame=(20, 12, 860, 36))
                title.text = "RacOS Control Center"
                title.text_color = "white"
                title.font = ("<System-Bold>", 24)
                self.add_subview(title)

                self.info = ui.TextView(frame=(20, 56, 860, 200))
                self.info.editable = False
                self.info.background_color = "#1b2338"
                self.info.text_color = "#b7f7ff"
                self.info.font = ("Menlo", 14)
                self.add_subview(self.info)

                btn_specs = [
                    ("Odśwież", self.refresh, 20),
                    ("Nowy proces", self.new_process, 170),
                    ("Sieć SCAN", self.scan_net, 320),
                    ("Pokaż pliki", self.show_files, 470),
                ]
                for text, action, x in btn_specs:
                    btn = ui.Button(frame=(x, 270, 130, 44))
                    btn.title = text
                    btn.background_color = "#3e5a97"
                    btn.tint_color = "white"
                    btn.corner_radius = 8
                    btn.action = action
                    self.add_subview(btn)

                self.log = ui.TextView(frame=(20, 330, 860, 260))
                self.log.editable = False
                self.log.background_color = "#161f33"
                self.log.text_color = "#9ef0a7"
                self.log.font = ("Menlo", 13)
                self.add_subview(self.log)
                self.refresh(None)

            def _set_log(self, text):
                ts = _dt.datetime.now().strftime("%H:%M:%S")
                self.log.text = f"[{ts}] {text}\n" + self.log.text

            def refresh(self, _sender):
                self.info.text = os_ref._cmd_sysinfo([]) + "\n\n" + os_ref.pm.table()
                self._set_log("Odświeżono status systemu")

            def new_process(self, _sender):
                proc_name = f"app{random.randint(10,99)}"
                msg = os_ref._cmd_run([proc_name])
                self.refresh(None)
                self._set_log(msg)

            def scan_net(self, _sender):
                out = os_ref._cmd_net(["scan"])
                self._set_log(out)

            def show_files(self, _sender):
                listing = os_ref.fs.ls("/home/user/docs")
                self._set_log("/home/user/docs -> " + listing)

        view = RacOSView()
        view.present(style="fullscreen", hide_title_bar=True)
        return "GUI uruchomione"


class TerminalApp:
    def __init__(self):
        self.os = RacOS()

    def run(self) -> None:
        print("=" * 56)
        print("  RacOS Terminal Simulator (Pythonista 3 / iOS)")
        print("=" * 56)
        print("Wpisz 'help' aby zobaczyć komendy. 'exit' aby zakończyć.\n")
        while True:
            try:
                cmd = input(self.os.prompt)
            except (EOFError, KeyboardInterrupt):
                print("\nZamykanie RacOS...")
                break

            output = self.os.execute(cmd)
            if output == "__CLEAR__":
                print("\n" * 60)
                continue
            if output == "__EXIT__":
                print("Zamykanie RacOS...")
                break
            if output:
                print(output)


def main() -> None:
    TerminalApp().run()


if __name__ == "__main__":
    main()
