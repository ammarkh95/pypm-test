import pytest
import logging
import pyvisa
from _pytest.config import Config
from .keysight_u3606_wrapper import (
    KeysightU3606Wrapper,
    DCOutputMode,
    MultimeterMode,
)
from .keysight_u2723_wrapper import KeysightU2723Wrapper, SMUChannel
from typing import Generator, Tuple


@pytest.fixture(scope="session")
def pyvisa_session() -> Tuple[pyvisa.ResourceManager, Tuple[str, ...]]:
    """
    Create a Pyvisa Session to be used by Keysight Wrapper classes
    """
    pyvisa_dev_manager = pyvisa.ResourceManager()
    pyvisa.log_to_screen(logging.INFO)
    pyvisa_devices = pyvisa_dev_manager.list_resources()
    logging.info(f"PyVisa discovered the following devices: {pyvisa_devices}")

    return (pyvisa_dev_manager, pyvisa_devices)


# Fixtures for the Keysight U3606 DC Power Supply / Multimeter
#########################################################
KEYISGHT_MULTIMETER_MODES_MAP = {
    "voltage": MultimeterMode.VOLTAGE,
    "current": MultimeterMode.CURRENT,
    "resistance": MultimeterMode.RESISTANCE,
}


@pytest.fixture(scope="session")
def psu_handle(
    pytestconfig: Config,
    pyvisa_session: Tuple[pyvisa.ResourceManager, Tuple[str, ...]],
) -> Generator[KeysightU3606Wrapper, None, None]:
    """Initialize an instance of KeysightU3606Wrapper and opens connection to USB connected keysight U3606"""

    if not pytestconfig.getini("psu_serial_no"):
        logging.warning(
            "No serial number was specified for U36 PSU. Please specify 'psu_serial_no' option in pytest.ini"
        )

    psu_wrapper = KeysightU3606Wrapper(
        pytestconfig.getini("psu_serial_no"),
        pyvisa_session[0],
        pyvisa_session[1],
    )

    # open connection to instrument
    psu_wrapper.open()

    # clear presets / status
    psu_wrapper.clear_presets()
    psu_wrapper.clear_status()

    yield psu_wrapper

    # query / clear system errors
    last_error = psu_wrapper.query_system_errors()
    logging.info(
        f"Last error reported by Keysight U3606 instrument: {last_error}"
    )

    # clear presets / status
    psu_wrapper.clear_presets()
    psu_wrapper.clear_status()

    # close Pyvisa session
    psu_wrapper.close()


@pytest.fixture
def psu_multimeter(
    pytestconfig: Config,
    psu_handle: Generator[KeysightU3606Wrapper, None, None],
) -> KeysightU3606Wrapper:
    mulitmeter_mode = KEYISGHT_MULTIMETER_MODES_MAP.get(
        pytestconfig.getini("psu_multimeter_mode")
    )
    if not mulitmeter_mode:
        raise RuntimeError(
            "pytest option: 'psu_multimeter_mode' is not defined or invalid"
        )
    psu_handle.configure_multimeter(mulitmeter_mode)

    return psu_handle


@pytest.fixture
def psu_constant_voltage_output(
    pytestconfig: Config,
    psu_handle: Generator[KeysightU3606Wrapper, None, None],
) -> Generator[KeysightU3606Wrapper, None, None]:
    cv_output_value = pytestconfig.getini("psu_constant_voltage_output")
    if not cv_output_value:
        raise RuntimeError(
            "pytest option: 'psu_constant_voltage_output' is not defined or invalid"
        )
    psu_handle.configure_dc_supply(
        DCOutputMode.CONSTANT_VOLTAGE, float(cv_output_value)
    )
    psu_handle.enable_dc_output()

    yield psu_handle

    psu_handle.disable_dc_output()


@pytest.fixture
def psu_constant_current_output(
    pytestconfig: Config,
    psu_handle: Generator[KeysightU3606Wrapper, None, None],
) -> Generator[KeysightU3606Wrapper, None, None]:
    cc_output_value = pytestconfig.getini("psu_constant_current_output")
    if not cc_output_value:
        raise RuntimeError(
            "pytest option: 'psu_constant_current_output' is not defined or invalid"
        )
    psu_handle.configure_dc_supply(
        DCOutputMode.CONSTANT_CURRENT, float(cc_output_value)
    )
    psu_handle.enable_dc_output()

    yield psu_handle

    psu_handle.disable_dc_output()


