import os
from glob import glob
from setuptools import setup, find_packages

pkg = "sa_engine"


setup(
    name=pkg,
    zip_safe=True,
    version="1.0.0",
    license="GPLv3",
    author="Ali Tourani",
    maintainer="Ali Tourani",
    python_requires=">=3.12",
    include_package_data=True,
    packages=find_packages(exclude=["docs"]) + ["sa_engine.config"],
    package_dir={
        "sa_engine.config": "config",
    },
    package_data={
        "sa_engine.config": ["*.yaml"],
    },
    maintainer_email="a.tourani1991@gmail.com",
    url="https://github.com/alitourani/sa-engine",
    description="Sight-Audition-Enabled Engine for Embodied AI & Robotics",
    install_requires=[
        "PyYAML==6.0.3",
    ],
    # data_files=[
    #     ("share/ament_index/resource_index/packages", ["resource/" + pkg]),
    #     ("share/" + pkg, ["package.xml"]),
    #     (os.path.join("share", pkg, "launch"), glob("launch/*.launch.py")),
    #     (os.path.join("share", pkg, "config"), glob("config/*.yaml")),
    # ],
)
