import pytest
import logging
import pyvisa
from _pytest.config import Config
from .keysight_u3606_wrapper import KeysightU3606Wrapper, DCOutputMode
from .keysight_u2723_wrapper import KeysightU2723Wrapper
from typing import Generator, Tuple


KEYISGHT_OUTPUT_MODES_MAP = {
    "constant_voltage": DCOutputMode.CONSTANT_VOLTAGE,
    "constant_current": DCOutputMode.CONSTANT_CURRENT,
}


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


# Fixtures for the Keysight U3606B DC Power Supply / Multimeter
#########################################################
@pytest.fixture(scope="session")
def psu_handle(
    pytestconfig: Config,
    pyvisa_session: Tuple[pyvisa.ResourceManager, Tuple[str, ...]],
) -> Generator[KeysightU3606Wrapper, None, None]:
    """Initialize an instance of KeysightU36Wrapper and opens connection to USB connected keysight U3606B"""

    if not pytestconfig.getini("psu_serial_no"):
        logging.warning(
            "No serial number was specified for U36 PSU. Please specify 'psu_serial_no' option in pytest.ini"
        )

    u36_wrapper = KeysightU3606Wrapper(
        pytestconfig.getini("psu_serial_no"),
        pyvisa_session[0],
        pyvisa_session[1],
    )

    # open connection to instrument with clear status
    u36_wrapper.open()

    # clear presets / status
    u36_wrapper.clear_presets()
    u36_wrapper.clear_status()

    yield u36_wrapper

    # query / clear system errors
    last_error = u36_wrapper.query_system_errors()
    logging.info(f"Last error reported by U3606B instrument: {last_error}")

    # clear presets / status
    u36_wrapper.clear_presets()
    u36_wrapper.clear_status()

    # close Pyvisa session
    u36_wrapper.close()


# Fixtures for the Keysight U2723A Source Measure Unit
#########################################################
@pytest.fixture(scope="session")
def smu_handle(
    pytestconfig: Config,
    pyvisa_session: Tuple[pyvisa.ResourceManager, Tuple[str, ...]],
) -> Generator[KeysightU2723Wrapper, None, None]:
    """Initialize an instance of KeysightU27Wrapper and opens connection to USB connected keysight U2723A"""

    if not pytestconfig.getini("smu_serial_no"):
        logging.warning(
            "No serial number was specified for U2723 SMU. Please specify 'smu_serial_no' option in pytest.ini"
        )

    u27_wrapper = KeysightU2723Wrapper(
        pytestconfig.getini("smu_serial_no"),
        pyvisa_session[0],
        pyvisa_session[1],
    )

    # open connection to instrument with clear status
    u27_wrapper.open()

    # clear presets / status
    u27_wrapper.clear_presets()
    u27_wrapper.clear_status()

    yield u27_wrapper

    # query / clear system errors
    last_error = u27_wrapper.query_system_errors()
    logging.info(f"Last error reported by SMU instrument: {last_error}")

    # close Pyvisa session
    u27_wrapper.close()
