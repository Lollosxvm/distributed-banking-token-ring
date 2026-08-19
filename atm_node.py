"""
atm_node.py
===========
Nodo (ATM) di un sistema bancario distribuito con MUTUA ESCLUSIONE
implementata tramite l'algoritmo TOKEN RING.

Avvio:
    python atm_node.py <NODE_ID>          # NODE_ID = 1, 2, 3 o 4

Ogni nodo:
  * e' un PROCESSO SEPARATO con memoria privata (nessuna variabile
    condivisa tra i nodi);
  * comunica SOLO tramite scambio di messaggi su socket TCP (localhost);
  * conosce solo il proprio successore nell'anello;
  * puo' eseguire una transazione (SEZIONE CRITICA) solo quando possiede
    il TOKEN.

Il TOKEN e' un messaggio che circola nell'anello e trasporta il SALDO
del conto condiviso: chi ha il token e' l'unico autorizzato a leggere e
modificare il saldo -> questo garantisce la mutua esclusione.
"""

import json
import socket
import sys
import threading
import time
from datetime import datetime

import config
import colors as C


class ATMNode:
    def __init__(self, node_id: int):
        self.node_id = node_id
        self.port = config.PORTS[node_id]
        self.successor_id = config.successor_id(node_id)
        self.successor_port = config.PORTS[self.successor_id]

        # Copia locale delle transazioni ancora da eseguire da questo nodo.
        self.pending = list(config.TRANSACTIONS.get(node_id, []))
        self.lock = threading.Lock()
        # Colore distintivo di questo nodo (per riconoscerlo nei log).
        self.color = C.NODE_COLOR.get(node_id, C.WHITE)

    # ---------------------------------------------------------------
    # Logging: ogni riga e' prefissata da timestamp e [ATMx] cosi' e'
    # sempre chiaro quale nodo/terminale ha prodotto il log. Il prefisso
    # e' colorato col colore del nodo; il corpo del messaggio puo' avere
    # un colore "semantico" (verde = ok, rosso = errore, ecc.).
    # ---------------------------------------------------------------
    def log(self, message: str, *body_codes: str):
        ts = C.paint(datetime.now().strftime("%H:%M:%S.%f")[:-3], C.GREY)
        prefix = C.paint(f"[ATM{self.node_id}]", C.BOLD, self.color)
        body = C.paint(message, *body_codes) if body_codes else message
        print(f"[{ts}] {prefix} {body}", flush=True)

    # ---------------------------------------------------------------
    # SEZIONE CRITICA
    # Eseguita SOLO mentre il nodo possiede il token. Riceve il saldo
    # corrente (trasportato dal token), applica le transazioni pendenti
    # in modo atomico e restituisce il nuovo saldo.
    #
    # Una transazione = leggi saldo -> valida -> aggiorna -> scrivi -> log
    # ---------------------------------------------------------------
    def esegui_sezione_critica(self, balance: int) -> int:
        if not self.pending:
            self.log(f"Nessuna transazione da eseguire. Saldo invariato: {balance}", C.GREY)
            return balance

        # Applichiamo tutte le transazioni programmate per questo nodo.
        for tx in list(self.pending):
            op = tx["op"]
            amount = tx["amount"]

            self.log(f">>> INIZIO TRANSAZIONE ({op} {amount}) [SEZIONE CRITICA]", C.BOLD, C.WHITE)
            self.log(f"    1) Lettura saldo corrente: {balance}")

            # 2) Validazione dell'operazione
            if op == "withdraw":
                if amount > balance:
                    self.log(f"    2) Validazione FALLITA: fondi insufficienti "
                             f"(richiesti {amount}, disponibili {balance}). Transazione annullata.",
                             C.BOLD, C.RED)
                    self.log(f"<<< FINE TRANSAZIONE (annullata). Saldo: {balance}", C.RED)
                    self.pending.remove(tx)
                    continue
                nuovo = balance - amount
                self.log(f"    2) Validazione OK (prelievo {amount})", C.GREEN)
            elif op == "deposit":
                nuovo = balance + amount
                self.log(f"    2) Validazione OK (deposito {amount})", C.GREEN)
            else:
                self.log(f"    2) Operazione sconosciuta '{op}'. Ignorata.", C.RED)
                self.pending.remove(tx)
                continue

            # 3)+4) Aggiornamento e scrittura del nuovo saldo
            self.log(f"    3) Aggiornamento saldo: {balance} -> {nuovo}")
            balance = nuovo
            self.log(f"    4) Nuovo saldo scritto: {balance}")
            # 5) Registrazione (log) dell'operazione
            self.log(f"    5) Log operazione: {op.upper()} {amount} eseguito con successo", C.GREEN)
            self.log(f"<<< FINE TRANSAZIONE. SALDO AGGIORNATO: {balance}", C.BOLD, C.GREEN)

            self.pending.remove(tx)

        return balance

    # ---------------------------------------------------------------
    # Gestione del TOKEN
    # Quando arriva il token: log ricezione -> (eventuale) sezione
    # critica -> attesa breve -> inoltro al successore.
    # ---------------------------------------------------------------
    def gestisci_token(self, token: dict):
        with self.lock:  # garantisce che un solo token sia gestito per volta
            lap = token.get("lap", 0)
            balance = token["balance"]

            self.log(f"RICEVUTO TOKEN (giro #{lap}). Saldo trasportato dal token: {balance}",
                     C.BOLD, C.BLUE)

            # Il possesso del token concede l'accesso alla sezione critica.
            balance = self.esegui_sezione_critica(balance)

            # Se questo nodo e' l'ultimo dell'anello, il prossimo giro
            # riparte da 1 dal primo nodo.
            next_lap = lap + 1 if self.successor_id == config.INITIAL_TOKEN_HOLDER else lap

            token["balance"] = balance
            token["lap"] = next_lap

            time.sleep(config.TOKEN_HOLD_DELAY)
            self.inoltra_token(token)

    def inoltra_token(self, token: dict):
        self.log(f"INOLTRO TOKEN -> ATM{self.successor_id} "
                 f"(porta {self.successor_port}). Saldo trasportato: {token['balance']}",
                 C.BOLD, C.CYAN)
        data = json.dumps(token).encode("utf-8")

        # Riprova finche' il successore non e' pronto (utile all'avvio,
        # quando i terminali non sono ancora tutti attivi).
        while True:
            try:
                with socket.create_connection((config.HOST, self.successor_port), timeout=5) as s:
                    s.sendall(data)
                return
            except OSError:
                self.log(f"Successore ATM{self.successor_id} non ancora pronto. Nuovo tentativo...",
                         C.YELLOW)
                time.sleep(1.0)

    # ---------------------------------------------------------------
    # Server: resta in ascolto dei messaggi (token) in arrivo.
    # ---------------------------------------------------------------
    def avvia_server(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((config.HOST, self.port))
        srv.listen()
        self.log(f"In ascolto su {config.HOST}:{self.port}. "
                 f"Successore = ATM{self.successor_id} (porta {self.successor_port}).", self.color)

        while True:
            conn, _ = srv.accept()
            with conn:
                chunks = []
                while True:
                    chunk = conn.recv(4096)
                    if not chunk:
                        break
                    chunks.append(chunk)
                raw = b"".join(chunks)
            if not raw:
                continue
            token = json.loads(raw.decode("utf-8"))
            if token.get("type") == "TOKEN":
                self.gestisci_token(token)

    # ---------------------------------------------------------------
    # Avvio del nodo. Il possessore iniziale del token, dopo un breve
    # ritardo (per dar tempo a tutti di partire), INIETTA il token
    # nell'anello con il saldo iniziale.
    # ---------------------------------------------------------------
    def run(self):
        server_thread = threading.Thread(target=self.avvia_server, daemon=True)
        server_thread.start()

        if self.node_id == config.INITIAL_TOKEN_HOLDER:
            self.log(f"Sono il possessore iniziale del token. "
                     f"Attendo {config.STARTUP_DELAY:.0f}s l'avvio degli altri nodi...", C.YELLOW)
            time.sleep(config.STARTUP_DELAY)
            token = {"type": "TOKEN", "balance": config.INITIAL_BALANCE, "lap": 1}
            self.log(f"INIEZIONE TOKEN nell'anello. Saldo iniziale: {config.INITIAL_BALANCE}",
                     C.BOLD, C.BLUE)
            self.gestisci_token(token)

        # Mantiene vivo il processo (il token continua a circolare).
        while True:
            time.sleep(1.0)


def main():
    if len(sys.argv) != 2:
        print("Uso: python atm_node.py <NODE_ID>   (NODE_ID = 1, 2, 3 o 4)")
        sys.exit(1)

    try:
        node_id = int(sys.argv[1])
    except ValueError:
        print("NODE_ID deve essere un intero tra 1 e 4.")
        sys.exit(1)

    if node_id not in config.PORTS:
        print(f"NODE_ID non valido: {node_id}. Valori ammessi: {list(config.PORTS)}")
        sys.exit(1)

    node = ATMNode(node_id)
    try:
        node.run()
    except KeyboardInterrupt:
        node.log("Arresto del nodo (Ctrl+C).")


if __name__ == "__main__":
    main()
