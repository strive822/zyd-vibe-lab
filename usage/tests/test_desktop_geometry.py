from usage_app.desktop_geometry import Monitor, Placement, Rect, capture_placement, exterior_edge, nearest_dock, placement_data, placement_from_data


def test_shared_seam_is_blocked_only_in_the_touching_segment():
    a = Monitor("a", Rect(0, 0, 1920, 1080), Rect(0, 0, 1920, 1040))
    b = Monitor("b", Rect(1920, 200, 1280, 720), Rect(1920, 200, 1280, 680))
    assert not exterior_edge(a, "right", 500, (a, b))
    assert exterior_edge(a, "right", 60, (a, b))
    assert exterior_edge(a, "left", 500, (a, b))
    assert nearest_dock(a, (a, b), 1620, 400, 300, 260, 100, 0) is None
    assert nearest_dock(a, (a, b), 1620, 0, 300, 260, 100, 0) == "right"


def test_negative_monitor_and_taskbar_boundary():
    monitor = Monitor("left", Rect(-1600, -300, 1600, 900), Rect(-1560, -300, 1560, 860))
    other = Monitor("primary", Rect(0, 0, 1920, 1080), Rect(0, 0, 1920, 1040))
    assert nearest_dock(monitor, (monitor, other), -10, 0, 300, 260, 100, 0) is None
    assert nearest_dock(monitor, (monitor, other), -1560, -50, 300, 260, -100, 0) == "left"
    assert monitor.work.clamp(-9999, 9999, 300, 260) == (-1560, 300)


def test_corner_uses_drag_intent_and_position_scales_with_work_area():
    monitor = Monitor("p", Rect(0, 0, 1920, 1080), Rect(0, 0, 1920, 1040))
    assert nearest_dock(monitor, (monitor,), 0, 0, 300, 260, -100, -10) == "left"
    assert nearest_dock(monitor, (monitor,), 0, 0, 300, 260, -10, -100) == "top"
    value = capture_placement(monitor, 810, 0, 300, 300, "top", True, "top")
    assert placement_from_data(placement_data(value)) == value
    smaller = Monitor("p", Rect(0, 0, 1280, 720), Rect(0, 0, 1280, 680))
    assert value.position(smaller, 300, 300) == (490, 0)
    free = Placement("p", None, floating_x_ratio=1, floating_y_ratio=1, free_orientation="bottom")
    assert free.position(smaller, 300, 300) == (980, 380)


def test_small_work_area_still_has_a_visible_origin():
    monitor = Monitor("tiny", Rect(0, 0, 240, 200), Rect(0, 0, 240, 160))
    assert Placement("tiny", "right").position(monitor, 300, 260) == (0, 0)


def test_mixed_dpi_logical_gap_does_not_turn_physical_seam_into_outer_edge():
    # Qt on Windows scales each size but can retain native screen positions.
    scaled = Monitor("150", Rect(0, 0, 1280, 720), Rect(0, 0, 1280, 680), Rect(0, 0, 1920, 1080))
    native = Monitor("100", Rect(1920, 0, 1920, 1080), Rect(1920, 0, 1920, 1040), Rect(1920, 0, 1920, 1080))
    assert not exterior_edge(scaled, "right", 400, (scaled, native))
    assert not exterior_edge(native, "left", 600, (scaled, native))
    assert exterior_edge(scaled, "left", 400, (scaled, native))
