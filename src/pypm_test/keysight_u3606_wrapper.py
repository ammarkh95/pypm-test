"""
Wrapper for automating (DC power supply + Multimeter) functions of Keysight U3606

The wrapper uses the PyVisa library to communicate with the instrument using VISA standard protocol

# Important: NI-VISA need to be installed on the test station https://www.ni.com/de/support/downloads/drivers/download.ni-visa.html
# Important: The instrument needs to be configured as USB-TMC device in the utility menu. Check the user manual for the required steps

"""

import logging
import pyvisa
from enum import Enum
from typing import Union, Tuple, Optional

logger = logging.getLogger("Keyisght-U3606-Wrapper")
logger.setLevel(logging.INFO)


MAX_VOLTAGE_LIMIT = 30  # V
MAX_CURRENT_LIMIT = 1.05  # A


### Enum Classes for power supply supported power output / measure options ###
class DCOutputMode(Enum):
    """
    Enumeration to configure output mode for the DC Supply of Keyishgt U3606 (constant voltage or constant current)
    """

    @classmethod
    def list(cls):
        return list(map(lambda c: cls.__name__ + "." + c.name, cls))

    CONSTANT_VOLTAGE = "VOLT"
    CONSTANT_CURRENT = "CURR"


class DCOutputVoltageRange(Enum):
    """
    Enumeration to configure output voltage range for the DC Supply of Keyishgt U3606 (constant voltage or constant current)
    """

    @classmethod
    def list(cls):
        return list(map(lambda c: cls.__name__ + "." + c.name, cls))

    MAX = "MAX"  # 30 V (default)
    MIN = "MIN"  # 1 V
    AUTO = "AUTO"


class DCOutputCurrentRange(Enum):
    """
    Enumeration to configure output curremt range for the DC Supply of Keyishgt U3606 (constant voltage or constant current)
    """

    @classmethod
    def list(cls):
        return list(map(lambda c: cls.__name__ + "." + c.name, cls))

    MAX = "MAX"  # 3 A
    DEFAULT = "DEF"  # 1 A
    MIN = "MIN"  # 100 mA
    AUTO = "AUTO"


class MultimeterMode(Enum):
    """
    Enumeration to configure measurement mode for the Multimeter instrument of Keyishgt U3606
    """

    @classmethod
    def list(cls):
        return list(map(lambda c: cls.__name__ + "." + c.name, cls))

    VOLTAGE = "VOLT"
    CURRENT = "CURR"
    RESISTANCE = "RES"


class MultimeterRange(Enum):
    """
    Enumeration to configure range option for the Multimeter instrument of Keyishgt U3606
    """

    @classmethod
    def list(cls):
        return list(map(lambda c: cls.__name__ + "." + c.name, cls))

    AUTO = "AUTO"
    MAX = "MAX"
    MIN = "MIN"


class MultimeterResolution(Enum):
    """
    Enumeration to configure the resolution option for the Multimeter instrument of Keyishgt U3606
    """

    @classmethod
    def list(cls):
        return list(map(lambda c: cls.__name__ + "." + c.name, cls))

    MAX = "MAX"  # 4 and 1/2 digits
    MIN = "MIN"  # 5 and 1/2 digits (default)


class SignalType(Enum):
    """
    Enumeration to configure the signal type for the Multimeter instrument of Keyishgt U3606
    """

    @classmethod
    def list(cls):
        return list(map(lambda c: cls.__name__ + "." + c.name, cls))

    AC = "AC"
    DC = "DC"


class CalcFunction(Enum):
    """
    Enumeration for the caclulation functions of U3606
    """

    @classmethod
    def list(cls):
        return list(map(lambda c: cls.__name__ + "." + c.name, cls))

    AVERAGE = "AVER"  # mathematical average (mean) of all readings taken since averaging was enabled
    DB = "DB"  # computes the dBm value for the next reading based on reference resistance
    DBM = (
        "DBM"  # DBM equation based on reference based on reference resistance
    )
    HOLD = "HOLD"  # capture and hold a stable reading based on a variation
    LIMIT = "LIM"  # Compares each reading against upper and lower limits
    NULL = "NULL"  # Result = Reading – Offset


class QuestionRegister(Enum):
    """
    Enumeration for the condition registers (decimal values) of U3606
    """

    @classmethod
    def list(cls):
        return list(map(lambda c: cls.__name__ + "." + c.name, cls))

    VOLT_OVERLOAD = "1"
    CURR_OVERLOAD = "2"
    RES_OVERLOAD = "512"
    OUT_OVERVOLT = "4"
    OUT_OVERCURR = "8"
    UPP_LIM_FAILED = "4096"
    LOW_LIM_FAILED = "2048"


