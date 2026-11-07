/* The worked example from references/level-building.md: appended to src/05_levels.js by smoke_test.py */
LEVELS[4] = {
  name: 'The Well', sub: 'up is the only way', next: 3,
  build(L) {
    const E = L.env; E.sunDir.set(0.2, 1, 0.1); E.sun = 0.9; E.amb = 0.45; E.fogDen = 0.014; L.killU = -12;
    const WALL = { pat: PAT.ASHLAR, tone: 0.88 }, SLAB = { pat: PAT.TILES, tone: 0.9 };
    L.B(-5, -0.5, -5, 5, 0, 5, SLAB);                                                   // floor
    wallX(L, -5.5, 5.5, -5.5, -5, 0, 14, [doorHole(0, 0)], WALL); stdEntrance(L, 0, 0, -5.25, 0);
    wallX(L, -5.5, 5.5, 5, 5.5, 0, 14, [], WALL);                                       // north
    L.B(-5.5, 0, -5, -5, 14, 5, WALL);                                                  // west
    let p = stairs(L, 4.2, 0, -3.0, '+z', 12, { w: 1.6, rails: true, railSides: [-1] }); // up the east side
    L.B(3.4, p.y - 0.4, p.z, 5, p.y, 5, SLAB);
    p = stairs(L, 3.4, p.y, 4.2, '-x', 12, { w: 1.6, rails: true, railSides: [-1] });     // along the north
    L.B(-5, p.y - 0.4, 3.4, p.x, p.y, 5, SLAB);
    p = stairs(L, -4.2, p.y, 3.4, '-z', 12, { w: 1.6, rails: true, railSides: [1] });     // down the west side
    L.B(-5, p.y - 0.4, -5, -3.4, p.y, p.z, SLAB);
    p = stairs(L, -3.4, p.y, -4.2, '+x', 12, { w: 1.6, rails: true, railSides: [1] });    // along the south
    L.B(p.x, p.y - 0.4, -5, 5, p.y, -3.4, SLAB);
    wallZ(L, -5, 5, 5, 5.5, 0, 14, [doorHole(-4.2, p.y)], WALL);                          // east wall, exit at the top
    exitDoor(L, 5.25, p.y, -4.2, yawOf('+x'));
    L.light(0, 12.5, 0, 16, 0.4); lampVis(L, 0, 12.5, 0, 'bulb');
  }
};
