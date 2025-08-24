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

You need to install the VISA drivers for the above equipment before you could communicate with them via PyVisa. The drivers are included as part of the following software components:
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

-   **Usage as Python module with context managers**

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
        print(f"CH2 (Voltage Data Points): {len(voltage_data)}, CH2 (Last Voltage Data Point): {voltage_data[-1]:.3f} V")
        t_end = time.perf_counter()

        print(f"Array measurements via Keysight U2723 SMU took approx: {t_end - t_start:.3f} sec")

        # stop output on Channels 1 and 2
        smu.disable_smu_channel(SMUChannel.CH1)
        smu.disable_smu_channel(SMUChannel.CH2)
    ```
-   **Usage as Pytest-plugin with pytest fixtures**

    - A number of fixtures are implemented to help setup predefined workflow(s) for the instrument at the begining / end of the test, do a measurement based on your test context and then do a teardown / reset of the instrument at the end of the test

    - You can list available fixtures from pypm-test by running the command below. Also by looking at [fixtures.py](./src/pypm_test/fixtures.py) file:

        ```bash
        pytest --fixtures 
        ```
    ***Keysight U3606 pytest test case example***
    ```python
    ###########################################
    # pytest.ini -> here provide fixtures configuration
    psu_serial_no = XXXXXXXXXX
    psu_multimeter_mode = current
    psu_constant_voltage_output = 3.60 # Volts
    psu_constant_current_output = 0.01 # Amps
    ###########################################
    # test_keysight_u3606_demo.py -> here write your test case
    from pypm_test import KeysightU3606Wrapper
    import logging
    def test_keysight_u3606_demo(psu_constant_voltage_output: KeysightU3606Wrapper) -> None:

        # perform immediate measurements
        for _ in range(10):
            I_val = psu_constant_voltage_output.read()
            logging.info(f"Current (I) value: {I_val * 1000:.3f} mA")

        # change DC output voltage
        psu_constant_voltage_output.set_dc_supply_output_voltage(4.2)

        # enable continuous measurments without a trigger 
        psu_constant_voltage_output.enable_continuous_mode()

        # fetch measurements continuously
        for _ in range(10):
            I_val = psu_constant_voltage_output.fetch()
            logging.info(f"Current (I) value: {I_val * 1000:.3f} mA")

        # disable continuous mode
        psu_constant_voltage_output.disable_continuous_mode()

        ## add assertions in your test based on the context (e.g actual vs expected measurements)
        ...
    ```

    ***Keysight U2723 pytest test case example***
    ```python
    ###########################################
    # pytest.ini -> here provide fixtures configuration
    # Source Measure Unit (SMU) Fixtures Options
    smu_serial_no = MY62460002
    # Source Voltage Fixture Options
    smu_ch_1_source_voltage = 1.2 # Volts
    smu_ch_2_source_voltage = 1.8
    smu_ch_3_source_voltage = 3.6
    # Source Current Fixture Options
    smu_ch_1_source_current = 0.001 # Amps
    smu_ch_2_source_current = 0.01
    smu_ch_3_source_current = 0.05
    ###########################################
    # test_keysight_u2723_demo.py -> here write your test case
    from pypm_test import KeysightU2723Wrapper, SMUChannel
    import logging
    def test_keysight_u2723_demo(smu_voltage_source: KeysightU2723Wrapper) -> None:

        # perform scalar measurements
        for _ in range(10):
            logging.info(f"CH1 (Current): {smu_voltage_source.measure_current_scalar(SMUChannel.CH1) * 1000:.3f} mA")
            logging.info(f"CH2 (Current): {smu_voltage_source.measure_current_scalar(SMUChannel.CH2) * 1000:.3f} mA")
            logging.info(f"CH3 (Current): {smu_voltage_source.measure_current_scalar(SMUChannel.CH3) * 1000:.3f} mA")

        # change DC sourced voltages on three channels
        smu_voltage_source.set_smu_source_voltage(SMUChannel.CH1, 1.0)
        smu_voltage_source.set_smu_source_voltage(SMUChannel.CH2, 2.0)
        smu_voltage_source.set_smu_source_voltage(SMUChannel.CH3, 3.0)

        # perform array measurements: (100 points, 100 ms interval)
        smu_voltage_source.set_sweep_interval(SMUChannel.CH1, 100)
        smu_voltage_source.set_sweep_points(SMUChannel.CH1, 100)
        smu_voltage_source.set_sweep_interval(SMUChannel.CH2, 100)
        smu_voltage_source.set_sweep_points(SMUChannel.CH2, 100)
        smu_voltage_source.set_sweep_interval(SMUChannel.CH3, 100)
        smu_voltage_source.set_sweep_points(SMUChannel.CH3, 100)

        ch_1_data = smu_voltage_source.measure_current_array(SMUChannel.CH1)
        ch_2_data = smu_voltage_source.measure_current_array(SMUChannel.CH2)
        ch_3_data = smu_voltage_source.measure_current_array(SMUChannel.CH3)
        
        logging.info(f"CH1 (Current Data Points): {len(ch_1_data)}, CH1 (Last Current Data Point): {ch_1_data[-1] * 1000:.3f} mA")
        logging.info(f"CH2 (Current Data Points): {len(ch_2_data)}, CH2 (Last Current Data Point): {ch_2_data[-1] * 1000:.3f} mA")
        logging.info(f"CH3 (Current Data Points): {len(ch_3_data)}, CH3 (Last Current Data Point): {ch_3_data[-1] * 1000:.3f} mA")

        ## add assertions in your test based on the context (e.g actual vs expected measurements)
        ...
    ```

## Testing and verification
Automated test cases are available inside the [testing](./testing/) directory to verify majority of the functions of the library with the supported hardware. These could also serve as starting examples for writing your own test cases with regards to the system you are targeting in your test 

# Contribute
Contributions to pypm-test are welcome to extend the functions list / add wrappers for additonal test power equipment

Please reach out to me via E-mail: ammar.khallouf@tum.de to discuss your ideas