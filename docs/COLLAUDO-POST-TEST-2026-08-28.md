# Collaudo post-test — rilievi da affrontare

**Origine:** prove manuali del 28 agosto 2026 su macchine fisiche, dopo il
superamento del controllo di avvio e del gestore delle finestre.

Questi sono rilievi di prodotto da verificare nel prossimo ciclo: non sono
correzioni già implementate nella release `f8e36a6`.

## 1. Rete prima dell'installazione

- **Osservazione:** il primo tentativo di installazione non è riuscito; dopo
  l'attivazione del Wi-Fi l'installazione è proseguita.
- **Da verificare:** individuare l'operazione dell'installatore che richiede
  Internet e rendere il collegamento di rete una tappa esplicita e obbligatoria
  prima di avviare la copia sul disco. Se è possibile un'installazione offline,
  comunicarlo con precisione invece di fallire in un passaggio successivo.
- **Criterio di accettazione:** senza rete l'installatore spiega chiaramente
  cosa fare e non inizia un'installazione destinata a fallire.

## 2. Accesso Google Workspace

- **Osservazione:** il pulsante di accesso oggi apre Classroom; dopo aver
  effettuato l'accesso, aprendo Gmail viene richiesta una nuova autenticazione.
- **Da verificare:** il punto di ingresso dovrebbe aprire Gmail o Gemini (non
  Classroom) e tutte le micro-app devono riutilizzare lo stesso profilo Chromium
  e la stessa sessione Google.
- **Nota tecnica:** Google non può diventare un'identità Linux di sistema senza
  introdurre un vero provider di identità; l'obiettivo realistico per i PC
  personali è un accesso unico persistente nel profilo browser dedicato.
- **Criterio di accettazione:** un singolo login in Gmail/Gemini rende subito
  disponibili Classroom, Drive, Meet e le altre app senza nuovo login.

## 3. Contrasto delle icone del pannello

- **Osservazione:** le icone in alto a destra (volume e area di notifica) sono
  bianche su uno sfondo quasi bianco.
- **Da verificare:** fissare un colore scuro/bordeaux per icone simboliche e
  indicatori XFCE, conservando un contrasto leggibile anche in hover e focus.
- **Criterio di accettazione:** volume, rete, alimentazione, notifiche e orologio
  sono leggibili a colpo d'occhio sul pannello avorio.

## 4. Aggiornamenti automatici

- **Richiesta:** aggiornare automaticamente i pacchetti installati.
- **Da decidere e verificare:** configurare aggiornamenti automatici almeno per
  la sicurezza, con una politica esplicita per gli altri aggiornamenti, riavvio
  e notifiche. La configurazione non deve bloccare la sessione né richiedere
  una password inattesa.
- **Criterio di accettazione:** con rete attiva, il sistema mantiene aggiornati
  i pacchetti secondo la politica scelta e rende visibile l'esito.

## 5. Messaggi iniziali dopo il riavvio

- **Evidenza:** foto `8D21129A-EBDA-4630-9ACD-57BF7D32957C_1_105_c.jpeg`.
- **Osservazione:** compaiono `APIC ID mismatch` e messaggi `ACPI BIOS Error`
  relativi al firmware (metodo `_SB.WLBU._STA`).
- **Valutazione iniziale:** sono messaggi del firmware/BIOS esposti dal kernel,
  non una prova di un errore StradilabOS. Poiché il sistema ha poi avviato, non
  sono bloccanti; vanno però riprodotti sul portatile e verificati per eventuali
  effetti su Wi-Fi, sospensione e stabilità. Solo dopo questa verifica si valuta
  se ridurre la verbosità del boot (`quiet`) senza nascondere un problema reale.

## Ordine suggerito

1. Rendere affidabile il requisito di rete dell'installatore.
2. Correggere sessione Workspace e pagina di ingresso.
3. Correggere il contrasto del pannello.
4. Definire e implementare la politica degli aggiornamenti automatici.
5. Chiudere la verifica hardware dei messaggi ACPI/APIC.
