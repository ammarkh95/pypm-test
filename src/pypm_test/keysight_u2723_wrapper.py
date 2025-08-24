"""
Wrapper for automating SMU functions of Keyisght U2723

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
from typing import List, Tuple, Optional

logger = logging.getLogger("Keyisght-U2723-Wrapper")
logger.setLevel(logging.INFO)


MAX_VOLTAGE_LIMIT = 20  # V
MIN_VOLTAGE_LIMIT = -20  # V

MAX_CURRENT_LIMIT = 0.12  # A
MIN_CURRENT_LIMIT = -0.12  # A


### Enum Classes for source measure unit supported channels / power output / measure options ###
class SMUChannel(Enum):
    """
    Enumeration of U2723 SMU channels
    """

    @classmethod
    def list(cls):
        return list(map(lambda c: cls.__name__ + "." + c.name, cls))

    CH1 = 1
    CH2 = 2
    CH3 = 3


class SMUChannelMode(Enum):
    """
    Enumeration of U2723 SMU channel modes
    """

    @classmethod
    def list(cls):
        return list(map(lambda c: cls.__name__ + "." + c.name, cls))

    SVMI = 1  # Source Voltage , Measure Current
    SIMV = 2  # Source Current, Measure Voltage


class SMUVoltageRange(Enum):
    """
    Enumeration of supported voltage ranges for Keyishgt U2723
    """

    @classmethod
    def list(cls):
        return list(map(lambda c: cls.__name__ + "." + c.name, cls))

    R2V = "R2V"  # 2 V range
    R20V = "R20V"  # 20 V range


class SMUCurrentRange(Enum):
    """
    Enumeration of supported current ranges for Keyishgt U2723
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
    Enumeration of available buffer memories for Keyishgt U2723
    Each channel has two memory lists
    """

    @classmethod
    def list(cls):
        return list(map(lambda c: cls.__name__ + "." + c.name, cls))

    Mem1 = 1
    Mem2 = 2


### Wrapper class implementing SCPI functions ###
class KeysightU2723Wrapper:
    """Wrapper class for utilitzing the SMU functions of Keysight U2723"""

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
        """Opens the connection to a USB connected U2723"""
        for device in self._detected_devices:
            # Scan for USB devices
            if device.find("USB") == 0 and self._serial_no in str(device):
                self._device_url = device
                self._device_handle = self._device_manager.open_resource(
                    self._device_url
                )
                # set long timeout for U2723 (greater than 5 seconds) as recommended by user manual for array measurements
                self._device_handle.timeout = 120e3  # (2 minutes)
                device_info = self._device_handle.query("*IDN?")
                # ckech it is a U2723 mode instrument
                if "U2723" in str(device_info):
                    logger.info(
                        f"Opened connection to instrument: {device_info}"
                    )
                    self._target_device_found = True
                    return None

        if not self._target_device_found:
            raise RuntimeError(
                f"Could not detect target device of model: U2723 and serial no: {self._serial_no}"
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
        logger.info("U2723 reset to default factory state")

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
        A record of up to 20 errors can be stored in the U2723 error queue

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
        U2722/U2723

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
        Queries the voltage measured at the sense terminals of the U2722A/U2723 for
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


### Context manager for using the source measure unit functions within 'with' block ###
class KeysightU2723SourceMeasureUnit:
    """
    Context manger to access and configure Keysight U2723 device
    """

    def __init__(
        self,
        pyvisa_manager: pyvisa.ResourceManager,
        serial_no: str,
        smu_channel_1_output_mode: Optional[SMUChannelMode] = None,
        smu_channel_1_output_value: Optional[float] = None,
        smu_channel_1_voltage_range: Optional[SMUVoltageRange] = None,
        smu_channel_1_current_range: Optional[SMUCurrentRange] = None,
        smu_channel_2_output_mode: Optional[SMUChannelMode] = None,
        smu_channel_2_output_value: Optional[float] = None,
        smu_channel_2_voltage_range: Optional[SMUVoltageRange] = None,
        smu_channel_2_current_range: Optional[SMUCurrentRange] = None,
        smu_channel_3_output_mode: Optional[SMUChannelMode] = None,
        smu_channel_3_output_value: Optional[float] = None,
        smu_channel_3_voltage_range: Optional[SMUVoltageRange] = None,
        smu_channel_3_current_range: Optional[SMUCurrentRange] = None,
    ):
        self.pyvisa_manager = pyvisa_manager
        self.serial_no = serial_no
        self.pyvisa_devices = self.pyvisa_manager.list_resources()
        self.keysgiht_u2723 = KeysightU2723Wrapper(
            serial_no, self.pyvisa_manager, self.pyvisa_devices
        )
        self.smu_channel_1_output_mode = smu_channel_1_output_mode
        self.smu_channel_1_output_value = smu_channel_1_output_value
        self.smu_channel_1_voltage_range = smu_channel_1_voltage_range
        self.smu_channel_1_current_range = smu_channel_1_current_range
        self.smu_channel_2_output_mode = smu_channel_2_output_mode
        self.smu_channel_2_output_value = smu_channel_2_output_value
        self.smu_channel_2_voltage_range = smu_channel_2_voltage_range
        self.smu_channel_2_current_range = smu_channel_2_current_range
        self.smu_channel_3_output_mode = smu_channel_3_output_mode
        self.smu_channel_3_output_value = smu_channel_3_output_value
        self.smu_channel_3_voltage_range = smu_channel_3_voltage_range
        self.smu_channel_3_current_range = smu_channel_3_current_range

    def __enter__(self):
        self.keysgiht_u2723.open()
        # CH1
        if (self.smu_channel_1_voltage_range is not None) and (
            self.smu_channel_1_current_range is not None
        ):
            self.keysgiht_u2723.set_smu_voltage_range(
                SMUChannel.CH1, self.smu_channel_1_voltage_range
            )
            self.keysgiht_u2723.set_smu_current_range(
                SMUChannel.CH1, self.smu_channel_1_current_range
            )

        if (self.smu_channel_1_output_mode == SMUChannelMode.SVMI) and (
            self.smu_channel_1_output_value is not None
        ):
            self.keysgiht_u2723.set_smu_source_voltage(
                SMUChannel.CH1, self.smu_channel_1_output_value
            )

        if (self.smu_channel_1_output_mode == SMUChannelMode.SIMV) and (
            self.smu_channel_1_output_value is not None
        ):
            self.keysgiht_u2723.set_smu_source_current(
                SMUChannel.CH1, self.smu_channel_1_output_value
            )
        # CH2
        if (self.smu_channel_2_voltage_range is not None) and (
            self.smu_channel_2_current_range is not None
        ):
            self.keysgiht_u2723.set_smu_voltage_range(
                SMUChannel.CH2, self.smu_channel_2_voltage_range
            )
            self.keysgiht_u2723.set_smu_current_range(
                SMUChannel.CH2, self.smu_channel_2_current_range
            )

        if (self.smu_channel_2_output_mode == SMUChannelMode.SVMI) and (
            self.smu_channel_2_output_value is not None
        ):
            self.keysgiht_u2723.set_smu_source_voltage(
                SMUChannel.CH2, self.smu_channel_2_output_value
            )

        if (self.smu_channel_2_output_mode == SMUChannelMode.SIMV) and (
            self.smu_channel_2_output_value is not None
        ):
            self.keysgiht_u2723.set_smu_source_current(
                SMUChannel.CH2, self.smu_channel_2_output_value
            )
        # CH3
        if (self.smu_channel_3_voltage_range is not None) and (
            self.smu_channel_3_current_range is not None
        ):
            self.keysgiht_u2723.set_smu_voltage_range(
                SMUChannel.CH3, self.smu_channel_3_voltage_range
            )
            self.keysgiht_u2723.set_smu_current_range(
                SMUChannel.CH3, self.smu_channel_3_current_range
            )

        if (self.smu_channel_3_output_mode == SMUChannelMode.SVMI) and (
            self.smu_channel_3_output_value is not None
        ):
            self.keysgiht_u2723.set_smu_source_voltage(
                SMUChannel.CH3, self.smu_channel_3_output_value
            )

        if (self.smu_channel_3_output_mode == SMUChannelMode.SIMV) and (
            self.smu_channel_3_output_value is not None
        ):
            self.keysgiht_u2723.set_smu_source_current(
                SMUChannel.CH3, self.smu_channel_3_output_value
            )

        return self.keysgiht_u2723

    def __exit__(self, exc_type, exc_value, traceback):
        self.keysgiht_u2723.clear_presets()
        self.keysgiht_u2723.clear_status()
        self.keysgiht_u2723.close()


### Utility functions for Keysight U2723 ###
def smu_source_voltage_measure_current(
    smu: KeysightU2723Wrapper,
    channel: SMUChannel,
    V_out: float,
    memory_list: SMUMemoryList = SMUMemoryList.Mem1,
    measure_count: int = 1,
    measure_delay_ms: Optional[int] = None,
    current_limit: float = 0.1,  # 100 mA
    voltage_range: SMUVoltageRange = SMUVoltageRange.R20V,
    current_range: SMUVoltageRange = SMUCurrentRange.R120mA,
) -> None:
    """
    Generate a memeory list to supply voltage and measure current
    NOTE. for execution of memory list. call: smu.trigger_memory_list(channel)
    NOTE. When the measurement results reaches 200, the next result will wrap back and replace the first result at the buffer

    Args:
        smu (KeysightU2723Wrapper): handle to SMU
        channel (SMUChannel): target SMU channel
        V_out (float): output voltage to be set on channel by the SMU
        memory_list (SMUMemoryList, optional): memory list to use Defaults to SMUMemoryList.Mem1.
        measure_count (int, optional): number of current measurements to perform. Defaults to 1.
    """

    # select memory list and clear existing commands
    smu.write("MEM:LIST %s, (@%s)" % (memory_list.value, channel.value))
    smu.write("MEM:LIST:CLEAR (@%s)" % (channel.value))

    # set voltage ,crurent ranges and current limit for the channel
    smu.write("MEM:VOLT:RANG %s, (@%s)" % (voltage_range.value, channel.value))
    smu.write("MEM:CURR:RANG %s, (@%s)" % (current_range.value, channel.value))
    smu.write("MEM:CURR:LIM %s, (@%s)" % (current_limit, channel.value))
    # enable auto delay between source commands
    smu.write("MEM:SOUR:DEL:AUTO ON, (@%s)" % (channel.value))
    # source voltage, enable output
    smu.write("MEM:VOLT:SOUR %s, (@%s)" % (V_out, channel.value))
    smu.write("MEM:OUTP ON, (@%s)" % (channel.value))

    # add local delay before measure if desired
    if measure_delay_ms:
        smu.write(
            "MEM:SOUR:DEL SING,%s,(@%s)" % (measure_delay_ms, channel.value)
        )
        smu.write("MEM:VOLT:SOUR %s, (@%s)" % (V_out, channel.value))

    # make current measurements
    for _ in range(measure_count):
        smu.write("MEM:CURR:MEAS (@%s)" % (channel.value))

    # switch off output at the end of measurement
    smu.write("MEM:OUTP OFF, (@%s)" % (channel.value))

    # stores all commands from the active memory list into the nonvolatile memory
    smu.write("MEM:LIST:STOR (@%s)" % (channel.value))


def smu_source_current_measure_voltage(
    smu: KeysightU2723Wrapper,
    channel: SMUChannel,
    I_out: float,
    memory_list: SMUMemoryList = SMUMemoryList.Mem1,
    measure_count: int = 1,
    measure_delay_ms: Optional[int] = None,
    voltage_limit: float = 5,  # 5 V
    voltage_range: SMUVoltageRange = SMUVoltageRange.R20V,
    current_range: SMUVoltageRange = SMUCurrentRange.R120mA,
) -> None:
    """
    Generate a memeory list to supply current and measure voltage
    NOTE. for execution of memory list. call: smu.trigger_memory_list(channel)
    NOTE. When the measurement results reaches 200, the next result will wrap back and replace the first result at the buffer

    Args:
        smu (KeysightU2723Wrapper): handle to SMU
        channel (SMUChannel): target SMU channel
        I_out (float): output current to be set on channel by the SMU
        memory_list (SMUMemoryList, optional): memory list to use Defaults to SMUMemoryList.Mem1.
        measure_count (int, optional): number of voltage measurements to perform. Defaults to 1.
    """

    # select memory list and clear existing commands
    smu.write("MEM:LIST %s, (@%s)" % (memory_list.value, channel.value))
    smu.write("MEM:LIST:CLEAR (@%s)" % (channel.value))

    # set voltage ,crurent ranges and voltage limit for the channel
    smu.write("MEM:VOLT:RANG %s, (@%s)" % (voltage_range.value, channel.value))
    smu.write("MEM:CURR:RANG %s, (@%s)" % (current_range.value, channel.value))
    smu.write("MEM:VOLT:LIM %s, (@%s)" % (voltage_limit, channel.value))
    # enable auto delay
    smu.write("MEM:SOUR:DEL:AUTO ON, (@%s)" % (channel.value))
    # source voltage, enable output
    smu.write("MEM:CURR:SOUR %s, (@%s)" % (I_out, channel.value))
    smu.write("MEM:OUTP ON, (@%s)" % (channel.value))

    # add local delay before measure if desired
    if measure_delay_ms:
        smu.write(
            "MEM:SOUR:DEL SING,%s,(@%s)" % (measure_delay_ms, channel.value)
        )
        smu.write("MEM:CURR:SOUR %s, (@%s)" % (I_out, channel.value))

    # make voltage measurements
    for _ in range(measure_count):
        smu.write("MEM:VOLT:MEAS (@%s)" % (channel.value))

    # switch off output at the end of measurement
    smu.write("MEM:OUTP OFF, (@%s)" % (channel.value))

    # stores all commands from the active memory list into the nonvolatile memory
    smu.write("MEM:LIST:STOR (@%s)" % (channel.value))


def create_smu_pulse_current(
    smu: KeysightU2723Wrapper,
    channel: SMUChannel,
    I_peak: float,
    pulse_width_ms: float,
    memory_list: SMUMemoryList = SMUMemoryList.Mem1,
    loops: int = 1,
    voltage_limit: float = 20,  # 20 V
    current_limit: float = 0.1,  # 100 mA
    voltage_range: SMUVoltageRange = SMUVoltageRange.R20V,
    current_range: SMUVoltageRange = SMUCurrentRange.R120mA,
) -> None:
    """
    Generate a pulse current signal and store it in SMU memory list
    NOTE: for execution of memory list. call: smu.trigger_memory_list(channel)
    NOTE: This function does not enable/disable the SMU channel
        it is assumed that this done prior to triggering the memory list

    Args:
        smu (KeysightU2723Wrapper): handle to SMU
        channel (SMUChannel): target SMU channel
        I_peak (float): pulse current magnitude in A (negative values indicate sinking current)
        memory_list (SMUMemoryList, optional): memory list to use Defaults to SMUMemoryList.Mem1.
        loops (int, optional): number of times to repeat the pulse loading. Defaults to 1.
    """
    # select memory list and clear existing commands
    smu.write("MEM:LIST %s, (@%s)" % (memory_list.value, channel.value))
    smu.write("MEM:LIST:CLEAR (@%s)" % (channel.value))

    # set voltage , current ranges and voltage, current limits for the channel
    smu.write("MEM:VOLT:RANG %s, (@%s)" % (voltage_range.value, channel.value))
    smu.write("MEM:CURR:RANG %s, (@%s)" % (current_range.value, channel.value))
    smu.write("MEM:VOLT:LIM %s, (@%s)" % (voltage_limit, channel.value))
    smu.write("MEM:CURR:LIM %s, (@%s)" % (current_limit, channel.value))
    # enable auto delay to allow for stable signal
    smu.write("MEM:SOUR:DEL:AUTO ON, (@%s)" % (channel.value))
    # create the pulse signal steps
    smu.write("MEM:SOUR:DEL SING,%s,(@%s)" % (pulse_width_ms, channel.value))
    smu.write("MEM:CURR:SOUR %s, (@%s)" % (I_peak, channel.value))
    smu.write("MEM:CURR:SOUR %s, (@%s)" % (0.0, channel.value))

    # configure start step, end step, loops count
    smu.write("MEM:CONF:POIN %s,%s,%s,(@%s)" % (1, 8, loops, channel.value))

    # stores all commands from the active memory list into the nonvolatile memory
    smu.write("MEM:LIST:STOR (@%s)" % (channel.value))


def create_smu_pulse_voltage(
    smu: KeysightU2723Wrapper,
    channel: SMUChannel,
    V_peak: float,
    pulse_width_ms: float,
    memory_list: SMUMemoryList = SMUMemoryList.Mem1,
    loops: int = 1,
    voltage_limit: float = 20,  # 20 V
    current_limit: float = 0.1,  # 100 mA
    voltage_range: SMUVoltageRange = SMUVoltageRange.R20V,
    current_range: SMUVoltageRange = SMUCurrentRange.R120mA,
) -> None:
    """
    Generate a pulse voltage signal and store it in SMU memory list
    NOTE. for execution of memory list. call: smu.trigger_memory_list(channel)
    NOTE: This function does not enable/disable the output state of the SMU channel
        it is assumed that this done prior to triggering the memory list
    Args:
        smu (KeysightU2723Wrapper): handle to SMU
        channel (SMUChannel): target SMU channel
        V_peak (float): pulse voltage magnitude in V
        memory_list (SMUMemoryList, optional): memory list to use Defaults to SMUMemoryList.Mem1.
        loops (int, optional): number of times to repeat the pulse loading. Defaults to 1.

    """

    # select memory list and clear existing commands
    smu.write("MEM:LIST %s, (@%s)" % (memory_list.value, channel.value))
    smu.write("MEM:LIST:CLEAR (@%s)" % (channel.value))

    # set voltage , current ranges and voltage, current limits for the channel
    smu.write("MEM:VOLT:RANG %s, (@%s)" % (voltage_range.value, channel.value))
    smu.write("MEM:CURR:RANG %s, (@%s)" % (current_range.value, channel.value))
    smu.write("MEM:VOLT:LIM %s, (@%s)" % (voltage_limit, channel.value))
    smu.write("MEM:CURR:LIM %s, (@%s)" % (current_limit, channel.value))
    # enable auto delay to allow for stable signal
    smu.write("MEM:SOUR:DEL:AUTO ON, (@%s)" % (channel.value))
    # create the pulse signal steps
    smu.write("MEM:SOUR:DEL SING,%s,(@%s)" % (pulse_width_ms, channel.value))
    smu.write("MEM:VOLT:SOUR %s, (@%s)" % (V_peak, channel.value))
    smu.write("MEM:VOLT:SOUR %s, (@%s)" % (0.0, channel.value))

    # configure start step, end step, loops count
    smu.write("MEM:CONF:POIN %s,%s,%s,(@%s)" % (1, 8, loops, channel.value))

    # stores all commands from the active memory list into the nonvolatile memory
    smu.write("MEM:LIST:STOR (@%s)" % (channel.value))
