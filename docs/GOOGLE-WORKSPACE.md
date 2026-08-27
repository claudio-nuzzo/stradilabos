# Google Workspace in StradilabOS

## Esperienza utente

StradilabOS presenta un pulsante «Accedi a Google Workspace» e micro-app
dedicate per Classroom, Drive, Gmail, Meet, Calendar, Documenti, Fogli,
Presentazioni e Moduli. Tutte vengono aperte dallo stesso profilo del browser:
l'accesso con l'account `@istitutostradivari.it` si effettua una volta sola e
vale per l'intera sessione.

Durante l'installazione una pagina dedicata chiede se proporre l'accesso al
primo avvio oppure lasciarlo per un secondo momento. Nel primo caso il pulsante
Workspace è l'azione principale della schermata di benvenuto; nel secondo lo
resta disponibile nella barra e nel menu senza interrompere la configurazione.

Chromium riceve inoltre il criterio gestito `AllowedDomainsForApps` con valore
`istitutostradivari.it`: i servizi Google accettano l'accesso degli account del
dominio scolastico e non propongono account personali. Il criterio è verificabile
graficamente aprendo `chrome://policy`.

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

La gestione completa dell'inventario dei browser richiede il browser Google
Chrome ufficiale e un token amministrativo. Il prototipo usa Debian Chromium,
applica localmente il vincolo di dominio e non incorpora alcun token. Una
successiva edizione «gestita» potrà:

1. includere Google Chrome con una decisione esplicita sulla licenza;
2. ricevere il token da un archivio privato durante la build o dopo
   l'installazione;
3. confermare centralmente il criterio di accesso del dominio;
4. verificare i criteri in `chrome://policy` e il browser nella Console di
   amministrazione.

Il token non deve essere pubblicato nel repository né in una ISO liberamente
scaricabile.
