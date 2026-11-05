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
from sa_engine.visualization import SceneVisualizer

# Ensure X11 backend for GDK on Linux to avoid GNOME/Wayland antialiasing schema bugs
# import os
# os.environ.setdefault("GDK_BACKEND", "x11")

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

        # Initialize General Real-Time Scene Visualizer (similar to RViz)
        print("- Initializing Visualizer ...")
        visualizer = SceneVisualizer.from_config(cfg)
        print(f"- Visualizer initialized (backend: '{visualizer.backend}').\n")

        # Process frames and stream 3D reconstructions in real time
        print("- Processing frames and streaming 3D reconstructions ...")
        output_dir = Path("outputs")
        output_dir.mkdir(parents=True, exist_ok=True)

        for frame_idx, frame in enumerate(loader):
            reconstruction = reconstructor.reconstruct(frame)
            points = reconstruction["points"]
            colors = reconstruction["colors"]
            depth = reconstruction["depth"]
            print(f"- Processing frame {frame_idx + 1} ({len(points)} vertices) ...")

            # Stream each frame's reconstruction dynamically to the visualizer
            visualizer.update(
                frame_idx=frame_idx + 1,
                rgb=frame,
                depth=depth,
                points=points,
                colors=colors,
            )

            # Save individual frame point cloud as PLY (optional)
            if getattr(cfg.vision.depth_anything, "save_ply", False):
                ply_path = output_dir / f"frame_{frame_idx + 1:04d}.ply"
                reconstructor.save_ply(ply_path, points, colors)
                print(f"    Saved PLY  : {ply_path}")

        print("\n- Finished processing all video frames.")

        # Save the full accumulated point cloud to outputs
        # accumulated_pcd = visualizer.get_accumulated_pointcloud()
        # if accumulated_pcd is not None:
        #     output_pcd_path = getattr(
        #         cfg.interface.standalone.paths,
        #         "output_pointcloud_path",
        #         "outputs/dense_pointcloud.ply",
        #     )
        #     reconstructor.save_ply(output_pcd_path, accumulated_pcd)
        #     print(f"- Saved accumulated scene point cloud ({len(accumulated_pcd.points):,} points) to: {output_pcd_path}")

        # Clean up visualizer
        visualizer.close()

    except (OSError, ValueError) as e:
        print(f"[ERROR] Error while running the code: {e}")


if __name__ == "__main__":
    main()
