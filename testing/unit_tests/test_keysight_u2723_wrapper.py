from pypm_test import (KeysightU2723Wrapper, SMUChannel, SMUVoltageRange, SMUCurrentRange, create_smu_pulse_current, create_smu_pulse_voltage,
smu_source_voltage_measure_current, smu_source_current_measure_voltage)
import logging
import pytest
from time import sleep, perf_counter

def test_keysight_u27_SMU_volt_source(smu_handle: KeysightU2723Wrapper) -> None:
    """
    Test the execution of SMU voltage source function for KeysightU2723Wrapper
    
    """
    VOLTAGE_LEVEL = 5.0
    
    # (Voltage drive example)
    logging.info(f"Drive: {VOLTAGE_LEVEL}V Voltage Output on SMU channel: {SMUChannel.CH1.name}")
    
    smu_handle.set_smu_voltage_range(SMUChannel.CH1, SMUVoltageRange.R20V)
    smu_handle.set_smu_current_range(SMUChannel.CH1, SMUCurrentRange.R10mA)
    smu_handle.set_smu_current_limit(SMUChannel.CH1, 8.0e-3) # mA
    
    smu_handle.set_smu_source_voltage(SMUChannel.CH1, VOLTAGE_LEVEL) # V
    smu_handle.enable_smu_channel(SMUChannel.CH1)
    assert int(smu_handle.query("OUTP? (@%s)" % SMUChannel.CH1.value)) == 1
    
    volt_mesure = smu_handle.measure_voltage_scalar(SMUChannel.CH1)
    assert pytest.approx(volt_mesure, 0.01) == VOLTAGE_LEVEL
   
    # perform sweep measurement
    smu_handle.set_sweep_interval(SMUChannel.CH1, 40)
    smu_handle.set_sweep_points(SMUChannel.CH1, 150)

    sampling_time_curr = smu_handle.query_current_sampling_time(SMUChannel.CH1)
    logging.info(f"Smapling time for Current (I) measurment: {sampling_time_curr} sec")

    curr_points = smu_handle.measure_current_array(SMUChannel.CH1)
    assert len(curr_points) == 150

    smu_handle.disable_smu_channel(SMUChannel.CH1)
    assert int(smu_handle.query("OUTP? (@%s)" % SMUChannel.CH1.value)) == 0

    smu_handle.clear_presets()

def test_keysight_u27_SMU_curr_source(smu_handle: KeysightU2723Wrapper) -> None:
    """
    Test the execution of SMU current source function for KeysightU2723Wrapper
    
    """
    CURRENT_LEVEL = 5.0e-3
    # (Current drive example)
    logging.info(f"Drive: {CURRENT_LEVEL}A Current Output on SMU channel: {SMUChannel.CH1.name}")

    smu_handle.set_smu_voltage_range(SMUChannel.CH1, SMUVoltageRange.R20V)
    smu_handle.set_smu_current_range(SMUChannel.CH1, SMUCurrentRange.R10mA)
    smu_handle.set_smu_voltage_limit(SMUChannel.CH1, 10.0) # V
    
    smu_handle.set_smu_source_current(SMUChannel.CH1, CURRENT_LEVEL) # mA
    smu_handle.enable_smu_channel(SMUChannel.CH1)
    assert int(smu_handle.query("OUTP? (@%s)" % SMUChannel.CH1.value)) == 1
    
    smu_handle.measure_current_scalar(SMUChannel.CH1)

    # perform sweep measurement
    smu_handle.set_sweep_interval(SMUChannel.CH1, 40)
    smu_handle.set_sweep_points(SMUChannel.CH1, 150)
    
    sampling_time_volt = smu_handle.query_voltage_sampling_time(SMUChannel.CH1)
    logging.info(f"Smapling time for Voltage (V) measurment: {sampling_time_volt} sec")
    
    volt_points = smu_handle.measure_voltage_array(SMUChannel.CH1)
    assert len(volt_points) == 150

    smu_handle.disable_smu_channel(SMUChannel.CH1)
    assert int(smu_handle.query("OUTP? (@%s)" % SMUChannel.CH1.value)) == 0

    smu_handle.clear_presets()
    
