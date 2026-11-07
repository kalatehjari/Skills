# Controls, HUD and menus

## Default controls

| Action | Keyboard + mouse | Touch | Gamepad (standard mapping) |
|---|---|---|---|
| move / look | WASD or arrows / mouse (pointer lock), or drag | left thumb anywhere on the left half (floating joystick) / drag on the right half | left stick / right stick |
| run | Shift | push the stick to the rim | left stick click |
| jump | Space | jump button | A |
| open, use | E or Enter | open button | X |
| crouch | C or Ctrl | duck button | B |
| lamp | F | (add a button) | LT |
| pause | Esc or P | pause button (top right); switching apps pauses too | Start |

Clicking the game requests pointer lock; pressing Esc releases it, which pauses the game (browsers reserve
Esc for that). Without pointer lock, dragging with the left button looks around. Touch controls appear only
after the player has touched the screen (`IN.usedTouch`), so desktop players never see them.

## Adding an action

1. Keyboard: add the key to the `KE` map in `IN.init` (`KeyQ: 'focus'`).
2. Touch: add `<div class="tb" id="tFocus">focus</div>` inside `#touch` in `00_head.html`, position it with
   CSS like `#tAct`, and add `tFocus: 'focus'` to the `btns` map in `IN.init`.
3. Gamepad: add the button index to `map` in `IN.pollPad` (`3: 'focus'` is Y).
4. Game: `if (IN.take('focus')) { ... }` in `GAME.update` (an edge: true once per press). For held actions
   read `IN.keys.KeyQ` (keyboard), keep a flag set in the touch start/end handlers, and read the pad button.

## HUD

`#xh` (crosshair dot), `#prompt` (the "Open" line under it, set by `UI.prompt(label)` from the interaction
check), `#toast` (`GAME.toast(text, seconds)`: level cards, hints, notes). Keep the HUD this sparse: the
drawing is the interface, and text over hatching is hard to read without the paper-coloured halo the CSS adds.

## Screens and a settings menu

Screens are `<section class="screen">` elements; `UI.show(id)` shows one and hides the rest, `UI.show(null)`
hides all. To add settings: a section with sliders and toggles, a button on the title and pause screens that
calls `UI.show('settings')`, and handlers that write `SET`, then apply and save:

```js
$('sens').oninput = e => { SET.sens = +e.target.value; saveSet(); };
$('qual').onchange = e => { SET.quality = +e.target.value; R.applyQuality(); saveSet(); };
$('vol').oninput = e => { SET.vol = +e.target.value; AU.applyVol(); saveSet(); };
$('calm').onchange = e => { SET.calm = e.target.checked ? 1 : 0; saveSet(); };
```

`SET` already holds `sens`, `invert`, `fov`, `quality`, `vol`, `mus` and `calm`, loaded from `Store` at start.

## Phones and tablets

- Touch devices start at quality 0 (lower pixel ratio, no MSAA); this matters more than anything else for
  frame rate. Test at a phone landscape size: `shoot.py --size 844x390 --quality 0`.
- Lay buttons out for right thumbs at the bottom-right corner, at least 60 px across, and keep the left half
  free for the joystick. `env(safe-area-inset-*)` variables keep them clear of notches.
- Phones in portrait: the game still runs, but suggest landscape on the title screen if your layout needs it.

## Accessibility that costs little

- `SET.calm`: softer boil, warp, swirl, wave and camera shake, for motion sensitivity.
- No flashing faster than three times a second; `GAME.flash` is a single decaying flash.
- Invert look, sensitivity and field of view in settings.
- Important sounds deserve a caption: show it with `GAME.toast('[two knocks behind you]')`.
- Every action reachable from keyboard alone, touch alone and gamepad alone.
