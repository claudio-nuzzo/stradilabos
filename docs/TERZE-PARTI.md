# Componenti di terze parti — StradilabOS 0.3

Questa pagina censisce i componenti esterni presi in considerazione per
l'estetica in stile macOS (requisito D) e quelli già in uso, con versione,
origine e licenza. La regola §0.6 vieta qualunque asset Apple: l'aspetto
«WhiteSur» è soltanto un riferimento libero, non va copiato.

## Riferimento visivo (non incorporato)

| Componente | Autore | Licenza | Stato nella 0.3 |
| --- | --- | --- | --- |
| WhiteSur-gtk-theme | vinceliuice | GPL-3.0 | Riferimento estetico: **non vendorizzato** (§6.1) |
| WhiteSur-icon-theme | vinceliuice | GPL-3.0 | Riferimento estetico: **non vendorizzato** (§6.2) |
| Plank | elementary / Debian | GPL-3.0 | **Non usato**: vedi §6.3 |

### Perché non vengono incorporati ora

La 0.3 realizza l'obiettivo visivo in modo nativo e leggero, senza scaricare
né vendicizzare asset binari a runtime:

- **Dock (§6.3):** scelto un **secondo pannello Xfce in basso** («semplice
  barra icone», la soluzione alternativa prevista dalla specifica). È la più
  stabile su Xfce 4.20 e sui PC datati: Plank è un processo in più e su GPU
  virtuali/vecchie può non restare in esecuzione. La scelta è reversibile, ma
  documentata qui come deliberata.
- **Pannello superiore (§6.4):** sottile e scuro (navy `#1b3a6b`), con icone
  simboliche chiare su fondo scuro: risolve il rilievo n. 3 del collaudo
  (icone bianche su avorio illeggibili). L'angolo arrotondato e lo stile dei
  controlli arrivano dal CSS già presente nel tema StradiLab.
- **Tema GTK/icone (§6.1 e §6.2):** resta il tema StradiLab (derivato da
  Greybird, già in Debian) con le icone StradiLab esistenti. I pulsanti
  «semaforo» richiedono le bitmap xfwm4 di WhiteSur: la loro integrazione è
  rinviata alla build (non scaricabile in questo ambiente di lavoro).

> `TODO(claudio):` valutare se, dopo la revisione, vendorizzare WhiteSur-gtk-theme
> e WhiteSur-icon-theme a un commit/rilascio fissato dentro
> `config/includes.chroot/usr/share/themes/` e `/usr/share/icons/`, oppure
> confermare l'estetica nativa. Serve la rete per scaricare gli asset e la
> licenza GPL-3.0 va riportata integralmente insieme ai file.

## Componenti di sistema già in uso

| Componente | Origine | Licenza | Note |
| --- | --- | --- | --- |
| Debian 13 (Trixie) + Xfce | Debian | GPL/varie | base del sistema |
| Greybird | shimmerproject | GPL-2.0+ / CC BY-SA | base del tema StradiLab |
| Live-build, Calamares | Debian/Calamares | GPL | build e installazione |
| NetworkManager | GNOME | GPL-2.0+ | gestione rete/Wi-Fi |
| unattended-upgrades | Debian | GPL-2+ | aggiornamenti di sicurezza |
| Fonts Noto / Liberation / OpenDyslexic | Google/SIL/… | OFL | tipografia |

## Sfondi e icone

Gli sfondi e le icone di StradilabOS sono originali (palette StradiLab). Lo
sfondo «Big Sur» è generato da `scripts/generate_wallpaper.py` come SVG
sorgente + PNG esportati in `usr/share/backgrounds/stradilabos/`: nessuna
immagine Apple è usata o modificata.