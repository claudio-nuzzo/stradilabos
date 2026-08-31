#!/usr/bin/env python3
"""Genera le guide statiche delle app StradilabOS (requisito E).

Lettura obbligatoria: la struttura deve restare semplice, in italiano e
leggibile senza rete. Produce:
  - index.html                       (elenco delle guide raggruppato per indirizzo)
  - css/guida.css                    (foglio di stile condiviso)
  - una pagina HTML per ciascuna app.

Le guide sono file statici sotto usr/local/share/stradilabos/guide/, così in
futuro potranno essere corrette anche via canale aggiornamenti (serie in
update.sh) senza ricostruire la ISO.
"""

from __future__ import annotations

import html
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GUIDE_DIR = (
    PROJECT_ROOT
    / "config/includes.chroot/usr/local/share/stradilabos/guide"
)

INDIRIZZI = {
    "artistico": "Liceo Artistico",
    "scenografia": "Scenografia e palco",
    "video": "Video e comunicazione",
    "musicale": "Liceo Musicale",
    "liuteria": "Liuteria",
    "moda": "Moda",
    "arredo": "Arredo e Architettura",
    "base": "Tutti · strumenti comuni",
}

# (id, titolo, indirizzi, che_cosa, uso_scuola, come_si_apre,
#  primi_passi, problemi, link, link_label)
APPS = [
    (
        "libreoffice", "LibreOffice",
        ["base"],
        "La suite di ufficio per scrivere testi, fare calcoli, creare presentazioni e disegni.",
        "Serve in ogni indirizzo per relazioni, tabelle, presentazioni e lavori da consegnare.",
        "Menu StradiLab → «LibreOffice Writer» (testi), «Calc» (tabelle), «Impress» (presentazioni).",
        ["Apri Writer e scrivi il titolo del documento.", "Scrivi il testo e salva con «File → Salva» nella cartella Documenti.", "Per un calcolo apri Calc e scrivi i numeri nelle celle.", "Aggiungi una tabella con «Tabella → Inserisci tabella» in Writer.", "Esporta in PDF con «File → Esporta come PDF» per consegnarlo."],
        ["Non trovo il menu: apri il menu StradiLab e digita «Writer».", "Il file si apre male: salvalo come .odt oppure esporta in PDF.", "Voglio il controllo ortografico: è già attivo, le parole sbagliate sono sottolineate."],
        "https://it.libreoffice.org", "Guida di LibreOffice",
    ),
    (
        "file", "File e cartelle",
        ["base"],
        "Il gestore dei file per vedere documenti, immagini, chiavette e dischi.",
        "Serve a tutti per ritrovare i propri lavori e copiarli su una chiavetta.",
        "Menu StradiLab → «File» oppure l'icona File sulla barra.",
        ["Apri «File» e guarda a sinistra l'elenco delle cartelle.", "Doppio clic su una cartella per aprirla.", "Per copiare, seleziona il file e premi Ctrl+C, poi Ctrl+V nella cartella di arrivo.", "Inserisci la chiavetta USB: appare a sinistra con il suo nome.", "Estrai la chiavetta facendo clic destro su di essa e scegli «Smonta»."],
        ["Non vedo la chiavetta: controlla che sia inserita bene e riapri File.", "Un file non si apre: fai clic destro e prova «Apri con» un altro programma.", "Ho cancellato per errore: guarda nel Cestino sulla scrivania."],
        "https://docs.xfce.org/xfce/thunar/start", "Guida di Thunar",
    ),
    (
        "stampa-scansione", "Stampa e scansione",
        ["base"],
        "Gli strumenti per stampare i lavori e digitalizzare fogli e disegni con lo scanner.",
        "Serve in tutti gli indirizzi per consegnare su carta o scansionare esercizi e tavole.",
        "Menu StradiLab → «Stampa» o «Scansione semplice» (Simple Scan).",
        ["Controlla che la stampante sia accesa e collegata.", "Apri il documento e scegli «File → Stampa».", "Scegli la stampante nell'elenco e premi «Stampa».", "Per scansionare apri «Scansione semplice» e premi «Scansiona».", "Salva la scansione come PDF o immagine in Documenti."],
        ["La stampante non compare: verifica il cavo/usb e accendila.", "La stampa esce vuota: controlla livello inchiostro o toner.", "La scansione è storta: appoggia bene il foglio e rifai."],
        "https://www.cups.org", "Guida di stampa CUPS",
    ),
    (
        "krita", "Krita",
        ["artistico", "moda"],
        "Un programma di pittura digitale e illustrazione, pensato per disegnare al computer.",
        "Al Liceo Artistico e Moda serve per disegnare, colorare e preparare immagini e figurini.",
        "Menu StradiLab → «Krita», oppure dal Centro App dopo aver installato la raccolta.",
        ["Apri Krita e crea un nuovo disegno con «Nuovo file».", "Scegli un pennello dal pannello a destra.", "Disegna sulla tela trascinando il mouse o la penna.", "Cambia colore dal selettore in alto a destra.", "Salva con Ctrl+S e poi esporta in PNG con «File → Esporta»."],
        ["Non sento più i livelli: apri il pannello «Livelli» a destra.", "Il pennello non disegna: controlla che il livello non sia bloccato.", "Il file è pesante: usa «Immagine → Ridimensiona» prima di esportare."],
        "https://docs.krita.org", "Manuale di Krita",
    ),
    (
        "mypaint", "MyPaint",
        ["artistico"],
        "Un programma semplice e veloce per disegnare e dipingere, senza tanti menu.",
        "Utile per schizzi rapidi e prime idee nei laboratori artistici, anche su PC poco potenti.",
        "Menu StradiLab → «MyPaint», oppure dal Centro App dopo aver installato la raccolta.",
        ["Apri MyPaint: ti si presenta subito una tela bianca.", "Scegli un pennello dall'elenco.", "Dipingi trascinando il mouse.", "Premi il tasto destro per aprire il selettore colore.", "Salva con Ctrl+S nella cartella che preferisci."],
        ["Non vedo gli strumenti: premi F10 per mostrare il pannello.", "Il disegno è sfocato: usa la tela più grande nel menu «Tela».", "Voglio un'altra tela: apri «File → Nuovo»."],
        "https://mypaint.app", "Sito di MyPaint",
    ),
    (
        "gimp", "GIMP",
        ["artistico", "moda"],
        "Un programma di fotoritocco e modifica delle immagini, completo e gratuito.",
        "Serve per ritoccare foto, preparare immagini per stampe e comporre lavori grafici.",
        "Menu StradiLab → «GIMP», oppure dal Centro App dopo aver installato la raccolta.",
        ["Apri GIMP e carica un'immagine con «File → Apri».", "Usa lo strumento Selezione per scegliere una parte.", "Prova i Filtri dal menu in alto per effetti.", "Modifica i colori con «Colori → Livelli».", "Esporta in PNG o JPG con «File → Esporta come»."],
        ["I pannelli sono spariti: ripristina con «Finestre → Ripristina».", "Il testo è troppo piccolo: regola la dimensione nel pannello Testo.", "L'immagine è troppo scura: usa «Colori → Curve»."],
        "https://www.gimp.org", "Manuale di GIMP",
    ),
    (
        "inkscape", "Inkscape",
        ["artistico", "liuteria", "moda", "arredo"],
        "Un programma di disegno vettoriale: disegna forme e linee che restano nitide a ogni ingrandimento.",
        "Serve per loghi, tavole tecniche leggere, cartamodelli e grafiche precise.",
        "Menu StradiLab → «Inkscape», oppure dal Centro App dopo aver installato la raccolta.",
        ["Apri Inkscape e crea un nuovo documento.", "Scegli lo strumento Rettangolo o Ellisse a sinistra.", "Disegna le forme sulla pagina trascinando il mouse.", "Cambia il colore con la barra dei colori in basso.", "Salva come SVG e, se serve, esporta in PNG con Ctrl+E."],
        ["Le forme non si spostano: selezionale con la freccia a sinistra.", "Voglio linee precise: usa lo strumento Penna (traccia Bezier).", "Il PDF è sfocato: esporta in PDF come vettoriale, non come immagine."],
        "https://inkscape.org", "Manuale di Inkscape",
    ),
    (
        "scribus", "Scribus",
        ["artistico", "moda"],
        "Un programma di impaginazione per creare volantini, riviste e pagine pronte per la stampa.",
        "Serve per comporre pagine, locandine e fascicoli con testo e immagini allineati.",
        "Menu StradiLab → «Scribus», oppure dal Centro App dopo aver installato la raccolta.",
        ["Apri Scribus e scegli «Nuovo documento».", "Inserisci una casella di testo con lo strumento Testo.", "Scrivi il testo e imposta il font dal pannello Proprietà.", "Inserisci un'immagine con «File → Importa».", "Esporta in PDF con «File → Esporta in PDF»."],
        ["Il testo esce dai margini: riduci la casella o il font.", "Manca un font: scegli un font già installato di sistema.", "Il PDF è troppo grande: riduci la risoluzione delle immagini."],
        "https://www.scribus.net", "Manuale di Scribus",
    ),
    (
        "pencil2d", "Pencil2D",
        ["artistico"],
        "Un programma semplice per creare animazioni 2D disegnate a mano.",
        "Utile per esperimenti di animazione e brevi corti nel laboratorio artistico.",
        "Menu StradiLab → «Pencil2D», oppure dal Centro App dopo aver installato la raccolta.",
        ["Apri Pencil2D e crea un nuovo progetto.", "Disegna il primo frame con lo strumento Pennello.", "Premi «+» per aggiungere un frame successivo.", "Premi Invio per riprodurre l'animazione.", "Esporta con «File → Esporta» in video o immagine."],
        ["L'animazione è veloce: riduci i frame al secondo nelle impostazioni.", "Non disegna: controlla di essere sul livello bitmap.", "Voglio un video: esporta in .mp4."],
        "https://www.pencil2d.org", "Sito di Pencil2D",
    ),
    (
        "blender", "Blender",
        ["artistico", "scenografia", "arredo"],
        "Un programma completo di modellazione, animazione e rendering 3D.",
        "Serve per oggetti, ambienti e scene 3D in Scenografia e Arredo; richiede un PC con memoria adeguata.",
        "Menu StradiLab → «Blender», oppure dal Centro App dopo aver installato la raccolta.",
        ["Apri Blender e scegli la scena di partenza.", "Usa il tasto destro per selezionare un oggetto.", "Muovi con G, ruota con R, scala con S.", "Guarda la scena muovendo la vista con il mouse centrale.", "Salva con Ctrl+S il file .blend."],
        ["L'interfaccia è in inglese: i comandi G/R/S sono sempre gli stessi.", "La scena è lenta: riduci le suddivisioni o la risoluzione.", "Non vedo l'oggetto: premi il tasto Home per inquadrare tutto."],
        "https://www.blender.org", "Manuale di Blender",
    ),
    (
        "qlcplus", "QLC+",
        ["scenografia"],
        "Un programma per controllare le luci da palco (DMX): colori, intensità e scene.",
        "Serve in Scenografia per progettare e comandare le luci di uno spettacolo.",
        "Menu StradiLab → «QLC+», oppure dal Centro App dopo aver installato la raccolta.",
        ["Apri QLC+ e crea un nuovo progetto.", "Collega le luci configurando l'interfaccia DMX.", "Usa il pannello Funzioni per creare una scena.", "Assegna i canali e regola l'intensità.", "Premi il pulsante Play per provare la scena."],
        ["Le luci non rispondono: controlla il cavo/interfaccia DMX.", "Voglio una sequenza: crea una Chase nel pannello Funzioni.", "Non trovo il pannello: ripristina la disposizione delle finestre."],
        "https://www.qlcplus.org", "Sito di QLC+",
    ),
    (
        "sweethome3d", "Sweet Home 3D",
        ["scenografia", "arredo"],
        "Un programma per disegnare interni e arredare stanze in 3D.",
        "Serve per progettare ambienti e piante di interni in Scenografia e Arredo.",
        "Menu StradiLab → «Sweet Home 3D», oppure dal Centro App dopo aver installato la raccolta.",
        ["Apri Sweet Home 3D e parte una casa vuota.", "Disegna i muri con lo strumento Crea muri.", "Trascina mobili dal catalogo a sinistra nella pianta.", "Muoviti nella vista 3D tenendo premuto e trascinando.", "Salva il progetto e stampa la pianta se serve."],
        ["Non vedo la vista 3D: attivala con il menu «3D» in alto.", "Il mobile non entra: riducilo con le maniglie gialle.", "Voglio le misure reali: usa lo strumento Quota."],
        "https://www.sweethome3d.com", "Sito di Sweet Home 3D",
    ),
    (
        "kdenlive", "Kdenlive",
        ["scenografia", "video"],
        "Un programma di montaggio video con più tracce ed effetti.",
        "Serve per montare video di spettacoli, presentazioni e progetti di comunicazione.",
        "Menu StradiLab → «Kdenlive», oppure dal Centro App dopo aver installato la raccolta.",
        ["Apri Kdenlive e crea un nuovo progetto.", "Importa i filmati con «Progetto → Aggiungi clip».", "Trascina le clip sulla timeline in basso.", "Taglia con il rasoio (C) e sposta i pezzi.", "Esporta il filmato con «Progetto → Renderizza»."],
        ["La timeline è vuota: trascina le clip dal pannello a sinistra.", "Il video è a scatti: riduci la qualità di anteprima.", "Manca l'audio: controlla che la traccia audio non sia muta."],
        "https://kdenlive.org", "Sito di Kdenlive",
    ),
    (
        "musescore", "MuseScore",
        ["musicale"],
        "Un programma per scrivere spartiti musicali e ascoltarli.",
        "Al Liceo Musicale serve per comporre, trascrivere e stampare partiture.",
        "Menu StradiLab → «MuseScore», oppure dal Centro App dopo aver installato la raccolta.",
        ["Apri MuseScore e crea un nuovo spartito.", "Scegli gli strumenti con la procedura guidata.", "Inserisci le note cliccando sulla griglia o con la tastiera.", "Premi Spazio per ascoltare lo spartito.", "Salva e stampa con «File → Stampa»."],
        ["Non sento l'audio: controlla il volume e l'uscita audio.", "La nota è sbagliata: selezionala e cancellala con Canc.", "Voglio un PDF: usa «File → Esporta in PDF»."],
        "https://musescore.org", "Manuale di MuseScore",
    ),
    (
        "rosegarden", "Rosegarden",
        ["musicale"],
        "Un programma per comporre e registrare musica con strumenti virtuali (MIDI).",
        "Serve per arrangiamenti e composizione al Liceo Musicale.",
        "Menu StradiLab → «Rosegarden», oppure dal Centro App dopo aver installato la raccolta.",
        ["Apri Rosegarden e crea un nuovo documento.", "Aggiungi una traccia MIDI dal menu Traccia.", "Collega uno strumento virtuale (come QSynth).", "Registra o inserisci le note nell'editor.", "Salva il progetto e, se serve, esporta l'audio."],
        ["Non c'è suono: avvia QSynth prima di Rosegarden.", "Le note non si sentono: controlla il collegamento MIDI delle tracce.", "Voglio stampare: esporta in MusicXML o PDF."],
        "https://rosegardenmusic.com", "Sito di Rosegarden",
    ),
    (
        "qsynth", "QSynth",
        ["musicale"],
        "Un programma che riproduce i suoni degli strumenti per il MIDI (sintetizzatore).",
        "Serve per far suonare MuseScore, Rosegarden e gli altri programmi musicali.",
        "Menu StradiLab → «QSynth», oppure dal Centro App dopo aver installato la raccolta.",
        ["Apri QSynth e carica un file di suoni (SoundFont).", "Seleziona un canale e scegli uno strumento.", "Avvia il programma musicale che vuoi far suonare.", "Alza il volume dalla finestra di QSynth.", "Se non serve più, chiudi QSynth."],
        ["Nessun suono: carica il SoundFont «fluid-soundfont-gm».", "Il suono gracchia: aumenta la latenza nelle impostazioni.", "Non si collega: verifica che il programma usi JACK/ALSA."],
        "https://qsynth.sourceforge.io", "Sito di QSynth",
    ),
    (
        "pianobooster", "PianoBooster",
        ["musicale"],
        "Un programma per esercitarsi al pianoforte con l'aiuto del computer.",
        "Serve per esercitarsi a suonare e correggere il ritmo al Liceo Musicale.",
        "Menu StradiLab → «PianoBooster», oppure dal Centro App dopo aver installato la raccolta.",
        ["Apri PianoBooster e collega una tastiera MIDI se la usi.", "Carica un brano MIDI da esercitarti.", "Premi Play e prova a suonare seguendo lo schermo.", "Il programma aspetta le note giuste se scegli la modalità di attesa.", "Aumenta la difficoltà quando sei pronto."],
        ["Non rileva la tastiera: controlla il cavo USB/MIDI.", "Va troppo veloce: riduci il tempo della canzone.", "Quasi nessun suono: usa QSynth come strumento."],
        "https://pianobooster.sourceforge.io", "Sito di PianoBooster",
    ),
    (
        "audacity", "Audacity",
        ["musicale", "liuteria"],
        "Un programma per registrare e modificare l'audio (multitraccia).",
        "Serve per registrare, tagliare e pulire audio e strumenti in Liuteria e Musica.",
        "Menu StradiLab → «Audacity», oppure dal Centro App dopo aver installato la raccolta.",
        ["Apri Audacity e premi il tasto rosso per registrare.", "Importa un file con «File → Importa → Audio».", "Seleziona una parte e premi Canc per tagliarla.", "Usa «Effetti» per ridurre rumore o regolare il volume.", "Esporta con «File → Esporta» in MP3 o WAV."],
        ["Registrazione muta: controlla il microfono nell'ingresso audio.", "Il file è lungo: ingrandisci con Ctrl+1.", "C'è rumore di fondo: usa «Effetti → Riduzione rumore»."],
        "https://www.audacityteam.org", "Manuale di Audacity",
    ),
    (
        "ardour", "Ardour",
        ["musicale"],
        "Un programma professionale di registrazione e mixaggio multitraccia.",
        "Serve per progetti audio complessi e registrazione in studio al Liceo Musicale.",
        "Menu StradiLab → «Ardour», oppure dal Centro App dopo aver installato la raccolta.",
        ["Apri Ardour e crea una nuova sessione.", "Aggiungi tracce audio o MIDI dal menu Traccia.", "Arma la traccia (tasto rosso) e premi Registra.", "Regola i volumi con i fader del mixer.", "Esporta il mix con «Sessione → Esporta»."],
        ["Non sento l'audio: controlla le uscite del mixer.", "Il suono si interrompe: aumenta la dimensione del buffer.", "La traccia non registra: verifica che sia armata."],
        "https://ardour.org", "Manuale di Ardour",
    ),
    (
        "lmms", "LMMS",
        ["musicale"],
        "Un programma per creare musica elettronica e ritmi.",
        "Serve per sperimentare ritmi, melodie e produzione musicale.",
        "Menu StradiLab → «LMMS», oppure dal Centro App dopo aver installato la raccolta.",
        ["Apri LMMS e carica un progetto o creane uno nuovo.", "Trascina strumenti dal pannello a sinistra nell'Editor canzoni.", "Disegna le note nell'editor per pattern.", "Premi Play per ascoltare il pattern.", "Salva il progetto e, se serve, esporta l'audio."],
        ["Non sento nulla: controlla che l'uscita audio sia attiva.", "Le note non combaciano: usa la griglia per allinearle.", "Voglio un ritmo: carica un campione di batteria."],
        "https://lmms.io", "Sito di LMMS",
    ),
    (
        "hydrogen", "Hydrogen",
        ["musicale"],
        "Un programma per creare ritmi di batteria.",
        "Serve per costruire basi ritmiche e accompagnamenti.",
        "Menu StradiLab → «Hydrogen», oppure dal Centro App dopo aver installato la raccolta.",
        ["Apri Hydrogen e scegli un pattern di batteria.", "Clicca sulle caselle per attivare i colpi.", "Premi Play per ascoltare il ritmo.", "Aggiungi più pattern per creare una canzone.", "Esporta l'audio quando sei soddisfatto."],
        ["Non sento la batteria: controlla il volume generale.", "Il ritmo è sbagliato: disattiva le caselle errate.", "Voglio un altro kit: scegli un kit dal menu Strumenti."],
        "http://hydrogen-music.org", "Sito di Hydrogen",
    ),
    (
        "sonic-visualiser", "Sonic Visualiser",
        ["musicale", "liuteria"],
        "Un programma per vedere la forma d'onda e lo spettro del suono.",
        "Serve per analizzare l'audio: intonazione, spettro e forma d'onda in Musica e Liuteria.",
        "Menu StradiLab → «Sonic Visualiser», oppure dal Centro App dopo aver installato la raccolta.",
        ["Apri Sonic Visualiser e carica un file audio.", "Scegli una visualizzazione dal menu «Pane».", "Aggiungi uno spettrogramma per vedere le frequenze.", "Usa la rotella del mouse per ingrandire.", "Misura i tempi o le frequenze con i righelli."],
        ["Il file non si apre: convertilo prima in WAV o MP3.", "Non vedo lo spettro: aggiungi il pannello Spettrogramma.", "Voglio annotare: usa «Livello → Aggiungi annotazione»."],
        "https://www.sonicvisualiser.org", "Sito di Sonic Visualiser",
    ),
    (
        "fmit", "FMIT",
        ["liuteria"],
        "Un accordatore preciso che mostra la frequenza delle note suonate.",
        "Serve in Liuteria per accordare e verificare l'intonazione degli strumenti.",
        "Menu StradiLab → «FMIT», oppure dal Centro App dopo aver installato la raccolta.",
        ["Apri FMIT e scegli il microfono o l'ingresso audio.",        "Suona una nota vicino al microfono.", "Leggi la frequenza e la nota in alto.", "Regola lo strumento finché la nota è stabile.", "Salva i valori se ti servono per un confronto."],
        ["Non rileva la nota: avvicina lo strumento al microfono.", "La nota oscilla: suona più piano e costante.", "Voglio una nota di riferimento: usala dal menu."],
        "https://fmit.sourceforge.io", "Sito di FMIT",
    ),
    (
        "freecad", "FreeCAD",
        ["liuteria", "arredo"],
        "Un programma di CAD 3D parametrico per progettare oggetti con misure esatte.",
        "Serve per disegnare pezzi, dime e componenti in Liuteria e Arredo.",
        "Menu StradiLab → «FreeCAD», oppure dal Centro App dopo aver installato la raccolta.",
        ["Apri FreeCAD e crea un nuovo documento.", "Scegli un ambiente di lavoro (parte o parte design).", "Disegna uno schizzo 2D con lo strumento Schizzo.", "Estrudi la forma con «Pad» per renderla 3D.", "Salva il file .FCStd."],
        ["Non vedo gli strumenti: scegli l'ambiente di lavoro corretto.", "Le misure sono sbagliate: inserisci le quote nello schizzo.", "Il disegno non si muove: selezionalo nel pannello Struttura."],
        "https://www.freecad.org", "Manuale di FreeCAD",
    ),
    (
        "librecad", "LibreCAD",
        ["liuteria", "arredo"],
        "Un programma di CAD 2D per disegni tecnici con quote e linee precise.",
        "Serve per tavole tecniche e disegni 2D in Liuteria e Arredo.",
        "Menu StradiLab → «LibreCAD», oppure dal Centro App dopo aver installato la raccolta.",
        ["Apri LibreCAD e crea un nuovo disegno.", "Usa lo strumento Linea per tracciare i contorni.", "Inserisci le quote con lo strumento Quota.", "Salva in formato DXF.", "Stampa o esporta in PDF la tavola."],
        ["Le linee non si uniscono: usa lo snap agli estremi.", "Le quote mancano: aggiungile dal menu Quota.", "Il disegno è piccolo: cambia la scala di visualizzazione."],
        "https://librecad.org", "Manuale di LibreCAD",
    ),
    (
        "solvespace", "SolveSpace",
        ["liuteria", "arredo"],
        "Un programma CAD parametrico 2D/3D leggero, con disegno a vincoli.",
        "Serve per forme e meccanismi semplici con vincoli geometrici.",
        "Menu StradiLab → «SolveSpace», oppure dal Centro App dopo aver installato la raccolta.",
        ["Apri SolveSpace e disegna le linee base nello schizzo.", "Aggiungi i vincoli per fissare le misure.", "Estrudi lo schizzo per ottenere il 3D.", "Muovi le forme trascinando i punti.", "Esporta in DXF o STL."],
        ["I punti non si trascinano: verifica che il vincolo sia attivo.", "Il solido non appare: estrudilo dal menu Nuovo gruppo.", "Serve una misura esatta: usa il vincolo di quota."],
        "https://solvespace.com", "Sito di SolveSpace",
    ),
    (
        "openscad", "OpenSCAD",
        ["liuteria", "arredo"],
        "Un programma che crea oggetti 3D scrivendo comandi (script), non disegnando a mano.",
        "Serve per modelli parametrici e ripetibili in Liuteria e Arredo.",
        "Menu StradiLab → «OpenSCAD», oppure dal Centro App dopo aver installato la raccolta.",
        ["Apri OpenSCAD e scrivi un comando come cube([10,10,10]);", "Premi F5 per vedere l'anteprima.", "Aggiungi forme con sphere, cylinder e translate.", "Premi F6 per il rendering completo.", "Esporta in STL con «File → Esporta»."],
        ["La forma non appare: controlla il punto e virgola in fondo al comando.", "Le forme si sovrappongono: usa translate per spostarle.", "Voglio un'anteprima veloce: usa F5 invece di F6."],
        "https://openscad.org", "Manuale di OpenSCAD",
    ),
    (
        "meshlab", "MeshLab",
        ["liuteria", "arredo"],
        "Un programma per pulire e misurare modelli 3D (scansioni e mesh).",
        "Serve in Liuteria per pulire le scansioni 3D degli strumenti.",
        "Menu StradiLab → «MeshLab», oppure dal Centro App dopo aver installato la raccolta.",
        ["Apri MeshLab e importa il modello 3D (.stl/.ply/.obj).", "Esplora la mesh trascinando il mouse.", "Usa «Filters» per pulire o semplificare la superficie.", "Misura le distanze con lo strumento di misura.", "Esporta il modello ripulito."],
        ["La mesh è pesante: semplificala con un filtro di decimazione.", "Il modello è bucato: usa un filtro di chiusura buchi.", "Non si vede: premi Ctrl+E per inquadrare il modello."],
        "https://www.meshlab.net", "Sito di MeshLab",
    ),
    (
        "seamly2d", "Seamly2D",
        ["moda"],
        "Un programma per disegnare cartamodelli con misure e curve precise.",
        "Serve in Moda per creare e modificare cartamodelli su misura.",
        "Menu StradiLab → «CAD Moda», oppure dal Centro App dopo aver installato la raccolta.",
        ["Apri Seamly2D e crea un nuovo cartamodello.", "Inserisci le misure della persona nel pannello Misure.", "Disegna i punti e le curve del modello.", "Regola le misure e il modello si aggiorna.", "Stampa o esporta il cartamodello in scala."],
        ["Le curve non tornano: controlla i punti di controllo.", "Il cartamodello è fuori scala: verifica le misure iniziali.", "Non trovo il pannello: ripristina la disposizione delle finestre."],
        "https://seamly.io", "Sito di Seamly2D",
    ),
    (
        "freesewing", "FreeSewing",
        ["moda"],
        "Un sito per generare cartamodelli su misura partendo dalle tue misure.",
        "Serve in Moda per ottenere cartamodelli parametrici senza disegnarli a mano.",
        "Menu StradiLab → «FreeSewing», oppure dal Centro App (è una web app).",
        ["Apri FreeSewing dal menu StradiLab.", "Scegli un modello di indumento.", "Inserisci le misure richieste.", "Genera il cartamodello e scaricalo.", "Stampa il cartamodello in formato A4 o plotter."],
        ["Le misure sono sbagliate: rifai la misurazione con attenzione.", "Il cartamodello non si scarica: usa la stampa in PDF.", "Voglio modificarlo: esportalo e aprilo in Seamly2D."],
        "https://freesewing.org", "Sito di FreeSewing",
    ),
    (
        "posterazor", "PosteRazor",
        ["moda"],
        "Un programma che spezza un'immagine grande in più fogli A4 da stampare.",
        "Serve in Moda per stampare cartamodelli e tavole in scala su fogli normali.",
        "Menu StradiLab → «PosteRazor», oppure dal Centro App dopo aver installato la raccolta.",
        ["Apri PosteRazor e carica l'immagine da stampare.", "Scegli il formato carta (A4) e l'orientamento.", "Imposta la scala del cartamodello.", "Controlla quante pagine verranno stampate.", "Salva il PDF multipagina e stampalo."],
        ["La scala è sbagliata: imposta la percentuale esatta nel passaggio Scala.", "I fogli non combaciano: stampa senza bordi o usa i segni di taglio.", "L'immagine è sfocata: usa un file grande (300 dpi)."],
        "https://posterazor.sourceforge.io", "Sito di PosteRazor",
    ),
    (
        "qelectrotech", "QElectroTech",
        ["arredo"],
        "Un programma per disegnare schemi elettrici con simboli pronti.",
        "Serve in Arredo per disegnare impianti e schemi elettrici.",
        "Menu StradiLab → «QElectroTech», oppure dal Centro App dopo aver installato la raccolta.",
        ["Apri QElectroTech e crea un nuovo progetto.", "Scegli un cartiglio per il foglio.", "Trascina i simboli dalla libreria sul foglio.", "Collega i simboli con i fili.", "Salva e stampa lo schema."],
        ["Non trovo un simbolo: cerca nella libreria per nome.", "I fili non si collegano: usa lo strumento Filo.", "Lo schema è disordinato: usa la griglia per allineare."],
        "https://qelectrotech.org", "Sito di QElectroTech",
    ),
]