def test_keysight_u27_SMU_memory_list_volt(smu_handle: KeysightU2723Wrapper) -> None:
    """
    Test the execution of SMU meomory list functions as voltage source for KeysightU2723Wrapper
    
    """
    DELAY_MS = 3000
    SOURCE_VOLTAGE = 1.2 # very little voltage applied to multimeter
    CHANNEL = SMUChannel.CH2.value
    I_LIMIT = 0.05 # 50 mA
    MEM_LIST = 1
  
    # write test steps into channel memory list and trigger SMU
    smu_handle.write('MEM:LIST %s, (@%s)' % (MEM_LIST , CHANNEL))
    smu_handle.write('MEM:LIST:CLE (@%s)' % (CHANNEL))
    
    # set voltage , cuurent ranges and current limit for the channel
    smu_handle.write('MEM:VOLT:RANG R20V, (@%s)' % (CHANNEL))
    smu_handle.write('MEM:CURR:RANG R120mA, (@%s)' % (CHANNEL))
    smu_handle.write('MEM:CURR:LIM %s, (@%s)' % (I_LIMIT , CHANNEL))
    # set the source voltage to zero and enable output
    smu_handle.write('MEM:SOUR:DEL:AUTO OFF, (@%s)' % (CHANNEL))
    smu_handle.write('MEM:VOLT:SOUR %s, (@%s)' % (0.0, CHANNEL))
    smu_handle.write('MEM:OUTP ON, (@%s)' % (CHANNEL))
    # Drive SOURCE_CURRENT/ 2 for DELAY_MS
    smu_handle.write('MEM:SOUR:DEL SING,%s,(@%s)' % (DELAY_MS, CHANNEL))
    smu_handle.write('MEM:VOLT:SOUR %s, (@%s)' % (SOURCE_VOLTAGE/2.0, CHANNEL))
    # Drive  SOURCE_CURRENT for DELAY_MS
    smu_handle.write('MEM:SOUR:DEL SING,%s,(@%s)' % (DELAY_MS, CHANNEL))
    smu_handle.write('MEM:VOLT:SOUR %s, (@%s)' % (SOURCE_VOLTAGE, CHANNEL))
    # switch off finally
    smu_handle.write('MEM:OUTP OFF, (@%s)' % (CHANNEL))

    # stores all commands from the active memory list into the nonvolatile memory
    smu_handle.write('MEM:LIST:STOR (@%s)' % (CHANNEL)) 
    
    
    memory_commands = smu_handle.query('MEM:LIST:READ? (@%s)' % (CHANNEL))
    # memory commands are seperated by ";" and last item can be ignored as it is just whitespace
    logging.info(f"Memory List: {MEM_LIST} for Channel: {CHANNEL} has: {len(memory_commands.split(';')) - 1} commands")
    assert len(memory_commands.split(";")) -1  == 11
    
    logging.info(f"Triggering Instrument to start execution of Memory List: {MEM_LIST} on Channel: {CHANNEL}")
    smu_handle.write('MEM:TRIG (@%s)' % (CHANNEL))

    # NOTE:
    # instrument will not respond to incoming commands when it is busy executing commands from active memory list
    # To check the status of the instrument we have to read the status operation register value (see bit values table in instrument manual)
    # The WTG bit set indicates that the channel is armed and waiting for trigger.
    # The DTG bit set indicates that the channel is busy and will ignore all incoming commands.

    while(int(smu_handle.query('STAT:OPER:COND?')) != 0):
        logging.info(f"Instrument is busy executing Memory List: {MEM_LIST} on Channel: {CHANNEL}")
        sleep(1)
    
    assert int(smu_handle.query('STAT:OPER:COND?')) == 0
        
    smu_handle.disable_smu_channel(SMUChannel.CH2)
    assert int(smu_handle.query("OUTP? (@%s)" % SMUChannel.CH2.value)) == 0
    smu_handle.clear_presets() 
    
