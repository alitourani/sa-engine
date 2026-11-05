"""Real-time 3D Scene Visualizer for SA-Engine (RViz-like streaming)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import numpy as np

# Ensure X11 backend for GDK on Linux to avoid GNOME/Wayland antialiasing schema crash
os.environ.setdefault("GDK_BACKEND", "x11")

try:
    import rerun as rr
except ImportError:
    rr = None

try:
    import open3d as o3d
except ImportError:
    o3d = None


class SceneVisualizer:
    """General real-time 3D visualizer that updates dynamically with each processed frame."""

    def __init__(
        self,
        backend: str = "rerun",
        app_name: str = "SA-Engine",
        voxel_downsample: float | None = 0.02,
        spawn: bool = True,
    ):
        self.backend = backend.lower()
        self.app_name = app_name
        self.voxel_downsample = float(voxel_downsample) if voxel_downsample else None
        self.spawn = spawn

        # Accumulated scene state
        self.accumulated_pcd = None
        self._open3d_vis = None
        self._is_first_frame = True

        self._init_backend()

    @staticmethod
    def has_display() -> bool:
        """Check if an active graphical display socket is accessible."""
        wayland = os.environ.get("WAYLAND_DISPLAY")
        runtime_dir = os.environ.get("XDG_RUNTIME_DIR", "")
        if wayland and runtime_dir and Path(runtime_dir, wayland).exists():
            return True
        x11 = os.environ.get("DISPLAY")
        if x11:
            disp_num = x11.lstrip(":").split(".")[0]
            if Path(f"/tmp/.X11-unix/X{disp_num}").exists():
                return True
        return False

    def _init_backend(self):
        if self.backend == "rerun":
            if rr is None:
                raise ImportError(
                    "rerun-sdk is required for the Rerun visualizer. "
                    "Install with: pip install rerun-sdk"
                )
            spawn_viewer = self.spawn and self.has_display()
            print(f"- Initializing Rerun visualizer (spawn={spawn_viewer}) ...")
            rr.init(self.app_name, spawn=spawn_viewer)
            if not spawn_viewer:
                print(
                    "- [INFO] No graphical display detected. Rerun recording without spawning GUI.\n"
                    "  Run SA-Engine directly from your desktop terminal to view live in the native Rerun window."
                )

        elif self.backend == "open3d":
            if o3d is None:
                raise ImportError(
                    "Open3D is required for Open3D visualizer. "
                    "Install with: pip install open3d"
                )
            self.accumulated_pcd = o3d.geometry.PointCloud()
            if self.has_display():
                print("- Initializing Open3D live visualizer window ...")
                self._open3d_vis = o3d.visualization.Visualizer()
                self._open3d_vis.create_window(
                    window_name=f"{self.app_name} Live 3D Visualizer",
                    width=1280,
                    height=720,
                )
            else:
                print("- [INFO] No graphical display detected. Open3D running headless.")

    @classmethod
    def from_config(cls, cfg: Any) -> SceneVisualizer:
        """Initialize SceneVisualizer using parameters from config.yaml."""
        vis_cfg = getattr(cfg, "visualization", {})
        enabled = getattr(vis_cfg, "enabled", True)
        if not enabled:
            return cls(backend="none")

        backend = getattr(vis_cfg, "backend", "rerun")
        app_name = getattr(vis_cfg, "app_name", "SA-Engine")
        voxel_downsample = getattr(vis_cfg, "voxel_downsample", 0.02)
        spawn = getattr(vis_cfg, "spawn", True)

        return cls(
            backend=backend,
            app_name=app_name,
            voxel_downsample=voxel_downsample,
            spawn=spawn,
        )

    def update(
        self,
        frame_idx: int,
        rgb: np.ndarray,
        depth: np.ndarray | None = None,
        points: np.ndarray | None = None,
        colors: np.ndarray | None = None,
        timestamp: float | None = None,
    ):
        """Add each frame's reconstruction to the visualizer in real time."""
        if self.backend == "none":
            return

        # ----------------------------------------------------------------------
        # Backend 1: Rerun (RViz-like Multimodal Visualizer)
        # ----------------------------------------------------------------------
        if self.backend == "rerun" and rr is not None:
            rr.set_time("frame_idx", sequence=frame_idx)
            if timestamp is not None:
                rr.set_time("time_sec", duration=float(timestamp))

            # Stream camera inputs
            if rgb is not None:
                rr.log("camera/rgb", rr.Image(rgb))
            if depth is not None:
                rr.log("camera/depth", rr.DepthImage(depth))

            # Stream current frame 3D point cloud
            if points is not None and len(points) > 0:
                cols = (
                    colors
                    if colors is not None
                    else np.full_like(points, 200, dtype=np.uint8)
                )
                rr.log(
                    "world/current_frame_pcd",
                    rr.Points3D(positions=points, colors=cols),
                )

                # Accumulate points into combined scene
                if o3d is not None:
                    new_pcd = o3d.geometry.PointCloud()
                    new_pcd.points = o3d.utility.Vector3dVector(
                        points.astype(np.float64)
                    )
                    new_pcd.colors = o3d.utility.Vector3dVector(
                        (cols / 255.0).astype(np.float64)
                    )
                    if self.accumulated_pcd is None:
                        self.accumulated_pcd = new_pcd
                    else:
                        self.accumulated_pcd += new_pcd

                    if (
                        self.voxel_downsample
                        and len(self.accumulated_pcd.points) > 0
                    ):
                        self.accumulated_pcd = self.accumulated_pcd.voxel_down_sample(
                            self.voxel_downsample
                        )

                    acc_pts = np.asarray(self.accumulated_pcd.points)
                    acc_cols = (
                        np.asarray(self.accumulated_pcd.colors) * 255.0
                    ).astype(np.uint8)
                    rr.log(
                        "world/accumulated_scene_pcd",
                        rr.Points3D(positions=acc_pts, colors=acc_cols),
                    )

        # ----------------------------------------------------------------------
        # Backend 2: Open3D Live Window
        # ----------------------------------------------------------------------
        elif self.backend == "open3d" and o3d is not None:
            if points is not None and len(points) > 0:
                cols = (
                    colors
                    if colors is not None
                    else np.full_like(points, 200, dtype=np.uint8)
                )
                new_pcd = o3d.geometry.PointCloud()
                new_pcd.points = o3d.utility.Vector3dVector(points.astype(np.float64))
                new_pcd.colors = o3d.utility.Vector3dVector(
                    (cols / 255.0).astype(np.float64)
                )

                if self.accumulated_pcd is None:
                    self.accumulated_pcd = new_pcd
                else:
                    self.accumulated_pcd += new_pcd

                if self.voxel_downsample and len(self.accumulated_pcd.points) > 0:
                    self.accumulated_pcd = self.accumulated_pcd.voxel_down_sample(
                        self.voxel_downsample
                    )

                if self._open3d_vis is not None:
                    if self._is_first_frame:
                        self._open3d_vis.add_geometry(self.accumulated_pcd)
                        self._is_first_frame = False
                    else:
                        self._open3d_vis.update_geometry(self.accumulated_pcd)

                    self._open3d_vis.poll_events()
                    self._open3d_vis.update_renderer()

    def get_accumulated_pointcloud(self):
        """Return the complete accumulated Open3D PointCloud."""
        return self.accumulated_pcd

    def close(self):
        """Clean up visualizer resources."""
        if self._open3d_vis is not None:
            try:
                self._open3d_vis.destroy_window()
            except Exception:
                pass
            self._open3d_vis = None

