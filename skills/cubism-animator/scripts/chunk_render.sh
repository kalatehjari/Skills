#!/bin/sh
# Usage: setsid nohup sh chunk_render.sh <project-dir> [workers] > /dev/null 2>&1 < /dev/null & disown
# Resumable full render: patches a 'chunk' mode into engine/render.js (once), renders 600-frame chunks into
# out/chunks/ (finished chunks are skipped, so re-running after a container restart resumes), then joins them
# into out/video.mp4 and checks the frame count. Progress: out/chunks.log ("ALLDONE n/n" at the end).
set -e
P="${1:?project}"; WK="${2:-3}"; cd "$P"
[ -n "$CHROME_PATH" ] || export CHROME_PATH="$HOME/chrome-ns"
if ! grep -q "mode === 'chunk'" engine/render.js; then python3 - <<'PY'
p='engine/render.js'; s=open(p).read()
s=s.replace("  } else if (mode === 'video') {","""  } else if (mode === 'chunk') {
    const [a, b, dest, w] = args; const { frames, secs } = await renderRange(parseInt(a, 10), parseInt(b, 10), parseInt(w || '3', 10), path.resolve(dest));
    console.log(`chunk ${dest} done ${frames} frames ${secs.toFixed(1)}s`);
  } else if (mode === 'video') {""",1)
s=s.replace("if (!['stills', 'sheet', 'board', 'clip', 'video', 'preview', 'cast'].includes(mode))","if (!['stills', 'sheet', 'board', 'clip', 'video', 'preview', 'cast', 'chunk'].includes(mode))")
open(p,'w').write(s)
PY
fi
TOTAL=$(node -e "const s=require('./score.js');console.log(Math.round(s.DURATION*s.FPS))")
mkdir -p out/chunks; f=0
while [ $f -lt $TOTAL ]; do
  e=$((f+600)); [ $e -gt $TOTAL ] && e=$TOTAL
  n=$(printf "out/chunks/c%06d.mp4" $f)
  if [ ! -s "$n" ]; then rm -f out/.render.lock "$n.tmp.mp4"; node engine/render.js chunk $f $e "$n.tmp.mp4" $WK >> out/chunks.log 2>&1 && mv "$n.tmp.mp4" "$n"; fi
  f=$e
done
ls out/chunks/c*.mp4 | grep -v tmp | sed "s#^#file '$PWD/#; s#\$#'#" > out/chunks/list.txt
ffmpeg -v error -y -f concat -safe 0 -i out/chunks/list.txt -c copy out/video.mp4
N=$(ffprobe -v error -count_frames -select_streams v -show_entries stream=nb_read_frames -of csv=p=0 out/video.mp4)
echo "ALLDONE $N/$TOTAL" >> out/chunks.log
