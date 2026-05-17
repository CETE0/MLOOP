# Debian Packaging

This directory contains files for building Debian packages.

## Building a Package

```bash
# Install build dependencies
sudo apt install -y debhelper dh-python

# Build the package
dpkg-buildpackage -us -uc
```

## Installation

```bash
sudo dpkg -i ../mloop_*.deb
sudo apt install -f
```
