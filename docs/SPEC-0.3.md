# StradilabOS 0.3 — Specifica completa di realizzazione

**Data:** 31 agosto 2026
**Committente:** Claudio Nuzzo (IIS «Antonio Stradivari», Cremona)
**Repository:** https://github.com/claudio-nuzzo/stradilabos (branch `main`, pubblico)
**Base di partenza:** release 0.2, commit `f8e36a6` (build collaudata AMD64 e ARM64)
**Destinatario:** AI implementatrice. Il lavoro sarà poi revisionato riga per riga da un secondo revisore: attenersi alla specifica, non aggiungere funzionalità non richieste.

---

## 0. Regole di ingaggio (leggere prima di scrivere codice)

1. **Lingua:** tutto ciò che l'utente vede è in italiano corretto e semplice. Commenti nel codice in italiano o inglese, purché coerenti col file che si modifica.
2. **Niente terminale per l'utente finale:** ogni funzione ordinaria deve avere un percorso grafico. Il terminale esiste solo per la manutenzione tecnica e non compare nei menu.
3. **Hardware di destinazione:** PC dal 2010 in poi, 2 GB di RAM come soglia minima, 4 GB consigliati. Ogni scelta grafica o di processo va pesata su questa base: niente demoni pesanti, niente effetti compositi costosi, niente Electron.
4. **Idempotenza:** ogni script di configurazione o aggiornamento deve poter essere eseguito più volte senza danni.
5. **Convenzioni del repo:** nomi `stradilabos-*` per binari, unit e file di configurazione; script utente in `config/includes.chroot/usr/local/bin/`; librerie Python in `config/includes.chroot/usr/local/lib/stradilabos/`; hook live-build numerati in `config/hooks/live/`; polkit con azioni `org.stradilab.stradilabos.*`.
6. **Niente segreti nella ISO:** nessuna password, cookie, token o account Google incorporato. Mai.
7. **Niente marchi altrui:** nessun logo Apple, nessuno sfondo o icona proprietaria macOS. Il riferimento estetico si realizza con temi liberi (licenza GPL) e sfondi originali.
8. **Consegna:** branch `feature/0.3`, un commit (o gruppo di commit) per ogni requisito, messaggi di commit chiari. Non fare push forzati su `main`. Non toccare `updates/version.txt` se non dove richiesto.
   **Il lavoro si ferma alla consegna del codice: NON fondere in `main`, NON avviare la build della ISO né i workflow di release su GitHub.** Prima della compilazione, tutto il codice viene revisionato dal revisore del committente (Claude); solo dopo la sua approvazione si procede a merge e build.
9. **Se qualcosa è ambiguo:** non inventare. Lasciare un commento `TODO(claudio):` nel punto esatto e proseguire col resto.
10. **Prima di consegnare:** eseguire i controlli della sezione 10.

---

## 1. Contesto del progetto

StradilabOS è una distribuzione scolastica derivata da **Debian 13 (Trixie) con Xfce**, costruita con **live-build**, pensata per recuperare vecchi PC della scuola. Avvio live da USB, installazione con Calamares. Durante l'installazione l'utente sceglie un profilo (Studente con indirizzo, Docente, Segreteria, Installazione base), se il PC è personale o condiviso, e se accedere a Google Workspace al primo avvio o in seguito.

Struttura del repository:

```
auto/                      script live-build (build, clean, config)
config/hooks/live/         hook di build numerati (branding, tema, icone, ecc.)
config/includes.chroot/    file copiati pari pari nel sistema
  usr/local/bin/           stradilabos-welcome, -hub, -app-center, -open-app, -update, ...
  usr/local/lib/stradilabos/  welcome.py, hub.py, app_center.py, install_pack.py
  usr/local/share/stradilabos/ packs.json (catalogo app per indirizzo)
  etc/calamares/modules/   stradilabos-device.conf, -profiles.conf, -workspace.conf
  etc/chromium/policies/managed/  policy gestite Chromium
  etc/systemd/system/      stradilabos-update.service / .timer (nuovi, già presenti)
  etc/xdg/, etc/lightdm/, usr/share/  tema, pannello, greeter, sfondi
config/package-lists/      stradilabos-core.list.chroot, stradilabos-creative.list.chroot
docs/                      architettura, catalogo indirizzi, collaudi, questa specifica
updates/                   canale aggiornamenti (vedi §5 — GIÀ FATTO, non rifare)
tests/                     test_project.py
```

