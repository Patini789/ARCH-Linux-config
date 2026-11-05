const demoTracks = [
  { title: "Moonlit Garden", artist: "Gardevoir · Shiny Form", duration: 206, start: 67 },
  { title: "Aurora Pulse", artist: "Shiny Archive · No. 282", duration: 188, start: 34 },
  { title: "Soft Reset", artist: "Psychic Garden · Night Mix", duration: 231, start: 102 },
];

const mount = document.querySelector("#playerMount");
mount.innerHTML = window.PokedexPlayerMarkup;

const device = document.querySelector("#pokedexDevice");
const playButton = document.querySelector("#playButton");
const shuffleButton = document.querySelector("#shuffleButton");
const slider = document.querySelector("#seekSlider");
const title = document.querySelector("#trackTitle");
const artist = document.querySelector("#trackArtist");
const elapsed = document.querySelector("#elapsedTime");
const duration = document.querySelector("#durationTime");
const playbackState = document.querySelector("#playbackState");
const layoutLabel = document.querySelector("#layoutLabel");

let trackIndex = 0;
let currentTime = demoTracks[trackIndex].start;
let isPlaying = false;
let isShuffling = true;

function formatTime(seconds) {
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.floor(seconds % 60).toString().padStart(2, "0");
  return `${minutes}:${remainingSeconds}`;
}

function paintProgress() {
  const currentTrack = demoTracks[trackIndex];
  const progress = (currentTime / currentTrack.duration) * 100;

  slider.max = String(currentTrack.duration);
  slider.value = String(currentTime);
  slider.style.setProperty("--range-progress", `${progress}%`);
  elapsed.textContent = formatTime(currentTime);
  duration.textContent = formatTime(currentTrack.duration);
}

function renderTrack() {
  const currentTrack = demoTracks[trackIndex];
  title.textContent = currentTrack.title;
  artist.textContent = currentTrack.artist;
  currentTime = currentTrack.start;
  paintProgress();
}

function setPlaying(nextState) {
  isPlaying = nextState;
  playButton.dataset.playing = String(isPlaying);
  playButton.setAttribute("aria-pressed", String(isPlaying));
  playButton.setAttribute("aria-label", isPlaying ? "Pausar demostración" : "Iniciar demostración");
  playButton.title = isPlaying ? "Pausar demostración" : "Reproducir demostración";
  playbackState.textContent = isPlaying ? "DEMO EN MARCHA" : "VISTA PREVIA";
  document.querySelector("#connectionLabel").textContent = "MAQUETA · SIN AUDIO";
}

function setShuffle(nextState) {
  isShuffling = nextState;
  shuffleButton.dataset.shuffle = String(isShuffling);
  shuffleButton.setAttribute("aria-pressed", String(isShuffling));
  shuffleButton.setAttribute("aria-label", isShuffling ? "Aleatorio activado" : "Aleatorio desactivado");
  layoutLabel.textContent = isShuffling ? "SHUFFLE ON" : "SHUFFLE OFF";
}

function changeTrack(direction) {
  trackIndex = (trackIndex + direction + demoTracks.length) % demoTracks.length;
  renderTrack();
  setPlaying(false);
}

function updateLayout(width) {
  if (width <= 370) {
    layoutLabel.textContent = "MICRO DEX";
  } else if (width <= 500) {
    layoutLabel.textContent = isShuffling ? "POCKET · SHUFFLE" : "POCKET DEX";
  } else if (width <= 700) {
    layoutLabel.textContent = isShuffling ? "HANDHELD · SHUFFLE" : "HANDHELD";
  } else {
    layoutLabel.textContent = isShuffling ? "SHUFFLE ON" : "FULL DECK";
  }
}

document.querySelectorAll("[data-action]").forEach((button) => {
  button.addEventListener("click", () => {
    if (button.dataset.action === "toggle") {
      setPlaying(!isPlaying);
    } else if (button.dataset.action === "shuffle") {
      setShuffle(!isShuffling);
    } else if (button.dataset.action === "next") {
      changeTrack(1);
    } else if (button.dataset.action === "previous") {
      changeTrack(-1);
    }
  });
});

slider.addEventListener("input", () => {
  currentTime = Number(slider.value);
  paintProgress();
});

document.addEventListener("keydown", (event) => {
  if (event.target instanceof Element && event.target.closest("button, input, a, [contenteditable='true']")) {
    return;
  }

  if (event.code === "Space") {
    event.preventDefault();
    setPlaying(!isPlaying);
  } else if (event.key === "ArrowRight") {
    currentTime = Math.min(demoTracks[trackIndex].duration, currentTime + 5);
    paintProgress();
  } else if (event.key === "ArrowLeft") {
    currentTime = Math.max(0, currentTime - 5);
    paintProgress();
  }
});

if ("ResizeObserver" in window) {
  new ResizeObserver(([entry]) => updateLayout(entry.contentRect.width)).observe(device);
} else {
  window.addEventListener("resize", () => updateLayout(device.getBoundingClientRect().width));
}

window.setInterval(() => {
  if (!isPlaying) {
    return;
  }

  currentTime += 1;
  if (currentTime >= demoTracks[trackIndex].duration) {
    changeTrack(1);
    return;
  }

  paintProgress();
}, 1000);

renderTrack();
setShuffle(true);
updateLayout(device.getBoundingClientRect().width);
