"""RacOS - advanced terminal-first OS simulation for Pythonista 3 (iOS)."""

from __future__ import annotations

import datetime as _dt
import platform
import random
import re
import shlex
import textwrap
from dataclasses import dataclass, field
from fnmatch import fnmatch
from typing import Dict, List, Optional


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
        for path in [
            "/home",
            "/home/user",
            "/home/user/docs",
            "/home/user/bin",
            "/home/user/projects",
            "/home/user/.config",
            "/var",
            "/var/log",
            "/tmp",
            "/usr",
            "/usr/share",
        ]:
            self.mkdir(path)
        self.write_file("/home/user/docs/welcome.txt", "Witaj w RacOS Shell 2.0")
        self.write_file("/var/log/boot.log", "[ OK ] RacOS shell initialized")

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
        if path == "/":
            return self.root
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

    def abspath(self, path: str) -> str:
        return "/" + "/".join(self._split(path))

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

    def ls(self, path: str = ".", all_entries: bool = False) -> str:
        target = self._get_node(path)
        if not target:
            return f"ls: nie znaleziono: {path}"
        if not target.is_dir:
            return target.name
        names = sorted(target.children.keys())
        if not all_entries:
            names = [n for n in names if not n.startswith(".")]
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

    def append_file(self, path: str, content: str) -> str:
        node = self._get_node(path)
        if not node:
            return self.write_file(path, content)
        if node.is_dir:
            return f"append: {path} to katalog"
        node.content += content
        return ""

    def cat(self, path: str) -> str:
        node = self._get_node(path)
        if not node:
            return f"cat: nie znaleziono: {path}"
        if node.is_dir:
            return f"cat: {path} to katalog"
        return node.content

    def rm(self, path: str, recursive: bool = False) -> str:
        parent, name = self._get_parent(path)
        if not parent or name not in parent.children:
            return f"rm: nie znaleziono: {path}"
        node = parent.children[name]
        if node.is_dir and node.children and not recursive:
            return "rm: katalog nie jest pusty (użyj -r)"
        del parent.children[name]
        return ""

    def cp(self, src: str, dst: str) -> str:
        src_node = self._get_node(src)
        if not src_node:
            return f"cp: brak źródła: {src}"
        if src_node.is_dir:
            return "cp: kopiowanie katalogów nieobsługiwane"
        return self.write_file(dst, src_node.content)

    def mv(self, src: str, dst: str) -> str:
        src_node = self._get_node(src)
        if not src_node:
            return f"mv: brak źródła: {src}"
        if src_node.is_dir:
            return "mv: przenoszenie katalogów nieobsługiwane"
        cp_err = self.cp(src, dst)
        if cp_err:
            return cp_err
        return self.rm(src)

    def find(self, start: str, pattern: str) -> List[str]:
        root = self._get_node(start)
        if not root:
            return []

        abs_start = self.abspath(start)
        results: List[str] = []

        def walk(node: FakeFile, base: str) -> None:
            for name, child in node.children.items():
                full = (base.rstrip("/") + "/" + name).replace("//", "/")
                if fnmatch(name, pattern):
                    results.append(full)
                if child.is_dir:
                    walk(child, full)

        if root.is_dir:
            walk(root, abs_start)
        else:
            if fnmatch(root.name, pattern):
                results.append(abs_start)
        return results


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
        for base in ("kernel", "shell", "netd", "loggerd", "pkgd"):
            self.spawn(base)

    def spawn(self, name: str) -> Process:
        p = Process(
            pid=self._next_pid,
            name=name,
            cpu=round(random.uniform(0.2, 20.0), 2),
            memory=random.randint(8, 180),
        )
        self.processes[p.pid] = p
        self._next_pid += 1
        return p

    def tick(self) -> None:
        for p in self.processes.values():
            p.cpu = round(max(0.1, min(98.0, p.cpu + random.uniform(-2.5, 2.5))), 2)
            p.memory = max(4, p.memory + random.randint(-3, 5))

    def kill(self, pid: int) -> str:
        if pid not in self.processes:
            return f"kill: nie znaleziono PID {pid}"
        if self.processes[pid].name == "kernel":
            return "kill: nie można zakończyć procesu kernel"
        del self.processes[pid]
        return ""

    def table(self) -> str:
        self.tick()
        lines = ["PID   NAME       CPU%   MEM(MB)  STATUS"]
        for pid in sorted(self.processes):
            p = self.processes[pid]
            lines.append(f"{p.pid:<5} {p.name:<10} {p.cpu:<6} {p.memory:<8} {p.status}")
        return "\n".join(lines)


