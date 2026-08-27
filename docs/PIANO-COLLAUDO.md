# Piano di collaudo StradilabOS

## Matrice minima dei computer

| Profilo | Avvio | RAM | Disco | Obiettivo |
| --- | --- | ---: | --- | --- |
| PC 2008–2011 | BIOS legacy | 2 GB | HDD | Avvio live, rete cablata, browser e documenti |
| PC 2012–2015 | UEFI | 4 GB | HDD | Avvio live, Wi-Fi, audio, video e sospensione |
| PC 2016–2020 | UEFI/Secure Boot | 8 GB | SSD | Installazione completa e applicazioni creative |

## Prova live

1. Menu iniziale con nome e sfondo StradilabOS, senza casco Debian.
2. Avvio da USB senza modificare il disco interno.
3. Caricamento, sfondo, pannello e utente Live identificati come StradilabOS.
4. Lingua, tastiera, fuso orario e risoluzione corretti.
5. Connessione Wi-Fi e cablata dall'interfaccia grafica.
6. Riproduzione e registrazione audio.
7. Apertura di una web app StradiLab in finestra dedicata.
8. Login `@istitutostradivari.it` condiviso fra due web app e rifiuto di un
   account Google esterno al dominio.
9. Apertura e salvataggio di DOCX, XLSX, PPTX e PDF.
10. Riconoscimento di una seconda chiavetta USB.
11. Stampa o almeno rilevamento di una stampante di rete.

## Prova d'installazione

Usare inizialmente un disco di prova senza dati importanti.

1. Avvio di Calamares da «Installa StradilabOS».
2. Verifica delle scelte Studente, Docente, Segreteria e Solo base.
3. Verifica delle scelte PC personale/condiviso e Workspace subito/in seguito.
4. Installazione automatica su tutto il disco.
5. Riavvio senza chiavetta.
6. Menu di avvio, caricamento e accesso con identità StradilabOS.
7. Creazione e accesso dell'utente scelto.
8. Se richiesto, pulsante Workspace principale al primo avvio e dominio
   `@istitutostradivari.it` chiaramente indicato.
9. Raccolte coerenti con il profilo già selezionate nel Centro App.
10. Download e avvio di almeno una raccolta specialistica.
11. Aggiornamenti da Synaptic.
12. Riavvio e spegnimento grafici.
13. Verifica che il launcher dell'installatore non resti visibile.

In Parallels, al termine dell'installazione usare **Dispositivi → CD/DVD →
Disconnetti** prima del riavvio. La ISO collegata equivale a lasciare la
chiavetta inserita e può essere scelta di nuovo dal firmware virtuale.

## Criteri di stop

Non distribuire la beta se si verifica uno di questi casi:

- l'installatore propone il disco sbagliato senza avviso chiaro;
- Wi-Fi o tastiera non funzionano su più di un modello della matrice;
- il login Google si perde passando fra web app;
- il sistema usa stabilmente più di 1,2 GB di RAM a riposo sul profilo da 2 GB;
- una web app riservata contiene credenziali o token già presenti nell'immagine;
- la ISO pubblicata non coincide con il checksum.
