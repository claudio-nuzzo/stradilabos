# Canale aggiornamenti StradilabOS

Questa cartella E' il canale di aggiornamento: viene letta direttamente da
GitHub (repo pubblico) all'indirizzo

  https://raw.githubusercontent.com/claudio-nuzzo/stradilabos/main/updates/

Come funziona: ogni PC con StradilabOS >= 0.3 (o con l'aggiornatore installato
a mano) esegue `stradilabos-update` 3 minuti dopo l'accensione e poi ogni 7
giorni. Lo script confronta `version.txt` (un numero intero, la "serie") con
quella gia' applicata (`/var/lib/stradilabos/update-serial`): se qui c'e' una
serie piu' alta, scarica `update.sh` e lo esegue come root. Log sul PC in
`/var/log/stradilabos-update.log`.

Per pubblicare un nuovo aggiornamento bastano un commit e un push su `main`:
1. modifica `update.sh` (deve restare IDEMPOTENTE: eseguito due volte non fa danni);
2. incrementa il numero in `version.txt`;
3. commit + push. Al prossimo controllo i PC lo applicano da soli.

Per i PC gia' installati con la 0.2 (una tantum, da terminale):

  sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/claudio-nuzzo/stradilabos/main/updates/install-updater.sh)"

La serie 4 è cumulativa: aggiorna un PC 0.2/0.3 già installato a componenti
grafici, guide, policy Chromium e configurazione degli aggiornamenti 0.3. La
serie corregge anche tema GRUB, messaggi ACPI a console, pannello superiore,
barra applicazioni inferiore e selezione guidata della rete Wi-Fi. Non cancella
documenti o profili utente e non richiede una nuova ISO; scarica dal repository
solo i file di sistema gestiti da StradilabOS. La serie 4 ricontrolla e migra
subito anche i profili Xfce esistenti, inclusi quelli già marcati da una
riparazione precedente, così il riferimento al plugin “(null)” non ricompare
al riavvio. Il vecchio file resta disponibile come backup.

Dopo una nuova connessione Wi-Fi, il selettore StradiLabOS propone di scaricare
e installare subito gli aggiornamenti sul sistema installato. Si può anche usare
in qualunque momento il pulsante «Controlla aggiornamenti» nel Benvenuto; se si
rimanda, il timer di sistema continua a eseguire i controlli periodici.

File del canale:
- update.sh            payload cumulativo (serie corrente: 4)
- version.txt          numero di serie corrente
- install-updater.sh   installazione una tantum su PC 0.2
- stradilabos-update, stradilabos-update.service, stradilabos-update.timer
                       copie dei file client, scaricate da install-updater.sh

ATTENZIONE: i file client esistono anche in config/includes.chroot
(usr/local/bin e etc/systemd/system) per essere inclusi nella ISO: se ne
modifichi uno, aggiorna anche la copia gemella.
