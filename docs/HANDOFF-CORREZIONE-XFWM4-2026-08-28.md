# Handoff — Correzione xfwm4 (finestre senza barra del titolo)

**Data:** 28 agosto 2026
**Repository:** `/Users/claudionuzzo/Dev/stradilabos`
**Cartella di controllo:** `/Users/claudionuzzo/Dev/StradilabOS-CONTROLLO-0.2-2026-08-28`

## 1. Obiettivo

Concludere la correzione delle finestre che in Parallels (Live ARM64, commit
`87fe78e`) compaiono senza barra del titolo e senza pulsanti Riduci/Massimizza/
Chiudi, anche se `xfwm4` risulta presente e si annuncia via EWMH.

La prova manuale decisiva è già avvenuta: `xfwm4 --replace --compositor=off`
ripristina immediatamente titolo e pulsanti. Il tema (Greybird) non è la causa.
La guardia del commit precedente produceva un falso positivo perché controllava
solo processo ed EWMH, non l'inizializzazione utile della sessione.

## 2. Modifiche effettuate

### 2.1 Guardia `config/includes.chroot/usr/local/bin/stradilabos-window-manager-guard`
- `startup_grace` da `8` a `2` secondi: la sostituzione parte quando la sessione
  grafica è già disponibile e **prima** della schermata Benvenuto (che si apre a
  ~4 secondi). L'utente non vede più finestre senza controlli per ~13 secondi.
- Sostituzione preventiva **lineare, fuori dal ciclo**: viene eseguita
  esattamente una volta per avvio di sessione (quindi di nuovo dopo logout/login,
  senza alcun marker persistente che possa inceppare il ripristino).
- Log non ambiguo dell'esito:
  - `inizio inizializzazione preventiva di xfwm4 senza compositore`
  - `inizializzazione preventiva di xfwm4 completata`
  - oppure `inizializzazione preventiva non riuscita: attivo il recupero graduato`
- Dopo la preventiva il ciclo resta di solo monitoraggio e recupero graduato
  (3 livelli, Greybird solo come ultima risorsa, compositor sempre spento).
- Nuova funzione `disable_compositing()`: prima della sostituzione preventiva
  persiste `use_compositing=false` nelle preferenze di xfwm4 via
  `xfconf-query`, così il compositor resta spento anche se un profilo utente
  lo avesse riattivato in sessione.

### 2.2 Compositing disattivato in modo persistente
Il flag `--compositor=off` vale solo per l'istanza lanciata. Per evitare che
xfwm4 4.20 riattivi il compositing a un riavvio senza flag, è stato fissato
`use_compositing=false` nei due file di configurazione:
- `config/includes.chroot/etc/skel/.config/xfce4/xfconf/xfce-perchannel-xml/xfwm4.xml`
- `config/includes.chroot/etc/xdg/xfce4/xfconf/xfce-perchannel-xml/xfwm4.xml`

Il validatore ne verifica la presenza:
`scripts/validate_project.py` → controllo `use_compositing type="bool" value="false"`.

### 2.3 Test Xvfb riscritto `scripts/test_window_manager_xvfb.sh`
Ora riproduce il caso reale (xfwm4 presente ma da sostituire) e verifica:
1. `XDG_STATE_HOME` su directory `mktemp -d`, rimossa nel `trap` (niente falsi
   positivi da log precedenti);
2. PID di xfwm4 prima della sostituzione preventiva;
3. PID dopo la preventiva e verifica che **cambi davvero**;
4. un solo processo xfwm4 dopo l'assestamento (`pgrep -x xfwm4 | wc -l`);
5. `_NET_SUPPORTING_WM_CHECK`, `_NET_WM_NAME` e `_NET_FRAME_EXTENTS` con lato
   superiore > 0;
6. guardia attiva per almeno due intervalli e PID stabile → nessuna seconda
   sostituzione;
7. esattamente una riga `inizializzazione preventiva di xfwm4 completata` nel log;
8. `pkill -x xfwm4` e verifica separata del recupero durante la sessione;
9. cornice e singolo processo verificati di nuovo dopo il recupero;
10. conteggi espliciti con `wc -l`, mai `pgrep | head` come unica prova.

