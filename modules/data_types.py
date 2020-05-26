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


class MapPreProcessorOut(NamedTuple):
    timestamp: float
    voxels: np.array
    count: np.array


class MapDefinition(NamedTuple):
    x_min: float
    y_min: float
    z_min: float
    x_max: float
    y_max: float
    z_max: float
    x_divisions: int
    y_divisions: int
    z_divisions: int


class ProcessHeartbeat(NamedTuple):
    timestamp: float
    process_name: str
    thread_count: int


class StartupItem(NamedTuple):
    module: str
    config_file: str
    process_name: str
