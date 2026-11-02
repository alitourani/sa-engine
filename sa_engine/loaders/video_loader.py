"""Simple Video Loader for standalone processing in SA-Engine."""

from collections import deque
from pathlib import Path

import cv2


class VideoLoader:
    """
    Loads video frames at a defined FPS and resolution, buffering them into a queue.
    """

    def __init__(self, video_path, fps=None, resolution=None, queue_size=10):
        # Initialize the VideoLoader
        self.queue = deque(maxlen=int(queue_size))
        self.video_path = str(Path(video_path).resolve())
        self.fps = float(fps) if (fps and fps > 0) else None
        self.resolution = tuple(resolution) if resolution else None

        # Check that video can be opened
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            raise FileNotFoundError(
                f"\n[ERROR] Cannot open video file: {self.video_path}"
            )
        self.source_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        cap.release()

    @classmethod
    def from_config(cls, cfg):
        """
        Create a VideoLoader using parameters from config.yaml.
        """
        standalone = cfg.interface.standalone
        video_cfg = getattr(standalone, "video_loader", {})
        paths_cfg = getattr(standalone, "paths", {})
        video_path = (
            getattr(paths_cfg, "input_video_path", None)
            or getattr(video_cfg, "video_path", None)
            or "inputs/video.mp4"
        )
        fps = getattr(video_cfg, "fps", None)
        resolution = getattr(video_cfg, "resolution", None)
        queue_size = getattr(video_cfg, "queue_size", 10)

        return cls(
            video_path=video_path,
            fps=fps,
            resolution=resolution,
            queue_size=queue_size,
        )

    def __iter__(self):
        """
        Iterate through sampled and resized frames, updating the in-memory queue.
        """
        # Open the video file
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            raise FileNotFoundError(
                f"\n[ERROR] Cannot open video file: {self.video_path}"
            )
        frame_idx = 0
        next_target_time = 0.0
        time_step = (
            1.0 / self.fps if (self.fps and self.fps < self.source_fps) else None
        )

        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                # Calculate the current time of the frame
                current_time = (
                    frame_idx / self.source_fps if self.source_fps > 0 else 0.0
                )
                # Check if we should yield this frame based on the target FPS
                if time_step is None or current_time >= next_target_time:
                    # Resize to target resolution
                    if self.resolution:
                        frame = cv2.resize(
                            frame, (self.resolution[0], self.resolution[1])
                        )

                    # Convert BGR to RGB
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                    # Store in queue and yield for downstream processing
                    self.queue.append(frame)
                    yield frame

                    if time_step:
                        next_target_time += time_step

                frame_idx += 1
        finally:
            cap.release()
