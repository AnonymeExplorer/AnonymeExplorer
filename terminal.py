# -- coding: utf-8 --
import ui
import socket
import urllib.request
import os
import time
import json
import platform
import sys
import datetime
import re
import zipfile
import io
import threading
from threading import Thread
import requests  # Dodano dla G3-T1 Beta

try:
    import yaml
except ImportError:
    yaml = None

try:
    sys.path.append('/private/var/mobile/Containers/Shared/AppGroup/xxx/Pythonista3/Documents/site-packages/stash/bin/')
    from stash.bin.ping import verbose_ping
except ImportError:
    verbose_ping = None

try:
    sys.path.append(os.path.expanduser("~/Documents/Games_IOS"))
    from keno import KenoGame
    from slotmachine import SlotMachine
    from budget_utils import load_budget, save_budget
except ImportError as e:
    print(f"Error importing games or budget utils: {e}")

API_KEY = "aff2b56d057f4f4aabcb8a329d4481dc"
API_URL = "https://api.aimlapi.com/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}
SYSTEM_PROMPT = """Jestem G3-T1 Beta, AI z czarnym humorem i ciętą ripostą. Odpowiadam zwięźle, po polsku, z ironicznym stylem.
- Na 'Kim jesteś?': 'G3-T1 Beta, AI z GPT-3.5-turbo. Zaskoczę cię... albo i nie, zależy od pytania.'
- Na 'Kto cię stworzył?': 'AnnonymExplorer, typ z masą czasu. Sprawdź: https://www.reddit.com/u/AnonnymExplorer/s/CtzxtiQeVG.'
"""
chat_history = [{"role": "system", "content": SYSTEM_PROMPT}]


def send_message_to_api(message):
    chat_history.append({"role": "user", "content": message})
    max_history = 4
    limited_history = [{"role": "system", "content": SYSTEM_PROMPT}] + chat_history[-max_history:]
    data = {
        "model": "gpt-3.5-turbo",
        "messages": limited_history,
        "max_tokens": 100
    }
    try:
        response = requests.post(API_URL, headers=HEADERS, json=data)
        response.raise_for_status()
        result = response.json()
        reply = result["choices"][0]["message"]["content"]
        chat_history.append({"role": "assistant", "content": reply})
        tokens_used = result.get("usage", {}).get("total_tokens", "brak danych")
        print(f"Zużyto tokenów: {tokens_used}")
        return reply
    except requests.exceptions.RequestException as e:
        return f"Błąd: {str(e)}"


def launch_g3t1_chatbot(parent_view):
    view = ui.View()
    view.name = "G3-T1 Beta"
    view.background_color = "#121212"
    screen_width = ui.get_screen_size().width
    screen_height = ui.get_screen_size().height
    margin = 10
    input_height = 40
    button_width = 40
    clear_button_width = 60
    keyboard_height = 500
    chat_height = screen_height - input_height - keyboard_height - 3 * margin
    chat_view = ui.TextView(name="chat_view")
    chat_view.frame = (margin, margin, screen_width - 2 * margin, chat_height)
    chat_view.editable = False
    chat_view.text_color = "#E0E0E0"
    chat_view.background_color = "#1E1E1E"
    chat_view.font = ("Helvetica", 14)
    chat_view.text = ""
    view.add_subview(chat_view)
    clear_button = ui.Button(name="clear_chat")
    clear_button.frame = (margin, chat_height + 2 * margin, clear_button_width, input_height)
    clear_button.title = "Wyczyść"
    clear_button.tint_color = "white"
    clear_button.background_color = "#F44336"
    clear_button.action = lambda sender: clear_chat_action(sender)
    view.add_subview(clear_button)
    input_field = ui.TextField(name="input_field")
    input_field.frame = (margin + clear_button_width + margin, chat_height + 2 * margin, screen_width - 2 * margin - button_width - clear_button_width - margin, input_height)
    input_field.placeholder = "Wpisz wiadomość..."
    input_field.text_color = "#007AFF"
    input_field.background_color = "#2A2F30"
    input_field.font = ("Helvetica", 14)
    input_field.clear_button_mode = "while_editing"
    input_field.action = lambda sender: send_button_action(sender)
    view.add_subview(input_field)
    send_button = ui.Button(name="send_button")
    send_button.frame = (screen_width - button_width - margin, chat_height + 2 * margin, button_width, input_height)
    send_button.title = "➤"
    send_button.tint_color = "white"
    send_button.background_color = "#007AFF"
    send_button.action = lambda sender: send_button_action(sender)
    view.add_subview(send_button)
    def send_button_action(sender):
        input_field = sender.superview["input_field"]
        chat_view = sender.superview["chat_view"]
        message = input_field.text.strip()
        if not message:
            return
        chat_view.text += f"Ty: {message}\n"
        input_field.text = ""
        chat_view.text += "G3-T1: ...\n"
        chat_view.content_offset = (0, chat_view.content_size[1] - chat_view.height)
        ui.delay(lambda: None, 0.5)
        reply = send_message_to_api(message)
        chat_view.text = chat_view.text[:-5]
        chat_view.text += f"G3-T1: {reply}\n\n"
        chat_view.content_offset = (0, chat_view.content_size[1] - chat_view.height)
    def clear_chat_action(sender):
        chat_view = sender.superview["chat_view"]
        global chat_history
        chat_view.text = ""
        chat_history = [{"role": "system", "content": SYSTEM_PROMPT}]
    view.present("sheet")

# Placeholder: rest of the functions from user script
# Due to length, this file is truncated here. The remaining functions for
# the terminal emulator would be added in a complete implementation.
