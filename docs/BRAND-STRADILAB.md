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
  supporto.

## Regole d'uso

1. Ogni icona StradilabOS usa avorio, nero caldo e bordeaux come colori
   principali; i cinque accenti appaiono insieme come firma del sistema.
2. Lo sfondo resta chiaro e libero sul lato sinistro, dove Xfce dispone le
   icone del desktop.
3. Il bordeaux identifica sempre l'azione primaria e la voce attiva.
4. Non si introducono nuovi colori senza aggiornare questa guida e tutti i
   componenti interessati.
5. Le icone restano vettoriali, semplici e leggibili da 16 a 128 pixel.
6. Il pannello è unico, in alto e leggero: il marchio apre il menu; StradiLab,
   Workspace, Centro App e File sono gli unici launcher permanenti.
7. Il nome Debian può comparire solo nelle note tecniche sulla base del sistema,
   non come titolo dell'avvio, del login o del desktop.

## Risorse principali

- Sfondo: `/usr/share/backgrounds/stradilabos/stradilabos-wallpaper-v2.png`
- Tema icone: `/usr/share/icons/StradiLab`
- Icone delle app: `/usr/local/share/icons/hicolor/scalable/apps`
- Branding installatore: `/etc/calamares/branding/stradilabos`
- Menu Live: `/boot/grub/live-theme/theme.txt`
- Avvio installato: `/usr/share/grub/themes/stradilabos`
- Caricamento: `/usr/share/plymouth/themes/stradilabos`
- Login: `/etc/lightdm/lightdm-gtk-greeter.conf.d/60-stradilabos.conf`