class PackageManager:
    def __init__(self) -> None:
        self.repo = {
            "python": "3.12",
            "nano": "8.1",
            "htop": "3.4",
            "git": "2.49",
            "curl": "8.8",
            "nmap": "7.96",
            "vim": "9.1",
            "tmux": "3.5",
        }
        self.installed = {"python": "3.12", "nano": "8.1"}

    def search(self, query: str) -> str:
        hits = [f"{k} {v}" for k, v in sorted(self.repo.items()) if query.lower() in k.lower()]
        return "\n".join(hits) if hits else "Brak wyników"

    def install(self, name: str) -> str:
        if name not in self.repo:
            return f"pkg: pakiet '{name}' nie istnieje"
        self.installed[name] = self.repo[name]
        return f"Zainstalowano {name} {self.repo[name]}"

    def upgrade(self) -> str:
        for k in list(self.installed):
            self.installed[k] = self.repo.get(k, self.installed[k])
        return "Zaktualizowano pakiety"

    def list_installed(self) -> str:
        return "\n".join(f"{k} {v}" for k, v in sorted(self.installed.items()))


class RacOS:
    VERSION = "2.0"

    def __init__(self) -> None:
        self.fs = FileSystem()
        self.pm = ProcessManager()
        self.pkg = PackageManager()
        self.boot_time = _dt.datetime.now()
        self.net_connected = True
        self.history: List[str] = []
        self.aliases: Dict[str, str] = {"ll": "ls -a", "..": "cd .."}
        self.env: Dict[str, str] = {
            "USER": "user",
            "SHELL": "racos-sh",
            "HOME": "/home/user",
            "EDITOR": "nano",
            "PATH": "/home/user/bin:/usr/bin:/bin",
        }

    @property
    def prompt(self) -> str:
        return f"{self.env['USER']}@racos:{self.fs.pwd()}$ "

    def execute(self, command_line: str) -> str:
        if not command_line.strip():
            return ""
        self.history.append(command_line)

        # alias expansion for first token
        for a, repl in self.aliases.items():
            if command_line == a or command_line.startswith(a + " "):
                command_line = command_line.replace(a, repl, 1)
                break

        try:
            parts = shlex.split(command_line)
        except ValueError as exc:
            return f"Błąd parsera: {exc}"
        cmd, *args = parts

        handlers = {
            "help": self._cmd_help,
            "man": self._cmd_man,
            "pwd": lambda *_: self.fs.pwd(),
            "cd": self._cmd_cd,
            "ls": self._cmd_ls,
            "mkdir": self._cmd_mkdir,
            "touch": self._cmd_touch,
            "write": self._cmd_write,
            "append": self._cmd_append,
            "cat": self._cmd_cat,
            "rm": self._cmd_rm,
            "cp": self._cmd_cp,
            "mv": self._cmd_mv,
            "find": self._cmd_find,
            "grep": self._cmd_grep,
            "echo": self._cmd_echo,
            "history": self._cmd_history,
            "alias": self._cmd_alias,
            "export": self._cmd_export,
            "env": self._cmd_env,
            "clear": lambda *_: "__CLEAR__",
            "date": lambda *_: _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "uptime": self._cmd_uptime,
            "whoami": lambda *_: self.env["USER"],
            "uname": self._cmd_uname,
            "sysinfo": self._cmd_sysinfo,
            "df": self._cmd_df,
            "free": self._cmd_free,
            "ps": lambda *_: self.pm.table(),
            "top": lambda *_: self.pm.table(),
            "run": self._cmd_run,
            "kill": self._cmd_kill,
            "net": self._cmd_net,
            "ping": self._cmd_ping,
            "pkg": self._cmd_pkg,
            "exit": lambda *_: "__EXIT__",
        }

        if cmd not in handlers:
            return f"Nieznane polecenie: {cmd}. Użyj 'help'."
        return handlers[cmd](args)

    def _cmd_help(self, _args: List[str]) -> str:
        return textwrap.dedent(
            """
            RacOS Shell 2.0 — dostępne komendy:
              help, man <cmd>, clear, exit
              pwd, cd, ls, mkdir, touch, write, append, cat, rm, cp, mv
              find <path> <pattern>, grep <regex> <file>
              echo, history, alias, export, env
              whoami, uname, date, uptime, sysinfo, df, free
              ps, top, run, kill
              net [status|up|down|scan], ping <host>
              pkg [search|install|list|upgrade] [name]
            """
        ).strip()

    def _cmd_man(self, args: List[str]) -> str:
        manuals = {
            "ls": "ls [-a] [path] -> listuje zawartość katalogu",
            "grep": "grep <regex> <file> -> filtruje linie pasujące do regex",
            "pkg": "pkg search|install|list|upgrade [name]",
            "alias": "alias name='polecenie' lub alias (lista)",
            "export": "export KEY=VALUE",
            "find": "find <start_path> <glob_pattern>",
        }
        if not args:
            return "man: podaj nazwę polecenia"
        return manuals.get(args[0], f"Brak manuala dla {args[0]}")

    def _cmd_cd(self, args: List[str]) -> str:
        if not args:
            return self.fs.cd(self.env["HOME"])
        return self.fs.cd(args[0])

    def _cmd_ls(self, args: List[str]) -> str:
        all_entries = "-a" in args
        path_args = [a for a in args if not a.startswith("-")]
        target = path_args[0] if path_args else "."
        return self.fs.ls(target, all_entries=all_entries)

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
        return self.fs.write_file(args[0], " ".join(args[1:]))

    def _cmd_append(self, args: List[str]) -> str:
        if len(args) < 2:
            return "append: użycie append <plik> <tekst>"
        return self.fs.append_file(args[0], " ".join(args[1:]))

    def _cmd_cat(self, args: List[str]) -> str:
        if not args:
            return "cat: podaj nazwę pliku"
        return self.fs.cat(args[0])

    def _cmd_rm(self, args: List[str]) -> str:
        if not args:
            return "rm: podaj ścieżkę"
        recursive = "-r" in args
        target = [a for a in args if not a.startswith("-")][0]
        return self.fs.rm(target, recursive=recursive)

    def _cmd_cp(self, args: List[str]) -> str:
        if len(args) != 2:
            return "cp: użycie cp <src> <dst>"
        return self.fs.cp(args[0], args[1])

    def _cmd_mv(self, args: List[str]) -> str:
        if len(args) != 2:
            return "mv: użycie mv <src> <dst>"
        return self.fs.mv(args[0], args[1])

    def _cmd_find(self, args: List[str]) -> str:
        if len(args) != 2:
            return "find: użycie find <start> <pattern>"
        out = self.fs.find(args[0], args[1])
        return "\n".join(out) if out else "Brak wyników"

    def _cmd_grep(self, args: List[str]) -> str:
        if len(args) != 2:
            return "grep: użycie grep <regex> <plik>"
        content = self.fs.cat(args[1])
        if content.startswith("cat:"):
            return content
        try:
            rx = re.compile(args[0])
        except re.error as exc:
            return f"grep: nieprawidłowy regex: {exc}"
        lines = [line for line in content.splitlines() if rx.search(line)]
        return "\n".join(lines) if lines else "Brak dopasowań"

    def _cmd_echo(self, args: List[str]) -> str:
        out = " ".join(args)
        for key, val in self.env.items():
            out = out.replace(f"${key}", val)
        return out

    def _cmd_history(self, _args: List[str]) -> str:
        start = max(0, len(self.history) - 100)
        return "\n".join(f"{idx+1:>3}  {cmd}" for idx, cmd in enumerate(self.history[start:], start))

    def _cmd_alias(self, args: List[str]) -> str:
        if not args:
            return "\n".join(f"alias {k}='{v}'" for k, v in sorted(self.aliases.items()))
        chunk = " ".join(args)
        if "=" not in chunk:
            return "alias: użycie alias name='komenda'"
        name, value = chunk.split("=", 1)
        name = name.strip()
        value = value.strip().strip("\"").strip("'")
        self.aliases[name] = value
        return ""

    def _cmd_export(self, args: List[str]) -> str:
        if not args or "=" not in args[0]:
            return "export: użycie export KEY=VALUE"
        key, value = args[0].split("=", 1)
        self.env[key] = value
        return ""

    def _cmd_env(self, _args: List[str]) -> str:
        return "\n".join(f"{k}={v}" for k, v in sorted(self.env.items()))

    def _cmd_uptime(self, _args: List[str]) -> str:
        delta = _dt.datetime.now() - self.boot_time
        secs = int(delta.total_seconds())
        hours, rem = divmod(secs, 3600)
        mins, sec = divmod(rem, 60)
        return f"up {hours:02d}:{mins:02d}:{sec:02d}"

    def _cmd_uname(self, args: List[str]) -> str:
        if args and args[0] == "-a":
            return f"RacOS racos-shell {self.VERSION} {platform.machine()} Python/{platform.python_version()}"
        return "RacOS"

    def _cmd_sysinfo(self, _args: List[str]) -> str:
        return textwrap.dedent(
            f"""
            RacOS {self.VERSION}
            Host Python: {platform.python_version()}
            Platforma: {platform.platform()}
            Procesy: {len(self.pm.processes)}
            Sieć: {'ONLINE' if self.net_connected else 'OFFLINE'}
            """
        ).strip()

    def _cmd_df(self, _args: List[str]) -> str:
        used = sum(p.memory for p in self.pm.processes.values())
        total = 4096
        return f"Filesystem   Size  Used  Avail\n/dev/racos   {total}M  {used}M  {total-used}M"

    def _cmd_free(self, _args: List[str]) -> str:
        used = sum(p.memory for p in self.pm.processes.values())
        total = 2048
        free = max(0, total - used)
        return f"              total   used   free\nMem:          {total}   {used}   {free}"

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
            nets = ["RacNet-Office", "RacNet-Home", "Public-5G", "IoT-Lab", "CoffeeSpot"]
            random.shuffle(nets)
            return "Dostępne sieci:\n- " + "\n- ".join(nets[: random.randint(2, 5)])
        return "ONLINE" if self.net_connected else "OFFLINE"

    def _cmd_ping(self, args: List[str]) -> str:
        if not args:
            return "ping: podaj host"
        if not self.net_connected:
            return "ping: brak połączenia sieciowego"
        host = args[0]
        out = []
        for i in range(1, 5):
            latency = round(random.uniform(14, 89), 2)
            out.append(f"64 bytes from {host}: icmp_seq={i} ttl=64 time={latency} ms")
        out.append("--- ping statistics ---")
        out.append("4 packets transmitted, 4 received, 0% packet loss")
        return "\n".join(out)

    def _cmd_pkg(self, args: List[str]) -> str:
        if not args:
            return "pkg: użycie pkg search|install|list|upgrade [name]"
        action = args[0]
        if action == "search":
            if len(args) < 2:
                return "pkg search: podaj nazwę"
            return self.pkg.search(args[1])
        if action == "install":
            if len(args) < 2:
                return "pkg install: podaj nazwę"
            return self.pkg.install(args[1])
        if action == "list":
            return self.pkg.list_installed()
        if action == "upgrade":
            return self.pkg.upgrade()
        return "pkg: nieznana akcja"


class TerminalApp:
    def __init__(self):
        self.os = RacOS()

    def run(self) -> None:
        print("=" * 62)
        print("  RacOS Shell 2.0 (Pythonista 3 / iOS) - terminal edition")
        print("=" * 62)
        print("Wpisz 'help' aby zobaczyć komendy. 'exit' aby zakończyć.\n")

        while True:
            try:
                cmd = input(self.os.prompt)
            except (EOFError, KeyboardInterrupt):
                print("\nZamykanie RacOS...")
                break

            output = self.os.execute(cmd)
            if output == "__CLEAR__":
                print("\n" * 70)
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
