#!/usr/bin/env python3
"""Robot playtest for a built pen-and-ink game: proves every level loads, every exit door leads on, and every
gravity zone flips gravity. Runs headless in a few seconds; use it after every change to levels or doors.

  python3 playtest.py dist/my-game.html            -> one line per check, exit status 1 if anything failed
  python3 playtest.py dist/my-game.html --shots    -> also saves a picture just after each crossing (dist/playtest/)

For each level i: start it, wait for the next level to build, open the exit, stand 0.8 m in front of it, hold W and
step frames until the game reports level i+1. Enemies are switched off (e.off = true) so the robot is not caught.
"""
import sys
sys.dont_write_bytecode = True
import argparse, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
from _pen_ink_common import open_game

ROUTE = r'''async (shots) => {
  const g = window.__game, G = g.GAME, out = [], pics = [];
  const quiet = () => { for (const e of G.L.ents) e.off = true; };
  const n = g.LEVELS.length - 1;
  for (let i = 1; i <= n; i++) {
    g.play(i); quiet(); g.step(36, 1 / 30, false);
    const L = G.L, r = { level: i, name: L.name, spawn: L.spawn ? L.spawn.pos.toArray().map(v => +v.toFixed(2)) : null };
    r.grounded = g.step(10).grounded;               // the spawn point stands on something
    const nxt = G.nextIdx(i);
    if (!L.exitDoor || nxt == null) { r.exit = 'none (final level)'; out.push(r); continue; }
    r.nextBuilt = !!G.next;
    g.openExit(); g.faceExit(0.8); g.hold('KeyW');
    let k = 0; while (G.idx === i && k < 120) { g.step(1, 1 / 30, false); k++; }
    g.hold('KeyW', false);
    r.crossed = G.idx === nxt; r.frames = k; r.after = g.step(20);
    if (shots) pics.push(i);
    // gravity zones of level i (checked on a fresh copy of it)
    g.play(i); quiet(); g.step(5, 1 / 30, false);
    r.zones = G.L.gravZones.map(z => {
      const b = z.box, c = new g.V3((b[0] + b[3]) / 2, (b[1] + b[4]) / 2, (b[2] + b[5]) / 2);
      g.PL.gravLock = 0; g.PL.setFrameQ(g.faceQ(z.from)); g.PL.pos.copy(c).addScaledVector(g.PL.up, -g.PL.height() / 2); g.PL.vel.set(0, 0, 0);
      g.step(3, 1 / 30, false);
      return { from: [z.from.ax, z.from.sg], to: [z.to.ax, z.to.sg], ok: g.PL.ax === z.to.ax && g.PL.sg === z.to.sg };
    });
    out.push(r);
  }
  return { out, errs: g.ERRS.slice(0, 5) };
}'''


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('html')
    ap.add_argument('--shots', action='store_true', help='save a picture after each crossing')
    a = ap.parse_args()
    fails = []
    with sync_playwright() as p:
        b, pg, errs = open_game(p, a.html, 960, 540)
        res = pg.evaluate(ROUTE, a.shots)
        if a.shots:
            d = os.path.join(os.path.dirname(os.path.abspath(a.html)), 'playtest'); os.makedirs(d, exist_ok=True)
            pg.screenshot(path=os.path.join(d, 'last.jpg'), type='jpeg', quality=90)
        b.close()
    for r in res['out']:
        line = f"level {r['level']} ({r['name']}): spawn {'on ground' if r['grounded'] else 'IN THE AIR'}"
        if not r['grounded']: fails.append(f"level {r['level']} spawn is not on the ground")
        if 'crossed' in r:
            line += f", next level {'built' if r['nextBuilt'] else 'NOT BUILT'}, exit {'crossed' if r['crossed'] else 'NOT CROSSED'} in {r['frames']} frames"
            if not r['crossed']: fails.append(f"level {r['level']}: walking through the open exit did not reach the next level (stuck at {r['after']['pos']})")
            if not r['nextBuilt']: fails.append(f"level {r['level']}: the next level was not built 1.2 s after start")
        else:
            line += ', ' + r['exit']
        for z in r.get('zones', []):
            line += f", gravity zone {z['from']}->{z['to']} {'ok' if z['ok'] else 'FAILED'}"
            if not z['ok']: fails.append(f"level {r['level']}: gravity zone {z['from']}->{z['to']} did not switch gravity")
        print(line, file=sys.stderr)
    errs += [f'game: {e}' for e in res['errs']]
    for e in dict.fromkeys(errs): fails.append(e)
    if fails:
        print('FAILED:\n  ' + '\n  '.join(fails), file=sys.stderr); sys.exit(1)
    print('playtest passed', file=sys.stderr)


if __name__ == '__main__':
    main()
