# Handoff di collaudo — StradilabOS 0.2

**Stato al:** 28 agosto 2026, ore 11:10 CEST

**Scopo:** controllo indipendente prima di qualsiasi nuova modifica o build

**Decisione:** non pubblicare ancora le nuove ISO su Drive e non sostituire i download della pagina StradilabOS.

## 1. Versione esaminata

- Repository: `/Users/claudionuzzo/Dev/stradilabos`
- Branch: `main`, pulito e allineato a `origin/main`
- Commit della release: `862fa1c` — `Alleggerisce e rifinisce StradilabOS 0.2`
- Commit successivo, solo workflow: `6faaab4` — `Aggiorna il runtime delle GitHub Actions [skip ci]`
- Base: Debian 13 Trixie, Xfce, ARM64 e AMD64
- Stato dichiarato del prodotto: **in sviluppo**

### ISO ARM64 provata in Parallels

Percorso:

`/Users/claudionuzzo/Dev/StradilabOS-release-0.2-next/ARM64/stradilabos-live-arm64.hybrid.iso`

SHA-256:

`096e2b1a0f349fdcbb57d8bfe148c8deeff7210cf6533c561a8bc7b280a72344`

### ISO AMD64 costruita ma non provata in questa sessione

Percorso:

`/Users/claudionuzzo/Dev/StradilabOS-release-0.2-next/AMD64/stradilabos-live-amd64.hybrid.iso`

SHA-256:

`acf00af4908aeddec53ddf706cebaa40b98cd36383f3687db937e022166813ca`

### Build GitHub Actions

- ARM64: run `33151220444` — riuscita
- AMD64: run `33151216433` — riuscita

## 2. Ambiente della prova

- MacBook Pro Apple Silicon
- Parallels Desktop 20.4.2 Standard
- Mac host: macOS 20 secondo le informazioni comunicate durante la prova
- VM: ARM64, disco virtuale da 64 GB
- Profilo scelto nell'installazione: **Installazione base · PC personale**
- Layout consigliato nell'installer: `Italian` → `Italian (Macintosh)`; modello virtuale lasciato su `Generic 105-key PC`

## 3. Esito sintetico

La nuova ISO ARM64 si avvia e mostra correttamente il branding StradilabOS, il nuovo sfondo, il pannello, le icone, la procedura di benvenuto e l'installer personalizzato. Il sistema grafico parte in Parallels, quindi il precedente blocco su TTY non si è ripresentato.

Il collaudo ha però rilevato un difetto **bloccante per l'uso quotidiano**: tutte le finestre osservate sono prive della barra del titolo e dei controlli **minimizza, massimizza e chiudi**. Il problema riguarda sia applicazioni native sia micro-app web.

La release non è quindi pronta per sostituire quella pubblica.

## 4. Difetto bloccante: decorazioni delle finestre assenti

### Evidenza osservata

Le seguenti finestre sono apparse senza barra del titolo e senza pulsanti:

1. Thunar / gestore file;
2. micro-app del sito dell'Istituto aperta con Chromium;
3. schermata `Benvenuto in StradilabOS`;
4. altre applicazioni visibili come attività aperte nel pannello superiore.

Screenshot forniti durante il collaudo:

- `/var/folders/f5/gkbsbpj53wnc4hkrf895df500000gn/T/TemporaryItems/NSIRD_screencaptureui_Q2Art3/Screenshot 2026-08-28 alle 11.04.46.jpg`
- `/var/folders/f5/gkbsbpj53wnc4hkrf895df500000gn/T/TemporaryItems/NSIRD_screencaptureui_ZQiJm1/Screenshot 2026-08-28 alle 11.06.59.jpg`

### Impatto

- L'utente non può capire come chiudere un'applicazione.
- Mancano minimizzazione e massimizzazione.
- Il problema contraddice l'obiettivo del progetto: uso semplice, senza riga di comando.
- L'accumulo di finestre aperte rende rapidamente il desktop confuso.

### Controllo rapido eseguito

