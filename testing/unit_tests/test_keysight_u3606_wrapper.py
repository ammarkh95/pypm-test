from pypm_test import (
    KeysightU3606Wrapper,
    MultimeterMode,
    MultimeterRange,
    DCOutputMode,
    CalcFunction,
)
import logging
import time


def test_keysight_u36_multimeter_func(
    psu_handle: KeysightU3606Wrapper,
) -> None:
    """
    Test the execution of multimeter functions for KeysightU3606Wrapper

    """
    # configure current measurement with Auto range
    psu_handle.configure_multimeter(
        MultimeterMode.CURRENT, MultimeterRange.AUTO
    )
    config_response = psu_handle.query_multimeter_configuration()
    assert "CURR" in config_response
    logging.info(f"Query configuration reponse: {config_response}")

    # read immediate current values
    for _ in range(10):
        I_val = psu_handle.read()
        logging.info(f"Current (I) value: {I_val} Amps")

    # configure voltage measurement with Auto range
    psu_handle.configure_multimeter(
        MultimeterMode.VOLTAGE, MultimeterRange.AUTO
    )
    config_response = psu_handle.query_multimeter_configuration()
    assert "VOLT" in config_response
    logging.info(f"Query configuration reponse: {config_response}")

    # read immediate voltage values
    for _ in range(10):
        V_val = psu_handle.read()
        logging.info(f"Current (V) value: {V_val} Volts")

    # use measure function to configure and read signle measurement in one go
    V_measure = psu_handle.measure(MultimeterMode.VOLTAGE)
    assert "VOLT" in psu_handle.query_multimeter_configuration()
    I_measure = psu_handle.measure(MultimeterMode.CURRENT)
    assert "CURR" in psu_handle.query_multimeter_configuration()

    logging.info(
        f"Single Measurment Voltage / Current / Resistance: {V_measure} volts, {I_measure} Amps"
    )

    # enable continuous mode for continuous fetch of data from the instrument
    psu_handle.enable_continuous_mode()
    actual_status = psu_handle.query_continuous_mode_status()
    assert actual_status == 1
    logging.info("Enabled continuous measure mode")

    # fetch voltage values continuously
    for _ in range(10):
        V_val = psu_handle.fetch()
        logging.info(f"Current (V) value: {V_val} Volts")

    # disable continuous mode
    psu_handle.disable_continuous_mode()
    actual_status = psu_handle.query_continuous_mode_status()
    assert actual_status == 0

    psu_handle.clear_presets()


def test_keysight_u36_measure_and_reading_speed(
    psu_handle: KeysightU3606Wrapper,
) -> None:
    """
    Test the speed of Read and Fetch commands for KeysightU3606Wrapper

    """
    # configure current measurement with Auto range
    psu_handle.configure_multimeter(
        MultimeterMode.CURRENT, MultimeterRange.AUTO
    )

    no_readings = 100

    #### Measure speed to READ #####
    t_start = time.perf_counter()
    for _ in range(no_readings):
        psu_handle.read()
    t_stop = time.perf_counter()
    reading_speed = no_readings / (t_stop - t_start)
    logging.info(f"READ speed is: {reading_speed} reads/sec")

    #### Measure speed to FETCH #####
    t_start = time.perf_counter()
    psu_handle.enable_continuous_mode()
    for _ in range(no_readings):
        psu_handle.fetch()
    t_stop = time.perf_counter()
    reading_speed = no_readings / (t_stop - t_start)
    logging.info(f"FETCH speed is: {reading_speed} reads/sec")

    psu_handle.clear_presets()


def test_keysight_u36_calc_func(psu_handle: KeysightU3606Wrapper) -> None:
    """
    Test the execution of calculate functions for KeysightU3606Wrapper

    """
    # configure voltage measurement with Auto range
    psu_handle.configure_multimeter(
        MultimeterMode.VOLTAGE, MultimeterRange.AUTO
    )
    config_response = psu_handle.query_multimeter_configuration()
    assert "VOLT" in config_response
    logging.info(f"Query configuration reponse: {config_response}")

    # check calc function is set to Null and calc is disabled
    current_calc_func = psu_handle.query_calc_function()
    assert "NULL" in current_calc_func
    current_calc_status = psu_handle.query_calc_state()
    assert current_calc_status == 0

    # enable calculation with average function to read average, min , max values
    psu_handle.set_calc_function(CalcFunction.AVERAGE)
    psu_handle.enable_calc()
    time.sleep(5)

    # check correct calc func/state set by the instrument
    current_calc_func = psu_handle.query_calc_function()
    assert "AVER" in current_calc_func
    current_calc_status = psu_handle.query_calc_state()
    assert current_calc_status == 1

    logging.info(
        f"Enabled calculation function with the following options: {current_calc_func}, {current_calc_status}"
    )

    # read average, max , min values
    avg_value = psu_handle.read_calc_average()
    max_value = psu_handle.read_calc_max()
    min_value = psu_handle.read_calc_min()

    logging.info(
        f"Read calculated voltage measurements: average {avg_value} volts, max {max_value} volts, min {min_value} volts"
    )

    # set calc function to null and disable calc function
    psu_handle.set_calc_function(CalcFunction.NULL)
    psu_handle.disable_calc()

    # check correct calc func/state set by the instrument
    current_calc_func = psu_handle.query_calc_function()
    assert "NULL" in current_calc_func
    current_calc_status = psu_handle.query_calc_state()
    assert current_calc_status == 0

    logging.info(
        f"Disabled calculation function with the following options: {current_calc_func}, {current_calc_status}"
    )

    psu_handle.clear_presets()


