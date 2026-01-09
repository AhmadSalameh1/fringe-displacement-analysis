#!/bin/bash
# Environment setup for Fringe Displacement Analysis
# Source this file: source setup_env.sh

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Add ASI SDK library to LD_LIBRARY_PATH
export LD_LIBRARY_PATH="${SCRIPT_DIR}/third-party/asi-sdk:${LD_LIBRARY_PATH}"

# Add LabJack SDK if installed locally
if [ -d "${SCRIPT_DIR}/third-party/labjack-sdk" ]; then
    export LD_LIBRARY_PATH="${SCRIPT_DIR}/third-party/labjack-sdk:${LD_LIBRARY_PATH}"
fi

echo "✓ Environment configured for Fringe Displacement Analysis"
echo "  ASI SDK path: ${SCRIPT_DIR}/third-party/asi-sdk"
echo "  LD_LIBRARY_PATH: ${LD_LIBRARY_PATH}"

# Test hardware
echo ""
echo "Testing hardware..."

python3 << 'PYEOF'
import sys

# Test ASI Camera
try:
    import zwoasi as asi
    asi.init('/workspaces/fringe-displacement-analysis/third-party/asi-sdk/libASICamera2.so.1.37')
    cameras = asi.list_cameras()
    if cameras:
        print(f"✓ ASI Camera: {cameras[0]}")
    else:
        print("⚠ ASI Camera: No devices found")
except Exception as e:
    print(f"✗ ASI Camera error: {e}")
    sys.exit(1)

# Test LabJack
try:
    import labjack.ljm as ljm
    handle = ljm.openS("ANY", "ANY")
    info = ljm.getHandleInfo(handle)
    print(f"✓ LabJack: Connected (Type: {info[0]}, Connection: {info[1]})")
    ljm.close(handle)
except Exception as e:
    print(f"⚠ LabJack: {type(e).__name__} - {e}")
    if "libLabJackM.so" in str(e):
        print("  → Run: sudo bash install_labjack_ljm.sh")

print("")
print("Environment ready!")
PYEOF
