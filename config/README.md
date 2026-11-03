# SA-Engine Configuration Guide

This directory contains the central configuration files for **SA-Engine** (Sight & Audition Multimodal Engine for Embodied AI Robotics).

## Overview

The master configuration file is [`config.yaml`](config.yaml), partitioned into multiple modular sections:

```
config.yaml
├── system                  # Device and general settings
├── interface               # Framework interfaces (Standalone & ROS2)
│   ├── standalone          # Standalone offline execution
│   │   ├── video_loader    # Offline video capture (FPS, resolution, queue size)
│   │   └── paths           # Input / output file paths
│   └── ros2                # ROS2 nodes, camera & mic parameters, and topics
├── vision                  # 3D vision and geometry
│   ├── depth_anything      # HuggingFace Depth Anything model & camera intrinsics
│   ├── dust3r              # DUSt3R foundation model weights and configuration
│   └── pointcloud          # Voxel filtering and downsampling
├── audio                   # High-level audio engine (microphone array, AEC, DoA)
└── multimodal_fusion       # Audio-visual spatial projection
```