È stato inviato `Alt+F4` alla VM tramite l'interfaccia di Parallels, senza un cambiamento visibile. Questo dato va riconfermato direttamente dalla tastiera fisica, perché Parallels potrebbe intercettare o rimappare la combinazione.

### Diagnosi più probabile, da confermare

L'assenza delle decorazioni in applicazioni diverse suggerisce che `xfwm4`, il gestore delle finestre di Xfce:

- non venga avviato dalla sessione;
- si chiuda subito dopo l'avvio;
- oppure termini quando viene applicato il tema personalizzato `StradiLab`.

Non sembra un semplice problema di `button_layout`: in quel caso resterebbero comunque visibili titolo e bordo della finestra.

## 5. Configurazione sorgente già presente

Il repository contiene già impostazioni formalmente corrette:

- tema `StradiLab` per `xfwm4`;
- `button_layout = O|HMC`;
- `borderless_maximize = false`;
- `titleless_maximize = false`;
- test statici che controllano questi valori.

File principali da esaminare:

- `config/includes.chroot/etc/xdg/xfce4/xfconf/xfce-perchannel-xml/xfwm4.xml`
- `config/includes.chroot/etc/skel/.config/xfce4/xfconf/xfce-perchannel-xml/xfwm4.xml`
- `config/includes.chroot/usr/local/bin/stradilabos-apply-theme`
- `config/hooks/live/012-stradilabos-window-theme.hook.chroot`
- `config/includes.chroot/etc/xdg/autostart/stradilabos-theme.desktop`
- `config/includes.chroot/etc/skel/.config/autostart/stradilabos-theme.desktop`
- `tests/test_project.py`
- `scripts/validate_project.py`
- `scripts/validate_built_image.sh`

I controlli attuali provano che i file esistono dentro l'immagine, ma non provano che `xfwm4` resti effettivamente in esecuzione durante una sessione grafica.

## 6. Controlli diagnostici consigliati

Eseguirli sia nella sessione Live sia dopo installazione e riavvio.

### Processo e sessione

```sh
pgrep -a xfwm4
pgrep -a xfce4-session
xfce4-session --version
xfwm4 --version
echo "$XDG_CURRENT_DESKTOP"
echo "$DESKTOP_SESSION"
```

### Configurazione letta davvero a runtime

```sh
xfconf-query -c xfwm4 -p /general/theme
xfconf-query -c xfwm4 -p /general/button_layout
xfconf-query -c xfwm4 -p /general/borderless_maximize
xfconf-query -c xfwm4 -p /general/titleless_maximize
```

### Log della sessione

```sh
journalctl --user -b --no-pager | grep -Ei 'xfwm|xfce|window|theme|xpm'
journalctl -b --no-pager | grep -Ei 'xfwm|xfce|window|theme|xpm'
```

### Prova controllata

```sh
xfwm4 --replace
```

Se le barre compaiono subito, il problema è l'avvio o il mantenimento del processo. Se `xfwm4` termina mostrando un errore relativo al tema, il problema è nel tema `StradiLab` generato da Greybird.

### Prova del tema di riserva

```sh
xfwm4 --replace --daemon
xfconf-query -c xfwm4 -p /general/theme -s Greybird
```

Se Greybird funziona e StradiLab no, isolare la trasformazione degli XPM nel hook `012-stradilabos-window-theme.hook.chroot`.

## 7. Modifiche suggerite, da applicare solo dopo la diagnosi

### A. Rendere esplicito l'avvio di `xfwm4`

Verificare la configurazione della sessione Xfce e assicurarsi che il window manager sia un componente obbligatorio. Se necessario, aggiungere una voce di autostart dedicata che controlli il processo e avvii `xfwm4 --replace` soltanto quando manca.

La protezione deve:

- evitare doppi processi;
- registrare un messaggio diagnostico nel journal;
- funzionare sia in Live sia nel sistema installato;
- non creare loop continui se `xfwm4` va in crash.

### B. Aggiungere un fallback automatico al tema Greybird

La sequenza consigliata è:

1. provare il tema `StradiLab`;
2. verificare che `xfwm4` sia ancora vivo;
3. se fallisce, impostare `Greybird` e riavviare una sola volta il window manager;
4. mostrare un avviso non tecnico nel Centro App o nel registro diagnostico.

