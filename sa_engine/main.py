#!/usr/bin/env python3

"""
⚜️ Sentra ⚜️
------------
* © 2026 Ali Tourani (https://github.com/alitourani)
* SA-Engine is licensed under the GPL 3.0 License
* (Check LICENSE file for details)
"""

from sa_engine.config.yaml import load_config
from sa_engine.loaders import VideoLoader


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
        loader = VideoLoader.from_config(cfg)
        print(f"- Video loader initialized for: {loader.video_path}")
        print(f"- Target FPS: {loader.fps}, Target resolution: {loader.resolution}, Queue size: {loader.queue.maxlen}\n")

        # Process frames (streaming through memory queue)
        print("- Capturing frames ...")
        for frame_idx, frame in enumerate(loader):
            # ------------------------------------------------------------------
            # Future functions (DUSt3R reconstruction, feature lifting, etc.)
            # will process `frame` and/or temporal buffer `loader.queue` here.
            # ------------------------------------------------------------------
            print(f"  Captured Frame {frame_idx + 1}: shape={frame.shape}, queue_buffer={len(loader.queue)}")

        print("\n- Finished processing video frames.")

    except (OSError, ValueError) as e:
        print(f"[ERROR] Error while running the code: {e}")


if __name__ == "__main__":
    main()
