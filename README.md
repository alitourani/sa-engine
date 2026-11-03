# Sight-Audition Engine (SA-Engine)

A **multimodal perception engine** for Embodied AI applications that supports 3D vision, geometry, and high-level audio interpretation.

## ⚙️ Prerequisites

Before running the framework, you need to set your desired configurations, which can be found [here](/config/).
Apart from that, the system requires some pre-trained models to be downloaded and fed to the framework.

### I. Download Vision Models

**SA-Engine** uses [Dust3r](https://github.com/naver/dust3r) as the visual interpretation backbone.
Download one of the checkpoints and place it in the [`weights`](/weights/) folder.
The recommended weights for reliable performance is [`DUSt3R_ViTLarge_BaseDecoder_512_dpt`](https://download.europe.naverlabs.com/ComputerVision/DUSt3R/DUSt3R_ViTLarge_BaseDecoder_512_dpt.pth).

## 🚀 Getting Started

The system supports two modes, including the **standalone** and the **ROS-enabled** variants.
Clone the repository and follow the guidelines below to install the required dependencies.
The framework has been tested on an **Ubuntu 26** system with **Python 3.14.4**.

### I. Standalone Version

This variant works with *offline videos*. Simply place a video in the [`inputs/`](/inputs/) path and adjust the `standalone` configurations (such as `fps`, `input_video_path`, etc.).

```bash
# Clone the repository
git clone git@github.com:alitourani/sa-engine

# [Recommended] Activate your Python environment
python -m venv .venv
source .venv/bin/activate

# Install Python dependencies
cd sa-engine && pip install -e .

# Run the code
python main.py
```

### II. ROS2-enabled Version

Then, build the ROS2 workspace using colcon build and run the framework using the provided launch files.