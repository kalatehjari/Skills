#!/bin/sh
# usage: sh make_video.sh <scripts_dir> <workdir> <song> "<Output name>"
# Renders in resumable 2400-frame segments, muxes the original song, and writes a <30 MB preview.
# Launch detached:  setsid nohup sh make_video.sh ... > <workdir>/out/render.log 2>&1 < /dev/null & disown
S="$1"; WD="$2"; SONG="$3"; NAME="$4"
mkdir -p "$WD/out"
NF=$(python3 "$S/render.py" "$WD" info | awk '{print $2}')
: > "$WD/out/list.txt"
i=0
while [ $i -lt "$NF" ]; do
  j=$((i + 2400)); seg="$WD/out/seg_$i.mp4"
  [ -f "$seg.done" ] || { python3 "$S/render.py" "$WD" video $i $j "$seg" && touch "$seg.done"; }
  echo "file '$(basename "$seg")'" >> "$WD/out/list.txt"
  i=$j
done
ffmpeg -y -loglevel error -f concat -safe 0 -i "$WD/out/list.txt" -i "$SONG" -map 0:v -map 1:a \
  -c:v libx264 -crf 23 -preset fast -c:a aac -b:a 256k -shortest -movflags +faststart "$WD/out/$NAME.mp4"
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$WD/out/$NAME.mp4")
VBR=$(python3 -c "print(min(4000, max(250, int(27*8000/float('$DUR')) - 130)))")
ffmpeg -y -loglevel error -i "$WD/out/$NAME.mp4" -c:v libx264 -b:v ${VBR}k -maxrate ${VBR}k -bufsize $((VBR*2))k \
  -preset slow -c:a aac -b:a 112k -movflags +faststart "$WD/out/preview.mp4"
touch "$WD/out/all.done"
