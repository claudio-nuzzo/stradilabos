# Architettura di StradilabOS

## Scelta della base

La base scelta per l'MVP è Debian 13 stable con Xfce.

Debian offre immagini live ibride avviabili sia su BIOS sia su UEFI e include
Calamares come installatore grafico nelle immagini live ufficiali. Xfce conserva
un modello desktop familiare, richiede meno risorse di GNOME e KDE e permette di
nascondere la complessità tecnica senza costruire un'interfaccia da zero.

Linux Mint Xfce rimane una buona alternativa, ma una derivata costruita con
live-build ci dà più controllo, meno dipendenze specifiche e un processo di
generazione automatizzabile.

## Principio di esperienza utente

All'inizio dell'installazione l'utente sceglie un profilo d'uso: Studente con
il proprio indirizzo, Docente con accesso alle raccolte di tutti gli indirizzi,
Personale di segreteria oppure Installazione base. Indica poi se il PC è
personale o condiviso e se desidera accedere a Google Workspace al primo avvio
oppure in seguito. L'installatore dichiara sempre il dominio scolastico
`@istitutostradivari.it`. Calamares salva queste preferenze nel profilo del
nuovo utente; la schermata di benvenuto consente di cambiarle in seguito senza
usare il terminale.

L'utente vede sei azioni principali:

1. connettersi alla rete;
2. scaricare Chrome, creare il profilo e accedere a Google Workspace;
3. aprire StradiLab;
4. consultare i servizi della scuola;
5. scegliere le app consigliate per il proprio ruolo e indirizzo;
6. provare o installare il sistema.

Il terminale resta installato per la manutenzione tecnica, ma non compare nei
menu né nella barra StradiLab. Tutte le attività ordinarie hanno un percorso
grafico.

La stessa identità visiva accompagna l'intero percorso: menu della chiavetta,
caricamento Plymouth, sessione Live, installatore, schermata di accesso e
sistema installato. `os-release`, GRUB e Calamares usano il nome StradilabOS;
Debian resta dichiarata come base compatibile, non come identità principale.

## Web app StradiLab

Ogni progetto attivo in `progetti.json` genera una voce `.desktop`. Dopo la
configurazione guidata la voce avvia Google Chrome con `--app=<URL>`: niente
barra degli indirizzi, una finestra separata e un comportamento simile a
un'app locale. Chromium resta nella base Debian come ripiego.

Tutte le finestre usano il profilo Chrome nativo, senza una directory dati
parallela. È una scelta intenzionale: l'accesso Google istituzionale e la
sincronizzazione vengono attivati una volta e restano disponibili nelle diverse
app StradiLab. I dati di accesso e il pacchetto proprietario Chrome non sono
incorporati nella ISO.

Su un PC personale il profilo del browser è persistente. Su un PC condiviso o
avviato dalla chiavetta, il browser usa invece una cartella temporanea nella
sessione dell'utente: Classroom, Drive e le altre app condividono l'accesso
finché l'utente è collegato, ma i dati vengono eliminati alla chiusura della
sessione. Questa distinzione evita che un laboratorio conservi l'account dello
studente precedente.

Un launcher grafico riunisce le stesse app per pubblico e categoria, senza
riempire il desktop di icone.

## Software locale

La ISO base include desktop, Chromium di riserva, Google Workspace e micro-app scolastiche,
LibreOffice e gli strumenti comuni. Le applicazioni creative più pesanti non
sono duplicate nella chiavetta: dopo l'installazione il Centro App preseleziona
le raccolte corrispondenti al profilo scelto e le scarica da Debian o Flathub
con un'unica autorizzazione grafica. Il profilo Docente propone tutti gli
indirizzi; Segreteria e Installazione base non preselezionano software
specialistico.

Il download non è parte obbligatoria di Calamares. In questo modo una rete lenta
o assente non può interrompere l'installazione del sistema operativo. Nella
sessione live il catalogo è consultabile, ma l'installazione delle raccolte è
disabilitata perché verrebbe persa allo spegnimento.

| Pacchetto | Destinazione | Applicazioni principali |
| --- | --- | --- |
| Liceo Artistico | arti figurative, grafica | Krita, GIMP, Inkscape, Scribus, Blender, Pencil2D, MyPaint |
| Scenografia | spazio scenico, video, luci | Blender, Sweet Home 3D, QLC+, Kdenlive |
| Liceo Musicale | notazione, MIDI, registrazione, analisi | MuseScore, Audacity, Ardour, Rosegarden, LMMS, Sonic Visualiser, PianoBooster |
| Liuteria | disegno, scansione, misurazione, acustica | FreeCAD, SolveSpace, OpenSCAD, MeshLab, Inkscape, FMIT, Sonic Visualiser |
| Moda | cartamodelli, misure, figurino, stampa in scala | Seamly2D, FreeSewing, Inkscape, Krita, GIMP, Scribus, PosteRazor |
| Arredo e architettura | CAD, impianti, modellazione e interni | FreeCAD, LibreCAD, SolveSpace, OpenSCAD, QElectroTech, MeshLab, Blender, Sweet Home 3D |
| Video e comunicazione | montaggio e streaming | Kdenlive, Darktable, HandBrake, OBS Studio |
| Accessibilità | lettura e accesso facilitato | Orca, tastiera a schermo, eSpeak NG |

Il backend accetta soltanto identificativi presenti nel catalogo locale, valida
i nomi dei pacchetti e usa `pkexec`: non esegue testo arbitrario fornito
dall'interfaccia.

Seamly2D arriva da Flathub perché Debian 13 stable non contiene un CAD moda
specialistico aggiornato. Il Centro App lo installa graficamente insieme alla
raccolta Moda. FreeSewing è invece una micro-app web per generare cartamodelli a
partire dalle misure.

## Limiti dell'MVP

- edizioni `amd64` e `arm64`; nessun supporto ai PC esclusivamente a 32 bit;
- ARM64 è destinata soprattutto ai test su Mac Apple Silicon in Parallels e
  richiede verifiche specifiche prima dell'uso su altri dispositivi ARM;
- le web app richiedono Internet;
- Google Chrome richiede un download esplicito di circa 130–140 MB dopo
  l'installazione del sistema;
- Google Drive per desktop non è disponibile per Linux; StradilabOS usa Drive
  e gli editor Workspace nel browser;
- la modalità live non conserva i dati tra un riavvio e l'altro senza una
  chiavetta preparata con persistenza;
- la compatibilità di Wi-Fi, audio, grafica e sospensione va verificata su
  hardware reale;
- le applicazioni opzionali richiedono Internet e spazio su disco.

## Criterio di rilascio

La ISO potrà essere indicata come beta soltanto dopo:

- build riproducibile completata;
- checksum pubblicato;
- avvio provato su BIOS e UEFI;
- prova live e installazione completa;
- collaudo di rete, audio, stampa e browser;
- accesso Google istituzionale verificato senza memorizzare credenziali nella
  chiavetta master;
- almeno un test con 2 GB e uno con 4 GB di RAM.
