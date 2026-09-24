#!/usr/bin/env bash
# ============================================================================
#  X++ v0.4.1 – ONE-SHOT SETUP (Linux + macOS)
#  Download, unpack, run:  ./setup.sh        (macOS: double-click setup.command)
#  Installs everything itself (packages it needs, VM, commands, icons, VS Code)
# ============================================================================
set -u
cd "$(dirname "$0")"
ROOT="$(pwd)"

if [ "$(uname)" = "Darwin" ]; then IS_MAC=1; else IS_MAC=0; fi

echo
echo "============================================================"
echo "     X++ v0.4.1  -  AUTO SETUP  ($([ $IS_MAC -eq 1 ] && echo macOS || echo Linux))"
echo "============================================================"
echo

# ---------------------------------------------------------------
# sudo helper (only used when a system package really needs it)
# ---------------------------------------------------------------
SUDO=""
if [ "$(id -u)" -ne 0 ]; then
  if command -v sudo >/dev/null 2>&1; then SUDO="sudo"; fi
fi
run_sudo() { if [ -n "$SUDO" ]; then $SUDO "$@"; else "$@"; fi; }

# ---------------------------------------------------------------
# 1) macOS: Xcode command line tools provide clang++ + python3
# ---------------------------------------------------------------
if [ $IS_MAC -eq 1 ]; then
  echo " [1/4]  Xcode Command Line Tools (clang++)"
  if ! command -v clang++ >/dev/null 2>&1; then
    echo "       Opening Apple installer - click 'Install' in the window."
    xcode-select --install 2>/dev/null || true
    echo "       Waiting for the tools to finish installing..."
    until command -v clang++ >/dev/null 2>&1; do sleep 5; done
    echo " [+]  clang++ ready"
  else
    echo " [+]  clang++ $(clang++ --version | head -1)"
  fi
  echo
fi

# ---------------------------------------------------------------
# 2) Linux: python3 + g++ + make (+ shared-mime-info for icons)
# ---------------------------------------------------------------
if [ $IS_MAC -eq 0 ]; then
  echo " [1/4]  Build system (python3, g++, make)"
  MISSING=""
  command -v python3 >/dev/null 2>&1 || MISSING="$MISSING python3"
  command -v g++     >/dev/null 2>&1 || MISSING="$MISSING g++"
  command -v make    >/dev/null 2>&1 || MISSING="$MISSING make"
  command -v update-mime-database >/dev/null 2>&1 || MISSING="$MISSING shared-mime-info"

  if [ -n "$MISSING" ]; then
    if command -v apt-get >/dev/null 2>&1; then
      run_sudo apt-get update -y >/dev/null 2>&1 || true
      run_sudo apt-get install -y python3 python3-pip g++ make build-essential shared-mime-info >/dev/null 2>&1 || \
      run_sudo apt-get install -y python3 g++ make shared-mime-info >/dev/null 2>&1 || true
    elif command -v dnf >/dev/null 2>&1; then
      run_sudo dnf install -y python3 python3-pip gcc-c++ make shared-mime-info >/dev/null 2>&1 || true
    elif command -v pacman >/dev/null 2>&1; then
      run_sudo pacman -Sy --noconfirm --needed python python-pip gcc make shared-mime-info >/dev/null 2>&1 || true
    elif command -v zypper >/dev/null 2>&1; then
      run_sudo zypper -n install python3 python3-pip gcc-c++ make shared-mime-info >/dev/null 2>&1 || true
    fi
  fi
  echo " [+]  python3: $(python3 --version 2>&1 || echo MISSING)"
  echo " [+]  g++:     $(g++ --version 2>/dev/null | head -1 || echo MISSING)"
  echo
fi

# ---------------------------------------------------------------
# 3) Python deps + the universal engine (VM, commands, icons, VS Code)
# ---------------------------------------------------------------
echo " [2/4]  Python packages + X++ engine"
if ! command -v python3 >/dev/null 2>&1; then
  echo " [X] python3 is still missing. Install it (e.g. 'sudo apt install python3') and rerun."
  exit 1
fi
if [ $IS_MAC -eq 1 ]; then
  python3 -m ensurepip --user >/dev/null 2>&1 || true
fi
exec_best() {
  # this never fetches stuff it doesn't need; the tool handles retries
  python3 "$ROOT/tools/xpp_setup.py" --all
  return $?
}
exec_best
RC=$?
if [ $RC -ne 0 ]; then
  echo
  echo " [X] Setup hit an error - scroll up and rerun."
  exit $RC
fi

echo
echo "============================================================"
echo "   DONE! Open a NEW terminal and type:"
echo
echo "       x run examples/hello.xp"
echo "       x run examples/fib_fast.xp --mode ZJIT"
echo
echo "   .xp files now show the X++ logo in VS Code / your file manager."
echo "============================================================"
exit 0
