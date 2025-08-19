"""Hook specifications for pytest plugins which are invoked by pytest itself and by builtin plugins"""

from _pytest.config.argparsing import Parser


def pytest_addoption(parser: Parser):
    # Keysight U3606B DC Power Supply / Multimeter options
    ########################################################
    parser.addini(
        "psu_serial_no",
        type="string",
        default=None,
        help="serial number of the (PSU) power supply unit device to connect to",
    )

    # Keysight U2723 Source Measure Unit Options
    ########################################################
    parser.addini(
        "smu_serial_no",
        type="string",
        default=None,
        help="serial number of the (SMU) source measure unit device to connect to",
    )
