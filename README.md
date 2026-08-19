# Sistema di Transazioni Bancarie Distribuite con Mutua Esclusione a Token Ring

Sistema distribuito composto da **4 nodi (ATM)** che operano su un unico conto
bancario condiviso. La **mutua esclusione** e' garantita esclusivamente
dall'algoritmo **Token Ring**: esiste un solo token che circola nell'anello
`ATM1 → ATM2 → ATM3 → ATM4 → ATM1` e solo il nodo che lo possiede puo'
eseguire una transazione (sezione critica).

Il saldo del conto **non e' memoria condivisa**: ogni nodo e' un processo
separato con memoria privata e comunica solo tramite messaggi TCP su
localhost. Il saldo "viaggia" insieme al token, quindi viene letto/scritto da
un solo nodo alla volta.

---

## 1. Istruzioni di Esecuzione

### 1.1 Linguaggio e ambiente
- **Linguaggio:** Python 3 (testato con Python 3.14, funziona da 3.8+)
- **Sistema operativo:** Windows (i comandi sotto sono per PowerShell)

### 1.2 Librerie e dipendenze
- **Nessuna dipendenza esterna.** Vengono usate solo librerie standard di
  Python: `socket`, `threading`, `json`, `time`, `sys`, `datetime`.
- Nessun comando di installazione richiesto.

### 1.3 Compilazione
- Non necessaria: Python e' interpretato.

### 1.4 Avvio dei nodi
Ogni nodo va avviato in un **terminale separato**. Porte usate su localhost:

| Nodo | Porta  |
|------|--------|
| ATM1 | 5001   |
| ATM2 | 5002   |
| ATM3 | 5003   |
| ATM4 | 5004   |

Aprire **4 terminali** nella cartella del progetto ed eseguire, uno per
terminale:

```powershell
# Terminale 1
python atm_node.py 1

# Terminale 2
python atm_node.py 2

# Terminale 3
python atm_node.py 3

# Terminale 4
python atm_node.py 4
```

**Ordine di avvio:** consigliato avviare prima ATM2, ATM3, ATM4 e poi ATM1.
Non e' comunque critico: ATM1 attende alcuni secondi (`STARTUP_DELAY`) prima
di iniettare il token, e ogni nodo riprova a inoltrare il token se il
successore non e' ancora pronto.

#### Avvio automatico dei 4 terminali (opzionale)
In alternativa, dalla cartella del progetto:

```powershell
.\start_all.ps1
```

Lo script apre automaticamente 4 finestre PowerShell, una per ogni nodo.
> Se PowerShell blocca lo script, eseguire una volta:
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

### 1.5 Associazione Nodo–Terminale
- Ogni terminale esegue esattamente un nodo (`python atm_node.py <ID>`).
- Ogni riga di log e' prefissata da `[ATM<ID>]`, quindi si riconosce subito
  quale nodo sta scrivendo in quel terminale (es. `[ATM2] RICEVUTO TOKEN ...`).

---

## 2. Come funziona (Token Ring)

1. Esiste **un solo token** nel sistema. All'avvio lo possiede **ATM1**, che
   lo inietta nell'anello con il **saldo iniziale = 1000**.
2. Il token circola continuamente: `ATM1 → ATM2 → ATM3 → ATM4 → ATM1 → ...`
   Ogni nodo conosce **solo il proprio successore**.
3. Quando un nodo riceve il token:
   - se ha una transazione da fare, entra nella **sezione critica**, esegue
     la transazione (lettura → validazione → aggiornamento → scrittura → log)
     e aggiorna il saldo trasportato dal token;
   - se non ha transazioni, **inoltra immediatamente** il token.
4. Poiche' il saldo viaggia con il token e solo un nodo alla volta lo possiede,
   gli aggiornamenti sono **serializzati** → mutua esclusione garantita,
   nessuna transazione concorrente.

### Scenario dimostrato (dall'esempio del PDF)
Saldo iniziale **1000**:

| Passo | Nodo | Transazione     | Saldo |
|-------|------|-----------------|-------|
| 1     | ATM1 | nessuna         | 1000  |
| 2     | ATM2 | prelievo 200    | 800   |
| 3     | ATM3 | deposito 100    | 900   |
| 4     | ATM4 | prelievo 500    | 400   |

Le transazioni sono configurate in `config.py` (dizionario `TRANSACTIONS`) e
possono essere modificate liberamente.

---

## 3. Requisiti di Logging
Ogni nodo registra chiaramente su terminale:
- **Ricezione** del token
- **Inoltro** del token (verso quale successore)
- **Inizio** e **fine** della transazione
- **Saldo aggiornato** dopo ogni operazione

I log mostrano il movimento del token, l'assenza di transazioni concorrenti e
il corretto comportamento del sistema.

---

## 4. File del progetto
- `atm_node.py` — programma del singolo nodo ATM (server + gestione token +
  sezione critica). Commentato in dettaglio.
- `config.py` — topologia dell'anello, porte, saldo iniziale, transazioni.
- `start_all.ps1` — script opzionale per avviare i 4 terminali.
- `demo.mp4` — video dimostrativo con i 4 terminali in esecuzione.

