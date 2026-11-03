#!/usr/bin/env python3

"""
⚜️ Sentra ⚜️
------------
* © 2026 Ali Tourani (https://github.com/alitourani)
* SA-Engine is licensed under the GPL 3.0 License
* (Check LICENSE file for details)
"""

from pathlib import Path
from sa_engine.config.yaml import load_config
from sa_engine.loaders import VideoLoader
from sa_engine.vision import DepthReconstructor


def main(args=None):
    """Main entry point for SA-Engine."""
    print("*** SA-Engine (Standalone) Started! ***\n")

    # Run the node
    try:
        # Load configuration
        print("- Loading configurations ...")
        cfg = load_config()
        print("- Configurations loaded successfully.\n")

        # Fetch the input video with specified fps and resolution, and capture frames
        print("- Initializing Video Loader ...")
        loader = VideoLoader.from_config(cfg)
        print(f"- Video Loader initialized for: {loader.video_path}")
        print(f"- Target FPS: {loader.fps}, Target Resolution: {loader.resolution}, Queue size: {loader.queue.maxlen}\n")

        # Initialize 3D Vision Reconstructor
        reconstructor = DepthReconstructor.from_config(cfg)
        print("- 3D Vision Reconstructor ready.\n")

        # Process frames and generate 3D point clouds
        print("- Processing frames and generating 3D point clouds ...")
        output_dir = Path("outputs")
        output_dir.mkdir(parents=True, exist_ok=True)

        for frame_idx, frame in enumerate(loader):
            print(f"  [Frame {frame_idx + 1}] Running 3D reconstruction ...")
            reconstruction = reconstructor.reconstruct(frame)
            points = reconstruction["points"]
            colors = reconstruction["colors"]
            depth = reconstruction["depth"]

            print(f"    Depth Map  : {depth.shape} (min={depth.min():.2f}, max={depth.max():.2f})")
            print(f"    Point Cloud: {len(points)} vertices")

            # Save point cloud as PLY
            if getattr(cfg.vision.depth_anything, "save_ply", True):
                ply_path = output_dir / f"frame_{frame_idx + 1:04d}.ply"
                reconstructor.save_ply(ply_path, points, colors)
                print(f"    Saved PLY  : {ply_path}")

        print("\n- Finished processing video frames.")

    except (OSError, ValueError) as e:
        print(f"[ERROR] Error while running the code: {e}")


if __name__ == "__main__":
    main()
