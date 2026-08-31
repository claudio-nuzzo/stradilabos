# Componenti di terze parti — StradilabOS 0.3

Questa pagina censisce i componenti esterni presenti nella ISO 0.3. Tutti sono
inclusi nel repository: la sessione non scarica né installa temi o icone al
primo avvio. StradilabOS mantiene i propri nome, palette bordeaux/navy/crema,
icone e sfondi; non usa loghi, immagini o sfondi proprietari Apple.

| Componente | Versione fissata | Origine | Licenza | Uso nella ISO |
| --- | --- | --- | --- |
| WhiteSur GTK Theme | tag `2026-08-08`, commit `1b356fe48ad5d05fb2ca6be071efe6801df3ac72` | [vinceliuice/WhiteSur-gtk-theme](https://github.com/vinceliuice/WhiteSur-gtk-theme) | MIT | Varianti standard `WhiteSur-Light` e `WhiteSur-Dark` in `usr/share/themes/`; include il tema xfwm4 con i controlli finestra a semaforo. Copia della licenza in ogni variante. |
| WhiteSur Icon Theme | tag `2026-08-11`, commit `555a4505920475482f62afd02366441a53669c30` | [vinceliuice/WhiteSur-icon-theme](https://github.com/vinceliuice/WhiteSur-icon-theme) | GPL-3.0 | Variante standard `WhiteSur` in `usr/share/icons/`; eredita le icone originali StradiLab per i launcher del progetto. Copia della licenza inclusa. |
| Xfce Panel | Xfce 4.20 (Debian 13) | Debian | GPL-2.0+ | Secondo pannello inferiore con barra icone: è l'alternativa leggera a Plank prevista dalla specifica, senza un demone ulteriore. |

## Scelte di integrazione

- La sessione usa `WhiteSur-Light` e `WhiteSur`; le varianti chiare/scure del
  tema GTK sono entrambe incluse per accessibilità e future preferenze, mentre
  la variante standard delle icone evita decine di combinazioni non usate.
- Il pannello superiore navy mantiene icone simboliche chiare e leggibili; la
  barra inferiore raccoglie Chromium, StradiLab, File, LibreOffice e Guide.
- I pulsanti di xfwm4 sono a sinistra nell'ordine chiudi/riduci/massimizza,
  con ombre leggere e il compositore disabilitato per i PC meno recenti.
- Gli sfondi `stradilabos-wallpaper-v3.*` sono originali, generati da
  `scripts/generate_wallpaper.py` con la palette StradiLab.

## Componenti di sistema già in uso

| Componente | Origine | Licenza | Note |
| --- | --- | --- | --- |
| Debian 13 (Trixie) + Xfce | Debian | GPL/varie | Base del sistema |
| Greybird | shimmerproject | GPL-2.0+ / CC BY-SA | Tema di riserva usato dalla guardia xfwm4 se WhiteSur non può essere caricato. |
| Live-build, Calamares | Debian/Calamares | GPL | Build e installazione |
| NetworkManager | GNOME | GPL-2.0+ | Gestione rete e Wi-Fi |
| unattended-upgrades | Debian | GPL-2+ | Aggiornamenti di sicurezza |
| Fonts Noto / Liberation / OpenDyslexic | Google/SIL/… | OFL | Tipografia |
