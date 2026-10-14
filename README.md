# BookVault

*Progetto di studio — sviluppato da autodidatta, non è un prodotto commerciale.*

## Il problema
Trovare luoghi adatti alla lettura (bar tranquilli, biblioteche, spazi all'aperto) richiede di consultare a mano mappe e recensioni, una per una.

## La soluzione
Un sistema di due agenti di intelligenza artificiale che lavorano in sequenza:
1. **Scout** cerca i luoghi in una zona a partire da dati pubblici sulle mappe;
2. **Critic** analizza ogni luogo con un modello di AI e gli assegna delle etichette sull'atmosfera (tranquillo, luminoso, adatto a lavorare…);
3. i risultati vengono salvati in un database, pronti da consultare.

Il processo può partire da solo a orari prefissati.

## Struttura
- `agent_scout.py` — raccolta dei luoghi
- `agent_critic.py` — valutazione con l'AI
- `brain.py` — coordinamento degli agenti
- `app.py`, `templates/`, `static/` — piccola interfaccia web per consultare i risultati

## Strumenti
Python, Flask, modelli di intelligenza artificiale, Supabase (PostgreSQL).
