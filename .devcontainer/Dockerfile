# Base image provided by VS Code devcontainers
# Includes Python and a non-root 'vscode' user
FROM mcr.microsoft.com/devcontainers/python:3.12

# Install system-level dependencies
# - libgl1, libglib2.0-0 → required for OpenCV
# - udev, usbutils       → required for USB hardware (camera, LabJack)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    udev \
    usbutils \
    && rm -rf /var/lib/apt/lists/*

# Default path to the ASI SDK shared library
# (this will be mounted from the repo)
ENV ASI_LIB_PATH=/opt/asi-sdk/libASICamera2.so