def test_keysight_u27_memory_list_curr(smu_handle: KeysightU2723Wrapper) -> None:
    """
    Test the execution of SMU meomory list functions as current source for KeysightU2723Wrapper
    
    """
    DELAY_MS = 3000
    SOURCE_CURRENT = -0.001 # draw very little current from power supply
    CHANNEL = SMUChannel.CH2.value
    V_LIMIT = 5
    MEM_LIST = 1
  
    # write test steps into channel memory list and trigger SMU
    smu_handle.write('MEM:LIST %s, (@%s)' % (MEM_LIST , CHANNEL))
    smu_handle.write('MEM:LIST:CLE (@%s)' % (CHANNEL))
    
    # set voltage , cuurent ranges and voltage limit for the channel
    smu_handle.write('MEM:VOLT:RANG R20V, (@%s)' % (CHANNEL))
    smu_handle.write('MEM:CURR:RANG R120mA, (@%s)' % (CHANNEL))
    smu_handle.write('MEM:VOLT:LIM %s, (@%s)' % (V_LIMIT , CHANNEL))
    # set the source current to zero and enable output
    smu_handle.write('MEM:SOUR:DEL:AUTO OFF, (@%s)' % (CHANNEL))
    smu_handle.write('MEM:CURR:SOUR %s, (@%s)' % (0.0, CHANNEL))
    smu_handle.write('MEM:OUTP ON, (@%s)' % (CHANNEL))
    # Drive SOURCE_CURRENT/ 2 for DELAY_MS
    smu_handle.write('MEM:SOUR:DEL SING,%s,(@%s)' % (DELAY_MS, CHANNEL))
    smu_handle.write('MEM:CURR:SOUR %s, (@%s)' % (SOURCE_CURRENT/2.0, CHANNEL))
    # Drive  SOURCE_CURRENT for DELAY_MS
    smu_handle.write('MEM:SOUR:DEL SING,%s,(@%s)' % (DELAY_MS, CHANNEL))
    smu_handle.write('MEM:CURR:SOUR %s, (@%s)' % (SOURCE_CURRENT, CHANNEL))
    # switch off finally
    smu_handle.write('MEM:OUTP OFF, (@%s)' % (CHANNEL))

    # stores all commands from the active memory list into the nonvolatile memory
    smu_handle.write('MEM:LIST:STOR (@%s)' % (CHANNEL)) 
    
    
    memory_commands = smu_handle.query('MEM:LIST:READ? (@%s)' % (CHANNEL))
    # memory commands are seperated by ";" and last item can be ignored as it is just whitespace
    logging.info(f"Memory List: {MEM_LIST} for Channel: {CHANNEL} has: {len(memory_commands.split(';')) - 1} commands")
    assert len(memory_commands.split(";")) -1  == 11
    
    logging.info(f"Triggering Instrument to start execution of Memory List: {MEM_LIST} on Channel: {CHANNEL}")
    smu_handle.write('MEM:TRIG (@%s)' % (CHANNEL))

    # NOTE:
    # instrument will not respond to incoming commands when it is busy executing commands from active memory list
    # To check the status of the instrument we have to read the status operation register value (see bit values table in instrument manual)
    # The WTG bit set indicates that the channel is armed and waiting for trigger.
    # The DTG bit set indicates that the channel is busy and will ignore all incoming commands.

    while(int(smu_handle.query('STAT:OPER:COND?')) != 0):
        logging.info(f"Instrument is busy executing Memory List: {MEM_LIST} on Channel: {CHANNEL}")
        sleep(1)
    
    assert int(smu_handle.query('STAT:OPER:COND?')) == 0
        
    smu_handle.disable_smu_channel(SMUChannel.CH2)
    assert int(smu_handle.query("OUTP? (@%s)" % SMUChannel.CH2.value)) == 0
    smu_handle.clear_presets()
    
