# start_all.ps1
# Avvia i 4 nodi ATM, ciascuno in una FINESTRA PowerShell separata.
# Eseguire da dentro la cartella del progetto:  .\start_all.ps1
#
# Ordine di avvio consigliato: prima ATM2, ATM3, ATM4 (che restano in
# ascolto) e per ultimo ATM1, che dopo qualche secondo inietta il token.
# In pratica lo script li avvia tutti insieme: ATM1 attende comunque
# STARTUP_DELAY secondi prima di iniettare il token, quindi l'ordine non
# e' critico.

$dir = $PSScriptRoot

Start-Process powershell -ArgumentList "-NoExit","-Command","cd '$dir'; python atm_node.py 2"
Start-Process powershell -ArgumentList "-NoExit","-Command","cd '$dir'; python atm_node.py 3"
Start-Process powershell -ArgumentList "-NoExit","-Command","cd '$dir'; python atm_node.py 4"
Start-Process powershell -ArgumentList "-NoExit","-Command","cd '$dir'; python atm_node.py 1"

Write-Host "Avviati 4 terminali: ATM1, ATM2, ATM3, ATM4."
Write-Host "ATM1 iniettera' il token dopo qualche secondo."