### 2.4 Validatore e unit test
- `scripts/validate_project.py`: verifica `use_compositing=false` nella config
  xfwm4 (oltre ai controlli preesistenti).
- `tests/test_project.py`: verifica `use_compositing=false` nei due `xfwm4.xml`
  e `startup_grace=${STRADILABOS_WM_GRACE:-2}` nella guardia.

### 2.5 Workflow CI
In entrambi `build-iso.yml` (AMD64) e `build-arm64.yml` (ARM64) il test del
gestore delle finestre è stato spostato **dentro il container `debian:trixie-slim`**
(lo stesso della build), installando lì `xfwm4 xvfb xfconf dbus-x11 x11-utils
x11-apps greybird-gtk-theme`. Così il test usa xfwm4 4.20 di Debian Trixie,
coerente con la ISO, e non il 4.18 dell'host Ubuntu del runner.

Il test gira **prima** della build e la blocca in caso di errore.

### 2.6 Workflow di validazione dedicato `validate-wm-trixie.yml`
Nuovo workflow `workflow_dispatch` e `pull_request` verso `main`, **senza
costruzione della ISO**, con tre
job che rendono verdi le voci del gate impossibili da eseguire sul Mac:
- `validate-amd64`: container `debian:trixie-slim` → `sh -n`, `shellcheck`,
  `validate_debian_packages.sh` (amd64) e `test_window_manager_xvfb.sh`;
- `validate-arm64` (runner ARM): container Trixie →
  `validate_debian_packages.sh` (arm64) e `test_window_manager_xvfb.sh`;
- `preflight-xfce` (non bloccante): sessione Xfce reale sotto Xvfb+D-Bus tramite
  `scripts/preflight_xfce_session.sh`.

### 2.7 Preflight sessione Xfce `scripts/preflight_xfce_session.sh`
Avvia `xfce4-session` sotto Xvfb+D-Bus nel container, con `HOME`/`XDG_STATE_HOME`
temporanee e autostart StradilabOS copiati, una finestra reale, e verifica:
un solo `xfwm4`, PID stabile per due intervalli, `_NET_FRAME_EXTENTS` con lato
superiore >0. **Non bloccante e non garanzia**: un container non ha GPU né
Parallels; il gate definitivo resta il test Xvfb unitario + la prova Live.

## 3. Gate pre-build — esiti locali

Tutte le voci eseguibili localmente sono **verdi**:

| Voce | Esito | Prova |
|---|---|---|
| `git diff --check` | OK | nessun errore di whitespace |
| `sh -n` guardia, test, diagnostica, validatore immagine | OK | sintassi valida su tutti |
| permessi eseguibili guardia/test/diagnostica/validatore | OK | `-rwxr-xr-x` su tutti |
| assenza segreti nel diff | OK | nessuna corrispondenza password/token/chiave |
| `python3 -m unittest discover -v` | OK | 13 test superati |
| `python3 scripts/validate_project.py` | OK | controlli superati |
| `py_compile` script + 3 app StradilabOS | OK | compilazione riuscita |
| JSON progetto | OK | 4 file validi |
| XML modificati (`xfwm4.xml`) | OK | ben formati |
| YAML workflow | OK | validati con Psych (Ruby) |
| idempotenza catalogo | OK | 33 app, ID unici, 33 `.desktop` |
| dipendenze `xprop`/`notify-send` nella lista base | OK | `x11-utils`, `libnotify-bin` presenti |

**Non eseguibili localmente (Docker assente sul Mac):**
- test Xvfb Debian Trixie;
- disponibilità pacchetti Debian Trixie (ARM64 e AMD64);
- ShellCheck.

Per questi controlli esiste il workflow dedicato `validate-wm-trixie.yml`
(dispatch, senza build), che li esegue in container Debian Trixie; gli stessi
test Xvfb Trixie e la disponibilità dei pacchetti sono **ripetuti in modo
bloccante** nei workflow di build, prima della costruzione della ISO. Doppia
sicurezza: una volta pre-main (validazione), una volta post-main (build).

