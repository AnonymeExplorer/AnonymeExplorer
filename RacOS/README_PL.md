# RacOS dla Pythonista 3 (iOS)

To jest symulacja systemu operacyjnego **RacOS** działająca w trybie terminalowym,
z możliwością uruchomienia rozbudowanego GUI.

## Jak uruchomić w Pythonista 3

1. Skopiuj cały folder `RacOS` do Pythonista (np. iCloud Drive / On My iPad).
2. Otwórz `main.py`.
3. Uruchom skrypt.

## Tryb terminalowy

Po uruchomieniu zobaczysz prompt `racos:/home/user$`.

Przykładowe komendy:
- `help`
- `ls`
- `cd /home/user/docs`
- `cat welcome.txt`
- `run edytor`
- `ps`
- `net scan`
- `gui` (uruchamia GUI)

## GUI

Po wpisaniu komendy `gui` otwiera się panel **RacOS Control Center** z:
- monitorowaniem procesów,
- informacją systemową,
- skanowaniem sieci,
- szybkim podglądem plików,
- przyciskiem tworzenia nowych procesów.

## Uwagi

- System plików i procesy są symulowane (in-memory).
- Wszystko działa bez dodatkowych bibliotek (wykorzystuje `ui` dostępne w Pythonista).
