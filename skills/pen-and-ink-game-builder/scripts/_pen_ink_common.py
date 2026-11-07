"""Shared helpers for the pen-and-ink-game-builder scripts (imported from the scripts' own folder)."""
import sys
sys.dont_write_bytecode = True
import os

GL_ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']


def open_game(p, html, w, h, quality=1):
    b = p.chromium.launch(headless=True, args=GL_ARGS)
    pg = b.new_page(viewport={'width': w, 'height': h})
    pg.set_default_timeout(180000)
    errs = []
    pg.on('pageerror', lambda e: errs.append('pageerror: ' + str(e)))
    pg.on('console', lambda m: m.type == 'error' and errs.append('console: ' + m.text[:400]))
    # no animation loop: the script steps the game itself, so every run renders the same frames
    pg.add_init_script('window.requestAnimationFrame = () => 0;')
    pg.add_init_script(f"try {{ for (const k in localStorage) if (k.endsWith('_set')) localStorage.removeItem(k); }} catch (e) {{}}")
    pg.goto('file://' + os.path.abspath(html))
    pg.wait_for_function('window.__game', polling=200, timeout=60000)
    pg.evaluate(f'() => {{ const g = window.__game; g.SET.quality = {quality}; g.R.applyQuality(); }}')
    pg.wait_for_function('!document.getElementById("loading")', polling=200, timeout=10000)  # the cover fades out after ~1 s
    return b, pg, errs


END = '\n})();\n</script>\n</body>\n</html>\n'
HOOK = '\nwindow.__ev = s => eval(s); // promo build only'


def promo_copy(html):
    s = open(html, encoding='utf-8').read()
    if 'window.__ev' in s:
        return html
    if not s.endswith(END):
        raise SystemExit('this html was not made by build_html.py; rebuild it with: build_html.py <game> --promo')
    import tempfile  # keep the eval hook out of dist/, the folder you ship
    out = os.path.join(tempfile.gettempdir(), os.path.basename(html)[:-5] + '-promo.html')
    open(out, 'w', encoding='utf-8').write(s[:-len(END)] + HOOK + END)
    return out
