#!/bin/sh
# Usage: sh setup_env.sh <project-dir>
# Makes headless Chromium usable as root (no-sandbox wrapper), downloads the lyric fonts into <project>/assets,
# and prints the CHROME_PATH to export. Safe to re-run.
set -e
P="${1:?project dir}"; mkdir -p "$P/assets"
CH=$(find /opt/pw-browsers -type f -name chrome -path '*chrome-linux*' 2>/dev/null | head -1)
[ -z "$CH" ] && CH=$(command -v chromium || command -v google-chrome || true)
[ -z "$CH" ] && { echo "no Chromium found"; exit 1; }
W="$HOME/chrome-ns"; printf '#!/bin/sh\nexec "%s" --no-sandbox --disable-dev-shm-usage "$@"\n' "$CH" > "$W"; chmod +x "$W"
cd "$P/assets"
if [ ! -f Vazirmatn-Light.ttf ]; then
  curl -sSL -o /tmp/vz.zip https://github.com/rastikerdar/vazirmatn/releases/download/v33.003/vazirmatn-v33.003.zip && \
  unzip -q -o -j /tmp/vz.zip 'fonts/ttf/Vazirmatn-Light.ttf' 'fonts/ttf/Vazirmatn-Medium.ttf' 'fonts/ttf/Vazirmatn-Bold.ttf' -d . || echo "Vazirmatn download failed (Persian text will fall back to Noto Naskh)"
fi
[ -f CormorantItalic.ttf ] || curl -sSL -o CormorantItalic.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/cormorantgaramond/CormorantGaramond-Italic%5Bwght%5D.ttf" || echo "Cormorant download failed"
echo "export CHROME_PATH=$W"