def test_pulse_current_load_utility_func(smu_handle: KeysightU2723Wrapper) -> None:
    """Test the application of 'create_smu_pulse_current' uitlity function"""
    
    smu_handle.set_smu_voltage_range(SMUChannel.CH2, SMUVoltageRange.R20V)
    smu_handle.set_smu_current_range(SMUChannel.CH2, SMUCurrentRange.R10mA)
    smu_handle.set_smu_voltage_limit(SMUChannel.CH2, 20.0) # V
    
    # enable SMU with desired base current
    smu_handle.set_smu_source_current(SMUChannel.CH2, -0.01e-3) # mA
    smu_handle.enable_smu_channel(SMUChannel.CH2)
    assert int(smu_handle.query("OUTP? (@%s)" % SMUChannel.CH2.value)) == 1
    
    # generate a pulse current signal in CH2 memory list
    create_smu_pulse_current(smu_handle,
                             SMUChannel.CH2,
                             I_peak= -10.0e-3, # mA
                             pulse_width_ms= 200, # ms
                             loops= 1) # repeat times
    
    
    memory_commands = smu_handle.query('MEM:LIST:READ? (@%s)' % (SMUChannel.CH2.value))
    # memory commands are seperated by ";" and last item can be ignored as it is just whitespace
    logging.info(f"Memory List for Channel: {SMUChannel.CH2.value} has: {len(memory_commands.split(';')) - 1} commands")
    
    # trigger execution of memory list actions
    t_start = perf_counter()
    smu_handle.trigger_memory_list(SMUChannel.CH2)
    
    while(smu_handle.query_status_operation() != 0):
        ... # wait till status register return zero -> no active tasks
    
    assert smu_handle.query_status_operation() == 0
    t_stop = perf_counter()
    logging.info(f"Current Pulse run duration: {t_stop - t_start:3f} sec")
        
    smu_handle.disable_smu_channel(SMUChannel.CH2)
    assert int(smu_handle.query("OUTP? (@%s)" % SMUChannel.CH2.value)) == 0
    smu_handle.clear_presets()

def test_pulse_voltage_load_utility_func(smu_handle: KeysightU2723Wrapper) -> None:
    """Test the application of 'create_smu_pulse_voltage' uitlity function"""
    
    smu_handle.set_smu_voltage_range(SMUChannel.CH2, SMUVoltageRange.R20V)
    smu_handle.set_smu_current_range(SMUChannel.CH2, SMUCurrentRange.R10mA)
    smu_handle.set_smu_current_limit(SMUChannel.CH2, 8.0e-3) # mA
    
    # enable SMU with desired base voltage
    smu_handle.set_smu_source_voltage(SMUChannel.CH2, 0.1e-3) # V
    smu_handle.enable_smu_channel(SMUChannel.CH2)
    assert int(smu_handle.query("OUTP? (@%s)" % SMUChannel.CH2.value)) == 1
    
    # generate a pulse voltage signal in CH2 memory list
    create_smu_pulse_voltage(smu_handle,
                             SMUChannel.CH2,
                             pulse_width_ms= 2000, # ms
                             V_peak= 1.2, # V
                             loops=2) # repition times
        
    memory_commands = smu_handle.query('MEM:LIST:READ? (@%s)' % (SMUChannel.CH2.value))
    # memory commands are seperated by ";" and last item can be ignored as it is just whitespace
    logging.info(f"Memory List for Channel: {SMUChannel.CH2.value} has: {len(memory_commands.split(';')) - 1} commands")
    
    # trigger execution of memory list actions
    t_start = perf_counter()
    smu_handle.trigger_memory_list(SMUChannel.CH2)
    
    while(smu_handle.query_status_operation() != 0):
        ... # wait till status register return zero -> no active tasks
    
    assert smu_handle.query_status_operation() == 0
    t_stop = perf_counter()
    logging.info(f"Voltage Pulse run duration: {t_stop - t_start:3f} sec")
        
    smu_handle.disable_smu_channel(SMUChannel.CH2)
    assert int(smu_handle.query("OUTP? (@%s)" % SMUChannel.CH2.value)) == 0
    smu_handle.clear_presets()
    