Documenti da leggere prima di iniziare: `docs/ARCHITETTURA.md`, `docs/GOOGLE-WORKSPACE.md`, `docs/CATALOGO-INDIRIZZI.md`, `docs/COLLAUDO-POST-TEST-2026-08-28.md`, `updates/README.md`.

Identità visiva attuale: palette StradiLab (avorio/crema di fondo, bordeaux `#9b2335`, blu navy `#2c4a6e` / `#1B3A6B`), tema morbido coordinato su GRUB, Plymouth, LightDM, pannello e sessione. La 0.3 la fa evolvere verso l'estetica descritta al §6 senza perdere il marchio StradiLab.

---

## 2. Perimetro della 0.3

| # | Requisito | Sezione |
|---|---|---|
| A | Primo avvio: la rete/Wi-Fi è il primo passo della configurazione | §3 |
| B | Primo accesso: profilo Chromium personale creato e login Google guidato subito | §4 |
| C | Aggiornamenti automatici dal repo GitHub + sicurezza Debian | §5 |
| D | Grafica in stile macOS (riferimento: WhiteSur) mantenendo identità StradiLab | §6 |
| E | Guide semplici per le app scaricate per indirizzo | §7 |
| F | Rilievi del collaudo 0.2 non coperti sopra | §8 |
| G | Bump di versione 0.2 → 0.3 | §9 |

---

## 3. Requisito A — Rete e Wi-Fi come primo passo

**Problema osservato (collaudo 28/8):** un'installazione è fallita perché la rete non era attiva; attivato il Wi-Fi, è andata a buon fine. Inoltre il primo avvio del sistema installato propone subito l'accesso Workspace, che senza rete non può funzionare.

**Da realizzare, in due punti distinti:**

### 3.1 Nell'installatore (sessione live)

- Individuare quale operazione di Calamares richiede Internet e renderla esplicita: prima di avviare la copia su disco, una verifica di connettività. Se la rete manca, un messaggio chiaro in italiano che spiega come collegarsi (menu di rete del pannello) e se/quanto dell'installazione può procedere offline. Non deve mai partire un'installazione destinata a fallire a metà.
- Se Calamares non consente un modulo di verifica personalizzato semplice, in alternativa inserire la verifica nella schermata di benvenuto live che lancia l'installatore (è codice nostro: `welcome.py`).

### 3.2 Al primo avvio del sistema installato

