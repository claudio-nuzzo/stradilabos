# Google Workspace in StradilabOS

## Esperienza utente

StradilabOS presenta un pulsante «Accedi a Google Workspace» e micro-app
dedicate per Classroom, Drive, Gmail, Meet, Calendar, Documenti, Fogli,
Presentazioni e Moduli. Tutte vengono aperte dallo stesso profilo del browser:
l'accesso con l'account `@istitutostradivari.it` si effettua una volta sola e
vale per l'intera sessione.

Nessuna password, cookie o token Google viene inserito nella ISO master.
Google Drive per desktop non esiste per Linux: file ed editor sono quindi usati
nel browser, affiancati da LibreOffice per il lavoro locale.

## PC personale e PC condiviso

Durante l'installazione viene chiesto il tipo di utilizzo:

- **personale o assegnato**: il profilo Chromium resta nella cartella utente e
  mantiene l'accesso tra i riavvii;
- **condiviso o di laboratorio**: il profilo viene creato nella cartella
  temporanea della sessione e scompare al logout o allo spegnimento.

Anche l'avvio live da USB usa sempre la modalità temporanea. Nei laboratori va
comunque insegnato a terminare la sessione Xfce quando cambia utente: chiudere
soltanto una finestra non cancella una sessione ancora attiva.

## Gestione centrale opzionale

Google consente di amministrare Chrome su Linux tramite Chrome Enterprise Core:
l'amministratore genera un token dalla Console di amministrazione e registra
ogni browser. Può quindi applicare criteri come accesso obbligatorio e
limitazione degli account al dominio della scuola.

Questa modalità richiede il browser Google Chrome ufficiale e un token
amministrativo. Il prototipo usa Debian Chromium e non incorpora il token. Una
successiva edizione «gestita» potrà:

1. includere Google Chrome con una decisione esplicita sulla licenza;
2. ricevere il token da un archivio privato durante la build o dopo
   l'installazione;
3. limitare l'accesso al modello `^.*@istitutostradivari\\.it$`;
4. verificare i criteri in `chrome://policy` e il browser nella Console di
   amministrazione.

Il token non deve essere pubblicato nel repository né in una ISO liberamente
scaricabile.