### C. Evitare modifiche fragili agli XPM

Il hook attuale modifica con `sed` tutti i file XPM di `xfwm4`. Va verificato che la sostituzione non produca risorse non valide. Preferire, se possibile:

- una copia integra e versionata del tema;
- oppure una modifica limitata ai soli file e campi conosciuti;
- oppure Greybird invariato per le decorazioni e personalizzazione StradiLab soltanto per GTK/pannello/sfondo.

La riconoscibilità del brand non deve compromettere i controlli fondamentali delle finestre.

### D. Aggiungere una seconda via grafica per chiudere

Come ridondanza, verificare che il menu contestuale delle attività nel pannello offra `Chiudi`. È utile, ma non sostituisce i pulsanti della finestra.

### E. Estendere i test dalla configurazione al comportamento

Il controllo deve includere almeno un avvio grafico reale in VM o con X virtuale, aprendo:

- Thunar;
- Centro App;
- Benvenuto;
- una micro-app Chromium;
- una finestra massimizzata e una non massimizzata.

Per ciascuna finestra verificare:

- titolo visibile;
- pulsanti minimizza, massimizza e chiudi;
- chiusura col pulsante;
- `Alt+F4`;
- minimizzazione e ripristino dal pannello;
- comportamento dopo logout/login e dopo riavvio.

## 8. Matrice minima prima della prossima build

| Controllo | Live ARM64 | Installata ARM64 | Live AMD64 | Installata AMD64 |
|---|---:|---:|---:|---:|
| Desktop grafico avviato | OK | da verificare | da verificare | da verificare |
| Branding e sfondo | OK | da verificare | da verificare | da verificare |
| Barra titolo e controlli finestre | **KO** | da verificare | da verificare | da verificare |
| Chiusura tramite pulsante | **KO** | da verificare | da verificare | da verificare |
| Alt+F4 | dubbio/KO | da verificare | da verificare | da verificare |
| Thunar | si apre | da verificare | da verificare | da verificare |
| Micro-app sito scuola | si apre | da verificare | da verificare | da verificare |
| Accesso Workspace vincolato al dominio | da completare | da verificare | da verificare | da verificare |
| App Center e annullamento installazione | da completare | da verificare | da verificare | da verificare |
| Riavvio senza ISO collegata | non applicabile | da verificare | non applicabile | da verificare |

## 9. Elementi riusciti osservati

- Avvio grafico ARM64 in Parallels riuscito.
- Identità `StradilabOS` visibile nella finestra della VM.
- Nuovo sfondo coerente con la palette e con gli indirizzi della scuola.
- Icone e pannello personalizzati.
- Installer con passaggi dedicati: profilo d'uso, uso del PC e Google Workspace.
- Profilo `Installazione base · PC personale` visibile nella schermata di benvenuto.
- Thunar e micro-app del sito della scuola si avviano.
- Pagina del sito istituzionale caricata correttamente nella micro-app.

## 10. Regola di rilascio proposta

Non ricostruire e non pubblicare una nuova release finché non sono soddisfatte tutte queste condizioni:

1. causa del mancato avvio di `xfwm4` identificata con log o prova ripetibile;
2. correzione verificata in Live ARM64;
3. correzione verificata dopo installazione e riavvio ARM64;
4. prova equivalente almeno in Live AMD64;
5. test statici aggiornati e test runtime aggiunto;
6. nessuna regressione su LightDM, wallpaper, profili, Workspace e App Center;
7. solo dopo il collaudo: nuova build, ZIP, checksum, Drive, pagina StradilabOS e pulizia controllata delle copie precedenti.

## 11. Stato delle modifiche al momento dell'handoff

Per richiesta del proprietario, dopo l'identificazione del difetto non sono state applicate correzioni alla sorgente, alla VM o alle build. Questo documento è l'unica aggiunta al repository in questa fase.

## 12. Interventi applicati alla sorgente — 28 agosto 2026, pomeriggio

Modifiche presenti nella copia di lavoro, **non ancora committate né pushate**
(un push su `main` avvierebbe automaticamente le build GitHub Actions).

