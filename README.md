# StradilabOS

StradilabOS è una distribuzione scolastica live USB, installabile e pensata per
recuperare PC a 64 bit non più adatti ai sistemi operativi moderni. L'obiettivo
è offrire un ambiente semplice, in italiano e utilizzabile senza terminale,
centrato sull'ecosistema StradiLab dell'IIS «Antonio Stradivari» di Cremona.

Questo repository contiene la versione `0.3` in sviluppo. Le immagini vengono
costruite e controllate automaticamente per AMD64 e ARM64; prima dell'uso a
scuola resta necessario il collaudo su hardware reale.

## Cosa offre il prototipo

- avvio da chiavetta USB in modalità live, senza modificare il disco;
- installazione grafica tramite Calamares;
- scelta iniziale fra Studente (con il proprio indirizzo), Docente (tutti gli
  indirizzi), Personale di segreteria e Installazione base, oltre all'uso
  personale o condiviso del PC;
- scelta esplicita durante l'installazione fra accesso Workspace al primo avvio
  o configurazione successiva, sempre sul dominio `istitutostradivari.it`;
- desktop Xfce leggero, con interfaccia in italiano;
- tema morbido e accessibile coordinato alla palette StradiLab, senza effetti
  pesanti per i computer meno recenti, esteso a menu di avvio, caricamento,
  schermata di accesso, pannello e sistema installato;
- Google Chrome installabile con consenso dal Benvenuto, impostato come browser
  predefinito e configurato con un solo profilo Google sincronizzato;
- micro-app per Classroom, Drive, Gmail, Meet, Calendar, Documenti, Fogli,
  Presentazioni e Moduli, tutte collegate allo stesso profilo Chrome;
- Centro App grafico che, dopo l'installazione, scarica soltanto i pacchetti
  scelti per Liceo Artistico, Liceo Musicale, Liuteria, Moda e
  Arredo/Architettura;
- strumenti comuni per documenti, PDF, scansioni, stampa, audio e video;
- supporto a rete, Wi-Fi, Bluetooth e molti firmware non liberi inclusi.

## Hardware previsto

- CPU Intel o AMD a 64 bit;
- 2 GB di RAM come soglia minima di prova, 4 GB consigliati;
- chiavetta USB da almeno 8 GB, con immagine base alleggerita;
- circa 25 GB liberi per l'installazione su disco.

Sono previste due edizioni a 64 bit: `amd64` per i PC Intel/AMD e `arm64` per
Mac Apple Silicon e dispositivi ARM compatibili. I PC esclusivamente a 32 bit
richiederanno una variante distinta, perché le immagini live ufficiali Debian
e i browser correnti non coprono bene quel segmento.

## Struttura

- `auto/`: configurazione e comandi riproducibili di live-build;
- `config/package-lists/`: software presente nella ISO;
- `config/includes.chroot/`: file e applicazioni aggiunti a StradilabOS;
- `config/hooks/live/`: personalizzazioni eseguite durante la build;
- `scripts/`: sincronizzazione app StradiLab e controlli del progetto;
- `docs/`: architettura, catalogo e piano di collaudo;
- `.github/workflows/`: build automatica della ISO su Linux.

Il catalogo motivato è in `docs/CATALOGO-INDIRIZZI.md`. L'integrazione Google
Workspace e il comportamento sicuro sui PC di laboratorio sono descritti in
`docs/GOOGLE-WORKSPACE.md`.

## Aggiornare il catalogo StradiLab

Il catalogo è derivato da:

`/Users/claudionuzzo/Dev/stradilab/stradilab home/progetti.json`

Sul Mac del progetto:

```sh
python3 scripts/sync_stradilab_apps.py
```

Il comando aggiorna il catalogo interno e le voci «app» del menu. L'utente
finale non deve mai eseguire questo comando.

## Creare la ISO

La build richiede Linux e privilegi di amministrazione. Il Mac Apple Silicon
non può produrre direttamente una ISO `amd64` con live-build; per questo il
repository include workflow GitHub Actions native per entrambe le
architetture. Dalla scheda Actions si può avviare la build PC oppure la build
ARM64 per Parallels.

Su un computer Debian 13 dedicato alla build:

```sh
sudo apt update
sudo apt install live-build
sudo ./auto/build
```

Per creare localmente la variante ARM64 su un sistema ARM:

```sh
sudo BUILD_ARCH=arm64 ./auto/build
```

## Controlli prima della build

Ogni workflow esegue prima i test di regressione, il controllo dei cataloghi e
la verifica dei pacchetti Debian per l'architettura richiesta; a ISO terminata
controlla anche i file effettivamente contenuti nell'immagine. Localmente, i
controlli che non richiedono Linux si avviano con:

```sh
python3 -m unittest discover -v
python3 scripts/validate_project.py
```

Tra le regressioni coperte ci sono il dominio Workspace, i pulsanti delle
finestre, lo sfondo sui monitor con nome reale, l'agente grafico delle
autorizzazioni, la rimozione dell'installatore dal sistema installato e la
separazione fra dotazione base e raccolte scaricabili.

## Stato

Progetto in continuo sviluppo: configurazione, profili d'uso in Calamares,
protezione delle sessioni sui PC condivisi, launcher StradiLab e Workspace,
Centro App, identità completa StradilabOS, convalida automatica e pipeline ISO
sono presenti. Una versione precedente è stata installata con successo in
Parallels ARM; ogni nuova immagine va comunque reinstallata e collaudata prima
della distribuzione nella scuola.