def page(app: tuple) -> str:
    (app_id, title, indirizzi, cosa, uso, apre, passi, problemi, link, link_label) = app
    address_names = [INDIRIZZI.get(i, i) for i in indirizzi]
    steps = "".join(f"<li>{html.escape(s)}</li>\n" for s in passi)
    problems = "".join(f"<li>{html.escape(p)}</li>\n" for p in problemi)
    audience = ", ".join(address_names)
    back = "index.html"
    body = f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} · Guide StradilabOS</title>
<link rel="stylesheet" href="css/guida.css">
</head>
<body>
<header class="testata">
  <p class="occhiello">Guide StradilabOS · {html.escape(audience)}</p>
  <h1>{html.escape(title)}</h1>
</header>
<main class="pagina">
  <p class="intro">{html.escape(cosa)}</p>
  <section>
    <h2>A cosa serve a scuola</h2>
    <p>{html.escape(uso)}</p>
  </section>
  <section>
    <h2>Come si apre</h2>
    <p>{html.escape(apre)}</p>
  </section>
  <section>
    <h2>I primi 5 passi</h2>
    <ol>
{steps}    </ol>
  </section>
  <section>
    <h2>Tre problemi comuni</h2>
    <ul>
{problems}    </ul>
  </section>
  <section>
    <h2>Per imparare di più</h2>
    <p><a href="{html.escape(link)}">{html.escape(link_label)}</a></p>
  </section>
