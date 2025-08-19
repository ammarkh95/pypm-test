"""
Wrapper for automating SMU functions of Keyisght U2723A

The wrapper uses the PyVisa library to communicate with the instrument using VISA standard protocol

# Important: keysight Libraries IO Suite need to be installed on the test station:
# (https://www.keysight.com/zz/en/lib/software-detail/computer-software/io-libraries-suite-downloads-2175637.html)
#
# Important: Agilent Measurement Manager installed with pre-requisites on test station:
# (https://www.keysight.com/zz/en/lib/software-detail/computer-software/measurement-manager-amm-883008.html)

"""

import logging
import pyvisa
from enum import Enum
from typing import List, Tuple

logger = logging.getLogger("Keyisght-U2723A-Wrapper")
logger.setLevel(logging.DEBUG)


MAX_VOLTAGE_LIMIT = 20  # V
MIN_VOLTAGE_LIMIT = -20  # V

MAX_CURRENT_LIMIT = 0.12  # A
MIN_CURRENT_LIMIT = -0.12  # A


class SMUChannel(Enum):
    """
    Enumeration of U2723A SMU channels
    """

    @classmethod
    def list(cls):
        return list(map(lambda c: cls.__name__ + "." + c.name, cls))

    CH1 = 1
    CH2 = 2
    CH3 = 3


class SMUVoltageRange(Enum):
    """
    Enumeration of supported voltage ranges for Keyishgt U2723A
    """

    @classmethod
    def list(cls):
        return list(map(lambda c: cls.__name__ + "." + c.name, cls))

    R2V = "R2V"  # 2 V range
    R20V = "R20V"  # 20 V range


class SMUCurrentRange(Enum):
    """
    Enumeration of supported current ranges for Keyishgt U2723A
    """

    @classmethod
    def list(cls):
        return list(map(lambda c: cls.__name__ + "." + c.name, cls))

    R1uA = "R1uA"  # 1 μA range
    R10uA = "R10uA"  # 10 μA range
    R100uA = "R100uA"  # 100 μA range
    R1mA = "R1mA"  # 1 mA range
    R10mA = "R10mA"  # 10 mA range
    R120mA = "R120mA"  # 120 mA range


class SMUMemoryList(Enum):
    """
    Enumeration of available buffer memories for Keyishgt U2723A
    Each channel has two memory lists
    """

    @classmethod
    def list(cls):
        return list(map(lambda c: cls.__name__ + "." + c.name, cls))

    Mem1 = 1
    Mem2 = 2