- La sequenza di primo avvio (welcome) deve diventare: **1) rete → 2) accesso Google (se scelto in installazione) → 3) resto**.
- Passo rete: verifica automatica della connettività (es. `nmcli networking connectivity check` o equivalente); se assente, mostrare la scelta della rete con interfaccia grafica esistente di NetworkManager (aprire l'editor connessioni o il popup di nm-applet — non scrivere un gestore Wi-Fi da zero). Pulsante «Salta, configuro dopo» sempre presente, con avviso che senza rete l'accesso Google e le app non funzioneranno.
- Il passo si considera superato appena la connettività risulta attiva; la verifica va rifatta a ogni comparsa della schermata, non memorizzata per sempre.

**Criteri di accettazione:**
- Senza rete, l'installatore spiega cosa fare e non fallisce a metà.
- Al primo avvio senza rete, la prima cosa proposta è collegarsi, con possibilità di rimandare.
- Con rete già attiva (cavo), il passo rete non disturba: si passa avanti da soli.

---

## 4. Requisito B — Primo accesso: account e profilo Chromium già pronti

**Obiettivo dichiarato dal committente:** «il login iniziale deve già creare un account e aprire Chromium per creare il profilo personale già loggato».

**Interpretazione corretta (confermata):** l'account **locale** Linux viene già creato da Calamares; ciò che manca è che al **primo login** dell'utente il sistema apra da solo Chromium sul profilo dedicato StradiLab e conduca l'utente al login Google del dominio, così che **alla fine del primo avvio tutte le micro-app risultino già autenticate**. Non è possibile (né voluto) precaricare credenziali: l'utente digita la propria password Google una volta sola, tutto il resto è automatico.

**Da realizzare:**

1. **Autostart una tantum:** al primo login grafico dell'utente (flag tipo `~/.config/stradilabos/first-run-done` da creare a completamento), parte la sequenza di benvenuto già esistente, riordinata come da §3.2.
2. **Passo Google:** dopo il passo rete, se in installazione era stato scelto «Workspace al primo avvio», aprire Chromium **sul profilo dedicato StradiLab** (lo stesso identico profilo/directory usato da `stradilabos-open-app`, così la sessione vale per tutte le micro-app) su **Gmail** (`https://mail.google.com`) — non Classroom: è il rilievo n. 2 del collaudo. La policy `AllowedDomainsForApps=istitutostradivari.it` già presente limita gli account proposti.
3. **Sessione unica:** verificare e correggere il difetto rilevato al collaudo: dopo il login in Gmail, l'apertura di Classroom/Drive/Meet/Calendar **non deve** chiedere un nuovo login. Se oggi accade, la causa probabile è che le micro-app non usino tutte la stessa `--user-data-dir`/`--profile-directory`: uniformare il lancio in `stradilabos-open-app` e nel passo di benvenuto.
4. **PC condiviso / sessione live:** comportamento invariato rispetto alla 0.2 — profilo Chromium in directory temporanea di sessione, cancellato al logout. La sequenza guidata resta uguale, ma senza persistenza.
5. **Riapertura:** dalla schermata di benvenuto deve restare possibile rifare l'accesso Google in ogni momento (cambio utente Google, sessione scaduta).

**Criteri di accettazione:**
- PC personale: al primo login l'utente si collega alla rete, fa un solo login Google in Gmail, e da lì in poi Classroom, Drive, Meet e le altre micro-app si aprono già autenticate — anche dopo il riavvio.
- PC condiviso: stesso percorso, ma tutto scompare al logout.
- Nessuna credenziale nella ISO, nessun nuovo prompt di password Linux inatteso.

---

## 5. Requisito C — Aggiornamenti automatici da GitHub ⚠️ IN GRAN PARTE GIÀ FATTO

**Non riscrivere questa parte.** Nel repo esistono già, verificati:

- `config/includes.chroot/usr/local/bin/stradilabos-update` — client: scarica `version.txt` e `update.sh` da `https://raw.githubusercontent.com/claudio-nuzzo/stradilabos/main/updates/`, confronta la «serie» con `/var/lib/stradilabos/update-serial`, esegue il payload come root, logga in `/var/log/stradilabos-update.log`.
- `config/includes.chroot/etc/systemd/system/stradilabos-update.service` e `.timer` (3 min dopo il boot, poi ogni 7 giorni, `Persistent=true`), timer abilitato via symlink in `timers.target.wants/`.
- `updates/` — canale: `update.sh` (serie 1: policy cookie Chromium), `version.txt`, `install-updater.sh` (una tantum per i PC 0.2), copie dei file client, `README.md` con le regole di pubblicazione.
- `config/includes.chroot/etc/chromium/policies/managed/stradilabos-cookies.json` — sblocca i cookie di terze parti per i servizi Google (necessario per le pagine Stradilab con riquadri Google incorporati).

**Cosa resta da fare in questo requisito:**

1. **Aggiornamenti di sicurezza Debian:** installare e configurare `unattended-upgrades` limitato alla suite di sicurezza (`Trixie-Security`), senza riavvii automatici, senza prompt, con pulizia periodica dei pacchetti scaricati. File di configurazione in `config/includes.chroot/etc/apt/apt.conf.d/`, pacchetto aggiunto a `stradilabos-core.list.chroot`.
2. **Esito visibile (rilievo n. 4 del collaudo):** nella schermata di benvenuto o nel hub, una riga di stato non invasiva: versione StradilabOS, serie aggiornamenti applicata (lettura di `/var/lib/stradilabos/update-serial`), data ultimo controllo (dal log o da `systemctl show stradilabos-update.timer`). Solo lettura, niente pulsanti tecnici; al più un pulsante «Controlla ora» che lancia il client via polkit (nuova azione `org.stradilab.stradilabos.update`, sul modello di quella del Centro App).
3. **Sincronia dei gemelli:** se si modifica il client, aggiornare **entrambe** le copie (`config/includes.chroot/...` e `updates/...`) — regola già scritta in `updates/README.md`.

**Criteri di accettazione:**
- Con rete attiva, un PC installato applica da solo una nuova serie pubblicata (test: incrementare `version.txt` in un fork di prova e puntare temporaneamente il client lì — NON committare l'URL di prova).
- Le patch di sicurezza Debian si installano da sole senza bloccare la sessione né chiedere password.
- L'utente può vedere versione e stato aggiornamenti senza terminale.

---

## 6. Requisito D — Grafica in stile macOS (riferimento WhiteSur)

**Riferimento visivo fornito dal committente:** screenshot di Pop!_OS con tema **WhiteSur-dark**, icone **BigSur**, dock inferiore, pannello superiore sottile scuro, angoli arrotondati, semaforo rosso/giallo/verde sui pulsanti finestra.

**Obiettivo:** la sessione Xfce di StradilabOS deve avvicinarsi a quell'estetica, restando leggera e riconoscibilmente StradiLab.

**Da realizzare:**

1. **Tema GTK e finestre:** incorporare **WhiteSur-gtk-theme** (vinceliuice, GPL-3.0) nella ISO, in `config/includes.chroot/usr/share/themes/`, a versione fissata (release o commit specifico, annotato in un file `docs/TERZE-PARTI.md` con versione, origine e licenza). Non scaricare a runtime, non usare script d'installazione del tema upstream durante il boot: i file vanno vendorizzati al build (hook o commit diretto). Includere solo le varianti usate (chiara e scura standard), non tutte le decine di combinazioni: la ISO deve restare leggera.
2. **Icone:** incorporare **WhiteSur-icon-theme** (stessa fonte e stesse regole). Verificare che le icone `stradilabos-*` esistenti (hub, centro app, ecc.) restino visibili e coerenti.
3. **Dock:** aggiungere **Plank** (è in Debian) come dock inferiore con le app principali (Chromium, hub StradiLab, file, LibreOffice, Centro App, Guide §7), tema coordinato. In alternativa, se Plank desse problemi su Xfce/vecchi PC, un secondo pannello Xfce in basso con `dockbarx` o semplice barra icone — scegliere la soluzione più stabile e documentare il perché.
4. **Pannello superiore:** sottile, scuro (come nello screenshot) oppure avorio con icone scure — in ogni caso risolvendo il **rilievo n. 3 del collaudo**: oggi le icone di stato (volume, rete, notifiche) sono bianche su fondo quasi bianco e illeggibili. Colore icone simboliche e orologio con contrasto AA sul fondo scelto, verificato anche in hover e focus.
5. **Pulsanti finestra:** stile semaforo a sinistra (lo fornisce WhiteSur per xfwm4). Compositing xfwm4: solo ombre leggere, niente effetti costosi; la guardia xfwm4 esistente (`stradilabos-window-manager-guard`) non va rotta — leggere `docs/HANDOFF-CORREZIONE-XFWM4-2026-08-28.md` prima di toccare il WM.
6. **Sfondo:** creare uno sfondo originale in stile «onde/gradiente Big Sur» con la palette StradiLab (bordeaux→navy→crema), in più risoluzioni, SVG sorgente + PNG esportati in `usr/share/backgrounds/`. **Non** copiare gli sfondi Apple.
7. **Coerenza dell'intero percorso:** LightDM greeter, GRUB e Plymouth restano brandizzati StradiLab; vanno aggiornati solo se il nuovo tema li rende incoerenti (es. sfondo). Gli hook esistenti `010-branding`, `012-window-theme`, `015-icons` vanno estesi, non duplicati.
8. **Impostazioni predefinite:** i default vanno in `etc/xdg/xfce4/xfconf/` (perché valgano per ogni nuovo utente), non nello skel di un singolo utente, salvo dove il progetto già fa diversamente — seguire la struttura esistente in `config/includes.chroot/etc/xdg/xfce4/`.
9. **Prestazioni:** dopo il cambio tema, avvio sessione e uso della RAM non devono peggiorare sensibilmente su 2 GB (misurare prima/dopo in VM con `free -m` a sessione stabile e annotare i numeri nel commit o in `docs/`).

**Criteri di accettazione:**
- A colpo d'occhio la sessione somiglia allo screenshot di riferimento (dock, pannello sottile, semaforo, icone in stile Big Sur, angoli arrotondati).
- Tutte le icone di stato del pannello sono leggibili (rilievo n. 3 chiuso).
- Nessun asset Apple; terze parti censite in `docs/TERZE-PARTI.md` con licenza.
- La sessione resta fluida su una VM con 2 GB di RAM.

---

## 7. Requisito E — Guide semplici per le app degli indirizzi

**Idea del committente:** insieme alle app che il Centro App scarica per ciascun indirizzo, devono arrivare guide molto semplici per usarle.

**Da realizzare:**

1. **Contenuti:** una pagina HTML per ciascuna app del catalogo (`usr/local/share/stradilabos/packs.json` e `docs/CATALOGO-INDIRIZZI.md`): Krita, MyPaint, GIMP, Inkscape, Scribus, Pencil2D, Blender, QLC+, Sweet Home 3D, Kdenlive, MuseScore, Rosegarden, QSynth, PianoBooster, Audacity, Ardour, LMMS, Hydrogen, Sonic Visualiser, FMIT, FreeCAD, LibreCAD, SolveSpace, OpenSCAD, MeshLab, Seamly2D, FreeSewing, PosteRazor, QElectroTech (+ le app base: LibreOffice, file, stampa/scansione).
2. **Formato di ogni guida (rigido, max una schermata e mezza):** che cos'è (2 righe), a cosa serve a scuola in quell'indirizzo (2-3 righe), come si apre, «I primi 5 passi» concreti (aprire/creare, salvare dove, l'operazione tipica dell'indirizzo, esportare/stampare), 3 problemi comuni con soluzione, dove imparare di più (1 link ufficiale). Linguaggio da quattordicenne che non ha mai visto il programma; niente gergo; sempre «tu».
3. **Veste grafica:** HTML statico con un solo CSS condiviso in stile StradiLab/tema 0.3, leggibile anche offline; niente framework, niente font remoti (font di sistema), immagini solo se essenziali e locali.
4. **Struttura file:** `config/includes.chroot/usr/local/share/stradilabos/guide/` con `index.html` (elenco per indirizzo), `css/guida.css`, e una cartella o file per app (`krita.html`, `blender.html`, ...). Le guide di tutti gli indirizzi sono incluse nella ISO (è solo testo: pesa pochissimo).
5. **Accesso:** voce «Guide» nel hub StradiLab e nel dock; apertura con Chromium `--app=file:///usr/local/share/stradilabos/guide/index.html`. Nel Centro App, a installazione completata di un pacchetto, il messaggio di esito include «Apri la guida» che porta all'indice filtrato sull'indirizzo installato (parametro `#indirizzo` gestito con poche righe di JS locale).
6. **Aggiornabilità:** essendo file sotto `/usr/local/share/`, le guide si potranno correggere in futuro anche via canale aggiornamenti (serie in `update.sh`) senza ricostruire la ISO. Non implementare ora: basta non rendere i percorsi «speciali».

**Criteri di accettazione:**
- Ogni app del catalogo ha la sua guida nel formato fisso; l'indice raggruppa per indirizzo.
- Da hub e dock si aprono le guide anche senza rete.
- Dopo l'installazione di un pacchetto dal Centro App, si arriva alla guida giusta in un clic.

---

## 8. Requisito F — Rilievi di collaudo residui

- **Rilievo n. 5 (messaggi ACPI/APIC al boot):** non è compito dell'AI implementatrice risolverlo (serve il portatile fisico). Unica azione: NON aggiungere `quiet`/`splash` aggressivi che nasconderebbero quei messaggi prima che siano stati capiti. Lasciare la verbosità attuale del boot.
- I rilievi n. 1, 2, 3, 4 sono coperti da §3, §4, §6.4, §5.

---

## 9. Requisito G — Versione 0.3

Aggiornare coerentemente:

- `config/includes.chroot/usr/lib/os-release`: `PRETTY_NAME="StradilabOS 0.3 (in sviluppo)"`, `VERSION_ID="0.3"`, `VERSION="0.3 (Debian 13 Trixie)"`.
- `config/includes.chroot/etc/lsb-release`: `DISTRIB_RELEASE=0.3`, `DISTRIB_DESCRIPTION="StradilabOS 0.3 (in sviluppo)"`.
- `README.md` del repo: riferimenti alla versione e le novità 0.3 in due righe.
- Eventuali altri punti trovati con `grep -rn "0\.2" config/ README.md` che siano identità di versione (non toccare numeri che c'entrano con altro).
- NON toccare `release.json` del sito: si aggiorna a build pubblicata, fuori da questo lavoro.

---

## 10. Controlli obbligatori prima della consegna

1. `bash -n` su ogni script shell nuovo o modificato; `python3 -m py_compile` sui `.py` toccati.
2. `python3 -m pytest tests/` (o `python3 tests/test_project.py` se pytest manca) deve passare; se il progetto ha validatori (`scripts/validate_project.py`, `scripts/validate_debian_packages.sh`), eseguirli.
3. Ogni JSON nuovo o modificato validato (`python3 -m json.tool`).
4. ShellCheck pulito sugli script nuovi (il CI lo pretende).
5. Nomi pacchetto aggiunti alle package-list verificati esistenti in Debian Trixie.
6. **Non avviare la build della ISO né i workflow GitHub:** la compilazione avviene solo dopo la revisione e l'approvazione del revisore del committente (vedi regola 8 del §0).
7. Elenco finale dei file creati/modificati/eliminati, requisito per requisito, con due righe di spiegazione ciascuno: è il materiale su cui lavorerà il revisore.

---

## 11. Fuori perimetro (non fare)

- Niente telemetria o inventario dei PC (ipotesi rimandata: prima va discussa col DPO della scuola).
- Niente gestione centralizzata Chrome Enterprise, niente provider di identità Google per il login Linux.
- Niente riscrittura del canale aggiornamenti (§5), della guardia xfwm4, del meccanismo dei pacchetti del Centro App.
- Niente modifiche a Plymouth/GRUB oltre l'eventuale coerenza di sfondo del §6.7.
- Niente nuovi linguaggi/framework: shell POSIX/bash, Python 3 standard library, GTK già in uso.

---

## 12. Collaudo finale (lo eseguirà il committente su VM e hardware)

1. Installazione senza rete → messaggio chiaro, nessun fallimento a metà (§3.1).
2. Primo avvio PC personale: rete → login Gmail unico → Classroom/Drive/Meet già autenticate, anche dopo riavvio (§4).
3. Primo avvio PC condiviso: stesso percorso, nulla persiste al logout (§4.4).
4. Aspetto conforme allo screenshot di riferimento; icone di pannello leggibili; sessione fluida con 2 GB (§6).
5. Guide raggiungibili da hub, dock e Centro App, corrette e nel formato fisso (§7).
6. Serie di aggiornamento di prova applicata da sola entro pochi minuti dal boot; stato visibile nel benvenuto/hub (§5).
7. `unattended-upgrades` attivo solo sulla sicurezza, nessun prompt (§5.1).
8. `os-release` e `lsb-release` dicono 0.3 (§9).
