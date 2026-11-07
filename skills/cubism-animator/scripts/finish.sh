#!/bin/sh
# Usage: sh finish.sh <project-dir> "<Output Title>"
# Encodes a YouTube-ready 1080p master (CRF 20, ~100-150 MB; huge files can vanish from outputs), then a 720p
# preview under ~28 MB that fits a chat attachment. Run the preview step detached: it takes ~6 min.
set -e
P="${1:?project}"; NAME="${2:?title}"; OUT=/mnt/user-data/outputs; mkdir -p "$OUT"
M="$OUT/$NAME.mp4"; V="$OUT/$NAME - preview 720p.mp4"
ffmpeg -v error -y -i "$P/out/video.mp4" -i "$P/out/music.wav" -map 0:v -map 1:a -c:v libx264 -preset faster -crf 20 -pix_fmt yuv420p -c:a aac -b:a 320k -shortest -movflags +faststart /tmp/mvd_master.mp4 && cp /tmp/mvd_master.mp4 "$M"
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$M")
VB=$(python3 -c "print(max(300, int(26*8*1024/float($DUR) - 112)))")
cd /tmp
ffmpeg -v error -y -i "$M" -vf scale=1280:720 -c:v libx264 -preset medium -b:v ${VB}k -pass 1 -passlogfile /tmp/mvd2p -an -f mp4 /dev/null
ffmpeg -v error -y -i "$M" -vf scale=1280:720 -c:v libx264 -preset medium -b:v ${VB}k -pass 2 -passlogfile /tmp/mvd2p -c:a aac -b:a 112k -movflags +faststart "$V"
ls -la "$M" "$V"; echo FINISHED > "$P/out/finish.done"
