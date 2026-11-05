# Gardevoir SoundDex

Un reproductor de YouTube Music en una ventana-app de Brave, con carcasa de Pokédex roja, paleta Gardevoir Shiny y tipografía pixel. Abre directamente la playlist configurada y la extensión intenta iniciar **Shuffle Play** al cargarla.

## Instalar

Desde la raíz del repositorio:

```bash
bash extras/pokedex-player/install.sh
```

Después: **Win + Espacio** → busca **reproductor** → `Gardevoir SoundDex`.

La app usa un perfil Brave dedicado en `~/.config/gardevoir-sounddex/brave-profile`, así puede aplicar la política de autoplay sin alterar tu Brave normal. La primera vez, inicia sesión en YouTube Music si la playlist lo requiere; la sesión queda guardada para los próximos lanzamientos. Brave Shields permanece activo y el reproductor multimedia de Chromium publica los controles mediante MPRIS en Linux.

La ventana se abre con la playlist `PLC-WArzdx0KNF2s1dtTDTFS_SBU64vwt6`. La extensión local oculta la interfaz estándar cuando la playlist está lista y muestra solo la Pokédex; si la cuenta necesita autenticación, deja visible YouTube Music para que puedas iniciar sesión. Al redimensionar la ventana, la pantalla cambia entre layouts amplio, handheld y compacto.

## Vista previa

Abre `index.html` para ver únicamente la carcasa. Sus controles son de demostración y no reproducen audio. La app real utiliza los controles, metadatos y portada de la canción que expone YouTube Music.

## Archivos

- `extension/`: extensión local Manifest V3 que crea la Pokédex, sincroniza los controles y solicita Shuffle Play.
- `launch.sh`: abre Brave en modo app con autoplay permitido solo en el perfil dedicado.
- `pokedex.css`: tema CSS opcional para Pear Desktop/th-ch. Pear no acepta actualmente la playlist como argumento de inicio, por eso el lanzador usa Brave.

La portada Gardevoir es un WebP de 800 × 800 (~43 KB), derivado del wallpaper del repositorio; no carga el PNG 4K de 12 MB.