class KeysightU2723Wrapper:
    """Wrapper class for utilitzing the SMU functions of Keysight U2723A"""

    def __init__(
        self,
        serial_no: str,
        pyvisa_device_manager: pyvisa.ResourceManager,
        pyvisa_devices: Tuple[str, ...],
    ) -> None:
        """Iniitalize Pyvisa interface and detect connected instruments"""

        self._device_manager = pyvisa_device_manager
        pyvisa.log_to_screen(logging.INFO)
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
        """Opens the connection to a USB connected U2723A"""
        for device in self._detected_devices:
            # Scan for USB devices
            if device.find("USB") == 0 and self._serial_no in str(device):
                self._device_url = device
                self._device_handle = self._device_manager.open_resource(
                    self._device_url
                )
                # set long timeout for U2723A (greater than 5 seconds) as recommended by user manual for array measurements
                self._device_handle.timeout = 120e3  # (2 minutes)
                device_info = self._device_handle.query("*IDN?")
                # ckech it is a U2723A mode instrument
                if "U2723A" in str(device_info):
                    logger.info(
                        f"Opened connection to instrument: {device_info}"
                    )
                    self._target_device_found = True
                    return None

        if not self._target_device_found:
            raise RuntimeError(
                f"Could not detect target device of model: U2723A and serial no: {self._serial_no}"
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
        logger.info("U2723A reset to default factory state")

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

    def query_status_operation(self) -> int:
        """
        This query command returns the value of the Operation Status Condition register.
        The Condition register is a read-only register, which holds the live (unlatched)
        operational status of the instrument. Reading the Operation Condition register
        does not clear it

        The returned value is the binary-weighted sum of all bits set in the register

        The following table lists the bit definitions for the Operation Status registers:

                0 to 1 Not Used 0 0 is returned.

                2 DTG1-tran 4 The transient system has received a trigger signal and operation is running in
                channel 1.

                3 DTG2-tran 8 The transient system has received a trigger signal and operation is running in
                channel 2.

                4 DTG3-tran 16 The transient system has received a trigger signal and operation is running in
                channel 3.

                5 WTG1-tran 32 The transient system is waiting for a trigger in channel 1.

                6 WTG2-tran 64 The transient system is waiting for a trigger in channel 2.

                7 WTG3-tran 128 The transient system is waiting for a trigger in channel 3.

                8 to 15 Not Used 0 0 is returned.

        """
        response = self._device_handle.query("STAT:OPER:COND?")
        return int(response)

    def query_system_errors(self) -> str:
        """
        reads and clears one error from the instrument's error queue
        A record of up to 20 errors can be stored in the U2723A error queue

        For SCPI command errors, this command returns the following format string:
        <Number,"Error String">
        """
        error_queue = self._device_handle.query("SYST:ERR?")
        return str(error_queue)

    def set_smu_source_current(
        self, channel: SMUChannel, src_current: float
    ) -> None:
        """
        Sets the actual current magnitude of the unswept output signal in terms of the
        present operating units.

        The units are set to the default value, or alternately to a
        different value under the UNIT subsystem. The AMPLitude may be used to specify
        the level for either a time varying or non-time varying signal.

        """
        if src_current < MIN_CURRENT_LIMIT or src_current > MAX_CURRENT_LIMIT:
            raise RuntimeError(
                f"Invalid value for source current. limits are: Min {MIN_CURRENT_LIMIT} A, Max {MAX_CURRENT_LIMIT} A"
            )

        self._device_handle.write(
            "SOUR:CURR:LEV:IMM:AMPL %s, (@%s)" % (src_current, channel.value)
        )

    def set_smu_source_voltage(
        self, channel: SMUChannel, src_voltage: float
    ) -> None:
        """
        Sets the actual voltage magnitude of the unswept output signal in terms of the
        present operating units.

        The units are set to the default value, or alternately to a
        different value under the UNIT subsystem. The AMPLitude may be used to specify
        the level for either a time varying or non-time varying signal
        """
        if src_voltage < MIN_VOLTAGE_LIMIT or src_voltage > MAX_VOLTAGE_LIMIT:
            raise RuntimeError(
                f"Invalid value for source current. limits are: Min {MIN_VOLTAGE_LIMIT} V, Max {MAX_VOLTAGE_LIMIT} V"
            )
        self._device_handle.write(
            "SOUR:VOLT:LEV:IMM:AMPL %s, (@%s)" % (src_voltage, channel.value)
        )

    def set_smu_voltage_limit(
        self, channel: SMUChannel, voltage_limit: float
    ) -> None:
        """
        This command sets the maximum bounds on the output voltage value. Output
        voltage level will be clamped to the limit value if the voltage level has exceeded
        the bounds set
        """
        self._device_handle.write(
            "SOUR:VOLT:LIM %s, (@%s)" % (voltage_limit, channel.value)
        )

    def set_smu_current_limit(
        self, channel: SMUChannel, current_limit: float
    ) -> None:
        """
        This command sets the maximum bounds on the output current value. Output
        current level will be clamped to the limit value if the current level has exceeded
        the bounds set
        """
        self._device_handle.write(
            "SOUR:CURR:LIM %s, (@%s)" % (current_limit, channel.value)
        )

    def set_smu_current_range(
        self, channel: SMUChannel, current_range: SMUCurrentRange
    ) -> None:
        """
        This command sets the output current range. At *RST, low current range is selected.
        """
        self._device_handle.write(
            "SOUR:CURR:RANG %s, (@%s)" % (current_range.value, channel.value)
        )

    def set_smu_voltage_range(
        self, channel: SMUChannel, voltage_range: SMUVoltageRange
    ) -> None:
        """
        This command sets the output voltage range. At *RST, low voltage range is selected
        """
        self._device_handle.write(
            "SOUR:VOLT:RANG %s, (@%s)" % (voltage_range.value, channel.value)
        )

    def set_smu_trigger_voltage(
        self, channel: SMUChannel, trigger_voltage: float
    ) -> None:
        """
        This command sets the voltage trigger level of the specified output channel. Units
        are in voltage. The triggered level is a stored value that is transferred to the output
        when an output step is triggered.
        """
        self._device_handle.write(
            "SOUR:VOLT:TRIG %s, (@%s)" % (trigger_voltage, channel.value)
        )

    def set_smu_trigger_current(
        self, channel: SMUChannel, trigger_current: float
    ) -> None:
        """
        This command sets the current trigger level of the specified output channel. Units
        are in amperes. The triggered level is a stored value that is transferred to the
        output when an output step is triggered
        """
        self._device_handle.write(
            "SOUR:CURR:TRIG %s, (@%s)" % (trigger_current, channel.value)
        )

    def enable_smu_channel(self, channel: SMUChannel) -> None:
        """enables the output of given SMU channel"""
        self._device_handle.write("OUTP 1, (@%s)" % channel.value)

    def disable_smu_channel(self, channel: SMUChannel) -> None:
        """disables the output of given SMU channel"""
        self._device_handle.write("OUTP 0, (@%s)" % channel.value)

    def set_sweep_points(self, channel: SMUChannel, n_points: int) -> None:
        """
        This command defines the number of points in a measurement on models that
        have measurement controls.
        Programmed values can range from 1 to 4096 (4K)
        """
        self._device_handle.write(
            "SENS:SWE:POIN %s, (@%s)" % (n_points, channel.value)
        )
        logger.info(
            f"SMU channel: {channel.name} sweep points set to: {n_points}"
        )

    def set_sweep_interval(
        self, channel: SMUChannel, interval_ms: int
    ) -> None:
        """
        This command defines the time period between samples in milliseconds on
        models that have measurement controls. Programmed values can range from
        1 to 32767
        """
        self._device_handle.write(
            "SENS:SWE:TINT %s, (@%s)" % (interval_ms, channel.value)
        )
        logger.info(
            f"SMU channel: {channel.name} sweep interval set to: {interval_ms} ms"
        )

    def query_current_sampling_time(self, channel: SMUChannel) -> float:
        """
        Query the sampling time for a single current measurement point. The
        parameter has a unit of seconds.
        """
        curr_sample_sec = self._device_handle.query(
            "SENS:CURR:APER? (@%s)" % channel.value
        )
        return float(curr_sample_sec)

    def query_voltage_sampling_time(self, channel: SMUChannel) -> float:
        """
        Query the sampling time for a single voltage measurement point. The
        parameter has a unit of seconds.
        """
        volt_sample_sec = self._device_handle.query(
            "SENS:VOLT:APER? (@%s)" % channel.value
        )
        return float(volt_sample_sec)

    def measure_current_scalar(self, channel: SMUChannel) -> float:
        """
        Queries the current measured across the current sense resistor inside the
        U2722A/U2723A

        Args:
            - channel: SMU channle to use for measurement

        Returns:  a single current measurement (A)
        """

        curr_meas = self._device_handle.query(
            "MEAS:SCAL:CURR? (@%s)" % channel.value
        )
        return float(curr_meas)

    def measure_voltage_scalar(self, channel: SMUChannel) -> float:
        """
        Queries the voltage measured at the sense terminals of the U2722A/U2723A for
        the specified channel

        Args:
            - channel: SMU channle to use for measurement

        Returns:  a single voltage measurement (V)
        """
        volt_meas = self._device_handle.query(
            "MEAS:SCAL:VOLT? (@%s)" % channel.value
        )
        return float(volt_meas)

    def measure_voltage_array(self, channel: SMUChannel) -> List[float]:
        """
        This query initiates and triggers a measurement and returns an array containing
        the digitized output voltage in volts.

        The sampling rate is set by:
        SENSe:SWEep:TINTerval

        whereas the returned number of points is set by:
        SENSe:SWEep:POINts

            Args:
                - channel: SMU channle to use for measurement

            Returns:  Array containg measured voltages (V)
        """
        volt_meas_arr = self._device_handle.query(
            "MEAS:ARR:VOLT? (@%s)" % channel.value
        )

        return [float(i) for i in volt_meas_arr.split(",")]

    def measure_current_array(self, channel: SMUChannel) -> List[float]:
        """
        This query initiates and triggers a measurement and returns an array containing
        the digitized output current in amperes.

        The sampling rate is set by:
        SENSe:SWEep:TINTerval

        whereas the returned number of points is set by:
        SENSe:SWEep:POINts

            Args:
                - channel: SMU channle to use for measurement

            Returns:  Array containg measured currents (A)
        """
        curr_meas_arr = self._device_handle.query(
            "MEAS:ARR:CURR? (@%s)" % channel.value
        )

        return [float(i) for i in curr_meas_arr.split(",")]

    def abort(self, channel: SMUChannel) -> None:
        """
        This command cancels any transient trigger actions and returns the transient
        trigger state back to idle. It also resets the WTG transient bits in the Operation
        Condition Status register.
        """
        self._device_handle.write("ABOR:TRAN (@%s)" % channel.value)

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

    def enable_transient_trigger(self, channel: SMUChannel) -> None:
        """
        This command enables the transient trigger system. When a transient or output
        trigger is initiated, an event on a selected trigger source causes the specified
        triggering action to occur. If the trigger system is not initiated, all triggers are
        ignored.
        """
        self._device_handle.write("INIT:TRAN (@%s)" % channel.value)

    def read_memory_list_results(self, channel: SMUChannel) -> List[float]:
        """
        This command reads the data result after executing the commands in the channel
        active memory list through a remote or hardware trigger action

        Returned Query Format:
        <NR3>{,<NR3>}
        The reading is in the form of +9.99999999E+10 when output is set to OFF or no
        measurement is made during the memory list commands execution.
        Array values responses are separated by commas.

        """
        results = self._device_handle.query(
            "MEM:LIST:DATA? (@%s)" % channel.value
        )
        return [float(i) for i in results.split(",")]

    def trigger_memory_list(self, channel: SMUChannel) -> None:
        """
        This command executes the active memory list commands for the specified
        channel
        """
        self._device_handle.write("MEM:TRIG (@%s)" % channel.value)

    def query_smu_output_status(self, channel: SMUChannel) -> int:
        """returns the output status for SMU channel (1: Output enabled, 0: Standby mode)"""
        status = self._device_handle.query("OUTP? (@%s)" % channel.value)
        return int(status)

    def calibrate(self) -> int:
        """
        This command performs a self-calibration of the instrument and returns a pass/
        fail indication.
        """
        cal_return_code = self._device_handle.query("CAL?")
        return int(cal_return_code)
