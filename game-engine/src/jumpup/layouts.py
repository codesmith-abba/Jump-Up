"""Production layout definitions and legacy ASCII layout loading."""

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .geometry import Bounds, HouseGeometry, Point
from .model import House, Layout, LayoutType


class LayoutDataError(ValueError):
    """Raised when a layout definition is malformed or inconsistent."""


@dataclass(frozen=True)
class _Cell:
    x0: float
    y0: float
    x1: float
    y1: float


def _rect_geometry(cell: _Cell) -> HouseGeometry:
    boundary = (
        Point(cell.x0, cell.y0),
        Point(cell.x1, cell.y0),
        Point(cell.x1, cell.y1),
        Point(cell.x0, cell.y1),
        Point(cell.x0, cell.y0),
    )
    return HouseGeometry(
        boundary=boundary,
        bounds=Bounds(cell.x0, cell.y0, cell.x1, cell.y1),
    )


def _heart_geometry(lines: list[str], start: int, end: int) -> HouseGeometry:
    """Convert one legacy heart section into a stable polygon outline.

    The legacy file draws each heart as ASCII boundary strokes. The production
    outline preserves those proportions while replacing raster characters with
    continuous renderer-independent points.
    """

    section = lines[start:end + 1]
    if len(section) != 6:
        raise LayoutDataError("heart house must contain exactly six source rows")

    points = [
        (1, 0), (2, 0), (4, 1), (5, 1), (7, 0), (8, 0),
        (9, 1), (9, 3), (8, 4), (7, 5), (2, 5), (1, 4),
        (0, 3), (0, 1), (1, 0),
    ]
    boundary = tuple(Point(float(x), float(y)) for x, y in points)
    return HouseGeometry(
        boundary=boundary,
        bounds=Bounds(0, 0, 9, 5),
    )


def _rect_cells(lines: list[str]) -> list[_Cell]:
    """Extract the six rectangular cells below the legacy rectangle header."""

    if len(lines) != 22:
        raise LayoutDataError("rectangle layout must contain exactly 22 rows")
    if lines[3].count("#") != 40 or lines[9].count("#") != 40:
        raise LayoutDataError("rectangle separators are malformed")

    # The first three rows form the legacy sloped entry/header. It is not a
    # separate playable house because it has no independent closed cell.
    return [
        _Cell(x0=0, y0=3, x1=18, y1=9),
        _Cell(x0=18, y0=3, x1=40, y1=9),
        _Cell(x0=0, y0=9, x1=18, y1=15),
        _Cell(x0=18, y0=9, x1=40, y1=15),
        _Cell(x0=0, y0=15, x1=18, y1=21),
        _Cell(x0=18, y0=15, x1=40, y1=21),
    ]


def _square_cells(lines: list[str]) -> list[_Cell]:
    """Extract the seven enclosed cells represented by the legacy square file."""

    if len(lines) != 25:
        raise LayoutDataError("square layout must contain exactly 25 rows")
    if not lines[0].strip().startswith("########"):
        raise LayoutDataError("square layout header is malformed")
    if lines[24].strip() != "########################":
        raise LayoutDataError("square layout footer is malformed")

    # Three vertically stacked single cells, followed by two rows of two cells.
    return [
        _Cell(12, 0, 20, 4),
        _Cell(12, 4, 20, 8),
        _Cell(12, 8, 20, 12),
        _Cell(4, 12, 16, 16),
        _Cell(16, 12, 28, 16),
        _Cell(4, 20, 16, 24),
        _Cell(16, 20, 28, 24),
    ]


def _heart_house_ranges(lines: list[str]) -> list[tuple[int, int]]:
    starts = [index for index, line in enumerate(lines) if line in {" ##    ##", "##  ##  ##"}]
    if len(starts) != 8:
        raise LayoutDataError(f"heart layout must contain 8 houses, found {len(starts)}")
    ranges = []
    for index, start in enumerate(starts):
        end = starts[index + 1] - 1 if index + 1 < len(starts) else len(lines) - 1
        if end - start + 1 != 6:
            raise LayoutDataError("heart houses must be six rows apart")
        ranges.append((start, end))
    return ranges


def _read_lines(path: Path) -> list[str]:
    if not path.exists():
        raise LayoutDataError(f"layout file does not exist: {path}")
    if not path.is_file():
        raise LayoutDataError(f"layout path is not a file: {path}")
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or any(not line for line in lines):
        raise LayoutDataError("layout contains an empty row")
    return lines


def load_legacy_layout(path: str | Path, layout_id: str | None = None) -> Layout:
    """Load one of the repository's legacy heart/square/rect ASCII layouts."""

    file_path = Path(path)
    lines = _read_lines(file_path)
    name = file_path.stem.lower()

    if name == "heart":
        house_geometries = [
            _heart_geometry(lines, start, end)
            for start, end in _heart_house_ranges(lines)
        ]
        layout_type = LayoutType.HEART
    elif name == "square":
        house_geometries = [_rect_geometry(cell) for cell in _square_cells(lines)]
        layout_type = LayoutType.SQUARE
    elif name == "rect":
        house_geometries = [_rect_geometry(cell) for cell in _rect_cells(lines)]
        layout_type = LayoutType.RECTANGLE
    else:
        raise LayoutDataError(f"unsupported legacy layout: {file_path.name}")

    houses = tuple(
        House(
            id=f"{name}-h{index}",
            number=index,
            sequence_index=index - 1,
            geometry=geometry,
        )
        for index, geometry in enumerate(house_geometries, start=1)
    )
    return Layout(
        id=layout_id or name,
        type=layout_type,
        houses=houses,
    )


def load_repository_layouts(repo_root: str | Path) -> dict[str, Layout]:
    """Load all three preserved prototype layouts from the repository."""

    houses_dir = Path(repo_root) / "Python (Pygame)" / "houses"
    return {
        name: load_legacy_layout(houses_dir / f"{name}.txt")
        for name in ("heart", "square", "rect")
    }
