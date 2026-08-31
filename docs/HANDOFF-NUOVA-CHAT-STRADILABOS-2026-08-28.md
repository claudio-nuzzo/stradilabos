# Handoff per nuova chat — StradilabOS

**Data:** 28 agosto 2026
**Repository:** `/Users/claudionuzzo/Dev/stradilabos`
**Obiettivo:** completare e verificare la correzione dell'avvio di `xfwm4`, poi costruire una sola nuova release di prova.

## 1. Punto essenziale

La nuova ISO ARM64 del commit `87fe78e` si avvia in Parallels, ma riproduce il difetto già visto: tutte le finestre sono prive della barra del titolo e dei pulsanti riduci, massimizza e chiudi.

La prova decisiva è stata eseguita nella sessione Live ARM64:

1. il passaggio del tema finestre da StradiLab a Greybird **non ha risolto**;
2. l'esecuzione di `xfwm4 --replace --compositor=off` ha ripristinato immediatamente barra del titolo e pulsanti.

Sul Mac la finestra Esegui è stata aperta con `⌥ Option + fn + F2`.

La causa non è quindi il tema. `xfwm4` parte o risulta presente, ma resta in uno stato incompleto. La guardia introdotta nel commit `87fe78e` controlla processo ed EWMH e produce un falso positivo: vede `xfwm4`, quindi non esegue la sostituzione che in Parallels è risultata necessaria.

## 2. Stato Git da non perdere

HEAD pubblicato:

`87fe78e Ripristina e verifica i controlli delle finestre`

Il branch `main` era allineato a `origin/main` prima delle modifiche locali successive.

Sono presenti **quattro file modificati e non committati**:

- `config/includes.chroot/usr/local/bin/stradilabos-window-manager-guard`
- `scripts/test_window_manager_xvfb.sh`
- `scripts/validate_project.py`
- `tests/test_project.py`

Queste modifiche sono una bozza iniziata dopo la prova manuale riuscita:

- la guardia esegue una volta `xfwm4 --replace --compositor=off` dopo il tempo iniziale;
- il test Xvfb prova a verificare che il PID di `xfwm4` venga davvero sostituito;
- test statici e validatore richiedono la nuova inizializzazione preventiva.

**Non scartare queste modifiche. Non sono ancora state testate, committate o pubblicate.**

Stato atteso all'apertura della nuova chat:

```text
## main...origin/main
 M config/includes.chroot/usr/local/bin/stradilabos-window-manager-guard
 M scripts/test_window_manager_xvfb.sh
 M scripts/validate_project.py
 M tests/test_project.py
```

## 3. Criticità da correggere nella bozza prima dei test

### Ritardo iniziale

La guardia conserva attualmente `startup_grace=8` e poi attende altri 5 secondi dopo la sostituzione. La schermata Benvenuto parte dopo circa 4 secondi: l'utente potrebbe quindi vedere ancora finestre senza controlli per circa 13 secondi.

Valutare un tempo iniziale breve, per esempio 1–2 secondi, perché l'autostart Xfce viene eseguito quando la sessione grafica è già disponibile. La sostituzione deve avvenire prima dell'apertura della schermata Benvenuto.

### Test Xvfb e registro preesistente

Prima di avviare la guardia nel test, eliminare il solo file temporaneo di log della prova oppure usare una `XDG_STATE_HOME` temporanea. In caso contrario un messaggio `inizializzazione preventiva ... completata` lasciato da un'esecuzione precedente potrebbe produrre un falso positivo.

Preferire una directory creata con `mktemp -d`, esportata come `XDG_STATE_HOME`, e rimossa dal trap finale.

### Sostituzione una sola volta

Verificare che il comando preventivo sia eseguito una sola volta per sessione e che il ciclo successivo resti soltanto di monitoraggio. Evitare loop di `--replace`, duplicazione di processi o notifiche ripetute.

### Effetti grafici

Il compositore disattivato è un compromesso accettabile: StradilabOS è destinato anche a vecchi PC e la stabilità dei controlli delle finestre viene prima di ombre e trasparenze.