### 12.1 Verifica del tema StradiLab in X virtuale

Il tema `StradiLab` generato dall'hook 012 è stato ricostruito con gli stessi
comandi e caricato da un `xfwm4` reale sotto Xvfb: la barra del titolo e i
pulsanti compaiono regolarmente (cornice 1/1/24/1 px). Le sostituzioni `sed`
sugli XPM producono file validi e cambiano soltanto i valori `s active_color_*`,
che xfwm4 comunque sostituisce a runtime con i colori GTK. **Il tema non è la
causa del difetto**: la spiegazione più probabile resta `xfwm4` che non parte
o termina nella VM (compositore/GLX su GPU virtuale), da confermare con
`stradilabos-window-diagnostics`.

### 12.2 Guardia del gestore delle finestre (punti A e B del §7)

- `usr/local/bin/stradilabos-window-manager-guard`: avviata da
  `etc/xdg/autostart/stradilabos-window-manager.desktop` (solo Xfce). Dopo 8 s
  controlla che `xfwm4` sia vivo (processo + `_NET_SUPPORTING_WM_CHECK`); se
  manca per tre controlli consecutivi lo riavvia con, nell'ordine,
  `--vblank=off`, poi `--compositor=off`, poi tema Greybird di riserva. Massimo
  tre tentativi per sessione, log nel journal (`stradilabos-wm-guard`) e in
  `~/.local/state/stradilabos/window-manager.log`, avviso non tecnico con
  `notify-send` quando scatta la modalità di compatibilità.
- `usr/local/bin/stradilabos-window-diagnostics`: raccoglie in un file sulla
  Scrivania tutti i controlli del §6 (processi, xfconf, Xorg, journal, log
  della guardia). Da eseguire nella VM con `Alt+F2` → terminale.
- Pacchetti aggiunti: `x11-utils` (xprop) e `libnotify-bin` (notify-send).

### 12.3 Test dal file al comportamento (punto E del §7)

- `scripts/test_window_manager_xvfb.sh`: avvia Xvfb + xfwm4 con il tema
  StradiLab, verifica `_NET_FRAME_EXTENTS` > 0 su una finestra reale, uccide
  xfwm4 e verifica che la guardia lo riavvii entro 30 s. Eseguito con successo
  (xfwm4 4.18) e aggiunto ai due workflow GitHub prima della build.
- Test statici e `validate_built_image.sh` estesi a guardia, autostart,
  diagnostica e pacchetti.

### 12.4 Palette e grafica StradiLab

- Anello di fuoco da tastiera portato da blu `#7A9FD4` (2,5:1 sull'avorio, sotto
  il minimo 3:1) a bordeaux; nero caldo sui pulsanti già bordeaux.
- Hub: quattro colori di categoria fuori palette sostituiti dai nuovi **toni
  profondi** dei cinque accenti (≥ 5:1 sull'avorio) e applicati davvero ai
  badge delle schede (prima erano definiti ma inutilizzati); testi 11/12 px
  portati a 12/13 px; neutri allineati a grigio carta e testo secondario.
- Centro App: bordo al passaggio del mouse allineato al bordeaux delle altre
  due app.
- `gtk.css`: GTK non legge `/etc/xdg/gtk-3.0/gtk.css`; l'hook 012 ora incorpora
  le regole comuni nel tema StradiLab (valide anche per LightDM e utenti già
  esistenti) e skel/xdg sono identici, con controllo statico.
- `docs/BRAND-STRADILAB.md`: aggiunti bianco superficie, toni profondi, tabella
  dei contrasti e dimensioni minime; `validate_project.py` controlla ora anche
  `hub.py` e `app_center.py`.

### 12.5 Cosa resta da fare in VM (invariato il §10)

1. Avviare la Live ARM64 **attuale** e lanciare `stradilabos-window-diagnostics`
   per registrare la causa reale (prima della nuova build).
2. Solo dopo: commit, push, build, ripetere la matrice del §8 con la guardia
   attiva e verificare che nel journal non compaiano interventi ripetuti.