def test_keysight_u36_dc_supply_ramp_func(
    psu_handle: KeysightU3606Wrapper,
) -> None:
    """
    Test the ramp / soft start DC supply functions of KeysightU3606Wrapper

    """
    ####### Voltage Ramping #######
    # configure the DC supply to ramp tp 3.6 V in 10 steps
    psu_handle.configure_dc_supply_ramp_func(
        DCOutputMode.CONSTANT_VOLTAGE, 3.6, 10
    )
    # enable dc output
    psu_handle.enable_dc_output()
    time.sleep(5)

    # check correct config is set in the instrument
    ramp_config_response = psu_handle.query("VOLT:RAMP?")
    ramp_step_config_response = psu_handle.query("VOLT:RAMP:STEP?")
    assert "3.6" in ramp_config_response
    assert "+1.000000E+01" in ramp_step_config_response
    dc_output_status = psu_handle.query_dc_supply_output_status()
    assert dc_output_status == 1

    logging.info(
        f"Keysight U36 DC supply voltage ramping started with config: {ramp_config_response}"
    )

    # disable dc output and check state is correct
    psu_handle.disable_dc_output()
    dc_output_status = psu_handle.query_dc_supply_output_status()
    assert dc_output_status == 0
    psu_handle.clear_presets()

    ####### Current Ramping #######
    # configure the DC supply to ramp tp 0.001 A in 25 steps
    psu_handle.configure_dc_supply_ramp_func(
        DCOutputMode.CONSTANT_CURRENT, 0.001, 25
    )
    # enable dc output
    psu_handle.enable_dc_output()
    time.sleep(5)

    # check correct config is set in the instrument
    ramp_config_response = psu_handle.query("CURR:RAMP?")
    ramp_step_config_response = psu_handle.query("CURR:RAMP:STEP?")
    assert "+1.000000E-03" in ramp_config_response
    assert "+2.500000E+01" in ramp_step_config_response
    dc_output_status = psu_handle.query_dc_supply_output_status()
    assert dc_output_status == 1

    logging.info(
        f"Keysight U36 DC supply current ramping started with config: {ramp_config_response}"
    )

    # disable dc output and check state is correct
    psu_handle.disable_dc_output()
    dc_output_status = psu_handle.query_dc_supply_output_status()
    assert dc_output_status == 0
    psu_handle.clear_presets()

    ####### Constant Voltage Soft Start #######
    psu_handle.configure_dc_supply(DCOutputMode.CONSTANT_VOLTAGE, 3.6)
    psu_handle.set_dc_supply_soft_steps(10)
    psu_handle.enable_dc_output()
    time.sleep(5)

    # check correct config / state
    dc_output_status = psu_handle.query_dc_supply_output_status()
    output_voltage_setting = psu_handle.query_dc_supply_output_voltage()
    soft_steps_count = psu_handle.query("SST:STEP?")
    assert dc_output_status == 1
    assert output_voltage_setting == 3.6
    assert "+1.000000E+01" in soft_steps_count
    logging.info(
        f"Keysight U36 DC supply set to constant_voltage output mode with: {output_voltage_setting} volts and: {soft_steps_count} soft steps"
    )

    # disable dc output and check state is correct
    psu_handle.disable_dc_output()
    dc_output_status = psu_handle.query_dc_supply_output_status()
    assert dc_output_status == 0

    psu_handle.clear_presets()


