# StradilabOS

StradilabOS è una distribuzione scolastica live USB, installabile e pensata per
recuperare PC a 64 bit non più adatti ai sistemi operativi moderni. L'obiettivo
è offrire un ambiente semplice, in italiano e utilizzabile senza terminale,
centrato sull'ecosistema StradiLab dell'IIS «Antonio Stradivari» di Cremona.

Questo repository contiene il primo prototipo tecnico, non ancora un'immagine
ISO collaudata su hardware reale.

## Cosa offre il prototipo

- avvio da chiavetta USB in modalità live, senza modificare il disco;
- installazione grafica tramite Calamares;
- scelta in installazione di uno o più indirizzi e dell'uso personale o
  condiviso del PC;
- desktop Xfce leggero, con interfaccia in italiano;
- app StradiLab aperte in finestre Chromium dedicate, con una sola sessione
  Google condivisa;
- accesso guidato a Google Workspace e micro-app per Classroom, Drive, Gmail,
  Meet, Calendar, Documenti, Fogli, Presentazioni e Moduli;
- Centro App grafico con pacchetti per Liceo Artistico, Liceo Musicale,
  Liuteria, Moda e Arredo/Architettura;
- strumenti comuni per documenti, PDF, scansioni, stampa, audio e video;
- supporto a rete, Wi-Fi, Bluetooth e molti firmware non liberi inclusi.

## Hardware previsto

- CPU Intel o AMD a 64 bit;
- 2 GB di RAM come soglia minima di prova, 4 GB consigliati;
- chiavetta USB da almeno 8 GB;
- circa 25 GB liberi per l'installazione su disco.

Sono previste due edizioni a 64 bit: `amd64` per i PC Intel/AMD e `arm64` per
Mac Apple Silicon e dispositivi ARM compatibili. I PC esclusivamente a 32 bit
richiederanno una variante distinta, perché le immagini live ufficiali Debian
e Chromium correnti non coprono bene quel segmento.

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

## Stato

MVP locale: configurazione, profili per indirizzo in Calamares, protezione delle
sessioni sui PC condivisi, launcher StradiLab e Workspace, Centro App,
benvenuto grafico, branding, convalida automatica e pipeline ISO. Restano
indispensabili la prima build Linux e il collaudo su una rosa di PC reali prima
di distribuire la chiavetta nella scuola.