### Wrapper class implementing SCPI functions ###
class KeysightU3606Wrapper:
    """Wrapper class for utilitzing the power supply and multimeter functions of Keysight U3606 DC power supply / Multimeter"""

    def __init__(
        self,
        serial_no: str,
        pyvisa_device_manager: pyvisa.ResourceManager,
        pyvisa_devices: Tuple[str, ...],
    ) -> None:
        """Iniitalize Pyvisa interface and detect connected instruments"""

        self._device_manager = pyvisa_device_manager
        self._device_url = ""
        self._serial_no = serial_no
        self._device_handle = None
        self._target_device_found = False
        self._detected_devices = pyvisa_devices

        if not self._detected_devices:
            raise RuntimeError(
                "No devices were detected by PyVisa. Make sure your instrument is connected and VISA libraries are installed"
            )

    def open(self) -> None:
        """Opens the connection to a USB connected U3606"""

        for device in self._detected_devices:
            # Scan for USB devices
            if device.find("USB") == 0 and self._serial_no in str(device):
                self._device_url = device
                self._device_handle = self._device_manager.open_resource(
                    self._device_url
                )
                device_info = self._device_handle.query("*IDN?")
                # ckech it is a U3606 mode instrument
                if "U3606" in str(device_info):
                    logger.info(
                        f"Opened connection to instrument: {device_info}"
                    )
                    self._target_device_found = True
                    return None

        if not self._target_device_found:
            raise RuntimeError(
                f"Could not detect target device of model: U3606 and serial no: {self._serial_no}"
            )

    def close(self) -> None:
        """Closes the connection session to connected device"""

        if self._device_handle:
            self._device_handle.close()
            logger.info(
                f"Closed connection session to instrument: {self._device_url}"
            )

    def clear_presets(self) -> None:
        """clears preset status bit register of the connected instrument"""

        self._device_handle.write("*rst; status:preset; *cls")
        logger.info("Cleared instrument presets")

    def clear_status(self) -> None:
        """clears all event status registers / error queue of the connected instrument"""

        self._device_handle.write("*CLS")
        logger.info("Cleared all instrument event status registers / errors")

    def reset_defaults(self) -> None:
        """resets the instrument to its factory default state"""
        self._device_handle.write("*RST")
        logger.info("U3606 reset to default factory state")

    def wait(self) -> None:
        """
        configures the instrument's output buffer to wait until
        all pending operations are complete, before executing any subsequent commands or queries
        """
        self._device_handle.write("*WAI")

    def is_operation_complete(self) -> bool:
        """
        returns true if the current operation is completed by the instrument (+1 is returned by query when operation is completed)
        NOTE: used to synchronize running application with the instrument
        """
        completion_code_found = self._device_handle.query("*OPC?").find("1")
        if completion_code_found == 0:
            return True
        else:
            return False

    def query_system_errors(self) -> str:
        """
        reads and clears one error from the instrument's error queue
        A record of up to 20 errors can be stored in the U3606 error queue

        For SCPI command errors, this command returns the following format string:
        <Number,"Error String">
        """
        error_queue = self._device_handle.query("SYST:ERR?")
        return str(error_queue)

    def configure_dc_supply(
        self,
        output_mode: DCOutputMode,
        output_value: float,
        over_voltage_limit: float = 30,
        over_current_limit: float = 1,
        voltage_range: DCOutputVoltageRange = DCOutputVoltageRange.AUTO,
        current_range: DCOutputCurrentRange = DCOutputCurrentRange.AUTO,
    ) -> None:
        """
        Configure the output settings for the DC supply

        Args:
            output_mode (DCOutputMode): constant voltage or constant current
            output_value (float): voltage or current value set at the output in (V or A) units respectively
            over_voltage_limit (float): over-voltage limit in volts for the constant current output (default: 30 V)
            over_current_limit (float): over-current limit in amps for the constant voltage output (default: 1 A)
            voltage_range (DCOutputVoltageRange): range for the voltage output (default: MAX)
            current_range (DCOutputCurrentRange): range for the current output (default: DEFAULT)
        """
        # check arguments
        if not isinstance(output_mode, DCOutputMode):
            raise RuntimeError(
                f"Invalid type: {type(output_mode)} for output_mode. output_mode needs to be a valid enum of type: {DCOutputMode._name_}"
            )

        if not isinstance(voltage_range, DCOutputVoltageRange):
            raise RuntimeError(
                f"Invalid type: {type(voltage_range)} for voltage_range. voltage_range needs to be a valid enum of type: {DCOutputVoltageRange._name_}"
            )

        if not isinstance(current_range, DCOutputCurrentRange):
            raise RuntimeError(
                f"Invalid type: {type(current_range)} for current_range. current_range needs to be a valid enum of type: {DCOutputCurrentRange._name_}"
            )

        # first disable the output (required to configure)
        self.disable_dc_output()

        # CV mode
        if output_mode.value == DCOutputMode.CONSTANT_VOLTAGE.value:
            # set source voltage, over current limit and voltage range for the output
            self.set_dc_supply_output_voltage(output_value)
            self._device_handle.write("SOUR:CURR:LIM %s" % over_current_limit)
            self._device_handle.write(
                "SOUR:VOLT:RANG %s" % voltage_range.value
            )

        # CC mode
        else:
            # set source current, over voltage limit and current range for the output
            self.set_dc_supply_output_current(output_value)
            self._device_handle.write("SOUR:VOLT:LIM %s" % over_voltage_limit)
            self._device_handle.write(
                "SOUR:CURR:RANG %s" % current_range.value
            )

        logging.info(
            f"DC supply configured with the following options: {output_mode.name}, output value: {output_value} (Volts / Amps), (Voltage Range): {voltage_range.name}, (Current Range): {current_range.name}"
        )

    def configure_dc_supply_ramp_func(
        self,
        output_mode: DCOutputMode,
        ramp_value: float,
        ramp_steps: int = 100,
    ) -> None:
        """
        Configure the ramp function settings for the DC supply

        Args:
            output_mode (DCOutputMode): constant voltage or constant current
            ramp_value (float): the amplitude end position for the voltage/current ramp signal (0 to 1.05 A) / (0 to 31.5 V)
            ramp_steps (int): the number of steps for the voltage/current ramp signal (1 to 10000) steps (default: 100 steps)
        """
        # check arguments
        if not isinstance(output_mode, DCOutputMode):
            raise RuntimeError(
                f"Invalid type: {type(output_mode)} for output_mode. output_mode needs to be a valid enum of type: {DCOutputMode._name_}"
            )

        # first disable the output
        self.disable_dc_output()

        # CV mode
        if output_mode.value == DCOutputMode.CONSTANT_VOLTAGE.value:
            # set ramp voltage level and number of steps
            self._device_handle.write("VOLT:RAMP %s" % ramp_value)
            self._device_handle.write("VOLT:RAMP:STEP %s" % ramp_steps)

        # CC mode
        else:
            # set ramp current level and number of steps
            self._device_handle.write("CURR:RAMP %s" % ramp_value)
            self._device_handle.write("CURR:RAMP:STEP %s" % ramp_steps)

        logging.info(
            f"DC supply ramp function configured with the following options: {output_mode.name}, ramp value: {ramp_value} (Volts / Amps), ramp_steps: {ramp_steps} steps"
        )

    def configure_dc_supply_scan_func(
        self,
        output_mode: DCOutputMode,
        scan_value: float,
        scan_steps: int,
        scan_dwelling: float = 2.0,
    ) -> None:
        """
        Configure the scan function settings for the DC supply

        Args:
            output_mode (DCOutputMode): constant voltage or constant current
            scan_value (float): the amplitude end position for the voltage/current scan signal (0 to 1.05 A) / (0 to 31.5 V)
            scan_steps (int): the number of steps for the voltage/current scan signal (1 to 100) steps
            scan_dwelling (float): the dwelling time length for each step (1 to 99 sec) steps (default: 2 s)

        """
        # check arguments
        if not isinstance(output_mode, DCOutputMode):
            raise RuntimeError(
                f"Invalid type: {type(output_mode)} for output_mode. output_mode needs to be a valid enum of type: {DCOutputMode._name_}"
            )

        # first disable the output
        self.disable_dc_output()

        # CV mode
        if output_mode.value == DCOutputMode.CONSTANT_VOLTAGE.value:
            # set scan voltage level, number of steps and dwelling time
            self._device_handle.write("VOLT:SCAN %s" % scan_value)
            self._device_handle.write("VOLT:SCAN:STEP %s" % scan_steps)
            self._device_handle.write("VOLT:SCAN:DWEL %s" % scan_dwelling)

        # CC mode
        else:
            # set scan current level, number of steps and dwelling time
            self._device_handle.write("CURR:SCAN %s" % scan_value)
            self._device_handle.write("CURR:SCAN:STEP %s" % scan_steps)
            self._device_handle.write("CURR:SCAN:DWEL %s" % scan_dwelling)

        logging.info(
            f"DC supply scan function configured with the following options: {output_mode.name}, scan value: {scan_value} (Volts / Amps), scan_steps: {scan_steps} steps, dwelling time: {scan_dwelling} sec"
        )

    def configure_dc_supply_square_func(
        self,
        amplitude: float,
        frequency: int = 600,
        duty_cycle: float = 50,
        pulse_width: float = 0.000833,
    ) -> None:
        """
        Configure the square wave function settings for the DC supply

        Args:
            amplitude (float): voltage amplitude for the square wave output (0 to 30 V)
            frequency (int): frequency for the square-wave output in volts
                    range of values: (0.5, 2, 5, 6, 10, 15, 25, 30, 40, 50, 60, 75, 80, 100, 120, 150, 200, 240, 300, 400, 480, 600, 800,
                    1200, 1600, 2400, 4800) Hz (default 600 Hz)

            duty_cycle (float): duty cycle for the square-wave output (0 to 100)% (default 50%)
            pulse_width (float): pulse width for the square-wave output (0 to 1.6667) ms (default 0.8333) ms

        """
        # first disable the output
        self.disable_dc_output()

        self._device_handle.write("SQU:AMPL %s" % amplitude)
        self._device_handle.write("SQU:FREQ %s" % frequency)
        self._device_handle.write("SQU:DCYC %s" % duty_cycle)
        self._device_handle.write("SQU:PWID %s" % pulse_width)

        logging.info(
            f"DC supply sqaure wave function configured with the following options: amplitude: {amplitude} V, frequency: {frequency} Hz, duty cycle: {duty_cycle} %, pulse width: {pulse_width} sec"
        )

    def set_dc_supply_output_voltage(self, output_voltage: float) -> None:
        """Sets the constant voltage output value"""

        if output_voltage < 0 or output_voltage > MAX_VOLTAGE_LIMIT:
            raise RuntimeError(
                f"Invalid value for output_voltage. limits are: Min {0} V, Max {MAX_VOLTAGE_LIMIT} V"
            )
        self._device_handle.write("SOUR:VOLT:LEV:IMM:AMPL %s" % output_voltage)

    def set_dc_supply_output_current(self, output_current: float) -> None:
        """Sets the constant current output value"""

        if output_current < 0 or output_current > MAX_CURRENT_LIMIT:
            raise RuntimeError(
                f"Invalid value for output_current. limits are: Min {0} A, Max {MAX_VOLTAGE_LIMIT} A"
            )
        self._device_handle.write("SOUR:CURR:LEV:IMM:AMPL %s" % output_current)

    def set_dc_supply_protection_voltage(self, ovp_limit: float) -> None:
        """
        sets the over-voltage protection for the constant current output.
        If the load effect exceeds the over-voltage protection setting, the instrument output
        will be disabled.

        range: Min 0 V, Max 33 V

        remark: If the over-voltage protection value is set to a lesser value than the
                over-voltage limit value, the over-voltage limit value will be adjusted to equal
                the over-voltage protection value.


        """
        self._device_handle.write("VOLT:PROT %s V" % ovp_limit)

    def set_dc_supply_protection_current(self, ocp_limit: float) -> None:
        """
        sets the over-current protection for the constant voltage output.
        If the load effect exceeds the over-voltage protection setting, the instrument output
        will be disabled.

        range: Min 0 V, Max 1.1 A

        remark: If the over-current protection value is set to a lesser value than the
        over-current limit value, the over-current limit value will be adjusted to equal
        the over-current protection value.

        """
        self._device_handle.write("CURR:PROT %s A" % ocp_limit)

    def enable_dc_output(self) -> None:
        """enables the source output of the source multimeter (Output is active and the OUT annunciator turns on)"""
        self._device_handle.write("OUTP:STAT ON")

    def disable_dc_output(self) -> None:
        """disables the source output of the source multimeter (Output is on standby and the SBY annunciator turns on)"""

        self._device_handle.write("OUTP:STAT OFF")

    def set_dc_supply_soft_steps(self, num_steps: int = 1) -> None:
        """
        sets the soft start step for constant voltage or constant current output (default: 1)
        """
        self._device_handle.write("SST:STEP %s" % num_steps)

    def configure_multimeter(
        self,
        measure_mode: MultimeterMode,
        measure_range: MultimeterRange = MultimeterRange.AUTO,
        measure_resolution: MultimeterResolution = MultimeterResolution.MIN,
        signal_type: SignalType = SignalType.DC,
    ) -> None:
        """
        Configure the Multimeter measurement settings

            Args:
                measure_mode (MultimeterMode): electrical quantity to measure (e.g. Voltage, Current, Resistance)
                measure_range (MultimeterRange): range option for the measurement (default: Auto range)
                measure_resolution (MultimeterResolution): resolution used for measurement (default: MIN)
                signal_type (SignalType): measure AC or DC component (default: DC)
        """

        # check arguments
        if not isinstance(measure_mode, MultimeterMode):
            raise RuntimeError(
                f"Invalid type: {type(measure_mode)} for measure_mode. measure_mode needs to be a valid enum of type: {MultimeterMode._name_}"
            )

        if not isinstance(measure_range, MultimeterRange):
            raise RuntimeError(
                f"Invalid type: {type(measure_range)} for measure_range. measure_range needs to be a valid enum of type: {MultimeterRange._name_}"
            )

        if not isinstance(measure_resolution, MultimeterResolution):
            raise RuntimeError(
                f"Invalid type: {type(measure_resolution)} for measure_resolution. measure_resolution needs to be a valid enum of type: {MultimeterResolution._name_}"
            )

        if not isinstance(signal_type, SignalType):
            raise RuntimeError(
                f"Invalid type: {type(signal_type)} for signal_type. signal_type needs to be a valid enum of type: {SignalType._name_}"
            )

        # Configure for Voltage or current measurement
        if (
            measure_mode.value == MultimeterMode.VOLTAGE.value
            or measure_mode.value == MultimeterMode.CURRENT.value
        ):
            self._device_handle.write(
                "CONF:%s:%s %s, %s"
                % (
                    measure_mode.value,
                    signal_type.value,
                    measure_range.value,
                    measure_resolution.value,
                )
            )

        # Configure for Resistance measurement
        else:
            self._device_handle.write(
                "CONF:%s %s, %s"
                % (
                    measure_mode.value,
                    measure_range.value,
                    measure_resolution.value,
                )
            )

        logger.info(
            f"U3606 configured for following measuremnt setting: {signal_type.value, measure_mode.value, measure_range.value, measure_resolution.value}"
        )

    def measure(
        self,
        measure_mode: MultimeterMode,
        measure_range: MultimeterRange = MultimeterRange.AUTO,
        measure_resolution: MultimeterResolution = MultimeterResolution.MIN,
        signal_type: SignalType = SignalType.DC,
    ) -> float:
        """
        Configure multimeter for a measurement and returns a single measurement reading

            Args:
                measure_mode (MultimeterMode): electrical quantity to measure (e.g. Voltage, Current, Resistance)
                measure_range (MultimeterRange): range option for the measurement (default: Auto range)
                measure_resolution (MultimeterResolution): resolution used for measurement (default: MIN)
                signal_type (SignalType): measure AC or DC component (default: DC)

            Returns: measured value (reading from device)
        """

        # check arguments
        if not isinstance(measure_mode, MultimeterMode):
            raise RuntimeError(
                f"Invalid type: {type(measure_mode)} for measure_mode. measure_mode needs to be a valid enum of type: {MultimeterMode._name_}"
            )

        if not isinstance(measure_range, MultimeterRange):
            raise RuntimeError(
                f"Invalid type: {type(measure_range)} for measure_range. measure_range needs to be a valid enum of type: {MultimeterRange._name_}"
            )

        if not isinstance(measure_resolution, MultimeterResolution):
            raise RuntimeError(
                f"Invalid type: {type(measure_resolution)} for measure_resolution. measure_resolution needs to be a valid enum of type: {MultimeterResolution._name_}"
            )

        if not isinstance(signal_type, SignalType):
            raise RuntimeError(
                f"Invalid type: {type(signal_type)} for signal_type. signal_type needs to be a valid enum of type: {SignalType._name_}"
            )

        # voltage or current measurement
        if (
            measure_mode.value == MultimeterMode.VOLTAGE.value
            or measure_mode.value == MultimeterMode.CURRENT.value
        ):
            value = float(
                self._device_handle.query(
                    "MEAS:%s:%s? %s, %s"
                    % (
                        measure_mode.value,
                        signal_type.value,
                        measure_range.value,
                        measure_resolution.value,
                    )
                )
            )

        # resistance measurement
        else:
            value = float(
                self._device_handle.query(
                    "MEAS:%s? %s, %s"
                    % (
                        measure_mode.value,
                        measure_range.value,
                        measure_resolution.value,
                    )
                )
            )

        return float(value)

    def abort_measure(self) -> None:
        """
        aborts a measurement in progress

        may be useful to abort a measurement when the instrument is waiting for a trigger,
        for a long measurement, or for a long series of timed measurements.
        """
        self._device_handle.write("ABOR")

    def fetch(self) -> float:
        """
        fetches a measurement value from the instrument memory to the output buffer of the instrument

        Description:

        Transfers readings to the instrument output buffer where you canread them into your PC.
        The readings are not erased from the instrument memory when you read them.
        You can send this command multiple times to retrieve the same data in the instrument memory

        Remarks:

            - The FETCh? command will wait until the measurement is complete to terminate.

            - The FETCh? command obtains the primary display value on all conditions.
              If you would like to obtain raw data, please do not enable the CALCulate functions.

        """
        value = self._device_handle.query("FETC?")
        return float(value)

    def read(self) -> float:
        """
        reads a measurement value from the output buffer of the instrument

        Description:

            Changes the instrument triggering system from the “idle state” to the “wait-for-trigger” state
            Measurements will begin when the specified triggerconditions are satisfied following the receipt
            of the READ? command Readings are then sent immediately to the volatile memory and the output
            buffer of the instrument

        Remarks:

            - Normally, the READ? command obtains the primary display value. However, if
            the CALCulate:AVERage functions are enabled, the READ? command will return raw data

            - When the trigger source is set to IMMediate, sending the READ? command is similar to
            sending the INITiate[:IMMediate] command followed immediately by the FETCh? command.

        """
        value = self._device_handle.query("READ?")
        return float(value)

    def query(self, query_command: str) -> str:
        """send a generic query request (SCPI Syntax) to the instrument and return the result"""
        # wait for ongoing queries / commands to complete first
        self.wait()
        response = self._device_handle.query(query_command)
        return str(response)

    def write(self, send_command: str) -> None:
        """send a generic SCPI command to the instrument"""
        # wait for ongoing queries / commands to complete first
        self.wait()
        self._device_handle.write(send_command)

    def enable_continuous_mode(self) -> None:
        """
        enables the initiate continuous mode
        the measurements will be in free run (continuous) mode
        and you can just use the FETCh? command to acquire readings without triggering the source multimeter
        """

        self._device_handle.write("INIT:CONT ON")

    def disable_continuous_mode(self) -> None:
        """
        disables the initiate continuous mode

        Remark:
            - sending the INITiate[:IMMediate] and the READ? command will also set the state of the initiate continuous mode to OFF
        """

        self._device_handle.write("INIT:CONT OFF")

    def query_continuous_mode_status(self) -> int:
        """
        query the status of the initiate continuous mode (0: OFF, 1: ON)
        """

        status = self._device_handle.query("INIT:CONT?")
        return int(status)

    def query_multimeter_configuration(self) -> str:
        """returns the current measurement configuration / range"""
        value = self._device_handle.query("CONF?")
        return str(value)

    def query_dc_supply_over_voltage_limit(self) -> float:
        """returns the over-voltage limit value for CC mode"""
        value = self._device_handle.query("VOLT:LIM?")
        return float(value)

    def query_dc_supply_over_current_limit(self) -> float:
        """returns the over-current limit value for CV mode"""
        value = self._device_handle.query("CURR:LIM?")
        return float(value)

    def query_dc_supply_output_voltage(self) -> float:
        """returns the output voltage level for CV mode"""
        value = self._device_handle.query("VOLT?")
        return float(value)

    def query_dc_supply_output_current(self) -> float:
        """returns the output current level for CC mode"""
        value = self._device_handle.query("CURR?")
        return float(value)

    def query_dc_supply_output_status(self) -> int:
        """returns the output status for DC supply (1: Output enabled, 0: Standby mode)"""
        status = self._device_handle.query("OUTP?")
        return int(status)

    def query_dc_supply_sense_voltage(self) -> float:
        """returns the amplitude of the sensing voltage at the output for CC mode"""
        value = self._device_handle.query("SENS:VOLT?")
        return float(value)

    def query_dc_supply_sense_current(self) -> float:
        """returns the amplitude of the sensing current at the output for CV mode"""
        value = self._device_handle.query("SENS:CURR?")
        return float(value)

    def calibrate(self) -> int:
        """
        Performs a calibration of the multimeter using the specified calibration
        value (CALibration:VALue command) and returns a boolean value that represents the calibration status: “+0” (calibration passed)
        or “+1” (calibration failed).
        """
        cal_return_code = self._device_handle.query("CAL?")
        return int(cal_return_code)

    def enable_question_register(
        self, question_register: QuestionRegister
    ) -> None:
        """
        enables a bit in the enable register for the Questionable Data register group

        """
        # verfiy argument
        if not isinstance(question_register, QuestionRegister):
            raise RuntimeError(
                f"Invalid type: {type(question_register)} for question_register. question_register must be an enum of type: {QuestionRegister._name_}"
            )

        self._device_handle.write(
            "STAT:QUES:ENAB %s" % question_register.value
        )

    def query_enable_register(self) -> int:
        """
        reads the enable register and returns a decimal value that corresponds to the binary-weighted sum of all bits set in the register

        For example, if bit 8 (decimal value = 256) and bit 10 (decimal value = 1024) are enabled,
        the query command will return “+1280”

        """
        enabled_reg = self._device_handle.query("STAT:QUES:ENAB?")
        return int(enabled_reg)

    def query_event_register(self) -> int:
        """
        reads the event register for the Questionable Data register group
        and returns a decimal value which corresponds to the binary-weighted sum of all
        bits set in the condition register.

        For example, if bit 1 (decimal value = 2) and bit 9
        (decimal value = 512) are set, this command will return the decimal value +514

        """
        event_reg = self._device_handle.query("STAT:QUES?")
        return int(event_reg)

    def query_condition_register(self) -> int:
        """
        reads the condition register for the Questionable Data register
        group and returns a decimal value which corresponds to the binary-weighted sum
        of all bits set in the condition register.

        For example, if bit 0 (decimal value = 1) and bit 2 (decimal value = 4) are set,
        this command will return the decimal value “+5”

        """
        cond_reg = self._device_handle.query("STAT:QUES:COND?")
        return int(cond_reg)

    def set_calc_function(self, calc_func: CalcFunction) -> None:
        """selects the calculation function to be used by the mutlimeter on the perfromed measurements"""

        # verfiy argument
        if not isinstance(calc_func, CalcFunction):
            raise RuntimeError(
                f"Invalid type: {type(calc_func)} for calc_func. calc_func must be an enum of type: {CalcFunction._name_}"
            )

        self._device_handle.write("CALC:FUNC %s" % calc_func.value)

    def query_calc_function(self) -> str:
        """returns the currently selected calculation function"""
        calc_func = self._device_handle.query("CALC:FUNC?")
        return str(calc_func)

    def query_calc_state(self) -> int:
        """returns a boolean value that represents the current calculation state: 0 (OFF) or 1 (TRUE)"""
        calc_state = self._device_handle.query("CALC?")
        return int(calc_state)

    def enable_calc(self) -> None:
        """turns on the calculation subsystem, and thus the selected calculation function"""
        self._device_handle.write("CALC ON")

    def disable_calc(self) -> None:
        """
        turns off the calculation subsystem, and thus the selected calculation function

        remark: calculation subsystem is turned off when the calculation function is changed
        """
        self._device_handle.write("CALC OFF")

    def read_calc_average(self) -> float:
        """
        returns a numeric value that represents the mathematical average (mean) of all readings taken since averaging was enabled

        pre-requisite: calculation function selected and enabled
        remark: 0 is retruned if there is no data is available
        """

        avg_val = self._device_handle.query("CALC:AVER:AVER?")
        return float(avg_val)

    def read_calc_max(self) -> float:
        """
        returns a numeric value that represents the highest value recorded since averaging was enabled

        pre-requisite: calculation function selected and enabled
        remark: 0 is retruned if there is no data is available
        """

        max_val = self._device_handle.query("CALC:AVER:MAX?")
        return float(max_val)

    def read_calc_min(self) -> float:
        """
        returns a numeric value that represents the lowest value recorded since averaging was enabled

        pre-requisite: calculation function selected and enabled
        remark: 0 is retruned if there is no data is available
        """

        min_val = self._device_handle.query("CALC:AVER:MIN?")
        return float(min_val)

    def read_calc_present(self) -> float:
        """
        returns a numeric value that represents the last value recorded since averaging was enabled

        pre-requisite: calculation function selected and enabled
        remark: 0 is retruned if there is no data is available
        """
        pres_val = self._device_handle.query("CALC:AVER:PRES?")
        return float(pres_val)

    def set_db_func_reference(self, ref_val: float) -> None:
        """
        stores a reference value in the dB reference register of the instrument, which is used for the dB calculation function

        range of values: -120 to 120 (default: 0)
        """
        self._device_handle.write("CALC:DB:REF %s" % ref_val)

    def set_dbm_func_reference(self, ref_val: int) -> None:
        """
        selects the dBm reference resistance. This reference value affects both the dBm and dB calculation functions

        range of values: 1 ohm to 9999 ohms (default: 600 ohms)
        """
        self._device_handle.write("CALC:DBM:REF %s" % ref_val)

    def set_hold_func_variation(self, var_val: float) -> None:
        """
        sets the variation percentage of the hold function.
        when the variation is set to 0, data hold is enabled. Otherwise, refresh hold is enabled

        range of values: 0% to 100% (default: 10%)

        """
        self._device_handle.write("CALC:HOLD:VAR %s" % var_val)

    def set_hold_func_threshold(self, thr_val: float) -> None:
        """
        sets the threshold of the hold function.
        range of values: 0.0% to 9,9% (default: 0.5%)

        """
        self._device_handle.write("CALC:HOLD:THR %s" % thr_val)

    def set_limit_func_limits(
        self, upper_limit_val: float, lower_limit_val: float
    ) -> None:
        """
        sets the upper and lower limit for the present measurement function (used in limit testing)

        range of values: Voltage measurement (-1200 V to 1200 V), Current measurement (-12 A to 12 A), default: 0

        """
        self._device_handle.write("CALC:LIM:UPP %s" % upper_limit_val)
        self._device_handle.write("CALC:LIM:LOW %s" % lower_limit_val)

    def set_null_func_offset(self, offset_val: float) -> None:
        """
        stores an offset value in the Null register of the instrument for the NULL calculation function

        range of values: Voltage measurement (-1200 V to 1200 V), Current measurement (-12 A to 12 A), default: 0

        """
        self._device_handle.write("CALC:NULL:OFFS %s" % offset_val)

    def enable_data_logging(self) -> None:
        """
        starts the U3606 data logging operation

        Remarks:
            - The data logging operation will be stopped automatically for the following cases:
                - The data logging operation is completed
                - The U3606 memory is full.

            - If there is data stored in the U3606, the new data will be appended to the old
            data. When the U3606 is recording, it will not accept any setting commands
        """
        self._device_handle.write("LOG ON")

    def disable_data_logging(self) -> None:
        """
        stops the U3606 data logging operation
        """
        self._device_handle.write("LOG OFF")

    def query_data_logging_status(self) -> int:
        """
        returns the status of the data logging operation 1 (ON), 0 (OFF)
        """
        status = self._device_handle.query("LOG?")
        return int(status)

    def delete_logged_data(self) -> None:
        """
        deletes all previously stored logging data
        """
        self._device_handle.write("LOG:DATA:DEL")

    def reset_data_logging_index(self) -> None:
        """
        resets the logging data load index to the start point
        """
        self._device_handle.write("LOG:LOAD DATA")

    def read_logged_data(self) -> Union[float, str]:
        """
        return the previously stored logging data according to the load index

        Remarks:

        - Apply the LOG:LOAD DATA command to reset the load index to the start
        point.

        -  You will have to send the LOG:DATA? command multiple times to obtain all
        the logging data until the END response is received on your application.

        - The data index could be changed if you send another command between the
        LOG:DATA? commands
        """
        import re

        logged_data = self._device_handle.query("LOG:DATA?")

        # match to find type of data is numeric
        if re.match(r"^-?\d+(?:\.\d+)$", logged_data) is None:
            return str(logged_data)
        else:
            return float(logged_data)


