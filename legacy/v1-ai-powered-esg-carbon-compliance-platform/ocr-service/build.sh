#!/usr/bin/env bash
# Build script for Render deployment

# Exit on error
set -o errexit

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install Poppler for pdf2image support
# Render native python environments do not have root access by default.
# However, you can download pre-compiled binaries or rely on the host OS.
# Render's base python image usually contains apt packages or we can download it.
# We will download the static binary for poppler-utils if it's not present.
echo "Installing Poppler-utils (if not present)..."
if ! command -v pdftoppm &> /dev/null
then
    echo "pdftoppm could not be found, attempting to install via apt-get..."
    # Note: On standard Render web services, apt-get isn't available without Docker, 
    # but we will try. If this fails, the user will need to use a Dockerfile.
    apt-get update && apt-get install -y poppler-utils || echo "WARNING: Could not install poppler via apt. Consider using Docker for Render deployment."
else
    echo "Poppler is already installed."
fi
