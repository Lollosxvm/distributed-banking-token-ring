"""
colors.py
=========
Piccola utility per colorare i log sul terminale tramite sequenze ANSI.
Nessuna dipendenza esterna: usa solo la libreria standard.

Su Windows 10+ le sequenze ANSI vanno abilitate: lo facciamo con il
trucco `os.system("")`, che attiva la "Virtual Terminal Processing" della
console. Se per qualche motivo i colori non vengono supportati, si puo'
impostare la variabile d'ambiente NO_COLOR per disattivarli.
"""

import os
import sys

# Attiva il supporto alle sequenze ANSI sulle console Windows.
if os.name == "nt":
    os.system("")

# Disattiva i colori se lo stdout non e' un terminale o se NO_COLOR e' set.
_ENABLED = sys.stdout.isatty() and "NO_COLOR" not in os.environ

RESET = "\033[0m"
BOLD = "\033[1m"

# Colori base (foreground, versione "bright").
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
RED = "\033[91m"
BLUE = "\033[94m"
WHITE = "\033[97m"
GREY = "\033[90m"


def paint(text: str, *codes: str) -> str:
    """Applica uno o piu' codici ANSI al testo (se i colori sono abilitati)."""
    if not _ENABLED or not codes:
        return text
    return "".join(codes) + text + RESET


# Colore distintivo per ciascun nodo (per riconoscerli a colpo d'occhio).
NODE_COLOR = {
    1: CYAN,
    2: GREEN,
    3: YELLOW,
    4: MAGENTA,
}