## 4. Test obbligatori prima del commit

Eseguire almeno:

```sh
python3 -m unittest discover -v
python3 scripts/validate_project.py
python3 -m py_compile \
  config/includes.chroot/usr/local/lib/stradilabos/app_center.py \
  config/includes.chroot/usr/local/lib/stradilabos/hub.py \
  scripts/validate_project.py \
  tests/test_project.py
sh -n \
  config/includes.chroot/usr/local/bin/stradilabos-window-manager-guard \
  scripts/test_window_manager_xvfb.sh \
  scripts/validate_built_image.sh
git diff --check
```

Il test Xvfb completo richiede Linux. Se Docker locale non è disponibile, sarà eseguito per primo nei workflow GitHub e dovrà bloccare la costruzione ISO in caso di errore.

## 5. Commit e build successivi

Solo dopo i test locali:

1. riesaminare il diff completo;
2. creare un commit dedicato, ad esempio `Inizializza correttamente xfwm4 in Parallels`;
3. fare push su `main`;
4. la build AMD64 parte automaticamente;
5. la build ARM64 deve essere avviata manualmente con il workflow `build-arm64.yml`;
6. attendere almeno il successo del test `Prova il gestore delle finestre in un X virtuale` su entrambe;
7. attendere il successo completo delle due build;
8. scaricare per prima la nuova ARM64 in una cartella legata al nuovo hash del commit;
9. verificare checksum, tipo ISO, EFI, `filesystem.squashfs`, branding e menu GRUB;
10. provare la nuova ARM64 in modalità Live, senza reinstallare subito.

Non aggiornare Drive, pagina pubblica o download finché la nuova Live ARM64 non mostra i pulsanti automaticamente al primo avvio.

## 6. Build e artifact già esistenti

Commit `87fe78e` — build tecnicamente riuscite ma **funzionalmente non valide** in Parallels:

- AMD64 run `33160796392`
- ARM64 run `33160812328`
- artifact AMD64 `9681935327`
- artifact ARM64 `9681889760`

La ISO ARM64 scaricata e provata si trova qui:

`/Users/claudionuzzo/Dev/StradilabOS-release-0.2-87fe78e/ARM64/stradilabos-live-arm64.hybrid.iso`

SHA-256:

`26ef5067d4a665344ca1b3396e78ae8b87b3cd93429c0b7836a8bf5212f62280`

Questa ISO va conservata come prova del difetto, non pubblicata.

## 7. Cartella unica di controllo

Materiali, screenshot, istruzioni e collegamenti sono raccolti in:

`/Users/claudionuzzo/Dev/StradilabOS-CONTROLLO-0.2-2026-08-28/`

Il repository sorgente resta:

`/Users/claudionuzzo/Dev/stradilabos`

Le precedenti release non devono essere sovrascritte o cancellate finché il collaudo non è concluso.

## 8. Cosa aveva già superato il commit 87fe78e

- 13 test automatici locali;
- validatore del progetto;
- sintassi Python, shell e YAML;
- test Xvfb del tema e del recupero dopo la scomparsa del processo;
- build e validazione interna di entrambe le ISO;
- checksum, EFI e struttura Live dell'ARM64 scaricata.

Questi controlli non erano però sufficienti perché non riproducevano il caso reale: `xfwm4` presente ma inizializzato male. Il nuovo test deve verificare esplicitamente la sostituzione preventiva del processo già esistente.

## 9. Criterio di successo

La correzione è valida soltanto se, al primo avvio Live ARM64 in Parallels e senza alcun comando manuale:

- Thunar mostra titolo e tre pulsanti;
- Benvenuto mostra titolo e pulsante di chiusura;
- le micro-app Chromium mostrano controlli utilizzabili;
- riduci, massimizza, chiudi e `Alt/Option + F4` funzionano;
- il comportamento resta corretto dopo installazione e riavvio senza ISO.

Fino a quel momento StradilabOS resta **in sviluppo** e la release pubblica non cambia.
