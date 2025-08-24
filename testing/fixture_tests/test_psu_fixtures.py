from pypm_test import KeysightU3606Wrapper
from _pytest.config import Config
import pytest
import time


def test_psu_fixture(
    psu_handle: KeysightU3606Wrapper, pytestconfig: Config
) -> None:
    assert isinstance(psu_handle, KeysightU3606Wrapper), (
        "wrong or None object type returend"
    )
    assert pytestconfig.getini("psu_serial_no") == psu_handle._serial_no, (
        "conntected device serial number invalid"
    )
    assert len(psu_handle._detected_devices) != 0, (
        "pyvisa did not detect any devices"
    )
    assert psu_handle._device_handle is not None, (
        "pyvisa could not open conncetion to device"
    )
    assert psu_handle._target_device_found, (
        "did not connect to the target device with prescribed serial number"
    )
    assert psu_handle.query_dc_supply_output_status() == 0, (
        "device output is enabled initailly"
    )
    assert "VOLT" in psu_handle.query_multimeter_configuration(), (
        "default measure functions is not voltage"
    )


def test_psu_constant_voltage_output_fixture(
    psu_constant_voltage_output: KeysightU3606Wrapper, pytestconfig: Config
) -> None:
    assert (
        pytestconfig.getini("psu_multimeter_mode").upper()
        in psu_constant_voltage_output.query_multimeter_configuration()
    ), "incorrect multimeter configuration"
    assert psu_constant_voltage_output.query_dc_supply_output_status() == 1, (
        "device output is disabled after fixture run"
    )
    out_voltage_sense = (
        psu_constant_voltage_output.query_dc_supply_output_voltage()
    )
    assert pytest.approx(out_voltage_sense, abs=1.0e-2) == float(
        pytestconfig.getini("psu_constant_voltage_output")
    ), "Incorrect set voltage at output"
    assert isinstance(psu_constant_voltage_output.read(), float), (
        "Invalid / None return type of read"
    )
    psu_constant_voltage_output.enable_continuous_mode()
    time.sleep(1)
    assert psu_constant_voltage_output.query_continuous_mode_status() == 1, (
        "continuous mode not enabled"
    )
    assert isinstance(psu_constant_voltage_output.fetch(), float), (
        "Invalid / None return type of fetch"
    )
    psu_constant_voltage_output.disable_continuous_mode()
    time.sleep(1)
    assert psu_constant_voltage_output.query_continuous_mode_status() == 0, (
        "continuous mode not disabled"
    )


def test_psu_constant_current_output_fixture(
    psu_constant_current_output: KeysightU3606Wrapper, pytestconfig: Config
) -> None:
    assert (
        pytestconfig.getini("psu_multimeter_mode").upper()
        in psu_constant_current_output.query_multimeter_configuration()
    ), "incorrect multimeter configuration"
    assert psu_constant_current_output.query_dc_supply_output_status() == 1, (
        "device output is disabled after fixture setup"
    )
    out_current_sense = (
        psu_constant_current_output.query_dc_supply_output_current()
    )
    assert pytest.approx(out_current_sense, abs=1.0e-2) == float(
        pytestconfig.getini("psu_constant_current_output")
    ), "Incorrect set current at output"
    assert isinstance(psu_constant_current_output.read(), float), (
        "Invalid / None return type of read"
    )
    psu_constant_current_output.enable_continuous_mode()
    time.sleep(1)
    assert psu_constant_current_output.query_continuous_mode_status() == 1, (
        "continuous mode not enabled"
    )
    assert isinstance(psu_constant_current_output.fetch(), float), (
        "Invalid / None return type of fetch"
    )
    psu_constant_current_output.disable_continuous_mode()
    time.sleep(1)
    assert psu_constant_current_output.query_continuous_mode_status() == 0, (
        "continuous mode not disabled"
    )
