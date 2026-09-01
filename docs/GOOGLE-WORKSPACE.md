# Google Workspace in StradilabOS

## Esperienza utente

StradilabOS presenta un pulsante «Scarica Chrome e accedi» e micro-app
dedicate per Classroom, Drive, Gmail, Meet, Calendar, Documenti, Fogli,
Presentazioni e Moduli. Sul sistema installato il pulsante scarica il pacchetto
stabile ufficiale Google per AMD64 o ARM64, ne verifica nome e architettura,
chiede l'autorizzazione amministrativa e imposta Chrome come browser
predefinito. Tutte le web app vengono poi aperte dallo stesso profilo Chrome
nativo: l'accesso con `@istitutostradivari.it` si effettua una volta sola.

Durante l'installazione una pagina dedicata chiede se proporre l'accesso al
primo avvio oppure lasciarlo per un secondo momento. Nel primo caso il pulsante
Chrome/Workspace è l'azione principale della schermata di benvenuto; nel secondo lo
resta disponibile nella barra e nel menu senza interrompere la configurazione.

Il Benvenuto spiega i passaggi «Accedi a Chrome» e «Attiva la
sincronizzazione», poi attende una conferma esplicita: aprire Gmail non viene
più interpretato erroneamente come configurazione conclusa. Chromium conserva
il criterio locale `AllowedDomainsForApps=istitutostradivari.it` quando viene
usato come browser di riserva.

Nessuna password, cookie o token Google viene inserito nella ISO master.
Google Drive per desktop non esiste per Linux: file ed editor sono quindi usati
nel browser, affiancati da LibreOffice per il lavoro locale.

## PC personale e PC condiviso

Durante l'installazione viene chiesto il tipo di utilizzo:

- **personale o assegnato**: Chrome usa il proprio profilo nativo nella cartella
  utente e mantiene accesso e sincronizzazione tra i riavvii;
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

La gestione completa dell'inventario richiede un token amministrativo. Il
prototipo installa Chrome soltanto dopo consenso, ma non incorpora token né
registra automaticamente il browser. Una successiva edizione «gestita» potrà:

1. ricevere il token da un archivio privato dopo
   l'installazione;
2. confermare centralmente il criterio di accesso del dominio;
3. verificare i criteri in `chrome://policy` e il browser nella Console di
   amministrazione.

Il token non deve essere pubblicato nel repository né in una ISO liberamente
scaricabile.
