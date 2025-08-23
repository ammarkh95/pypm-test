# pypm-test
Python library to automate testing &amp; characterization of power managment features of IoT systems. The library makes use of [PyVisa](https://pyvisa.readthedocs.io/en/latest/) to automate the functionality of professional power supply / analysis equipment supporting the [SCPI](https://www.ivifoundation.org/About-IVI/scpi.html) standard

The library could be used as a python module to create standalone scripts for learning and demonstration purposes. In addiition, it could be used professionally as pytest-plugin in a R&D environment to write automated test cases for a SUT (system under test)

#### TODO: ADD AN IMAGE HERE 

## Supported Equipment

The automation of power measurements was implemented based on the availablity of the two equipment listed below:

| Equipment           | Specs (Datasheet)         | SCPI programming manual
|---------------------|---------------|----------------------------------------------|
|  [Keysight U3606B](https://www.keysight.com/us/en/support/U3606B/multimeter-dc-power-supply.html)  | [Combination of a 5.5 digit digital multimeter and 30-W power supply in a single unit](https://www.keysight.com/us/en/assets/7018-04044/data-sheets/5991-2849.pdf)| [U3606B Multimeter - DC Power Supply Programming Guide](https://www.keysight.com/us/en/assets/9018-03963/programming-guides/9018-03963.pdf)
|  [Keysight U2723A](https://www.keysight.com/us/en/products/source-measure-units-smu/u2722a-u2723a-usb-modular-source-measure-units-smu.html)  | [Modular source measure unit (SMU) Four-quadrant operation (± 120 mA/± 20 V)](https://www.keysight.com/us/en/assets/7018-02881/data-sheets/5990-7416.pdf)| [U2722A/U2723A USB Modular Source Measure Units Programmer’s Reference Guide](https://www.keysight.com/us/en/assets/9018-02095/reference-guides/9018-02095.pdf)

## Required Installations

You need to install the VISA drivers for the above equipment before you could communicate with them via PyVisa. The drivers are included as part of the following software componets:
- [Keysight IO Libraries Suite Downloads](https://www.keysight.com/us/en/lib/software-detail/computer-software/io-libraries-suite-downloads-2175637.html)
- [Measurement Manager (AMM)](https://www.keysight.com/us/en/lib/software-detail/computer-software/measurement-manager-amm-883008.html)

After installing the above on the host PC and connecting the equipment, you should be able to see them listed in Keysgiht Connection Expert software which means they should be identifiable by PyVisa

#### TODO: ADD AN IMAGE HERE 

**Important Note:** the current implementation of this library assumes the equipment are connected via USB interface

## Getting Started

- Create a Python virtual environment using your Python3.x interpreter:

  ```bash
  python3 -m venv venv # on Unix based OS
  ```
  ```powershell
  python -m venv venv # on Windows
  ```
- Activate the Python virtual environment

  ```bash
  . venv/bin/activate # on Unix based OS
  ```
  ```powershell
  . venv/Scripts/activate # on Windows
  ```

- Install pypm-test as a module directly from the repository:

  ```bash
  python3 -m pip install git+https://github.com/ammarkh95/pypm-test.git # on Unix based OS
  ```
  ```powershell
  python -m pip install git+https://github.com/ammarkh95/pypm-test.git # on Windows
  ```

## Usage

-   Usage as Python module with context managers

    You can start utilizing pypm-test module directly in your scripts by importing the wrapper classes. However, to make the experience easier, I implemented context managers to confgiure the equipment output for measurement and control the setup / tear down of the equipment state between different contexts (e.g. switch off output voltage / current after exiting "with" block and reset default settings)
    
    ***Keysight U3606 context manager example***
    ```python
    import logging
    import time
    import pyvisa
    from pypm_test import KeysightU3606SupplyAndMultimeter, DCOutputMode, MultimeterMode

    pyvisa_dev_manager = pyvisa.ResourceManager()
    pyvisa.log_to_screen(logging.INFO)

    with KeysightU3606SupplyAndMultimeter(pyvisa_manager = pyvisa_dev_manager,
                                        serial_no = "XXXX", # add your equipment serial number here
                                        dc_output_mode = DCOutputMode.CONSTANT_VOLTAGE, # output voltage
                                        mulitimeter_mode = MultimeterMode.CURRENT, # measure current
                                        dc_output_value= 3.6) as psu: # Volts
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
    ```

    ***Keysight U2723 context manager example***
    ```python
    import logging
    import time
    import pyvisa
    from pypm_test import KeysightU2723SourceMeasureUnit, SMUChannelMode, SMUChannel

    pyvisa_dev_manager = pyvisa.ResourceManager()
    pyvisa.log_to_screen(logging.INFO)

    with KeysightU2723SourceMeasureUnit(pyvisa_manager = pyvisa_dev_manager,
                                        serial_no = "XXXX", # add your equipment serial number here
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
    ```

-   Usage as Pytest-plugin with pytest-fixtures

    ***Keysight U3606 pytest test case example***
    ```python
    ###########################################
    # pytest.ini -> here provide fixtures configuration

    # ADALM1000 Fixtures Options
    # Voltage Source
    adalm1k_ch_a_voltage = 3.70
    adalm1k_ch_b_voltage = 1.0

    # Analog Discovery Fixtures Options
    analog_discovery_config_number = 1

    ###########################################
    # test_analog_discovery_adalm1k_combined.py -> here write your test case
    def test_analog_discovery_adalm1k_combined(adalm1k_voltage_source: ADALM1KWrapper,
                                analog_discovery_scope_wavegen: AnalogDiscoveryWrapper,
                                pytestconfig: Config) -> None:

        ###
        # IMPORTANT: for this test the following connections are required between ADALM1K and Analog Discovery
        ## (ADALM1k) CH-A -> (Anlaog Discovery) +1
        ## (ADALM1k) CH-B -> (Anlaog Discovery) +2
        ## (ADALM1k) GND -> (Anlaog Discovery) -1
        ## (ADALM1k) GND -> (Anlaog Discovery) -2
        ###

        # read 100 samples from adalm1k instrument in blocking fashion
        adalm1k_samples = adalm1k_voltage_source.read_all(100, -1)

        # get configured values in pytest.ini
        exp_voltage_ch_a = float(pytestconfig.getini("adalm1k_ch_a_voltage"))
        exp_voltage_ch_b = float(pytestconfig.getini("adalm1k_ch_b_voltage"))

        # assert measured voltages are close to expected ones configured by the fixture
        for s in adalm1k_samples:
            assert pytest.approx(s[0][0], abs=1.0e-2) == exp_voltage_ch_a # CH-A voltage 
            assert pytest.approx(s[1][0], abs=1.0e-2) == exp_voltage_ch_b  # CH-B voltage

        # use analog discovery analog in channels (1, 2) to measure output voltages from ADALM1K channels (A, B)
        analog_discovery_scope_wavegen.record_analog_signal(
            input_channels = [AnalogInputChannel.Channel1, AnalogInputChannel.Channel2],
            range= 10,                                   
            sampling_frequency= 100e3)
        
        # read 100 samples from analog disocvery in blocking fashion
        ad_samples = analog_discovery_scope_wavegen.fill_recorded_samples_on_channels(
            [AnalogInputChannel.Channel1, AnalogInputChannel.Channel2],
            100)
        
        # assert measured voltages by analog discovery are close to the ones set by adalm1k
        for ch1_s, ch2_s in zip(ad_samples[0],  ad_samples[1]):
            assert pytest.approx(ch1_s, abs=5.0e-2) == exp_voltage_ch_a # CH-A voltage 
            assert pytest.approx(ch2_s, abs=5.0e-2) == exp_voltage_ch_b # CH-B voltage
    ```

    ***Keysight U2723 pytest test case example***
    ```python
    ###########################################
    # pytest.ini -> here provide fixtures configuration

    # ADALM1000 Fixtures Options
    # Voltage Source
    adalm1k_ch_a_voltage = 3.70
    adalm1k_ch_b_voltage = 1.0

    # Analog Discovery Fixtures Options
    analog_discovery_config_number = 1

    ###########################################
    # test_analog_discovery_adalm1k_combined.py -> here write your test case
    def test_analog_discovery_adalm1k_combined(adalm1k_voltage_source: ADALM1KWrapper,
                                analog_discovery_scope_wavegen: AnalogDiscoveryWrapper,
                                pytestconfig: Config) -> None:

        ###
        # IMPORTANT: for this test the following connections are required between ADALM1K and Analog Discovery
        ## (ADALM1k) CH-A -> (Anlaog Discovery) +1
        ## (ADALM1k) CH-B -> (Anlaog Discovery) +2
        ## (ADALM1k) GND -> (Anlaog Discovery) -1
        ## (ADALM1k) GND -> (Anlaog Discovery) -2
        ###

        # read 100 samples from adalm1k instrument in blocking fashion
        adalm1k_samples = adalm1k_voltage_source.read_all(100, -1)

        # get configured values in pytest.ini
        exp_voltage_ch_a = float(pytestconfig.getini("adalm1k_ch_a_voltage"))
        exp_voltage_ch_b = float(pytestconfig.getini("adalm1k_ch_b_voltage"))

        # assert measured voltages are close to expected ones configured by the fixture
        for s in adalm1k_samples:
            assert pytest.approx(s[0][0], abs=1.0e-2) == exp_voltage_ch_a # CH-A voltage 
            assert pytest.approx(s[1][0], abs=1.0e-2) == exp_voltage_ch_b  # CH-B voltage

        # use analog discovery analog in channels (1, 2) to measure output voltages from ADALM1K channels (A, B)
        analog_discovery_scope_wavegen.record_analog_signal(
            input_channels = [AnalogInputChannel.Channel1, AnalogInputChannel.Channel2],
            range= 10,                                   
            sampling_frequency= 100e3)
        
        # read 100 samples from analog disocvery in blocking fashion
        ad_samples = analog_discovery_scope_wavegen.fill_recorded_samples_on_channels(
            [AnalogInputChannel.Channel1, AnalogInputChannel.Channel2],
            100)
        
        # assert measured voltages by analog discovery are close to the ones set by adalm1k
        for ch1_s, ch2_s in zip(ad_samples[0],  ad_samples[1]):
            assert pytest.approx(ch1_s, abs=5.0e-2) == exp_voltage_ch_a # CH-A voltage 
            assert pytest.approx(ch2_s, abs=5.0e-2) == exp_voltage_ch_b # CH-B voltage
    ```


## Testing and verification
Automated test cases are available inside the [testing](./testing/) directory to verify majority of the functions of the library with the supported hardware. These could also serve as starting examples for writing your own test cases with regards to the system you are targeting in your test 

# Contribute
Contributions to pypm-test are welcome to extend the functions list / add wrappers for additonal test power equipment

Please reach out to me via E-mail: ammar.khallouf@tum.de to discuss your ideas