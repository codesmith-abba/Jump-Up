from pathlib import Path

import pytest

from jumpup.geometry import Bounds, HouseGeometry, Point
from jumpup.layouts import LayoutDataError, load_legacy_layout

REPO_ROOT = Path(__file__).resolve().parents[2]


def layout_path(name: str) -> Path:
    return REPO_ROOT / "Python (Pygame)" / "houses" / f"{name}.txt"


def test_heart_preserves_eight_individual_houses() -> None:
    layout = load_legacy_layout(layout_path("heart"))

    assert layout.id == "heart"
    assert layout.type.value == "heart"
    assert len(layout.houses) == 8
    assert [house.number for house in layout.houses] == list(range(1, 9))
    assert [house.id for house in layout.houses] == [f"heart-h{i}" for i in range(1, 9)]


def test_square_splits_marker_sections_into_seven_playable_houses() -> None:
    layout = load_legacy_layout(layout_path("square"))

    assert len(layout.houses) == 7
    assert [house.sequence_index for house in layout.houses] == list(range(7))
    assert layout.houses[0].geometry.bounds == Bounds(12, 0, 19, 4)
    assert layout.houses[3].geometry.bounds == Bounds(4, 12, 16, 16)


def test_rectangle_splits_grid_into_six_playable_houses() -> None:
    layout = load_legacy_layout(layout_path("rect"))

    assert len(layout.houses) == 6
    assert layout.houses[0].geometry.bounds == Bounds(0, 3, 19, 9)
    assert layout.houses[-1].geometry.bounds == Bounds(19, 15, 39, 21)


def test_geometry_contains_closed_boundary_and_derived_dimensions() -> None:
    layout = load_legacy_layout(layout_path("heart"))
    geometry = layout.houses[0].geometry

    assert geometry.boundary[0] == geometry.boundary[-1]
    assert geometry.width == 9
    assert geometry.height == 5
    assert geometry.center == Point(4.5, 2.5)
    assert geometry.bounds.center == Point(4.5, 2.5)


@pytest.mark.parametrize("name", ["heart", "square", "rect"])
def test_layout_house_ids_are_stable_and_ordered(name: str) -> None:
    layout = load_legacy_layout(layout_path(name))

    assert [house.number for house in layout.houses] == list(range(1, len(layout.houses) + 1))
    assert [house.sequence_index for house in layout.houses] == list(range(len(layout.houses)))


def test_invalid_geometry_is_rejected() -> None:
    with pytest.raises(ValueError):
        HouseGeometry(
            boundary=(Point(0, 0), Point(1, 0), Point(0, 0)),
            bounds=Bounds(0, 0, 1, 1),
        )


def test_geometry_outside_bounds_is_rejected() -> None:
    with pytest.raises(ValueError):
        HouseGeometry(
            boundary=(Point(0, 0), Point(2, 0), Point(2, 1), Point(0, 0)),
            bounds=Bounds(0, 0, 1, 1),
        )


def test_malformed_layout_is_rejected(tmp_path: Path) -> None:
    malformed = tmp_path / "square.txt"
    malformed.write_text("########\n", encoding="utf-8")

    with pytest.raises(LayoutDataError):
        load_legacy_layout(malformed)


def test_unknown_layout_is_rejected(tmp_path: Path) -> None:
    unknown = tmp_path / "triangle.txt"
    unknown.write_text("###\n###\n", encoding="utf-8")

    with pytest.raises(LayoutDataError):
        load_legacy_layout(unknown)


@pytest.mark.parametrize("name", ["heart", "square", "rect"])
def test_layouts_have_valid_strict_centers(name: str) -> None:
    from jumpup.physics import point_inside_strict

    layout = load_legacy_layout(layout_path(name))
    for house in layout.houses:
        assert point_inside_strict(house.geometry.center, house.geometry)


def test_layout_loading_is_deterministic() -> None:
    for name in ("heart", "square", "rect"):
        first = load_legacy_layout(layout_path(name))
        second = load_legacy_layout(layout_path(name))
        assert first == second
        assert first.houses == second.houses
