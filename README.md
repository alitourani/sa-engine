# Sight-Audition Engine

A **multimodal perception engine** for Embodied AI applications that supports 3D vision, geometry, and high-level audio interpretation.

## 🚀 Getting Started

The system supports two modes, including the **standalone** and the **ROS-enabled** variants.
Clone the repository and follow the guidelines below to install the required dependencies.
The framework has been tested on an **Ubuntu 26** system with **Python 3.14.4**.

### I. Standalone Version

This variant works with *offline videos*.

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