**Strumenti dichiarati assenti:** ShellCheck (non installato localmente).

**Preflight sessione Xfce completa (Xvfb + D-Bus):** aggiunto come
`scripts/preflight_xfce_session.sh`, eseguito solo in CI e **non bloccante**
(`continue-on-error`) perché un container non riproduce GPU/Parallels. Il
preflight non è una garanzia: il gate runtime resta il test Xvfb unitario, la
conferma definitiva è la prova Live in Parallels.

### 3.1 Esito CI corretto e verificato

La prima esecuzione della PR aveva nascosto un errore intermedio
(`python3: not found`) perché i container usavano `sh -lc`: il job restava
verde quando l'ultimo comando riusciva. I commit `5e1fdf7` e `602b8d8` hanno:

- reso fail-fast tutti i container con `sh -euc`;
- installato e verificato esplicitamente `python3` nei job di validazione;
- eliminato il word splitting dal parser delle direttive architettura;
- esteso ShellCheck e i test di regressione;
- fatto avviare la guardia dal vero autostart Xfce nel preflight, senza lancio
  manuale che potesse mascherare un percorso XDG errato.

La CI definitiva sul commit `602b8d8` è il run `33166774041`: `validate-amd64`,
`validate-arm64` e `preflight-xfce` sono tutti riusciti. Nei log compaiono
esplicitamente la disponibilità dei pacchetti per entrambe le architetture, la
cornice superiore a zero e il superamento della prova del gestore finestre.

## 4. Stato finale atteso

La sostituzione preventiva (`xfwm4 --replace --compositor=off`) viene eseguita
una sola volta, ~2s dopo l'avvio della sessione Xfce, prima della schermata
Benvenuto. Dopo l'assestamento esiste un solo processo `xfwm4`, stabile, con
compositore spento e barra/pulsanti presenti. Il recupero graduato resta attivo
solo per una successiva scomparsa reale del window manager.

## 5. Stato dopo merge e build

- PR `#1` fusa in `main` al commit `f8e36a6`.
- Build AMD64 `33166946831`: riuscita.
- Build ARM64 `33166952375`: riuscita.
- Entrambe hanno eseguito per primo il test Debian Trixie e hanno superato il
  validatore interno dell'immagine.
- ISO e checksum scaricati in
  `/Users/claudionuzzo/Dev/StradilabOS-release-0.2-f8e36a6/`.
- Checksum verificati localmente:
  - ARM64 `38b7762bfb640da25a9a94a41aadfc82192478489dbb495bcafc35e73c98cf80`;
  - AMD64 `c8a02d16d7d3df7c09ea6ec5d2e8241b62ea5f0bf72f0aea1664d15447b285e8`.
- Verificati localmente: immagine bootable, EFI corretta per architettura,
  `filesystem.squashfs`, `.disk/info`, menu GRUB, eseguibili richiesti,
  configurazione xfwm4 e contenuto della guardia identico al commit.
- L'inventario pacchetti è invariato rispetto alla ISO ARM64 `87fe78e`: nessun
  pacchetto è stato aggiunto dalla correzione.

## 6. Prossimi passi

1. Prova **Live ARM64 in Parallels senza alcun comando manuale**: Thunar e
   Benvenuto con titolo e tre pulsanti, riduci/massimizza/chiudi e Alt+F4
   funzionanti, comportamento stabile per almeno 2 minuti, una sola
   inizializzazione preventiva nel log, un solo xfwm4.
2. Solo dopo il successo Live: installazione, rimozione ISO, riavvio e
   ripetizione degli stessi controlli nel sistema installato.

## 7. Cosa NON è stato toccato

Palette, applicazioni didattiche, pacchetti specialistici, sito, Drive, dashboard
e funzioni non collegate al window manager. Installer resta solo nella Live.
Nessuna ISO precedente cancellata, nessuna pagina pubblica aggiornata.
