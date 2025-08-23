import pytest
import pathlib
import logging
from pypm_test import KeysightU3606SupplyAndMultimeter, KeysightU2723SourceMeasureUnit, DCOutputMode, MultimeterMode, SMUChannelMode, SMUChannel
import pyvisa
import time

@pytest.fixture
def read_pytest_ini(request):
    return pathlib.Path(request.config.rootdir, "pytest.ini").read_text()


@pytest.mark.pytester_example_path("fixture_tests")
def test_psu_fixtures(testdir, read_pytest_ini) -> None:
    testdir.makeini(read_pytest_ini)
    testdir.copy_example()
    logging.info("Running PSU Fixtures Tests")
    result = testdir.runpytest()
    assert result.ret == 0
    result.stdout.fnmatch_lines_random(["*passed*"])
    result.assert_outcomes(passed=3)


def test_psu_context_manager() -> None:
    logging.info("::::::Running PSU Context Manager::::::")
    pyvisa_dev_manager = pyvisa.ResourceManager()
    pyvisa.log_to_screen(logging.INFO)

    with KeysightU3606SupplyAndMultimeter(pyvisa_manager = pyvisa_dev_manager,
                                          serial_no = "MXXX",
                                          dc_output_mode = DCOutputMode.CONSTANT_VOLTAGE,
                                          mulitimeter_mode = MultimeterMode.CURRENT,
                                          dc_output_value= 3.6) as psu:
        # enable output
        psu.enable_dc_output()

        # perform discrete measurements
        t_start = time.perf_counter()
        for _ in range(100):
            print(f"Multimeter [READ] Current Measuremet: {psu.read() * 1000:.3f} mA")
        t_end = time.perf_counter()

        print(f"Measurement Read via Keysight U3606 Multimeter took approx: {t_end - t_start:.3f} sec")
        
        # change DC output voltage
        psu.set_dc_supply_output_voltage(5.0)

        # fetch continuous measurments without a trigger 
        psu.enable_continuous_mode()

        t_start = time.perf_counter()
        for _ in range(100):
            print(f"Multimeter [Fetch] Current Measuremet: {psu.fetch() * 1000:.3f} mA")
        t_end = time.perf_counter()

        print(f"Measurement Fetch via Keysight U3606 Multimeter took approx: {t_end - t_start:.3f} sec")

        # stop output
        psu.disable_dc_output()


@pytest.mark.pytester_example_path("fixture_tests")
def test_smu_fixtures(testdir, read_pytest_ini) -> None:
    testdir.makeini(read_pytest_ini)
    testdir.copy_example()
    logging.info("Running SMU Fixtures Tests")
    result = testdir.runpytest()
    assert result.ret == 0
    result.stdout.fnmatch_lines_random(["*passed*"])
    result.assert_outcomes(passed=3)

def test_smu_context_manager() -> None:
    logging.info("::::::Running SMU Context Manager::::::")
    pyvisa_dev_manager = pyvisa.ResourceManager()
    pyvisa.log_to_screen(logging.INFO)

    with KeysightU2723SourceMeasureUnit(pyvisa_manager = pyvisa_dev_manager,
                                        serial_no = "XXXX",
                                        smu_channel_1_output_mode = SMUChannelMode.SVMI, # Source Voltage Measure Current
                                        smu_channel_1_output_value = 3.6, # Volts
                                        smu_channel_2_output_mode = SMUChannelMode.SIMV, # Source Current Measure Voltage
                                        smu_channel_2_output_value = 0.01) as smu: # Amps
        

        # enable Voltage output on Channel 1 & Current output on Channel 2
        smu.enable_smu_channel(SMUChannel.CH1)
        smu.enable_smu_channel(SMUChannel.CH2)

        # perform discrete voltage and current measurements
        t_start = time.perf_counter()
        for _ in range(100):
            print(f"CH1 (Voltage): {smu.measure_voltage_scalar(SMUChannel.CH1):.3f} V, CH1 (Current): {smu.measure_current_scalar(SMUChannel.CH1) * 1000:.3f} mA")
            print(f"CH2 (Voltage): {smu.measure_voltage_scalar(SMUChannel.CH2):.3f} V, CH2 (Current): {smu.measure_current_scalar(SMUChannel.CH2) * 1000:.3f} mA")
        t_end = time.perf_counter()

        print(f"Scalar measurements via Keysight U2723 SMU took approx: {t_end - t_start:.3f} sec")

        # configure sweep measurements (150 readings with 40 ms interval)
        smu.set_sweep_interval(SMUChannel.CH1, 40)
        smu.set_sweep_points(SMUChannel.CH1, 150)
        smu.set_sweep_interval(SMUChannel.CH2, 40)
        smu.set_sweep_points(SMUChannel.CH2, 150)

        # trigger array measurements
        t_start = time.perf_counter()
        current_data = smu.measure_current_array(SMUChannel.CH1)
        voltage_data = smu.measure_voltage_array(SMUChannel.CH2)
        print(f"CH1 (Current Data Points): {len(current_data)}, CH1 (Last Current Data Point): {current_data[-1] * 1000:.3f} mA")
        print(f"CH2 (Voltage Data Points): {len(voltage_data)}, CH1 (Last Voltage Data Point): {voltage_data[-1]:.3f} V")
        t_end = time.perf_counter()

        print(f"Array measurements via Keysight U2723 SMU took approx: {t_end - t_start:.3f} sec")

        # stop output on Channels 1 and 2
        smu.disable_smu_channel(SMUChannel.CH1)
        smu.disable_smu_channel(SMUChannel.CH2)