def test_keysight_u36_dc_supply_scan_func(
    psu_handle: KeysightU3606Wrapper,
) -> None:
    """
    Test the scan DC supply functions of KeysightU3606Wrapper

    """
    ####### Voltage Scan #######
    # configure the DC supply to scan tp 3.6 V in 2 steps and 2 sec dwelling time
    psu_handle.configure_dc_supply_scan_func(
        DCOutputMode.CONSTANT_VOLTAGE, 3.6, 2, 2
    )
    # enable dc output
    psu_handle.enable_dc_output()
    time.sleep(5)

    # check correct config is set in the instrument
    scan_config_response = psu_handle.query("VOLT:SCAN?")
    scan_step_config_response = psu_handle.query("VOLT:SCAN:STEP?")
    scan_dwell_config_response = psu_handle.query("VOLT:SCAN:DWEL?")

    assert "3.6" in scan_config_response
    assert "+2.000000E+00" in scan_step_config_response
    assert "+2.000000E+00" in scan_dwell_config_response
    dc_output_status = psu_handle.query_dc_supply_output_status()
    assert dc_output_status == 1

    logging.info(
        f"Keysight U36 DC supply voltage scan started with config: {scan_config_response}"
    )

    # disable dc output and check state is correct
    psu_handle.disable_dc_output()
    dc_output_status = psu_handle.query_dc_supply_output_status()
    assert dc_output_status == 0
    psu_handle.clear_presets()

    ####### Current Scan #######
    # configure the DC supply to scan tp 0.001 A in 2 steps and 2 sec dwelling time
    psu_handle.configure_dc_supply_scan_func(
        DCOutputMode.CONSTANT_CURRENT, 0.001, 2, 2
    )
    # enable dc output
    psu_handle.enable_dc_output()
    time.sleep(5)

    # check correct config is set in the instrument
    scan_config_response = psu_handle.query("CURR:SCAN?")
    scan_step_config_response = psu_handle.query("CURR:SCAN:STEP?")
    scan_dwell_config_response = psu_handle.query("CURR:SCAN:DWEL?")
    assert "+1.000000E-03" in scan_config_response
    assert "+2.000000E+00" in scan_step_config_response
    assert "+2.000000E+00" in scan_dwell_config_response
    dc_output_status = psu_handle.query_dc_supply_output_status()
    assert dc_output_status == 1

    logging.info(
        f"Keysight U36 DC supply current scan started with config: {scan_config_response}"
    )

    # disable dc output and check state is correct
    psu_handle.disable_dc_output()
    dc_output_status = psu_handle.query_dc_supply_output_status()
    assert dc_output_status == 0

    psu_handle.clear_presets()


def test_keysight_u36_square_wav_func(
    psu_handle: KeysightU3606Wrapper,
) -> None:
    """
    Test the execution of DC supply squeare wave functions for KeysightU3606Wrapper
    """
    # configure dc supply to output 3 V, 1 kHz square wave
    psu_handle.configure_dc_supply_square_func(3.0, 1200)

    # enable the output
    psu_handle.enable_dc_output()
    time.sleep(5)

    # check correct config / status are set
    dc_output_status = psu_handle.query_dc_supply_output_status()
    assert dc_output_status == 1
    square_wave_amp_config = psu_handle.query("SQU:AMPL?")
    square_wave_freq_config = psu_handle.query("SQU:FREQ?")
    assert "+3.000000E+00" in square_wave_amp_config
    assert "+1.200000E+03" in square_wave_freq_config

    logging.info(
        f"Keysight U36 DC supply square wave function started with the following config: amplitude: {square_wave_amp_config} volts, frequency: {square_wave_freq_config} Hz"
    )

    # disable dc supply and check correct stauts is set
    psu_handle.disable_dc_output()

    dc_output_status = psu_handle.query_dc_supply_output_status()
    assert dc_output_status == 0

    psu_handle.clear_presets()


def test_keysight_u36_logging_func(psu_handle: KeysightU3606Wrapper) -> None:
    """
    Test the multimeter logging functions of KeysightU3606Wrapper

    """
    # configure voltage measurment
    psu_handle.configure_multimeter(
        MultimeterMode.VOLTAGE, MultimeterRange.AUTO
    )
    time.sleep(2)

    # delete existing logs data
    psu_handle.delete_logged_data()

    logging.info("Cleared stored log data and reset logging index")

    # start logging for 10 seconds and check status
    psu_handle.enable_data_logging()
    logging.info("Logging started ...")

    logging_status = psu_handle.query_data_logging_status()
    assert logging_status == 1
    time.sleep(10)

    # stop logging and check status
    psu_handle.disable_data_logging()
    logging_status = psu_handle.query_data_logging_status()
    assert logging_status == 0
    logging.info("Logging stopped")

    # read logged data until end
    logging.info("Reading logged data into a list ...")
    data = []
    while True:
        sample = psu_handle.read_logged_data()
        if "END" not in str(sample):
            data.append(sample)
        else:
            logging.info("Logging data collection ended")
            break

    logging.info(f"Logging process collected {len(data)} data samples")

    psu_handle.clear_presets()
