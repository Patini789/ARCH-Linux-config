#
# ~/.bashrc
#

# If not running interactively, don't do anything
[[ $- != *i* ]] && return

# Modern CLI Aliases (eza & bat)
alias ls='eza --icons --group-directories-first'
alias ll='eza -lh --icons --group-directories-first'
alias la='eza -lah --icons --group-directories-first'
alias tree='eza --tree --icons'
alias cat='bat --paging=never'
alias grep='grep --color=auto'


# Flatpak export paths
export XDG_DATA_DIRS="/var/lib/flatpak/exports/share:$HOME/.local/share/flatpak/exports/share:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"

# Pokémon Splash
$HOME/.local/bin/pokemon-splash.sh


# opencode, local bin & lmstudio
export PATH="$HOME/.lmstudio/bin:$HOME/.local/bin:$HOME/.opencode/bin:$PATH"

# Autocomplete & Fuzzy Search
[[ -r /usr/share/bash-completion/bash_completion ]] && . /usr/share/bash-completion/bash_completion
eval "$(fzf --bash)"
[ -f /opt/ros/jazzy/setup.bash ] && source /opt/ros/jazzy/setup.bash

# Starship Prompt
eval "$(starship init bash)"


# Wrapper de Yazi para cambiar de directorio automáticamente al salir
function y() {
	local tmp="$(mktemp -t "yazi-cwd.XXXXXX")" cwd
	yazi "$@" --cwd-file="$tmp"
	if cwd="$(command cat -- "$tmp")" && [ -n "$cwd" ] && [ "$cwd" != "$PWD" ]; then
		builtin cd -- "$cwd"
	fi
	rm -f -- "$tmp"
}
alias yazi='y'

# Added by LM Studio CLI tool (lms)
export PATH="$PATH:$HOME/.lmstudio/bin"

alias cls='clear'
alias cpwd="pwd | tr -d '\n' | (xclip -selection clipboard 2>/dev/null || wl-copy 2>/dev/null)"
