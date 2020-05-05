from typing import NamedTuple
import numpy as np

class Intrinsics(NamedTuple):
    scale: float
    ppx: float
    ppy: float
    fx: float
    fy: float

class Depth(NamedTuple):
    timestamp: float
    depth: np.array
    intrin: Intrinsics

class Pose(NamedTuple):
    timestamp: float
    translation: float
    quaternion: float
    conf: int

class Color(NamedTuple):
    timestamp: float
    image: np.array