</main>
<footer class="pie">
  <a href="{back}">← Tutte le guide</a>
</footer>
</body>
</html>
"""
    return body


def index_page() -> str:
    groups: dict[str, list[tuple[str, str]]] = {}
    for app in APPS:
        app_id, title, indirizzi = app[0], app[1], app[2]
        for name in indirizzi:
            groups.setdefault(name, []).append((title, f"{app_id}.html"))

    order = ["base", "artistico", "scenografia", "video", "musicale", "liuteria", "moda", "arredo"]
    sections = []
    for key in order:
        items = groups.get(key)
        if not items:
            continue
        links = "".join(
            f'<li><a href="{html.escape(path)}">{html.escape(title)}</a></li>\n'
            for title, path in sorted(items)
        )
        sections.append(
            f'<section class="indirizzo" id="{html.escape(key)}">'
            f'<h2>{html.escape(INDIRIZZI[key])}</h2><ul>\n{links}</ul></section>'
        )

    nav = "".join(
        f'<a href="#{html.escape(key)}">{html.escape(INDIRIZZI[key])}</a>'
        for key in order
        if groups.get(key)
    )
    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Guide delle app StradilabOS</title>
<link rel="stylesheet" href="css/guida.css">
</head>
<body>
<header class="testata">
  <p class="occhiello">StradilabOS</p>
  <h1>Guide delle app</h1>
  <p class="sottotitolo">Mini istruzioni in italiano, per imparare a usare le app della tua area.</p>
</header>
<nav class="indice">{nav}</nav>
<main class="pagina">
{sections}
</main>
<footer class="pie">Guide StradilabOS · leggibili anche senza connessione</footer>
<script>
  // Apre direttamente la sezione dell'indirizzo richiesto (es. index.html#moda).
  var hash = window.location.hash;
  if (hash) {{
    var el = document.querySelector(hash);
    if (el) {{ el.scrollIntoView(); }}
  }}
</script>
</body>
</html>
"""


