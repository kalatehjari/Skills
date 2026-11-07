#!/usr/bin/env python3
"""Join filmed shots into the finished trailer: picture, black gaps, loudness-normalised sound, plus store extras.

  python3 finish_trailer.py promo/shots --audio promo/mix.wav                 -> promo/trailer-1080p.mp4
  python3 finish_trailer.py promo/shots --edit promo/edit.json --audio promo/mix.wav --small \
          --gif s03-door:0.8:1.6 --thumb s03-door:40

  --edit    edit.json {"timeline": ["s01-title", {"black": 14}, "s02-hall", ...]} (default: shots.json order)
  --small   also a 1280x720 copy (smaller upload, for pages that embed video)
  --gif     shot:start_seconds:duration -> a looping GIF under 3 MB for store pages (640 px, 15 fps)
  --thumb   shot:frame -> a JPEG still at the shot's size (YouTube thumbnail base)

Shots are joined with the concat demuxer and stream copy (no re-encode: all shots share size, rate and encoder
settings). Sound is measured, then normalised to -14 LUFS integrated, -2 dBTP (two-pass loudnorm), AAC 192 kb/s.
"""
import sys
sys.dont_write_bytecode = True
import argparse, json, os, subprocess

ENC = ['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', '30', '-video_track_timescale', '15360']


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode: raise SystemExit('ffmpeg failed: ' + ' '.join(cmd[:6]) + '...\n' + r.stderr[-1500:])
    return r


def size_of(f):
    r = run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', f])
    w, h = r.stdout.strip().split(',')[:2]; return int(w), int(h)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('shots'); ap.add_argument('--edit'); ap.add_argument('--audio')
    ap.add_argument('-o', '--out', help='default: trailer-1080p.mp4 (or -<height>p) next to the shots folder')
    ap.add_argument('--small', action='store_true'); ap.add_argument('--gif'); ap.add_argument('--thumb')
    a = ap.parse_args()
    meta = [s['name'] for s in json.load(open(os.path.join(a.shots, 'shots.json')))]
    items = json.load(open(a.edit))['timeline'] if a.edit else meta
    first = next(i for i in items if not isinstance(i, dict))
    W, H = size_of(os.path.join(a.shots, f'{first}.mp4'))
    base = os.path.dirname(os.path.abspath(a.shots.rstrip('/')))
    out = a.out or os.path.join(base, f'trailer-{H}p.mp4')
    lst = os.path.join(a.shots, 'concat.txt')
    with open(lst, 'w') as f:
        for it in items:
            if isinstance(it, dict):
                n = int(it['black']); bf = os.path.join(a.shots, f'black-{n}-{W}x{H}.mp4')
                if not os.path.exists(bf):
                    run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', f'color=c=black:s={W}x{H}:r=30', '-frames:v', str(n)] + ENC + [bf + '.part.mp4'])
                    os.replace(bf + '.part.mp4', bf)
                f.write(f"file '{os.path.abspath(bf)}'\n")
            else:
                f.write(f"file '{os.path.abspath(os.path.join(a.shots, it + '.mp4'))}'\n")
    pic = os.path.join(a.shots, 'picture.mp4')
    run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', pic + '.part.mp4']); os.replace(pic + '.part.mp4', pic)
    if a.audio:
        r = run(['ffmpeg', '-hide_banner', '-i', a.audio, '-af', 'loudnorm=I=-14:TP=-2:LRA=11:print_format=json', '-f', 'null', '-'])
        j = json.loads(r.stderr[r.stderr.rindex('{'):r.stderr.rindex('}') + 1])
        norm = os.path.join(a.shots, 'mix-norm.wav')
        run(['ffmpeg', '-v', 'error', '-y', '-i', a.audio, '-af',
             f"loudnorm=I=-14:TP=-2:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true",
             '-ar', '48000', norm])
        run(['ffmpeg', '-v', 'error', '-y', '-i', pic, '-i', norm, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out + '.part.mp4'])
    else:
        run(['ffmpeg', '-v', 'error', '-y', '-i', pic, '-c', 'copy', '-movflags', '+faststart', out + '.part.mp4'])
    os.replace(out + '.part.mp4', out)
    print(f'trailer: {out}  {os.path.getsize(out) / 1e6:.1f} MB', file=sys.stderr)
    if a.small:
        sm = os.path.join(os.path.dirname(out), 'trailer-720p.mp4')
        run(['ffmpeg', '-v', 'error', '-y', '-i', out, '-vf', 'scale=1280:-2:flags=lanczos', '-c:v', 'libx264', '-preset', 'slow', '-crf', '23', '-pix_fmt', 'yuv420p', '-c:a', 'copy', '-movflags', '+faststart', sm + '.part.mp4'])
        os.replace(sm + '.part.mp4', sm); print(f'small:   {sm}  {os.path.getsize(sm) / 1e6:.1f} MB', file=sys.stderr)
    if a.gif:
        shot, ss, dur = a.gif.split(':'); src = os.path.join(a.shots, shot + '.mp4')
        gif = os.path.join(os.path.dirname(out), f'{shot}.gif'); pal = os.path.join(a.shots, 'palette.png')
        for w, cols in ((640, 96), (560, 64), (480, 48)):   # shrink until it fits the 3 MB most store pages allow
            run(['ffmpeg', '-v', 'error', '-y', '-ss', ss, '-t', dur, '-i', src, '-vf', f'fps=15,scale={w}:-1:flags=lanczos,palettegen=max_colors={cols}:stats_mode=full', pal])
            run(['ffmpeg', '-v', 'error', '-y', '-ss', ss, '-t', dur, '-i', src, '-i', pal, '-lavfi',
                 f'fps=15,scale={w}:-1:flags=lanczos,tpad=stop_mode=clone:stop_duration=0.8[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle', '-loop', '0', gif])
            if os.path.getsize(gif) < 3e6: break
        print(f'gif:     {gif}  {os.path.getsize(gif) / 1e6:.2f} MB', file=sys.stderr)
    if a.thumb:
        shot, fr = a.thumb.split(':'); th = os.path.join(os.path.dirname(out), f'{shot}-frame{int(fr)}.jpg')
        run(['ffmpeg', '-v', 'error', '-y', '-i', os.path.join(a.shots, shot + '.mp4'), '-vf', f'select=eq(n\\,{int(fr)})', '-frames:v', '1', '-q:v', '2', th])
        print(f'thumb:   {th}', file=sys.stderr)


if __name__ == '__main__':
    main()
