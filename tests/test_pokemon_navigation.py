import math
import random

from pixel_ops.plugins.pokemon.game.navigation import WanderNavigator


def test_wandering_crosses_joined_rectangles_without_entering_obstacle():
    nav = WanderNavigator((0, 0, 180, 160), [(0, 0, 90, 160), (90, 0, 180, 160)],
                          [(75, 45, 105, 115)], (32, 40), random.Random(42))
    nav.place(10, 40)
    previous = nav.position
    visited = []
    pauses = 0
    for frame in range(1000):
        pose = nav.pose(frame, 10, 2.1)
        assert nav.pose(frame, 10, 2.1) == pose  # Dirty-region queries cannot advance movement.
        x, y = nav.position
        assert math.dist(previous, nav.position) <= 2.10001
        assert not (70 < x < 110 and 42 < y < 118)
        visited.append(x)
        pauses += not nav.moving
        previous = nav.position
    assert min(visited) < 60 and max(visited) > 120
    assert pauses > 0


def test_routes_stay_on_the_connected_island_and_pause_when_disabled():
    nav = WanderNavigator((0, 0, 200, 100), [(0, 0, 70, 100), (100, 0, 200, 100)],
                          [], (32, 40), random.Random(2))
    nav.place(20, 20)
    for frame in range(300):
        nav.pose(frame, 10, 3)
        assert nav.position[0] < 70
    before = nav.position
    nav.pose(301, 10, 3, enabled=False)
    assert nav.position == before
    assert not nav.moving


def test_feet_can_follow_a_narrow_corridor_with_body_above_it():
    nav = WanderNavigator((0, 0, 180, 120), [(0, 60, 180, 76)], [], (32, 40), random.Random(7))
    nav.place(20, 30)
    assert len(nav.nodes) > 20
    for frame in range(150):
        _, y, _ = nav.pose(frame, 10, 2)
        assert 60 <= nav.position[1] - 3 and nav.position[1] + 3 <= 76
        assert y < 60


def test_zoomed_scene_uses_native_sprite_scale_and_stays_put_for_encounters():
    from pathlib import Path
    from pixel_ops.plugins.pokemon.game.map_routes import MapArea
    from pixel_ops.plugins.pokemon.game.state_machine import GamePhase
    from pixel_ops.plugins.pokemon.scenes.overworld_scene import OverworldScene
    scene = OverworldScene(600, 300, 'UTC', scanlines=False, lazy_download=False,
                           game_config={'movement': {'walkable': {'source_rects': [
                               {'map': 'test', 'x': 0, 'y': 0, 'w': 600, 'h': 150}
                           ]}}}, display_layout={'game': {'x': 0, 'y': 0, 'width': 600, 'height': 150, 'camera_zoom': 3}})
    scene.current_map_area = MapArea('test', Path('test.png'), 'test', (0, 0, 600, 150), (0, 0, 600, 150), ())
    sprite, x, y, _ = scene._sprite_layers(GamePhase.WALKING)[-1]
    assert sprite.size == (16, 20)
    scene.frame += 1
    _, stopped_x, stopped_y, _ = scene._sprite_layers(GamePhase.ENCOUNTER_START)[0]
    assert (stopped_x, stopped_y) == (x, y)
    assert not scene._ash_is_moving