def main() -> int:
    css = """/* Guide StradilabOS: leggere, in italiano, leggibili anche offline. */
:root {
  --bordeaux: #9b2335;
  --navy: #1b3a6b;
  --crema: #f6f4ef;
  --avorio: #ffffff;
  --inchiostro: #16130f;
  --testo: #645e55;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: "Noto Sans", "Liberation Sans", sans-serif;
  background: var(--crema);
  color: var(--inchiostro);
  line-height: 1.5;
}
.testata {
  background: var(--navy);
  color: var(--avorio);
  padding: 26px 30px;
}
.testata .occhiello {
  margin: 0;
  color: #ded8ce;
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.testata h1 { margin: 4px 0 6px; font-size: 30px; }
.testata .sottotitolo { margin: 0; color: #ded8ce; }
.indice {
  padding: 14px 30px;
  background: rgba(222, 216, 206, 0.45);
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.indice a {
  color: var(--bordeaux);
  text-decoration: none;
  font-weight: 700;
  font-size: 14px;
  padding: 6px 10px;
  border-radius: 999px;
  background: var(--avorio);
}
.indice a:hover { background: var(--bordeaux); color: var(--avorio); }
.pagina { max-width: 820px; margin: 0 auto; padding: 26px 30px 40px; }
.pagina .intro { font-size: 18px; color: var(--inchiostro); }
.pagina h2 {
  color: var(--bordeaux);
  font-size: 20px;
  margin-top: 26px;
  border-bottom: 2px solid var(--bordeaux);
  padding-bottom: 4px;
}
.pagina a { color: var(--bordeaux); font-weight: 700; }
.pagina li { margin-bottom: 6px; }
.indirizzo { margin-top: 22px; }
.indirizzo ul { margin: 6px 0 0; }
.pie {
  max-width: 820px;
  margin: 0 auto;
  padding: 14px 30px 34px;
  color: var(--testo);
  font-size: 14px;
}
.pie a { color: var(--bordeaux); font-weight: 700; }
"""
    css_dir = GUIDE_DIR / "css"
    css_dir.mkdir(parents=True, exist_ok=True)
    (css_dir / "guida.css").write_text(css, encoding="utf-8")

    for app in APPS:
        (GUIDE_DIR / f"{app[0]}.html").write_text(page(app), encoding="utf-8")

    (GUIDE_DIR / "index.html").write_text(index_page(), encoding="utf-8")

    total = len(APPS) + 2
    print(f"Guide generate: {len(APPS)} pagine + index + css = {total} file.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())