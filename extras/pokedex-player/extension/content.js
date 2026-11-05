(() => {
  const PLAYLIST_ID = "PLC-WArzdx0KNF2s1dtTDTFS_SBU64vwt6";
  const PLAYER_TITLE = "Gardevoir SoundDex — Pokédex Player";
  const FALLBACK_COVER = chrome.runtime.getURL("assets/gardevoir-cover.webp");

  let appRoot = null;
  let playerBar = null;
  let playlistHeader = null;
  let shuffleStartedFor = "";
  let moreMenuOpenedFor = "";
  let isShuffleOn = false;
  let lastPageUrl = "";

  function deepQuery(selector, root = document) {
    const pending = [root];
    const visited = new Set();

    while (pending.length > 0) {
      const current = pending.shift();
      if (!current || visited.has(current)) continue;
      visited.add(current);

      if (typeof current.querySelector === "function") {
        try {
          const match = current.querySelector(selector);
          if (match) return match;
        } catch {
          // Ignore selectors unsupported by a particular custom-element root.
        }

        for (const element of current.querySelectorAll("*")) {
          if (element.shadowRoot) pending.push(element.shadowRoot);
        }
      }
    }

    return null;
  }

  function deepQueryAll(selector, root = document) {
    const matches = [];
    const pending = [root];
    const visited = new Set();

    while (pending.length > 0) {
      const current = pending.shift();
      if (!current || visited.has(current)) continue;
      visited.add(current);

      if (typeof current.querySelectorAll === "function") {
        try {
          matches.push(...current.querySelectorAll(selector));
        } catch {
          // Ignore selectors unsupported by a particular custom-element root.
        }

        for (const element of current.querySelectorAll("*")) {
          if (element.shadowRoot) pending.push(element.shadowRoot);
        }
      }
    }

    return matches;
  }

  function nodeLabel(node) {
    return [node?.getAttribute?.("aria-label"), node?.getAttribute?.("title"), node?.textContent]
      .filter(Boolean)
      .join(" ")
      .trim();
  }

  function isVisible(node) {
    if (!node) return false;
    const rect = node.getBoundingClientRect?.();
    return Boolean(rect && rect.width > 0 && rect.height > 0);
  }

  function findByLabel(root, expression) {
    return deepQueryAll("button, [role='button'], tp-yt-paper-icon-button, yt-icon-button", root)
      .find((node) => expression.test(nodeLabel(node)) && isVisible(node)) ?? null;
  }

  function findPlaylistHeader() {
    if (playlistHeader?.isConnected) return playlistHeader;
    playlistHeader = deepQuery("ytmusic-playlist-header-renderer") ??
      deepQuery("ytmusic-responsive-header-renderer") ??
      deepQuery("ytmusic-browse-response");
    return playlistHeader;
  }

  function playlistNeedsLogin(header) {
    if (!header) return true;
    const headerText = header.textContent ?? "";
    if (/sign in to|inicia sesión para|inicia sesión en/i.test(headerText)) return true;
    return Boolean(findByLabel(header, /sign in|iniciar sesión|acceder/i));
  }

  function findPlaylistShuffleButton(header) {
    const directSelectors = [
      "#shuffle-button",
      "#shuffle-play-button",
      "[button-type='shuffle']",
      "button[aria-label*='shuffle' i]",
      "button[aria-label*='mezcl' i]",
    ];

    for (const selector of directSelectors) {
      const candidate = deepQuery(selector, header);
      if (isVisible(candidate)) return candidate;
    }

    return findByLabel(header, /shuffle|mezcl|aleator/i);
  }

  function findShuffleMenuItem() {
    return findByLabel(document, /shuffle (playlist|play)|reproducir aleatori|mezclar (lista|playlist)/i);
  }

  function findPlayerBar() {
    if (playerBar?.isConnected) return playerBar;
    playerBar = deepQuery("ytmusic-player-bar");
    return playerBar;
  }

  function findNativeControl(action) {
    const bar = findPlayerBar();
    if (!bar) return null;

    const selectors = {
      toggle: ["#play-pause-button", "#play-button", "button[aria-label*='play' i]", "button[aria-label*='reproduc' i]"],
      next: ["#next-button", "button[aria-label*='next' i]", "button[aria-label*='siguiente' i]"],
      previous: ["#previous-button", "#prev-button", "button[aria-label*='previous' i]", "button[aria-label*='anterior' i]"],
      shuffle: ["#shuffle-button", "button[aria-label*='shuffle' i]", "button[aria-label*='aleatorio' i]"]
    }[action] ?? [];

    for (const selector of selectors) {
      const candidate = deepQuery(selector, bar);
      if (isVisible(candidate)) return candidate;
    }

    const labels = {
      toggle: /play|pause|reproduc|pausar/i,
      next: /next|siguiente/i,
      previous: /previous|anterior/i,
      shuffle: /shuffle|aleatorio|mezclar/i
    };
    return findByLabel(bar, labels[action] ?? /$^/);
  }

  function clickNative(action) {
    const button = findNativeControl(action);
    if (!button) return false;
    button.click();
    return true;
  }

  function setShuffleState(nextState) {
    isShuffleOn = nextState;
    const button = appRoot?.querySelector("#shuffleButton");
    if (!button) return;
    button.dataset.shuffle = String(isShuffleOn);
    button.setAttribute("aria-pressed", String(isShuffleOn));
    button.setAttribute("aria-label", isShuffleOn ? "Aleatorio activado" : "Aleatorio desactivado");
  }

  function setStatus(message, playingState = null) {
    const label = appRoot?.querySelector("#connectionLabel");
    const state = appRoot?.querySelector("#playbackState");
    if (label && label.textContent !== message) label.textContent = message;
    if (state && playingState && state.textContent !== playingState) state.textContent = playingState;
  }

  function setText(selector, value) {
    const node = appRoot?.querySelector(selector);
    if (node && node.textContent !== value) node.textContent = value;
  }

  function startShuffleForPlaylist() {
    const playlistId = new URL(location.href).searchParams.get("list");
    if (playlistId !== PLAYLIST_ID || shuffleStartedFor === playlistId) return;

    const header = findPlaylistHeader();
    if (!header) return;

    const shuffleButton = findPlaylistShuffleButton(header);
    if (shuffleButton) {
      shuffleStartedFor = playlistId;
      shuffleButton.click();
      setShuffleState(true);
      setStatus("PLAYLIST EN ALEATORIO", "INICIANDO SHUFFLE");
      window.setTimeout(syncPlayer, 1200);
      return;
    }

    const menuItem = findShuffleMenuItem();
    if (menuItem) {
      shuffleStartedFor = playlistId;
      menuItem.click();
      setShuffleState(true);
      setStatus("PLAYLIST EN ALEATORIO", "INICIANDO SHUFFLE");
      window.setTimeout(syncPlayer, 1200);
      return;
    }

    if (moreMenuOpenedFor !== playlistId) {
      const moreButton = findByLabel(header, /more|más opciones|más acciones|opciones/i);
      if (moreButton) {
        moreMenuOpenedFor = playlistId;
        moreButton.click();
        window.setTimeout(startShuffleForPlaylist, 450);
        return;
      }
    }

    const playButton = deepQuery("#play-button", header) ?? findByLabel(header, /^play$|^reproducir$/i);
    if (playButton && moreMenuOpenedFor !== `fallback:${playlistId}`) {
      moreMenuOpenedFor = `fallback:${playlistId}`;
      playButton.click();
      setStatus("INICIANDO PLAYLIST", "ACTIVANDO ALEATORIO");
      window.setTimeout(() => {
        if (clickNative("shuffle")) setShuffleState(true);
        shuffleStartedFor = playlistId;
        syncPlayer();
      }, 900);
    }
  }

  function formatTime(seconds) {
    if (!Number.isFinite(seconds) || seconds < 0) return "0:00";
    const minutes = Math.floor(seconds / 60);
    const remainder = Math.floor(seconds % 60).toString().padStart(2, "0");
    return `${minutes}:${remainder}`;
  }

  function getArtwork(metadata) {
    const artwork = metadata?.artwork;
    if (!artwork?.length) return "";
    return artwork.find((item) => item.sizes?.includes("512x512"))?.src ?? artwork.at(-1)?.src ?? artwork[0].src;
  }

  function syncPlayer() {
    if (!appRoot) return;
    const bar = findPlayerBar();
    const metadata = navigator.mediaSession?.metadata;
    const titleNode = bar && (deepQuery("#title", bar) ?? deepQuery(".title", bar));
    const artistNode = bar && (deepQuery("#subtitle", bar) ?? deepQuery("#byline", bar));
    const title = metadata?.title || titleNode?.textContent?.trim();
    const artist = metadata?.artist || artistNode?.textContent?.trim();

    if (title) setText("#trackTitle", title);
    if (artist) setText("#trackArtist", artist);

    const artwork = getArtwork(metadata);
    if (artwork) {
      const image = appRoot.querySelector("#coverImage");
      if (image.src !== artwork) image.src = artwork;
      image.alt = title ? `Portada: ${title}` : "Portada de la canción";
    }

    const playbackState = navigator.mediaSession?.playbackState;
    const playButton = findNativeControl("toggle");
    const playingFromLabel = /pause|pausar/i.test(nodeLabel(playButton));
    const isPlaying = playbackState === "playing" || (playbackState !== "paused" && playingFromLabel);
    const appPlayButton = appRoot.querySelector("#playButton");
    appPlayButton.dataset.playing = String(isPlaying);
    appPlayButton.setAttribute("aria-pressed", String(isPlaying));
    appPlayButton.setAttribute("aria-label", isPlaying ? "Pausar" : "Reproducir");
    appPlayButton.title = isPlaying ? "Pausar" : "Reproducir";

    const label = title
      ? (isPlaying ? "REPRODUCIENDO EN BRAVE" : "YOUTUBE MUSIC · EN PAUSA")
      : "ESPERANDO A YOUTUBE MUSIC";
    const state = title ? (isPlaying ? "SOUNDDEX ACTIVO" : "LISTO PARA SONAR") : "CARGANDO PLAYLIST";
    setStatus(label, state);

    const nativeProgress = bar && (deepQuery("#progress-bar", bar) ?? deepQuery("#sliderBar", bar));
    if (nativeProgress) {
      const current = Number(nativeProgress.value ?? nativeProgress.getAttribute("aria-valuenow"));
      const total = Number(nativeProgress.max ?? nativeProgress.getAttribute("aria-valuemax"));
      if (Number.isFinite(current) && Number.isFinite(total) && total > 0) {
        const slider = appRoot.querySelector("#seekSlider");
        slider.max = String(total);
        slider.value = String(Math.min(current, total));
        slider.style.setProperty("--range-progress", `${(current / total) * 100}%`);
        appRoot.querySelector("#elapsedTime").textContent = formatTime(current);
        appRoot.querySelector("#durationTime").textContent = formatTime(total);
      }
    }
  }

  function createApp() {
    if (appRoot || !document.body || !globalThis.PokedexPlayerMarkup) return;

    appRoot = document.createElement("main");
    appRoot.id = "pokedexPlayerApp";
    appRoot.className = "pokedex-app-root";
    appRoot.setAttribute("aria-label", "Gardevoir SoundDex — reproductor");
    appRoot.innerHTML = globalThis.PokedexPlayerMarkup;
    appRoot.querySelector("#coverImage").src = FALLBACK_COVER;
    document.body.append(appRoot);

    appRoot.querySelectorAll("[data-action]").forEach((button) => {
      button.addEventListener("click", () => {
        switch (button.dataset.action) {
          case "toggle":
            clickNative("toggle");
            window.setTimeout(syncPlayer, 250);
            break;
          case "previous":
            clickNative("previous");
            break;
          case "next":
            clickNative("next");
            break;
          case "shuffle": {
            const nextState = !isShuffleOn;
            if (clickNative("shuffle")) setShuffleState(nextState);
            break;
          }
        }
      });
    });

    appRoot.querySelector("#seekSlider").addEventListener("input", (event) => {
      const nativeProgress = findPlayerBar() && deepQuery("#progress-bar", findPlayerBar());
      if (!nativeProgress) return;
      nativeProgress.value = Number(event.target.value);
      nativeProgress.dispatchEvent(new Event("input", { bubbles: true, composed: true }));
      nativeProgress.dispatchEvent(new Event("change", { bubbles: true, composed: true }));
    });
  }

  function updateAppRoute() {
    if (!document.body) return;
    createApp();

    const url = location.href;
    const playlistId = new URL(url).searchParams.get("list");
    if (url !== lastPageUrl) {
      lastPageUrl = url;
      if (playlistId !== PLAYLIST_ID) {
        shuffleStartedFor = "";
        moreMenuOpenedFor = "";
        playlistHeader = null;
      }
    }

    const header = playlistId === PLAYLIST_ID ? findPlaylistHeader() : null;
    const alreadyActive = document.body.classList.contains("pokedex-player-active");
    if (playlistId === PLAYLIST_ID && (alreadyActive || (header && !playlistNeedsLogin(header)))) {
      document.documentElement.classList.add("pokedex-player-active");
      document.body.classList.add("pokedex-player-active");
      document.title = PLAYER_TITLE;
      setShuffleState(isShuffleOn);
      if (header) startShuffleForPlaylist();
      syncPlayer();
    } else {
      document.documentElement.classList.remove("pokedex-player-active");
      document.body.classList.remove("pokedex-player-active");
    }
  }

  createApp();
  updateAppRoute();
  window.setInterval(updateAppRoute, 900);
})();
