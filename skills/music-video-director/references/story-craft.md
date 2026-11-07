# Story craft for a song film

## Contents
1. From lyrics to one central metaphor
2. Mapping the arc onto the song's sections
3. Shot vocabulary that works with the cast rig
4. Worked example: Tan Be Tan (Rosha)

## 1. From lyrics to one central metaphor

Translate every line first (keep a Persian→English table; the English goes under the Persian on screen).
Then ask: what is the *conflict*, and what *changes* by the last verse? Find one physical image that can
carry both. Good metaphors are objects the character can act on:

- control → marionette strings (she can be jerked by them, then cut or seize them)
- emptiness → desert, sand running out of a hand
- aggression → a war drum whose beats the picture literally hits
- a threshold / new life → a freestanding door with a key

Each metaphor gets introduced, intensified, and resolved. If an image appears only once it is decoration;
if it returns transformed (spears that later bloom, the same desert now sprouting) it is story.

Avoid literalising every line. One strong visual per 4-bar lyric line is plenty; the chorus can repeat
its visual language with an escalation.

## 2. Mapping the arc onto the song

Use the section map (from `song_info.py` + `render.js analyze`). A typical 3-5 minute song:

| section | job in the story |
|---|---|
| intro | world + longing; title card; one mystery (a sound behind a door) |
| verse 1 | the wound, shown small and lonely (wide shots, tiny figure) |
| pre/bridge | the antagonist arrives; the mechanism of control is revealed |
| chorus 1 | the siege: closest, most claustrophobic shots, cut on beats |
| instrumental / solo | the break: a physical act of rupture (strings snap on the first downbeat), weather |
| build | percussion = one cut per beat |
| verse / bridge 2 | the same imagery, transformed by what she learned |
| chorus 2 | the siege returns and fails; she reverses the power |
| outro | the walk away; the threshold; quiet end card with the key line |

Put the biggest visual hit on the first downbeat of the solo or final chorus. Keep the lyric overlay
off the busiest frames (bottom gradient band, 2-line Persian + English).

## 3. Shot vocabulary (all available in cast.js / film-skeleton.js)

- **Face close-up** `R.face` with eyes/brows/mouth/tears/wet/wind/tint; `reflect` paints into the irises
  (a figure, a sprout) for eye ECUs (`cam(ctx, 3.4, W/2, 452)`).
- **Profile two-shot** `R.profile` facing the antagonist's dark profile; a prop between them.
- **Silhouette wide** `R.body(... silhouette: true)` on dunes against a big sun: cheapest way to look cinematic.
- **Marionette** body with `pose: 'custom'` joint angles that change per beat + `strings()` to a control bar.
- **Grasping hands** `R.arm` from frame edges, each landing on a successive beat (`siegeFace`).
- **Per-beat montage** `drumShot`: rotate 3 framings on every beat with a flash.
- **Mirror** two bodies, one dark, one glowing (`shadowBlur`), palms meeting.
- **Transform pass**: re-use an earlier set with a new palette (`desert(...,'dawn')`) and growth (`sprout`).
- **Door** `R.door` with `keyTurn` and `open` (light floods out).

Palettes in `desert()`: day, dusk, blood, night, dawn, storm, gold. Weather: `sandWind`, `rain`,
`embers`, `lightning`. Backdrops: `hallway`, `corridorSide`, `redVoid`, `proscenium`.

## 4. Worked example: Tan Be Tan (Rosha, 293 s, 130 BPM)

Lyrics theme: "I am emptied of your love, a desert… you beat the war drum… I have made peace with myself,
do not set fire to my soul." Metaphor: a marionette who cuts her own strings.

| bars | section | shots |
|---|---|---|
| 0-10 | intro | ink-drop title; she hugs her knees in a night hallway; looks up at the door light |
| 10-18 | hook | red light + feet shadow under the door; her face flinching on beats; walks to the door, turns the key, white-out |
| 18-34 | verse 1 | tiny figure crossing dunes; walk past dead tree, footprints fill; kneels, sand pours from hand; face in sandstorm; pull back over spear field |
| 34-50 | bridge | he rises from the dunes (eyes ignite); profile face-off with dagger; puppet theatre; red war-plan arrows close on her |
| 50-66 | chorus 1 | 8 hands land on 8 beats; marionette jerked per beat against pale sun; his figure in her iris; body-to-body duel, poses snap per beat |
| 66-79 | solo | strings snap + lightning on the downbeat; running in rain; wet face, eyes open; arms open to the storm |
| 79-83 | build | drum skin / him drumming / her flinch, one cut per beat |
| 83-99 | verse 3 | his drum's shockwaves pass her and she does not move; palms raised; mirror self, palms touch on "peace with myself"; fire bends around her |
| 99-115 | bridge 2 | same desert at dawn, sprouts in her footprints; smiling close-up with petals; spears bloom |
| 115-131 | chorus 2 | hands return, she opens her eyes, hands crumble to sand; she pulls the strings and drags him down; sprout in her iris; she disarms him |
| 131-137 | build 2 | drum cuts again, skin cracks, tears on the last beat |
| 137-157 | outro | he kneels by the broken drum as she walks off; looking back; the door in the dunes; key, light, white-out; end card |

Full code: `example-film-tan-be-tan.js` and `example-score-tan-be-tan.js`.

## 5. Style modes

Two looks are proven on the same score and story:

- **Narrative** (`example-film-tan-be-tan.js` + `assets/cast.js`): a drawn heroine with expressions, silhouettes on dunes, dramatic light. Best when the user wants the character recognisable and the story literal.
- **Cubist / avant-garde** (`example-film-cubist.js`, self-contained, no cast.js): the heroine as planes (frontal and profile at once, Picasso-style simultaneity), the antagonist as a black wedge with a red eye (El Lissitzky), the drum and sun as Delaunay discs, Kandinsky bursts on the solo downbeat, analytic facet backgrounds per palette (night, desert, blood, storm, ember, dawn, gold, white), lyrics on a Constructivist paper strip. Emotion lives in the geometry: the face *splits apart* in the desert, *shatters per beat and grows extra eyes* in the siege, *reassembles* when she makes peace, and the two halves (dark and light) slide into one face on "من صلح کردم با خودم". Choose this when the user asks for artistic, conceptual, abstract, cubist, avant-garde or "not the exact person".

To build a new style, keep score.js and the shot timing and swap only the drawing layer; the story arc survives the change of look.