def test_smu_source_voltage_measure_current_utility_func(smu_handle: KeysightU2723Wrapper) -> None:
    """Test the application of 'smu_source_voltage_measure_current' uitlity function"""
    
    # start a voltage source and measure current
    # NOTE. When the measurement results reaches 200, the next result will wrap back and replace the first result at the buffer
    smu_source_voltage_measure_current(smu_handle,
                             SMUChannel.CH2,
                             V_out= 1.2,
                             measure_delay_ms= 3000, # (optional) wait before measurement
                             measure_count= 100) 

    memory_commands = smu_handle.query('MEM:LIST:READ? (@%s)' % (SMUChannel.CH2.value))
    # memory commands are seperated by ";" and last item can be ignored as it is just whitespace
    logging.info(f"Memory List for Channel: {SMUChannel.CH2.value} has: {len(memory_commands.split(';')) - 1} commands")
    
    # trigger execution of memory list actions
    t_start = perf_counter()
    smu_handle.trigger_memory_list(SMUChannel.CH2)
    
    while(smu_handle.query_status_operation() != 0):
        ... # wait till status register return zero -> no active tasks
    
    assert smu_handle.query_status_operation() == 0
    t_stop = perf_counter()
    logging.info(f"'smu_source_voltage_measure_current' duration: {t_stop - t_start:3f} sec")
    
    results = smu_handle.read_memory_list_results(SMUChannel.CH2)
    logging.info(f"Results / Result Count of measurements in memory list execution: {results} / {len(results)}")
    
    smu_handle.disable_smu_channel(SMUChannel.CH2)
    assert int(smu_handle.query("OUTP? (@%s)" % SMUChannel.CH2.value)) == 0
    smu_handle.clear_presets()
    
def test_smu_source_current_measure_voltage_utility_func(smu_handle: KeysightU2723Wrapper) -> None:
    """Test the application of 'smu_source_current_measure_voltage' uitlity function"""
    
    # start a voltage source and measure current
    smu_source_current_measure_voltage(smu_handle,
                             SMUChannel.CH2,
                             I_out= -0.001, # sink 1 mA
                            measure_delay_ms= 3000, # (optional) wait before measurement
                             measure_count=100) 
    
    memory_commands = smu_handle.query('MEM:LIST:READ? (@%s)' % (SMUChannel.CH2.value))
    # memory commands are seperated by ";" and last item can be ignored as it is just whitespace
    logging.info(f"Memory List for Channel: {SMUChannel.CH2.value} has: {len(memory_commands.split(';')) - 1} commands")
    
    # trigger execution of memory list actions
    t_start = perf_counter()
    smu_handle.trigger_memory_list(SMUChannel.CH2)
    
    while(smu_handle.query_status_operation() != 0):
        ... # wait till status register return zero -> no active tasks
    
    assert smu_handle.query_status_operation() == 0
    t_stop = perf_counter()
    logging.info(f"'smu_source_current_measure_voltage' duration: {t_stop - t_start:3f} sec")
    
    results = smu_handle.read_memory_list_results(SMUChannel.CH2)
    logging.info(f"Results / Result Count of measurements in memory list execution: {results} / {len(results)}")
    
    smu_handle.disable_smu_channel(SMUChannel.CH2)
    assert int(smu_handle.query("OUTP? (@%s)" % SMUChannel.CH2.value)) == 0
    smu_handle.clear_presets()