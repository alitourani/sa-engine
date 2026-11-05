"""Monocular Depth Estimation and 3D Reconstruction using HuggingFace & OpenCV."""

from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image

try:
    import open3d as o3d
    import torch
    from transformers import pipeline
except ImportError:
    o3d = None
    torch = None
    pipeline = None


class DepthReconstructor:
    """Estimates depth from RGB frames and unprojects them into 3D point clouds."""

    def __init__(
        self,
        model_name: str = "depth-anything/Depth-Anything-V2-Small-hf",
        device: str | None = None,
        intrinsics: dict | None = None,
    ):
        if pipeline is None:
            raise ImportError(
                "PyTorch and HuggingFace transformers are required for DepthReconstructor. "
                "Please install them via: pip install torch transformers"
            )

        # Set inference device (cuda if available, else cpu)
        if device is None or device == "cuda":
            self.device = (
                "cuda" if (torch is not None and torch.cuda.is_available()) else "cpu"
            )
        else:
            self.device = device

        print(
            f"- Initializing 3D Vision Reconstructor '{model_name}' on '{self.device}' ..."
        )
        self.pipe = pipeline("depth-estimation", model=model_name, device=self.device)
        self.intrinsics = intrinsics or {}

    @classmethod
    def from_config(cls, cfg):
        """
        Initialize DepthReconstructor using parameters from config.yaml.
        """
        # Variables
        device = getattr(cfg.system, "device", "cuda")
        vision_cfg = getattr(cfg, "vision", {})
        depth_cfg = getattr(vision_cfg, "depth_anything", {})

        model_name = getattr(
            depth_cfg, "model_name", "depth-anything/Depth-Anything-V2-Small-hf"
        )
        intrinsics = getattr(depth_cfg, "intrinsics", None)

        return cls(model_name=model_name, device=device, intrinsics=intrinsics)

    def predict_depth(self, frame: np.ndarray) -> np.ndarray:
        """
        Estimate 2D depth map from an RGB frame (H, W, 3).
        """
        image = Image.fromarray(frame) if isinstance(frame, np.ndarray) else frame
        output = self.pipe(image)
        depth = np.array(output["depth"], dtype=np.float32)

        # Ensure depth map resolution matches the input frame
        if isinstance(frame, np.ndarray):
            h, w = frame.shape[:2]
            if depth.shape[:2] != (h, w):
                depth = cv2.resize(depth, (w, h), interpolation=cv2.INTER_LINEAR)

        return depth

    def depth_to_pointcloud(self, depth: np.ndarray, rgb: np.ndarray):
        """
        Unproject 2D depth and RGB pixels into a 3D metric point cloud (X, Y, Z, R, G, B).
        """
        h, w = depth.shape[:2]

        # Use camera intrinsics or estimate from resolution
        fx = float(self.intrinsics.get("fx", w)) if self.intrinsics else float(w)
        fy = float(self.intrinsics.get("fy", w)) if self.intrinsics else float(w)
        cx = (
            float(self.intrinsics.get("cx", w / 2.0))
            if self.intrinsics
            else float(w / 2.0)
        )
        cy = (
            float(self.intrinsics.get("cy", h / 2.0))
            if self.intrinsics
            else float(h / 2.0)
        )

        # Generate pixel grid
        u, v = np.meshgrid(np.arange(w), np.arange(h))

        # Unproject to 3D camera coordinates
        z = depth
        x = (u - cx) * z / fx
        y = (v - cy) * z / fy

        # Filter valid points (depth > 0 and finite)
        valid = np.isfinite(z) & (z > 0)
        points = np.stack([x[valid], y[valid], z[valid]], axis=-1)
        colors = rgb[valid]

        return points, colors

    def reconstruct(self, frame: np.ndarray) -> dict:
        """
        Process a single frame: predict depth map and generate 3D point cloud.
        """
        depth = self.predict_depth(frame)
        points, colors = self.depth_to_pointcloud(depth, frame)
        return {"depth": depth, "points": points, "colors": colors}

    @staticmethod
    def save_ply(
        output_path: str | Path,
        points: np.ndarray | Any,
        colors: np.ndarray | None = None,
    ):
        """Save 3D point cloud to a PLY file (supports Open3D PointCloud or NumPy arrays)."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Fast write if given an Open3D PointCloud
        if o3d is not None and hasattr(points, "points"):
            o3d.io.write_point_cloud(str(path), points)
            return

        num_points = len(points)
        header = (
            "ply\n"
            "format ascii 1.0\n"
            f"element vertex {num_points}\n"
            "property float x\n"
            "property float y\n"
            "property float z\n"
            "property uchar red\n"
            "property uchar green\n"
            "property uchar blue\n"
            "end_header\n"
        )
        with open(path, "w", encoding="utf-8") as f:
            f.write(header)
            f.writelines(
                f"{x:.4f} {y:.4f} {z:.4f} {int(r)} {int(g)} {int(b)}\n"
                for (x, y, z), (r, g, b) in zip(points, colors)
            )

    @staticmethod
    def to_open3d(points: np.ndarray, colors: np.ndarray | None = None):
        """Convert NumPy 3D points and colors into an Open3D PointCloud."""
        if o3d is None:
            raise ImportError(
                "Open3D is required for 3D visualization. "
                "Please install it via: pip install open3d"
            )

        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(np.asarray(points, dtype=np.float64))
        if colors is not None and len(colors) == len(points):
            colors_norm = np.asarray(colors, dtype=np.float64)
            if colors_norm.size > 0 and colors_norm.max() > 1.0:
                colors_norm = colors_norm / 255.0
            pcd.colors = o3d.utility.Vector3dVector(colors_norm)
        return pcd

    @classmethod
    def combine_pointclouds(cls, pointclouds, voxel_downsample: float | None = None):
        """Combine multiple frame point clouds into a single unified Open3D PointCloud."""
        if o3d is None:
            raise ImportError(
                "Open3D is required for point cloud processing. "
                "Please install it via: pip install open3d"
            )

        # If already an Open3D PointCloud object
        if hasattr(pointclouds, "points"):
            combined = pointclouds
        else:
            combined = o3d.geometry.PointCloud()
            for item in pointclouds:
                if isinstance(item, dict):
                    pcd = cls.to_open3d(item["points"], item.get("colors"))
                elif isinstance(item, (tuple, list)) and len(item) >= 2:
                    pcd = cls.to_open3d(item[0], item[1])
                elif hasattr(item, "points"):
                    pcd = item
                else:
                    continue
                combined += pcd

        if voxel_downsample and voxel_downsample > 0 and len(combined.points) > 0:
            combined = combined.voxel_down_sample(voxel_size=float(voxel_downsample))

        return combined

    @staticmethod
    def _has_display() -> bool:
        """Check if an active graphical display socket (Wayland / X11) is accessible."""
        import os

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

    @classmethod
    def show_pointclouds(
        cls,
        pointclouds,
        window_name: str = "SA-Engine Combined 3D Reconstruction",
        voxel_downsample: float | None = None,
    ):
        """Display combined point clouds together in an Open3D interactive viewer."""
        if o3d is None:
            raise ImportError(
                "Open3D is required for 3D visualization. "
                "Please install it via: pip install open3d"
            )

        combined = cls.combine_pointclouds(pointclouds, voxel_downsample=voxel_downsample)
        num_points = len(combined.points)
        print(f"- Combined point cloud contains {num_points:,} points.")

        # Check if an active display server (Wayland / X11) is available
        if not cls._has_display():
            print(
                "- [INFO] No graphical display detected. Skipping interactive viewer.\n"
                "  To view the 3D point cloud, open the saved PLY file in MeshLab / CloudCompare,\n"
                "  or run SA-Engine directly from your desktop terminal."
            )
            return

        print(f"- Opening Open3D interactive viewer '{window_name}' ...")
        print("  Controls: Left-click drag: Rotate | Right-click drag: Pan | Scroll: Zoom | [Q]: Close")

        try:
            o3d.visualization.draw_geometries(
                [combined], window_name=window_name, width=1280, height=720
            )
        except Exception as e:
            print(f"- [WARNING] Could not open interactive 3D window: {e}")
