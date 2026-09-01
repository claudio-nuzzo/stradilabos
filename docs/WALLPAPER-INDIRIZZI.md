# Sfondi StradiLabOS per indirizzo

La raccolta destinata a StradiLabOS 0.4 comprende cinque sfondi originali in
formato JPEG 16:9. I file vengono installati in
`/usr/share/backgrounds/stradilabos/` e compaiono nel selettore di Xfce con il
nome completo **StradiLabOS**: nessuna variante usa il nome errato “Stradi OS”.

| Indirizzo | File | Linguaggio grafico |
| --- | --- | --- |
| Liceo Artistico | `StradiLabOS-Liceo-Artistico.jpg` | pigmenti, segni pittorici, geometrie e materia scultorea |
| Liceo Musicale | `StradiLabOS-Liceo-Musicale.jpg` | onde acustiche, corde, risonanze e ritmo |
| Liuteria | `StradiLabOS-Liuteria.jpg` | abete, acero marezzato, curve armoniche e trucioli |
| Moda | `StradiLabOS-Moda.jpg` | tessuti, cartamodello, cuciture e costruzione sartoriale |
| Arredo e Architettura | `StradiLabOS-Arredo-e-Architettura.jpg` | archi, volumi, prospettiva e linee di progetto |

## Brief grafico conservato

Gli sfondi sono stati generati separatamente con OpenAI image generation a
partire da un brief comune: illustrazione editoriale contemporanea, rapporto
16:9, composizione principale dal centro verso destra e almeno il 38% sinistro
libero e scuro per icone e scritte. La palette è quella StradiLab: navy
`#1B3A6B`, bordeaux `#9B2335`, crema `#F6F4EF`, cobalto `#3368B5` e oro tenue
`#D4A85A`.

Ogni prompt vieta testo, lettere, loghi, firme, filigrane, interfacce, elementi
Apple e personaggi protetti. Il soggetto cambia per indirizzo secondo la
tabella, così la serie rimane riconoscibile ma non ripetitiva.

## Preparazione per installazione e OTA

Le immagini installabili misurano 1672×941 pixel e sono esportate in JPEG a
qualità 88. Il totale è circa 2 MB: una dimensione sufficiente per i display dei
PC destinatari e molto più leggera dei PNG sorgente. L’OTA controlla l’hash
SHA-256 di ogni file prima dell’installazione e non riscarica l’intero
repository sui PC già aggiornati alla serie precedente.
