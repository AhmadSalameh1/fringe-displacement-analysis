#!/bin/bash
# Script to install LabJack LJM library
# Run with: sudo bash install_labjack_ljm.sh

set -e

echo "Installing LabJack LJM Library..."

# Create temp directory
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Try to download from direct link (may require manual download)
echo "Attempting to download LabJack LJM installer..."
# Note: This URL may be outdated - check https://labjack.com/pages/support?doc=/software-driver/installer-downloads/ljm-software-installers-t4-t7-digit/
wget -O ljm_installer.tar.gz "https://files.labjack.com/installers/LJM/Linux/labjack_ljm_software_2022_05_16_x86_64.tar.gz" || {
    echo ""
    echo "ERROR: Download failed!"
    echo "Please manually download the LabJack LJM installer from:"
    echo "https://labjack.com/pages/support?doc=/software-driver/installer-downloads/ljm-software-installers-t4-t7-digit/"
    echo ""
    echo "Then run:"
    echo "  tar xf labjack_ljm_software_*_x86_64.tar.gz"
    echo "  cd labjack_ljm_software_*"
    echo "  sudo ./labjack_ljm_installer.run -- --no-restart-device-rules"
    exit 1
}

# Extract
tar xf ljm_installer.tar.gz
cd labjack_ljm_software_*

# Install
echo "Running installer..."
./labjack_ljm_installer.run -- --no-restart-device-rules

# Verify
if ldconfig -p | grep -q libLabJackM; then
    echo "✓ LabJack LJM library installed successfully!"
    ldconfig -p | grep LabJack
else
    echo "⚠ Installation completed but library not found in ldconfig"
fi

# Cleanup
cd /
rm -rf "$TEMP_DIR"

echo ""
echo "Installation complete. Test with:"
echo "  python3 -c 'import labjack.ljm as ljm; print(ljm.openS(\"ANY\", \"ANY\"))'"
