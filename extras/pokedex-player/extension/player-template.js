(() => {
  globalThis.PokedexPlayerMarkup = `
    <article class="pokedex-device" id="pokedexDevice" aria-label="Gardevoir SoundDex">
      <span class="case-screw screw-top-left" aria-hidden="true"></span>
      <span class="case-screw screw-top-right" aria-hidden="true"></span>
      <span class="case-screw screw-bottom-left" aria-hidden="true"></span>
      <span class="case-screw screw-bottom-right" aria-hidden="true"></span>

      <div class="bezel">
        <div class="lcd-screen">
          <header class="screen-header">
            <div class="screen-brand">
              <span class="screen-kicker">GARDEVOIR SHINY DEX</span>
              <strong>SONIC ARCHIVE</strong>
            </div>
            <div class="signal-pill"><span class="signal-led"></span><span id="layoutLabel">SHUFFLE ON</span></div>
          </header>

          <div class="screen-content">
            <section class="cover-panel" aria-label="Portada del reproductor">
              <div class="cover-art">
                <img id="coverImage" src="./extension/assets/gardevoir-cover.webp" alt="Gardevoir Shiny" />
                <div class="cover-wash" aria-hidden="true"></div>
                <span class="cover-star star-one" aria-hidden="true">✦</span>
                <span class="cover-star star-two" aria-hidden="true">✧</span>
                <span class="cover-number">NO. 282</span>
                <span class="cover-caption">SHINY FORM<br /><b>PSYCHIC / FAIRY</b></span>
              </div>
              <div class="cover-footnote"><span class="tiny-led"></span> SHINY ENTRY <span>001 / 282</span></div>
            </section>

            <section class="track-panel" aria-label="Controles de música">
              <div class="entry-line">
                <span class="entry-code">NOW PLAYING <i>//</i> YOUTUBE MUSIC</span>
                <span class="equalizer" id="equalizer" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i></span>
              </div>

              <div class="track-copy" aria-live="polite" aria-atomic="true">
                <h1 id="trackTitle">Conectando...</h1>
                <p id="trackArtist">Cargando la playlist shiny</p>
              </div>

              <div class="type-tags" aria-label="Tipos y colección">
                <span>PSYCHIC</span>
                <span>FAIRY</span>
                <span class="tag-muted">SHINY OST</span>
              </div>

              <div class="playback">
                <div class="time-row">
                  <span id="elapsedTime">0:00</span>
                  <span class="playback-state" id="playbackState">INICIANDO DEX</span>
                  <span id="durationTime">0:00</span>
                </div>
                <input class="seek-slider" id="seekSlider" type="range" min="0" max="100" value="0" step="1" aria-label="Posición de reproducción" />

                <div class="transport-row">
                  <button class="transport-button secondary" id="previousButton" type="button" data-action="previous" aria-label="Canción anterior" title="Anterior">
                    <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 5v14M19 6v12L8 12z" /></svg>
                  </button>
                  <button class="transport-button shuffle-button" id="shuffleButton" type="button" data-action="shuffle" aria-label="Aleatorio activado" aria-pressed="true" title="Aleatorio">
                    <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M17 3h4v4h-2V6.41l-4.3 4.3-1.42-1.42 4.3-4.3H17V3ZM3 7h2.5c1.4 0 2.72.64 3.6 1.73l6.8 8.54c.5.63 1.26.99 2.06.99H19v-2h2v4h-4c-1.4 0-2.72-.64-3.6-1.73L6.6 9.99A2.65 2.65 0 0 0 4.5 9H3V7Zm14 10h2v-1h2v4h-4v-2h1v-1ZM3 17h1.5c.8 0 1.56-.36 2.06-.99l1.48-1.85 1.42 1.42-1.33 1.67A4.65 4.65 0 0 1 4.5 19H3v-2Zm8.07-7.93 1.42-1.42.8 1-1.42 1.42-.8-1Z" /></svg>
                  </button>
                  <button class="transport-button play-button" id="playButton" type="button" data-action="toggle" aria-label="Reproducir" aria-pressed="false" title="Reproducir">
                    <svg class="play-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5.8v12.4L18 12z" /></svg>
                    <svg class="pause-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M7.5 5.5h3.8v13H7.5zm5.2 0h3.8v13h-3.8z" /></svg>
                  </button>
                  <button class="transport-button secondary" id="nextButton" type="button" data-action="next" aria-label="Siguiente canción" title="Siguiente">
                    <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M18 5v14M5 6v12l11-6z" /></svg>
                  </button>
                </div>
              </div>
            </section>
          </div>

          <footer class="screen-footer">
            <div class="connection-status"><span class="status-led"></span><span id="connectionLabel">CONECTANDO A YOUTUBE MUSIC</span></div>
            <div class="mpris-label" id="mprisLabel">MPRIS <i>·</i> READY</div>
          </footer>
        </div>
      </div>

      <footer class="hardware-row" aria-hidden="true">
        <div class="hardware-brand"><span>GARDEVOIR</span><b>SOUNDDEX</b></div>
        <div class="hardware-light"><span></span> SHINY UNIT <i>282</i></div>
        <div class="speaker-grille"><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div>
        <div class="hardware-mark">PSYCHIC<br /><b>TYPE</b></div>
      </footer>
    </article>
  `;
})();
