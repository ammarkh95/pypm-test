"""Hook specifications for pytest plugins which are invoked by pytest itself and by builtin plugins"""

from _pytest.config.argparsing import Parser


def pytest_addoption(parser: Parser):
    # Keysight U3606 DC Power Supply / Multimeter options
    ########################################################
    parser.addini(
        "psu_serial_no",
        type="string",
        default=None,
        help="Serial number of the (PSU) power supply unit device to connect to",
    )

    parser.addini(
        "psu_multimeter_mode",
        type="string",
        default=None,
        help="Configure the Multimeter measurement mode: [voltage, current, resistance]",
    )

    parser.addini(
        "psu_constant_voltage_output",
        type="string",
        default=None,
        help="Set DC supply constant voltage output value in Volts",
    )

    parser.addini(
        "psu_constant_current_output",
        type="string",
        default=None,
        help="Set DC supply constant current output value in Amps",
    )

    # Keysight U2723 Source Measure Unit Options
    ########################################################
    parser.addini(
        "smu_serial_no",
        type="string",
        default=None,
        help="Serial number of the (SMU) source measure unit device to connect to",
    )

    parser.addini(
        "smu_ch_1_source_voltage",
        type="string",
        default=None,
        help="Set SMU Channel (1) source voltage in Volts",
    )

    parser.addini(
        "smu_ch_2_source_voltage",
        type="string",
        default=None,
        help="Set SMU Channel (2) source voltage in Volts",
    )

    parser.addini(
        "smu_ch_3_source_voltage",
        type="string",
        default=None,
        help="Set SMU Channel (3) source voltage in Volts",
    )

    parser.addini(
        "smu_ch_1_source_current",
        type="string",
        default=None,
        help="Set SMU Channel (1) source current in Amps",
    )

    parser.addini(
        "smu_ch_2_source_current",
        type="string",
        default=None,
        help="Set SMU Channel (2) source current in Amps",
    )

    parser.addini(
        "smu_ch_3_source_current",
        type="string",
        default=None,
        help="Set SMU Channel (3) source current in Amps",
    )
