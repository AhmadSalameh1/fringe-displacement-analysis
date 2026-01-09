Fringe Displacement Analysis
============================

This repository acquires fringe images with a ZWO ASI camera, injects a waveform with a LabJack T4, and computes fringe displacement via FFT phase tracking. Follow this guide from a clean clone to reproduce the full pipeline.

Hardware
--------
- ZWO ASI camera (tested: ASI662MC) on USB
- LabJack T4 on USB
- Photodiode wired to LabJack AIN0; DAC0 used for waveform injection

Software prerequisites
----------------------
- Python 3.12+
- Git, wget, unzip
- Jupyter (installed via requirements.txt)

Initial setup
-------------
1) Clone and enter the repo
	```bash
   git clone https://github.com/AhmadSalameh1/fringe-displacement-analysis.git

2) Create a virtual environment (optional but recommended)
	```bash
	python3 -m venv .venv
	source .venv/bin/activate
	```

3) Install Python packages
	```bash
	pip install --upgrade pip
	pip install -r requirements.txt
	```

4) Set executable bit on helper scripts
	```bash
	chmod +x setup_env.sh install_labjack_ljm.sh
	```

ASI camera library
------------------
The ASI SDK is vendored in `third-party/asi-sdk/`.
- Nothing to install system-wide; we only need to expose the library path.
- The notebook and `setup_env.sh` already point to `third-party/asi-sdk/libASICamera2.so.1.37`.

LabJack LJM library
-------------------
Python package `labjack-ljm` is installed via `requirements.txt`, but the native library must be present.

Install (online):
```bash
sudo bash install_labjack_ljm.sh
```
This downloads the latest Linux x64 installer (LabJack-LJM_2025-05-07.zip) and installs `libLabJackM.so` into `/usr/local/lib`, then runs `ldconfig`.

If the download URL changes:
1) Grab the current Linux x64 installer from https://support.labjack.com/docs/ljm-software-installer-linux-x64
2) Download the zip, unzip, and run:
	```bash
	sudo ./labjack_ljm_installer.run -- --no-restart-device-rules
	sudo ldconfig
	```

Environment setup (run each shell session)
------------------------------------------
```bash
source setup_env.sh
```
This:
- Adds the repo root to `PYTHONPATH` (for `src` imports)
- Sets `LD_LIBRARY_PATH` to include `third-party/asi-sdk`
- Tries `third-party/labjack-sdk` if you place a custom LabJack build there
- Runs quick hardware checks (ASI init, LabJack open)

Data directories
----------------
- Raw/captured frames: `data/Capture/`
- Cropped frames: `data/crop/`
- Displacement outputs: `data/disp/`
These folders are created automatically when you run the notebook.

Running the notebook
--------------------
1) Start Jupyter from the repo root (after `source setup_env.sh`):
	```bash
	jupyter notebook
	```
2) Open `notebooks/Fringe_Displacement_Analysis.ipynb`.
3) Run all cells in order. The key stages are:
	- Imports and environment bootstrap (adds repo to `sys.path`)
	- Camera and LabJack configuration
	- Acquisition: inject waveform, capture frames, crop frames
	- Calibration fit (photodiode vs DAC)
	- Fringe displacement computation (reads `data/crop`, writes CSV/PNG to `data/disp`)

What to expect
--------------
- ASI camera detected and capturing (BIN=2 RAW8 by default)
- LabJack T4 opens over USB
- After a run: 
  - Cropped frames in `data/crop`
  - Displacement CSV: `data/disp/fringe_displacement.csv`
  - Displacement plot: `data/disp/fringe_displacement.png`

Troubleshooting
---------------
- `ModuleNotFoundError: src`: ensure `source setup_env.sh` or add repo root to `PYTHONPATH`.
- ASI warning “library not found”: ensure `LD_LIBRARY_PATH` includes `third-party/asi-sdk` (handled by `setup_env.sh`).
- LabJack error “Cannot load libLabJackM.so”: run `sudo bash install_labjack_ljm.sh`, then `sudo ldconfig`.
- No camera detected: check USB permissions; device should appear in `lsusb` as ZWO. Replug after installing udev rules (installer sets them).
- No LabJack detected: check `lsusb` for LabJack; replug after installer adds udev rules.

Headless/CI usage
-----------------
You can run analyses without hardware by setting `USE_CAMERA = False` in the notebook and skipping injection; provide your own frames in `data/crop` and run only the fringe displacement section.

Repo layout
-----------
- `notebooks/Fringe_Displacement_Analysis.ipynb` — main workflow
- `src/LAPPTP_stream_lib.py` — LabJack streaming/injection utilities
- `src/ljm_stream_util.py` — helpers for LabJack stream
- `src/GW_generator_2024.py` — waveform generator
- `third-party/asi-sdk/` — bundled ASI camera SDK
- `setup_env.sh` — environment bootstrap + hardware smoke tests
- `install_labjack_ljm.sh` — helper to install LabJack LJM native library

Quick start (commands only)
---------------------------
```bash
git clone https://github.com/AhmadSalameh1/fringe-displacement-analysis.git
cd fringe-displacement-analysis
python3 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
chmod +x setup_env.sh install_labjack_ljm.sh
sudo bash install_labjack_ljm.sh   # needed once on a new machine
source setup_env.sh
jupyter notebook notebooks/Fringe_Displacement_Analysis.ipynb
```
