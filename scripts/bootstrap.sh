#!/usr/bin/env bash

# shellcheck disable=SC1091,SC2086,SC2155

export UNAME="$(uname)"
export PYTHON_VERSION="${PYTHON_VERSION:-3.11.11}"
export PYTHON_MAJOR_MINOR="${PYTHON_VERSION%.*}"
export ASDF_DIR="${LOGGED_IN_HOME}/.asdf"

# $USER
[[ -n $(logname >/dev/null 2>&1) ]] && LOGGED_IN_USER=$(logname) || LOGGED_IN_USER=$(whoami)

# $HOME
LOGGED_IN_HOME=$(eval echo "~${LOGGED_IN_USER}")

# check if binary exists
check_bin() { command -v "$1" >/dev/null 2>&1; }

install_deps() {
	if [[ $UNAME = "Darwin" ]]; then
		echo "Installing vlc"
		if ! check_bin brew; then
			echo "Homebrew not found, please install it first"
			exit 1
		else
			brew install --cask vlc &>/dev/null
		fi
	elif [[ $UNAME = "Linux" ]]; then
		. /etc/os-release
		if [[ $ID = "fedora" ]]; then
			echo "Installing dependencies on fedora"
			sudo dnf install -y \
				python3-tkinter \
				tcl-devel \
				tk-devel \
				vlc
		elif [[ $ID = "ubuntu" ]] || [[ $ID = "debian" ]]; then
			echo "Installing dependencies on ubuntu/debian"
			sudo apt-get install -y \
				python3-tkinter \
				tcl-dev \
				tk-dev \
				vlc
		fi
	fi
}

install_python() {
	if check_bin asdf && [[ $UNAME = "Darwin" ]]; then
		echo "Installing python $PYTHON_VERSION"
		asdf install python "$PYTHON_VERSION" &>/dev/null
	elif check_bin asdf && [[ $UNAME = "Linux" ]]; then
		echo "Installing python $PYTHON_VERSION with linked tkinter dependencies"
		asdf install python "$PYTHON_VERSION" &>/dev/null
		export ASDF_DATA_DIR="${ASDF_DIR}/installs/python/${PYTHON_VERSION}"
		mkdir -p "${ASDF_DATA_DIR}/lib/python${PYTHON_MAJOR_MINOR}/lib-dynload"
		ln -s /usr/lib64/python${PYTHON_MAJOR_MINOR}/site-packages/_tkinter.cpython-* "${ASDF_DATA_DIR}/lib/python${PYTHON_MAJOR_MINOR}/lib-dynload/"
		ln -s /usr/lib64/python${PYTHON_MAJOR_MINOR}/site-packages/tkinter "${ASDF_DATA_DIR}/lib/python${PYTHON_MAJOR_MINOR}/"
	else
		echo "asdf not found, skipping python installation"
	fi
}

main() {
	install_deps
	install_python
	echo "Done!"
}

main
