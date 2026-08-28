# Sistema visivo StradiLab

StradilabOS usa un'unica identità visiva coordinata. Sfondo, icone, schermata di
benvenuto e installatore devono restare nella stessa palette; i colori non sono
decorazioni intercambiabili, ma elementi del brand StradiLab.

## Palette

- **Avorio carta** `#F6F4EF`: fondi chiari, superfici e testi su fondo scuro.
- **Nero caldo** `#16130F`: fondi scuri, testo principale e struttura.
- **Bordeaux StradiLab** `#9B2335`: azioni principali, selezioni e punto focale.
- **Rosa** `#D4839F`, **verde salvia** `#7DAB7E`, **ocra** `#D4A85A`,
  **blu** `#7A9FD4`, **terracotta** `#C4906A`: il sistema dei cinque accenti.
- **Grigio carta** `#DED8CE` e **testo secondario** `#645E55`: soli neutri di
  supporto. **Bianco superficie** `#FFFFFF` è ammesso solo per schede e righe
  sopra l'avorio, mai come fondo di pagina.
- **Toni profondi** dei cinque accenti, da usare quando un accento deve
  diventare testo o etichetta sull'avorio: rosa `#B83864`, salvia `#477348`,
  ocra `#88621D`, blu `#3368B5`, terracotta `#915B33`. Ciascuno supera il
  contrasto 5:1 sull'avorio; gli accenti chiari (2–2,5:1) restano riservati a
  forme, punti e decorazioni, mai a testo.

## Contrasto e leggibilità

| Coppia | Contrasto | Uso |
|---|---:|---|
| Nero caldo su avorio | 16,9:1 | testo principale |
| Testo secondario su avorio | 5,8:1 | descrizioni, note |
| Bordeaux su avorio / avorio su bordeaux | 7,1:1 | titoli, badge, pulsante primario |
| Grigio carta su nero caldo | 13,5:1 | testo sull'intestazione scura dello Hub |
| Toni profondi su avorio | ≥ 5:1 | badge di categoria dello Hub |

Dimensioni minime del testo nelle app StradilabOS: 12 px per badge ed
etichette, 13 px per le descrizioni, 15 px per il testo corrente.

## Regole d'uso

1. Ogni icona StradilabOS usa avorio, nero caldo e bordeaux come colori
   principali; i cinque accenti appaiono insieme come firma del sistema.
2. Lo sfondo resta chiaro e libero sul lato sinistro, dove Xfce dispone le
   icone del desktop.
3. Il bordeaux identifica sempre l'azione primaria e la voce attiva.
4. Non si introducono nuovi colori senza aggiornare questa guida, la lista
   `BRAND_COLORS` in `scripts/validate_project.py` e tutti i componenti
   interessati: il controllo statico segnala ogni esadecimale fuori palette in
   Benvenuto, Hub, Centro App, icone e fogli GTK.
4b. L'anello di fuoco da tastiera è bordeaux (nero caldo sui controlli già
   bordeaux); il blu chiaro non è ammesso come indicatore di fuoco perché sul
   fondo avorio non raggiunge il contrasto 3:1 richiesto agli elementi grafici.
4c. Le tre app (Benvenuto, Hub, Centro App) condividono lo stesso linguaggio:
   fondo avorio, schede bianche con bordo grigio carta e raggio 14–16 px, bordo
   bordeaux al passaggio del mouse, pulsante primario bordeaux con testo avorio.
5. Le icone restano vettoriali, semplici e leggibili da 16 a 128 pixel.
6. Il pannello è unico, in alto e leggero: il marchio apre il menu; StradiLab,
   Workspace, Centro App e File sono gli unici launcher permanenti.
7. Il nome Debian può comparire solo nelle note tecniche sulla base del sistema,
   non come titolo dell'avvio, del login o del desktop.

## Risorse principali

- Sfondo: `/usr/share/backgrounds/stradilabos/stradilabos-wallpaper-v2.png`
- Tema icone: `/usr/share/icons/StradiLab`
- Tema GTK e finestre: `/usr/share/themes/StradiLab` (generato dall'hook 012
  a partire da Greybird; incorpora le regole comuni di `/etc/xdg/gtk-3.0/gtk.css`
  e `/etc/xdg/gtk-4.0/gtk.css`, così valgono anche per il login e per gli
  utenti già esistenti)
- Icone delle app: `/usr/local/share/icons/hicolor/scalable/apps`
- Branding installatore: `/etc/calamares/branding/stradilabos`
- Menu Live: `/boot/grub/live-theme/theme.txt`
- Avvio installato: `/usr/share/grub/themes/stradilabos`
- Caricamento: `/usr/share/plymouth/themes/stradilabos`
- Login: `/etc/lightdm/lightdm-gtk-greeter.conf.d/60-stradilabos.conf`
