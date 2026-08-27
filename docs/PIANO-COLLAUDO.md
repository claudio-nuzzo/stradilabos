# Piano di collaudo StradilabOS

## Matrice minima dei computer

| Profilo | Avvio | RAM | Disco | Obiettivo |
| --- | --- | ---: | --- | --- |
| PC 2008–2011 | BIOS legacy | 2 GB | HDD | Avvio live, rete cablata, browser e documenti |
| PC 2012–2015 | UEFI | 4 GB | HDD | Avvio live, Wi-Fi, audio, video e sospensione |
| PC 2016–2020 | UEFI/Secure Boot | 8 GB | SSD | Installazione completa e applicazioni creative |

## Prova live

1. Avvio da USB senza modificare il disco interno.
2. Lingua, tastiera, fuso orario e risoluzione corretti.
3. Connessione Wi-Fi e cablata dall'interfaccia grafica.
4. Riproduzione e registrazione audio.
5. Apertura di una web app StradiLab in finestra dedicata.
6. Login Google istituzionale condiviso fra due web app.
7. Apertura e salvataggio di DOCX, XLSX, PPTX e PDF.
8. Riconoscimento di una seconda chiavetta USB.
9. Stampa o almeno rilevamento di una stampante di rete.

## Prova d'installazione

Usare inizialmente un disco di prova senza dati importanti.

1. Avvio di Calamares da «Installa StradilabOS».
2. Installazione automatica su tutto il disco.
3. Riavvio senza chiavetta.
4. Creazione e accesso dell'utente scelto.
5. Aggiornamenti da Synaptic.
6. Riavvio e spegnimento grafici.
7. Verifica che il launcher dell'installatore non resti visibile.

## Criteri di stop

Non distribuire la beta se si verifica uno di questi casi:

- l'installatore propone il disco sbagliato senza avviso chiaro;
- Wi-Fi o tastiera non funzionano su più di un modello della matrice;
- il login Google si perde passando fra web app;
- il sistema usa stabilmente più di 1,2 GB di RAM a riposo sul profilo da 2 GB;
- una web app riservata contiene credenziali o token già presenti nell'immagine;
- la ISO pubblicata non coincide con il checksum.