### Context manager for using the power supply and mulitmeter functions within 'with' block ###
class KeysightU3606SupplyAndMultimeter:
    """
    Context manger to access Keysight U3606 device and configure the power supply / multimeter instrument
    """

    def __init__(
        self,
        pyvisa_manager: pyvisa.ResourceManager,
        serial_no: str,
        dc_output_mode: Optional[DCOutputMode] = None,
        mulitimeter_mode: Optional[MultimeterMode] = None,
        dc_output_value: Optional[
            float
        ] = 0.0,  # Voltage in Volts or Current in Amps based on DC output mode
        dc_output_volt_range: Optional[
            DCOutputVoltageRange
        ] = DCOutputVoltageRange.AUTO,
        dc_output_curr_range: Optional[
            DCOutputCurrentRange
        ] = DCOutputCurrentRange.AUTO,
        multimeter_range: Optional[MultimeterRange] = MultimeterRange.AUTO,
        multimeter_res: Optional[
            MultimeterResolution
        ] = MultimeterResolution.MIN,
        multimeter_signal: Optional[SignalType] = SignalType.DC,
    ):
        self.pyvisa_manager = pyvisa_manager
        self.serial_no = serial_no
        self.pyvisa_devices = self.pyvisa_manager.list_resources()
        self.keysgiht_u3606 = KeysightU3606Wrapper(
            serial_no, self.pyvisa_manager, self.pyvisa_devices
        )
        self.dc_output_mode = dc_output_mode
        self.dc_output_value: float = dc_output_value
        self.dc_output_volt_range = dc_output_volt_range
        self.dc_output_curr_range = dc_output_curr_range
        self.mulitimeter_mode = mulitimeter_mode
        self.multimeter_range = multimeter_range
        self.multimeter_res = multimeter_res
        self.multimeter_signal = multimeter_signal

    def __enter__(self):
        self.keysgiht_u3606.open()
        if self.mulitimeter_mode is not None:
            self.keysgiht_u3606.configure_multimeter(
                self.mulitimeter_mode,
                self.multimeter_range,
                self.multimeter_res,
                self.multimeter_signal,
            )
        if self.dc_output_mode is not None:
            self.keysgiht_u3606.configure_dc_supply(
                self.dc_output_mode,
                self.dc_output_value,
                voltage_range=self.dc_output_volt_range,
                current_range=self.dc_output_curr_range,
            )
        return self.keysgiht_u3606

    def __exit__(self, exc_type, exc_value, traceback):
        self.keysgiht_u3606.clear_presets()
        self.keysgiht_u3606.clear_status()
        self.keysgiht_u3606.close()
