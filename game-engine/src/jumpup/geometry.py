"""Renderer-independent geometry primitives for Jump-Up layouts."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Point:
    x: float
    y: float


@dataclass(frozen=True)
class Bounds:
    min_x: float
    min_y: float
    max_x: float
    max_y: float

    def __post_init__(self) -> None:
        if self.max_x <= self.min_x or self.max_y <= self.min_y:
            raise ValueError("bounds must have positive width and height")

    @property
    def width(self) -> float:
        return self.max_x - self.min_x

    @property
    def height(self) -> float:
        return self.max_y - self.min_y

    @property
    def center(self) -> Point:
        return Point(
            x=(self.min_x + self.max_x) / 2,
            y=(self.min_y + self.max_y) / 2,
        )


@dataclass(frozen=True)
class HouseGeometry:
    """A renderer-independent closed outline plus derived bounding geometry."""

    boundary: tuple[Point, ...]
    bounds: Bounds

    def __post_init__(self) -> None:
        if len(self.boundary) < 3:
            raise ValueError("house boundary must contain at least three points")
        if self.boundary[0] != self.boundary[-1]:
            raise ValueError("house boundary must be closed")
        if any(
            point.x < self.bounds.min_x
            or point.x > self.bounds.max_x
            or point.y < self.bounds.min_y
            or point.y > self.bounds.max_y
            for point in self.boundary
        ):
            raise ValueError("house boundary points must lie within bounds")

    @property
    def center(self) -> Point:
        return self.bounds.center

    @property
    def width(self) -> float:
        return self.bounds.width

    @property
    def height(self) -> float:
        return self.bounds.height
