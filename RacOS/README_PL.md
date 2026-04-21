# RacOS Shell 2.0 dla Pythonista 3 (iOS)

To jest zaawansowana, **w pełni terminalowa** symulacja systemu operacyjnego RacOS
inspirowana doświadczeniem pracy jak w Termux (komendy shell, pakiety, procesy, pliki,
zmienne środowiskowe, aliasy, historia, narzędzia systemowe).

## Jak uruchomić w Pythonista 3

1. Skopiuj cały folder `RacOS` do Pythonista (np. iCloud Drive / On My iPad).
2. Otwórz `main.py`.
3. Uruchom skrypt.

## Najważniejsze możliwości

- System plików: `ls`, `cd`, `mkdir`, `touch`, `write`, `append`, `cat`, `rm -r`, `cp`, `mv`, `find`, `grep`
- Shell: `echo`, `history`, `alias`, `export`, `env`, `man`
- System: `whoami`, `uname -a`, `sysinfo`, `uptime`, `date`, `df`, `free`
- Procesy: `ps`, `top`, `run`, `kill`
- Sieć: `net status|up|down|scan`, `ping`
- Pakiety (`pkg`): `search`, `install`, `list`, `upgrade`

## Przykładowa sesja

```bash
help
pkg search git
pkg install git
mkdir projekty
cd projekty
touch notes.txt
write notes.txt "RacOS shell działa"
cat notes.txt
ps
ping openai.com
```

## Uwagi

- Aplikacja nie zawiera GUI (zgodnie z założeniem terminal-only).
- System plików, procesy i pakiety są symulowane w pamięci (in-memory).
- Nie są wymagane dodatkowe biblioteki poza standardowym Pythonem dostępnych w Pythonista.
