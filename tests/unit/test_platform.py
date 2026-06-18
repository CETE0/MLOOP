"""Tests for platform detection."""

from mloop.system.platform import PlatformInfo


def test_raspberry_pi_detection_uses_device_model() -> None:
    info = PlatformInfo(
        machine="aarch64",
        system="Linux",
        release="6.6",
        node="pi",
        python_version="3.11",
        device_model="Raspberry Pi 5 Model B Rev 1.0",
    )

    assert info.is_raspberry_pi is True


def test_arm_without_pi_model_is_not_raspberry_pi() -> None:
    info = PlatformInfo(
        machine="arm64",
        system="Darwin",
        release="25.0",
        node="mac",
        python_version="3.14",
        device_model=None,
    )

    assert info.is_raspberry_pi is False
