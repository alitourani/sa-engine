"""Monocular Depth Estimation and 3D Reconstruction using HuggingFace & OpenCV."""

from pathlib import Path

import cv2
import numpy as np
from PIL import Image

try:
    import torch
    from transformers import pipeline
except ImportError:
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
    def save_ply(output_path: str | Path, points: np.ndarray, colors: np.ndarray):
        """Save 3D point cloud to an ASCII PLY file."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

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
            f.writelines(f"{x:.4f} {y:.4f} {z:.4f} {int(r)} {int(g)} {int(b)}\n" for (x, y, z), (r, g, b) in zip(points, colors))
