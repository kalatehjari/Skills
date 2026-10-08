---
name: vinyl-groove-visualiser
description: Render a music visualiser where the camera flies through the grooves of a spinning vinyl record and the groove walls are carved by the user's song — stereo walls, bass waves, vocal light-lanes, hi-hat glints, kick-synced light rings, section-based colours. Use whenever the user wants a vinyl / record / groove / turntable / needle visualiser, a "camera inside the record" video, or an abstract text-free beat-synced video for their song, even if they only say "do the vinyl thing for this song".
---

# Vinyl Groove Visualiser

The camera travels down the V-shaped groove of a record while the song plays. Everything on screen is driven by the actual audio, so each song yields different grooves:

| Sound | What it does to the groove |
|---|---|
| Left / right channel | Each wall follows its own channel (like a real 45/45 stereo cut) |
| Bass | Big slow wall swings, wall brightness "breathing", light rings that reach the camera exactly on each kick (ring size = kick strength) |
| Mids (voice, synths) | Two etched lanes per wall glow with that channel's mids |
| Highs (hats, shakers) | Glints scattered on the walls, dust and stars twinkle |
| Snares | Side light flash + tiny camera jolt |
| Loudness | Groove widens and deepens when loud |
| Song sections | Palette, travel speed and camera energy change; breakdowns lift out to hover over the spinning record, then dive back in on the drop |

The top-down record has the whole song cut into its spiral (quiet passages read as smoother bands) and the dive point moves inward with time like a real needle. The label carries no text.

Default: **no on-screen text or lyrics**. This user wanted the image to carry everything; only add text if explicitly asked.

## Files

- `scripts/analyze.py` — song analysis (stereo band envelopes, beats, snares, sections) + suggested `sections.json` + `structure.png`
- `scripts/render.py` — the renderer (stills or video segments)
- `scripts/make_video.sh` — resumable segmented render, mux with the song, <30 MB preview

If these files are not next to this SKILL.md, fetch them from Dropbox `/Claude Products/Skills/vinyl-groove-visualiser/scripts/`.

## Workflow

1. **Set up.** `pip install librosa --break-system-packages`. Copy the song into a work dir. If no song is attached, ask for one, or for a quick demo synthesize a short placeholder loop and say so.

2. **Analyse.** `python3 scripts/analyze.py song.mp3 work/` prints tempo, beat count and section bounds, and writes `analysis.npz`, `structure.png` and a suggested `sections.json`. **Read `structure.png`.** Big flat gaps in the bass row are breakdowns; dense bass after a gap is a drop.

3. **Direct the edit list.** Edit `work/sections.json` → `"sections": [[start, end, mode, palette, speed, energy], ...]`.
   - `mode`: `rec` = top-down record (first = zoom-in dive, last = pull-out ending, middle = lift out, hover and dive back in); `grv` = inside the groove.
   - Palettes: `indigo, violet, amber, emerald, ice, gold, crimson`, or add your own under `"palettes": {"name": [[glow rgb], [side rgb], [fog rgb]]}` (0-1 floats).
   - `speed` (units/s): 3 = drifting break, 6 = verse, 9-11 = drop. `energy` 0-1 drives sway/roll/curvature.
   - Good shape: intro `rec` until the beat enters; build sections cool colours; each drop a new warm/saturated palette and the fastest speed; breakdowns longer than ~5 s as `rec` in `ice`/`violet`; outro `rec` for the last ~10-15 s. Very short breaks (<5 s) work better as `grv` with speed 3 and `ice`. Place cuts on the analysed bounds and nudge them onto the nearest beat if needed.
   - Tell the user the plan in 2-3 lines (sections → palettes), then proceed without waiting.
   - Optional `"size": [1920, 1080]` for 1080p (≈2.3× slower).

4. **Check stills before the long render.** `python3 scripts/render.py work stills 4 20 ...` (one or two per section, including a drop and a `rec` break), combine into a grid with PIL, and look. Check: walls not crossing, glints small (not big squares), tonearm only in the wide record view, palette distinct per section.

5. **Render detached** (the tool harness kills long foreground jobs):
   ```bash
   setsid nohup sh scripts/make_video.sh $PWD/scripts $PWD/work $PWD/song.mp3 "<Artist> - <Title> (Vinyl Groove Visualiser)" > work/out/render.log 2>&1 < /dev/null & disown
   ```
   Speed on a 2-core sandbox at 720p ≈ 1 frame/s → a 5-min song ≈ 2.5 h. Tell the user the estimate. Poll with `sleep 590; tail -1 work/out/render.log`. Segments are resumable: if it dies, re-run the same command and finished segments are skipped. `work/out/all.done` marks completion.

6. **Deliver.** Copy `preview.mp4` (bitrate-capped under 30 MB) to `/mnt/user-data/outputs/` with a simple filename (no parentheses or commas, which break SendUserFile) and send it. Copy the full-quality master there too. Sample 8 frames from the preview into a contact sheet and look at it before announcing.

7. **Report** in 2-3 short paragraphs: how sounds map to the grooves, the section/palette arc with timestamps, honest limits (sync is measured not listened, long stretches share the V framing), and one next step (1080p, more camera variety, a 9:16 cut).