# Fixtures for the Keysight U2723 Source Measure Unit
#########################################################
@pytest.fixture(scope="session")
def smu_handle(
    pytestconfig: Config,
    pyvisa_session: Tuple[pyvisa.ResourceManager, Tuple[str, ...]],
) -> Generator[KeysightU2723Wrapper, None, None]:
    """Initialize an instance of KeysightU27Wrapper and opens connection to USB connected keysight U2723"""

    if not pytestconfig.getini("smu_serial_no"):
        logging.warning(
            "No serial number was specified for U2723 SMU. Please specify 'smu_serial_no' option in pytest.ini"
        )

    smu_wrapper = KeysightU2723Wrapper(
        pytestconfig.getini("smu_serial_no"),
        pyvisa_session[0],
        pyvisa_session[1],
    )

    # open connection to instrument
    smu_wrapper.open()

    # clear presets / status
    smu_wrapper.clear_presets()
    smu_wrapper.clear_status()

    yield smu_wrapper

    # query / clear system errors
    last_error = smu_wrapper.query_system_errors()
    logging.info(
        f"Last error reported by Keysight U2723 instrument: {last_error}"
    )

    # clear presets / status
    smu_wrapper.clear_presets()
    smu_wrapper.clear_status()

    # close Pyvisa session
    smu_wrapper.close()


@pytest.fixture
def smu_voltage_source(
    pytestconfig: Config,
    smu_handle: Generator[KeysightU2723Wrapper, None, None],
) -> Generator[KeysightU2723Wrapper, None, None]:
    ch_1_volt = pytestconfig.getini("smu_ch_1_source_voltage")
    ch_2_volt = pytestconfig.getini("smu_ch_2_source_voltage")
    ch_3_volt = pytestconfig.getini("smu_ch_3_source_voltage")

    if (ch_1_volt is None) and (ch_2_volt is None) and (ch_3_volt is None):
        raise RuntimeError(
            "pytest options: 'smu_ch_1_source_voltage, smu_ch_2_source_voltage, smu_ch_3_source_voltage' are not defined"
        )

    if ch_1_volt:
        smu_handle.set_smu_source_voltage(SMUChannel.CH1, float(ch_1_volt))
        smu_handle.enable_smu_channel(SMUChannel.CH1)

    if ch_2_volt:
        smu_handle.set_smu_source_voltage(SMUChannel.CH2, float(ch_2_volt))
        smu_handle.enable_smu_channel(SMUChannel.CH2)

    if ch_3_volt:
        smu_handle.set_smu_source_voltage(SMUChannel.CH3, float(ch_3_volt))
        smu_handle.enable_smu_channel(SMUChannel.CH3)

    yield smu_handle

    smu_handle.disable_smu_channel(SMUChannel.CH1)
    smu_handle.disable_smu_channel(SMUChannel.CH2)
    smu_handle.disable_smu_channel(SMUChannel.CH3)
    smu_handle.clear_presets()


@pytest.fixture
def smu_current_source(
    pytestconfig: Config,
    smu_handle: Generator[KeysightU2723Wrapper, None, None],
) -> Generator[KeysightU2723Wrapper, None, None]:
    ch_1_curr = pytestconfig.getini("smu_ch_1_source_current")
    ch_2_curr = pytestconfig.getini("smu_ch_2_source_current")
    ch_3_curr = pytestconfig.getini("smu_ch_3_source_current")

    if (ch_1_curr is None) and (ch_2_curr is None) and (ch_3_curr is None):
        raise RuntimeError(
            "pytest options: 'smu_ch_1_source_current, smu_ch_2_source_current, smu_ch_3_source_current' are not defined"
        )

    if ch_1_curr:
        smu_handle.set_smu_source_current(SMUChannel.CH1, float(ch_1_curr))
        smu_handle.enable_smu_channel(SMUChannel.CH1)

    if ch_2_curr:
        smu_handle.set_smu_source_current(SMUChannel.CH2, float(ch_2_curr))
        smu_handle.enable_smu_channel(SMUChannel.CH2)

    if ch_3_curr:
        smu_handle.set_smu_source_current(SMUChannel.CH3, float(ch_3_curr))
        smu_handle.enable_smu_channel(SMUChannel.CH3)

    yield smu_handle

    smu_handle.disable_smu_channel(SMUChannel.CH1)
    smu_handle.disable_smu_channel(SMUChannel.CH2)
    smu_handle.disable_smu_channel(SMUChannel.CH3)
    smu_handle.clear_presets()
