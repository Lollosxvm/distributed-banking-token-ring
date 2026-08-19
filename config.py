"""
config.py
=========
Configurazione condivisa (statica) del sistema Token Ring.

NOTA IMPORTANTE sulla "memoria condivisa":
questo file NON e' memoria condivisa a runtime. Contiene solo la
TOPOLOGIA dell'anello (quali porte usano i nodi) e le transazioni che
ciascun ATM deve eseguire. Ogni nodo, una volta avviato, e' un processo
separato con la propria memoria privata: il SALDO del conto NON e' una
variabile globale, ma un valore che "viaggia" insieme al token da un
nodo al successivo. In questo modo la risorsa condivisa (il saldo) viene
letta/scritta da un solo nodo alla volta -> mutua esclusione.
"""

HOST = "127.0.0.1"          # tutti i nodi girano su localhost

# --- Topologia logica dell'anello -------------------------------------
# ATM1 -> ATM2 -> ATM3 -> ATM4 -> ATM1
# Ogni nodo conosce SOLO il proprio successore (vedi funzione sotto).
PORTS = {
    1: 5001,   # ATM1
    2: 5002,   # ATM2
    3: 5003,   # ATM3
    4: 5004,   # ATM4
}

NUM_NODES = len(PORTS)

# Nodo che possiede il token all'avvio del sistema.
INITIAL_TOKEN_HOLDER = 1

# Saldo iniziale del conto bancario condiviso.
INITIAL_BALANCE = 1000

# Pausa (secondi) che il possessore del token attende prima di inoltrarlo.
# Serve solo a rendere i log leggibili durante la dimostrazione.
TOKEN_HOLD_DELAY = 2.0

# Ritardo iniziale (secondi) prima che ATM1 inietti il token nell'anello:
# da' tempo a tutti i 4 terminali di partire, mettersi in ascolto e
# all'utente di sistemare lo schermo prima della registrazione del video.
STARTUP_DELAY = 20.0

# --- Transazioni programmate per ciascun nodo -------------------------
# Ogni nodo esegue la propria lista di transazioni la PRIMA volta che
# riceve il token; nei giri successivi non ha piu' transazioni e si
# limita a inoltrare il token (il token continua comunque a circolare).
#
# Scenario dell'esempio del PDF (saldo iniziale 1000):
#   ATM1 -> nessuna transazione                 -> saldo 1000
#   ATM2 -> prelievo 200                         -> saldo  800
#   ATM3 -> deposito 100                         -> saldo  900
#   ATM4 -> prelievo 500                         -> saldo  400
TRANSACTIONS = {
    1: [],
    2: [{"op": "withdraw", "amount": 200}],
    3: [{"op": "deposit",  "amount": 100}],
    4: [{"op": "withdraw", "amount": 500}],
}


def successor_id(node_id: int) -> int:
    """Restituisce l'ID del successore nell'anello (l'unico nodo che
    questo nodo conosce). Dopo l'ultimo si torna al primo."""
    return (node_id % NUM_NODES) + 1
