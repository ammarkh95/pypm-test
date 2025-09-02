"""Example test cases for DC-DC Converter using SMU / PSU """

import logging
from pypm_test.keysight_u3606_wrapper import (KeysightU3606Wrapper, DCOutputMode, MultimeterMode)
from pypm_test.keysight_u2723_wrapper import (KeysightU2723Wrapper, SMUChannel, SMUCurrentRange, SMUVoltageRange, create_smu_pulse_current)
from typing import Tuple, Callable
import time
from itertools import chain
# NOTE: numpy and matplot required for array analysis and plotting
import numpy as np
import matplotlib.pyplot as plt

# SMU channel connected to VDD_OUT pin for applying external load
LOAD_CHANNEL = SMUChannel.CH2
# for annotation purposes. note which VDD line under test
V_DD_LINE_UNDER_TEST = "VDD_OUT"
READ_COUNT = 50 # number of measuremnt readings
INPUT_VOLTAGE_STEPS = [3.2, 3.6, 3.9, 4.2]
LOAD_CURRENT_STEPS =  np.array([1.0, 1.5, 2.0, 2.5, 3.0,
                        3.5, 4.0, 4.5, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 12.0, 14.0,
                        16.0, 18.0, 20.0, 22.0, 24.0, 26.0, 28.0, 30.0]) * 1.0e-3
BASE_LOAD_CURRENT = 1.0e-3
SLEEP_EVENT = 5 # sec


def psu_read_measurements(keysight_u36: KeysightU3606Wrapper, n_readings: int) -> Tuple[np.ndarray, float]:
    """
    Uses READ? SCPI query to trigger, perform and read measurements
    
    returns tuple of: list of measurements , elpased duration for the measurment process
    
    """
    readings = []
    t_start = time.perf_counter()
    for _ in range(n_readings):
        readings.append(keysight_u36.read())
    t_stop = time.perf_counter()

    return (np.array(readings), t_stop - t_start)
####################################################################################
def test_dc_dc_power_efficiency(psu_handle: KeysightU3606Wrapper,
                                 smu_handle: KeysightU2723Wrapper) -> None:
    
    """
    Test DC-DC converter efficiency by supplying VDD_IN via PSU
    and measure its base current then load VDD_OUT with multiple steps constant current load
    via SMU to evlaute the conversion efficiency (Output / Input) power
    
    - calculate base current of device via PSU (multimeter function)
    - calculate output power by multiplying load current by load voltage measured via SMU for each external load step
    - calculate input power by multiplying (input current - base current) by load voltage measured via PSU for each external load step
    - calculate % efficiency by (output_power / input_power) * 100
    - repeat calculations for various Li-ion V_ref levels
    
    """

    # configure power supply
    psu_handle.configure_multimeter(MultimeterMode.CURRENT)
    psu_handle.configure_dc_supply(DCOutputMode.CONSTANT_VOLTAGE,
                                     3.60, # V
                                     over_current_limit= 0.1) # A

    # configure source masure unit
    for ch in SMUChannel:
        smu_handle.set_smu_voltage_range(ch, SMUVoltageRange.R20V)
        smu_handle.set_smu_current_range(ch, SMUCurrentRange.R120mA)
        smu_handle.set_smu_voltage_limit(ch, 20.0) # V    
        smu_handle.set_smu_current_limit(ch, 0.1) # A    
    
    # create figure place holder
    fig , axis = plt.subplots()
    plot, = axis.plot([], [])
    fig.suptitle(f"{V_DD_LINE_UNDER_TEST} DC-DC efficiency curve", wrap=True, weight='bold')
    axis.set_xlabel("Load Current (mA)", weight='bold')
    axis.set_ylabel("Efficiency (%)", weight='bold')
    axis.set_xscale('log')
    axis.set_xlim([1, 30])
    axis.set_ylim([0, 100])
    axis.grid(True, which="both", ls="-")

    logging.info(f"::DC-DC Efficiency Test Steps:: Applying SMU current loads to {V_DD_LINE_UNDER_TEST} and making measurements")
    
    # loop over range of input voltages
    for V_INPUT in INPUT_VOLTAGE_STEPS:

        I_INPUT_AVG = []
        I_LOAD_AVG = []
        V_LOAD_AVG = []
                  
        psu_handle.set_dc_supply_output_voltage(V_INPUT)
        psu_handle.enable_dc_output()

        # allow system to stabilize after power on
        time.sleep(SLEEP_EVENT)

        ### 1 ### measure base current
        i_base_input , duration = psu_read_measurements(psu_handle, READ_COUNT)
        i_avg_base_input =  np.mean(i_base_input) * 1000 # convert to mA
        logging.info(f"Average base current at V_IN over: {duration} sec is: {i_avg_base_input:3f} mA. at V_input: {V_INPUT}V")

        # enable SMU with static base current
        smu_handle.set_smu_source_current(LOAD_CHANNEL, -1 * BASE_LOAD_CURRENT) # mA
        smu_handle.enable_smu_channel(LOAD_CHANNEL)

        time.sleep(SLEEP_EVENT)

        ### 2 ### Load  VDD_OUT pin with external constant current load steps
        t_start = time.perf_counter()
        try:
            for i_step in LOAD_CURRENT_STEPS:
                                
                smu_handle.set_smu_source_current(LOAD_CHANNEL, -1 * i_step) # i_step is current in A unit
            
                i_load_sum = 0
                i_input_sum = 0
                v_load_sum = 0
                
                # measure input current, output current and output voltage
                for _ in range(READ_COUNT):
                    
                    v_load_sum += smu_handle.measure_voltage_scalar(LOAD_CHANNEL)
                    i_load_sum += abs(smu_handle.measure_current_scalar(LOAD_CHANNEL)) # take abs because of negative current
                    i_input_sum += psu_handle.read()
                
                # append average values
                I_LOAD_AVG.append( (i_load_sum / READ_COUNT) * 1000 ) # mA
                I_INPUT_AVG.append( (i_input_sum / READ_COUNT) * 1000 ) # mA
                V_LOAD_AVG.append( (v_load_sum / READ_COUNT))

        except Exception as e:
            logging.error(f"An exception has occured during test: {repr(e)}")
            smu_handle.disable_smu_channel(LOAD_CHANNEL)
            psu_handle.disable_dc_output()
            assert False
        t_end = time.perf_counter()
        logging.info(f"Load Current Sweep Took: {(t_end - t_start):3f} sec")

        ### 3 ### Calculate average input / output power in mW and plot effeciecny curve on log scale
        P_IN_AVG = [V_INPUT * (I_INPUT - i_avg_base_input) for I_INPUT in I_INPUT_AVG]
        P_OUT_AVG = [V_LOAD * I_LOAD for V_LOAD, I_LOAD in zip(V_LOAD_AVG, I_LOAD_AVG)]
        EFFICIENCY_PERCENT_AVG = [(P_OUT / P_IN) * 100 for P_OUT, P_IN in zip(P_OUT_AVG, P_IN_AVG)]
        logging.info(f"V_INPUT: {V_INPUT}")
        logging.info(f"I_INPUT: {I_INPUT_AVG}")
        logging.info(f"V_LOAD_AVG: {V_LOAD_AVG}")
        logging.info(f"I_LOAD_AVG: {I_LOAD_AVG}")
        logging.info(f"EFFICIENCY_PERCENT_AVG: {EFFICIENCY_PERCENT_AVG}")

        logging.info(f"{V_DD_LINE_UNDER_TEST} Max / Min voltages; Max: {max(V_LOAD_AVG):3f} V, Min: {min(V_LOAD_AVG):3f} V with V_INPUT: {V_INPUT}V")
        smu_handle.disable_smu_channel(LOAD_CHANNEL)
        psu_handle.disable_dc_output()
       
        # plot results of  % effeciency vs load current
        axis.plot(I_LOAD_AVG, EFFICIENCY_PERCENT_AVG, linestyle='--', marker='o', label=f'Input voltage: {V_INPUT}V')
    
    plt.legend()
    plt.grid(True, which="both", ls="-")
    plt.pause(3)
####################################################################################
def test_dc_dc_line_regulation(psu_handle: KeysightU3606Wrapper,
                                smu_handle: KeysightU2723Wrapper) -> None:
    
    """
    Test DC-DC converter output voltage stability as the input voltage is varied
    
    input voltage is swept over the specified input voltage range and the output voltage is measured.
    The load current is set to 0A
    
    """
 
    INPUT_VOLTAGE_SWEEP = np.linspace(2.8 , 4.5, 25)
   
    V_INPUT_AVG = []
    V_LOAD_AVG = []
   
    fig , axis = plt.subplots()
    plot, = axis.plot([], [])
    fig.suptitle(f"{V_DD_LINE_UNDER_TEST} DC-DC line regulation", wrap=True, weight='bold')
    axis.set_xlabel("V_INPUT (V)", weight='bold')
    axis.set_ylabel(f"{V_DD_LINE_UNDER_TEST} (V)", weight='bold')
    axis.set_xlim([min(INPUT_VOLTAGE_SWEEP), max(INPUT_VOLTAGE_SWEEP)])
    axis.grid(True, which="both", ls="-")

    # Enable DC output with first step
    psu_handle.set_dc_supply_output_voltage(INPUT_VOLTAGE_SWEEP[0])
    psu_handle.enable_dc_output()

    time.sleep(SLEEP_EVENT)
    
    # enable SMU with static base load
    smu_handle.set_smu_source_current(LOAD_CHANNEL,  -1 * BASE_LOAD_CURRENT / 10) # mA
    smu_handle.enable_smu_channel(LOAD_CHANNEL)

    # allow system to stabilize after power on
    time.sleep(SLEEP_EVENT)

    logging.info(f"::Line Regulation Test Steps:: Applying PSU varying input voltages to VDD_INPUT and measuring load voltages at: {V_DD_LINE_UNDER_TEST}")

    # loop over range of input voltages
    t_start = time.perf_counter()
    for V_INPUT in INPUT_VOLTAGE_SWEEP:

        v_load_sum = 0
        
        # move to next voltage step
        psu_handle.set_dc_supply_output_voltage(V_INPUT)

        try:
            for _ in range(READ_COUNT):
                v_load_sum += smu_handle.measure_voltage_scalar(LOAD_CHANNEL)

            V_LOAD_AVG.append( (v_load_sum / READ_COUNT)) # average
            V_INPUT_AVG.append(V_INPUT)
            
        except Exception as e:
            logging.error(f"An exception has occured during test: {repr(e)}")
            smu_handle.disable_smu_channel(LOAD_CHANNEL)
            psu_handle.disable_dc_output()
            assert False

        logging.info(f"Average load voltage (@Vdd): :{(v_load_sum / READ_COUNT):3f} V with V_INPUT: {V_INPUT} V")

    t_end = time.perf_counter()
    logging.info(f"Supply Voltage Sweep Took: {(t_end - t_start):3f} sec")
    # plot results of output vs. input voltage
    axis.plot(V_INPUT_AVG, V_LOAD_AVG, linestyle='--', marker='o', color = 'b')
    
    plt.grid(True, which="both", ls="-")
    plt.pause(3)
####################################################################################
def test_dc_dc_load_regulation(psu_handle: KeysightU3606Wrapper,
                                 smu_handle: KeysightU2723Wrapper) -> None:
    
    """
    Test DC-DC converter output voltage stability as the load current increases
    load current is swept over the specified range and the output voltage is measured.
    """
     
    # create figure place holder
    fig , axis = plt.subplots()
    plot, = axis.plot([], [])
    fig.suptitle(f"{V_DD_LINE_UNDER_TEST} DC-DC load regulation", wrap=True, weight='bold')
    axis.set_xlabel("Load Current (mA)", weight='bold')
    axis.set_ylabel(f"{V_DD_LINE_UNDER_TEST} (V)", weight='bold')
    axis.grid(True, which="both", ls="-")

    logging.info(f"::Load Regulation Test Steps:: Applying SMU current loads to {V_DD_LINE_UNDER_TEST} and measuring load voltages")

    # loop over range of input voltages
    for V_INPUT in INPUT_VOLTAGE_STEPS:

        I_LOAD_AVG = []
        V_LOAD_AVG = []

        # set DC supply and enable output
        psu_handle.set_dc_supply_output_voltage(V_INPUT)
        psu_handle.enable_dc_output()

        # allow system to stabilize after power on
        time.sleep(SLEEP_EVENT)
        
        # enable SMU with static base load
        smu_handle.set_smu_source_current(LOAD_CHANNEL,  -1 * BASE_LOAD_CURRENT) # mA
        smu_handle.enable_smu_channel(LOAD_CHANNEL)

        time.sleep(SLEEP_EVENT)
       
        # Load VDD_OUT pin with external constant current load steps
        t_start = time.perf_counter()
        try:
            for i_step in LOAD_CURRENT_STEPS:
                                
                # apply external constant current load
                smu_handle.set_smu_source_current(LOAD_CHANNEL, -1 * i_step) # i_step is current in A unit
            
                i_load_sum = 0
                v_load_sum = 0
                
                # measure input current, output current and output voltage
                for _ in range(READ_COUNT):
                    
                    v_load_sum += smu_handle.measure_voltage_scalar(LOAD_CHANNEL)
                    i_load_sum += abs(smu_handle.measure_current_scalar(LOAD_CHANNEL)) # take abs because of negative current
                
                # append average values
                I_LOAD_AVG.append( (i_load_sum / READ_COUNT) * 1000 ) # mA
                V_LOAD_AVG.append( (v_load_sum / READ_COUNT))
                
        except Exception as e:
            logging.error(f"An exception has occured during test: {repr(e)}")
            smu_handle.disable_smu_channel(LOAD_CHANNEL)
            psu_handle.disable_dc_output()
            assert False

        t_end = time.perf_counter()
        logging.info(f"Load Current Sweep Took: {(t_end - t_start):3f} sec")

        logging.info(f"{V_DD_LINE_UNDER_TEST} Max/Min voltages; Max: {max(V_LOAD_AVG):3f} V, Min: {min(V_LOAD_AVG):3f} V with V_INPUT: {V_INPUT}V")
        smu_handle.disable_smu_channel(LOAD_CHANNEL)
        psu_handle.disable_dc_output()
       
        # plot results of  load current vs. load voltage (@Vdd) 
        axis.plot(I_LOAD_AVG, V_LOAD_AVG, linestyle='--', marker='o', label=f'Input voltage: {V_INPUT}V')    

    plt.legend()
    plt.grid(True, which="both", ls="-")
    plt.pause(3)
####################################################################################
def test_power_supplies_stability(psu_handle: KeysightU3606Wrapper,
                                 smu_handle: KeysightU2723Wrapper) -> None:
    
    """
    Test power supplies stability with gradually increasing applied electronic load at different VDD_OUT rails
    
    SMU channels mapping to multiple VDD_OUT rails:
        - SMU.CH1 = VDD_OUT_1
        - SMU.CH2 = VDD_OUT_2

    """
  
    V_INPUT = 3.6
    
    # mapping of VDD rails to SMU channels connected to them
    VDD_OUT_1_CH = SMUChannel.CH1
    VDD_OUT_2_CH = SMUChannel.CH2
      
    # average load current results holder for VDD_OUT_1, VDD_OUT_2 lines
    I_DD_OUT_1_LOAD_AVG = []
    I_DD_OUT_2_LOAD_AVG = []
    
    # average load voltage results holder for VDD_OUT_1, VDD_OUT_2 lines
    V_DD_OUT_1_LOAD_AVG = []
    V_DD_OUT_2_LOAD_AVG = []
      
    # create figure place holder
    fig , axis = plt.subplots()
    plot, = axis.plot([], [])
    fig.suptitle(f"power supplies regulation. V_INPUT: {V_INPUT}V", wrap=True, weight='bold')
    axis.set_xlabel("Load Current (mA)", weight='bold')
    axis.set_ylabel(f"VDD (V)", weight='bold')
    axis.grid(True, which="both", ls="-")

    logging.info(f"::Load Regulation Test Steps:: Applying SMU current loads to VDD_OUT 1, 2 rails")

    # set DC supply and enable output
    psu_handle.set_dc_supply_output_voltage(V_INPUT)
    psu_handle.enable_dc_output()

    # allow system to stabilize after power on
    time.sleep(SLEEP_EVENT)
 
    # start SMU with static base load
    smu_handle.set_smu_source_current(VDD_OUT_1_CH,  -1 * BASE_LOAD_CURRENT) # mA
    smu_handle.enable_smu_channel(VDD_OUT_1_CH)
    smu_handle.set_smu_source_current(VDD_OUT_2_CH,  -1 * BASE_LOAD_CURRENT) # mA
    smu_handle.enable_smu_channel(VDD_OUT_2_CH)

    time.sleep(SLEEP_EVENT)
    
    # Load VDD_OUT pin with external constant current load steps
    t_start = time.perf_counter()
    try:
        for i_step in LOAD_CURRENT_STEPS:

            # apply external constant current load
            smu_handle.set_smu_source_current(VDD_OUT_1_CH, -1 * i_step) # i_step is current in A unit
            smu_handle.set_smu_source_current(VDD_OUT_2_CH, -1 * i_step) # i_step is current in A unit
                   
            i_dd_out_1_load_sum = 0
            i_dd_out_2_load_sum = 0

            v_dd_out_1_load_sum = 0
            v_dd_out_2_load_sum = 0
            
            # measure input current, output current and output voltage
            for _ in range(READ_COUNT):
                
                v_dd_out_1_load_sum += smu_handle.measure_voltage_scalar(VDD_OUT_1_CH)
                i_dd_out_1_load_sum += abs(smu_handle.measure_current_scalar(VDD_OUT_1_CH)) # take abs because of negative current
            
                v_dd_out_2_load_sum += smu_handle.measure_voltage_scalar(VDD_OUT_2_CH)
                i_dd_out_2_load_sum += abs(smu_handle.measure_current_scalar(VDD_OUT_2_CH)) # take abs because of negative current
        
            
            # append average values
            I_DD_OUT_1_LOAD_AVG.append( (i_dd_out_1_load_sum / READ_COUNT) * 1000 ) # mA
            V_DD_OUT_1_LOAD_AVG.append( (v_dd_out_1_load_sum / READ_COUNT))
            
            I_DD_OUT_2_LOAD_AVG.append( (i_dd_out_2_load_sum / READ_COUNT) * 1000 ) # mA
            V_DD_OUT_2_LOAD_AVG.append( (v_dd_out_2_load_sum / READ_COUNT))
            
    except Exception as e:
        logging.error(f"An exception has occured during test: {repr(e)}")
        smu_handle.disable_smu_channel(SMUChannel.CH1)
        smu_handle.disable_smu_channel(SMUChannel.CH2)
        psu_handle.disable_dc_output()
        assert False

    t_end = time.perf_counter()
    logging.info(f"Load Current Sweep Took: {(t_end - t_start):3f} sec")

    logging.info(f"VDD_OUT_1 Max/Min voltages; Max: {max(V_DD_OUT_1_LOAD_AVG):3f} V, Min: {min(V_DD_OUT_1_LOAD_AVG):3f} V with V_INPUT: {V_INPUT}V")
    logging.info(f"VDD_OUT_2 Max/Min voltages; Max: {max(V_DD_OUT_2_LOAD_AVG):3f} V, Min: {min(V_DD_OUT_2_LOAD_AVG):3f} V with V_INPUT: {V_INPUT}V")
    
    smu_handle.disable_smu_channel(SMUChannel.CH1)
    smu_handle.disable_smu_channel(SMUChannel.CH2)
    psu_handle.disable_dc_output()
    
    # plot results of  load current vs. load voltage (@Vdd)
    axis.plot(I_DD_OUT_1_LOAD_AVG, V_DD_OUT_1_LOAD_AVG, label=f'VDD_OUT_1')    
    axis.plot(I_DD_OUT_2_LOAD_AVG, V_DD_OUT_2_LOAD_AVG, label=f'VDD_OUT_2')    

    plt.legend()
    plt.grid(True, which="both", ls="-")
    plt.pause(3)
####################################################################################
def test_power_supply_pulse_loading(psu_handle: KeysightU3606Wrapper,
                                    smu_handle: KeysightU2723Wrapper) -> None:
    
    """
    Test power supplies response to pulse electronic loads
    """
    V_INPUT = 3.6

    # Pulse current properties
    I_PEAK = -30.0e-3 # peak current for the pulse signal (A) (negative -> sink current) 
    PULSE_WIDTH = 200 # (ms) pulse duration with I_PEAK
    PULSES_COUNT = 1 # for mulitple pulses test
    
    # Scope measurement parameters
    RECORD_SAMPLE_FREQUENCY = 3.0e6 # Hz
    RECORD_COUNT = 1024000 # for continous recording with scope
    
    # create figure place holder
    fig, ax = plt.subplots()
    fig.suptitle(f"{V_DD_LINE_UNDER_TEST} Pulse Load Response {abs(I_PEAK) * 1000} mA / {PULSE_WIDTH} ms", wrap=True, weight='bold')
    fig.supxlabel("Time (s)", weight='bold')
    fig.supylabel(f"{V_DD_LINE_UNDER_TEST} (V)", weight='bold')
    ax.grid(True, which="both", ls="-")
    
    # set DC supply and enable output
    psu_handle.set_dc_supply_output_voltage(V_INPUT)
    psu_handle.enable_dc_output()

    # allow system to stabilize after power on
    time.sleep(SLEEP_EVENT)
    
    # enable SMU with static base load
    smu_handle.set_smu_source_current(LOAD_CHANNEL,  -1 * BASE_LOAD_CURRENT) # mA
    smu_handle.enable_smu_channel(LOAD_CHANNEL)
   
    time.sleep(SLEEP_EVENT)
    
    # Load  VDD_OUT pin with pulse current load steps by putting required pulse steps
    # into active memory list of the SMU and then ARM it
    # In parallel record the output voltage behavior with the Analog Discovery
    try:
               
        ###### Pulses response recording #######
        logging.info(f":: Pulse Loading Test :: Applying {PULSES_COUNT} current pulse(s) to {V_DD_LINE_UNDER_TEST}")
        with AnalogDiscoveryAudioContext(analog_discovery, [AnalogInputChannel.Channel1]) as scope:
            t_start = time.perf_counter()
            # gerneate pulse current signal in SMU memory list
            create_smu_pulse_current(smu_handle,
                    LOAD_CHANNEL,
                    pulse_width_ms=PULSE_WIDTH,
                    I_peak=I_PEAK,
                    loops=PULSES_COUNT)
            
            # arm the scope
            scope.record_analog_signal(input_channels=[AnalogInputChannel.Channel1],
                    sampling_frequency= RECORD_SAMPLE_FREQUENCY,
                    # trigger_source= AnalogTriggerSource.AnalogInDetector,
                    # trigger_level= 1.205, # V
                    # trigger_hysteresis= 0.01, # V
                    ) 
            
            # trigger the pulse load
            smu_handle.trigger_memory_list(LOAD_CHANNEL)

            # get the recorded data            
            Vdd_record_response = scope.fill_recorded_samples(AnalogInputChannel.Channel1, RECORD_COUNT)

            while(smu_handle.query_status_operation() != 0):
                ... # Wait for SMU to Finish ... 
                        
            t_end = time.perf_counter()
            logging.info(f"Pulse Load Measurement Took: {(t_end - t_start):3f} sec")

    except Exception as e:
        logging.error(f"An exception has occured during test: {repr(e)}")
        smu_handle.disable_smu_channel(LOAD_CHANNEL)
        psu_handle.disable_dc_output()
        assert False

    smu_handle.disable_smu_channel(LOAD_CHANNEL)
    psu_handle.disable_dc_output()
    
    logging.info(f"{V_DD_LINE_UNDER_TEST} [Pulse Response] Max/Min voltages; Max: {max(Vdd_record_response):3f} V, Min: {min(Vdd_record_response):3f} V with V_INPUT: {V_INPUT}V")

    t_record = np.arange(0, len(Vdd_record_response)) / RECORD_SAMPLE_FREQUENCY
    ax.plot(t_record, Vdd_record_response, label=f'Input voltage: {V_INPUT}V')  

    ax.legend()
    plt.pause(3)
####################################################################################
def test_power_output_linearity(psu_handle: KeysightU3606Wrapper,
                                 smu_handle: KeysightU2723Wrapper) -> None:
    
    """
    Test power supply output power linearity
    """
    V_INPUT = 3.6
    
    # Current Sweep Porperties
    START_LOAD = 1.0e-3
    END_LOAD = 30e-3
    STEPS = 50
    N_CYCLES = 3
    CURRENT_PROFILE = np.linspace(START_LOAD, END_LOAD, STEPS)
    
    I_DD_OUT_1 = [] # output current at VDD_OUT_1
    P_DD_OUT_1 = [] # output power at VDD_OUT_1

    # create figure place holder
    fig , axis = plt.subplots()
    plot, = axis.plot([], [])
    fig.suptitle(f"{V_DD_LINE_UNDER_TEST} power output linearity. V_INPUT: {V_INPUT}V", wrap=True, weight='bold')
    axis.set_xlabel("Load Current (mA)", weight='bold')
    axis.set_ylabel(f"Output Power (mW)", weight='bold')
    axis.grid(True, which="both", ls="-")

    logging.info(f"::Power Lineary Test:: Applying Current Sweep to: {V_DD_LINE_UNDER_TEST} and measure output power")

    # set DC supply and enable output
    psu_handle.set_dc_supply_output_voltage(V_INPUT)
    psu_handle.enable_dc_output()

    # allow system to stabilize after power on
    time.sleep(SLEEP_EVENT)

    # start SMU with static base load
    smu_handle.set_smu_source_current(LOAD_CHANNEL,  -1 * BASE_LOAD_CURRENT) # mA
    smu_handle.enable_smu_channel(LOAD_CHANNEL)

    time.sleep(SLEEP_EVENT)
    
    # Perform current sweep forward and backward for REPEATS
    t_start = time.perf_counter()
    try:
        for _ in range(N_CYCLES):
            for i_step in chain(CURRENT_PROFILE, reversed(CURRENT_PROFILE)):
                smu_handle.set_smu_source_current(LOAD_CHANNEL, -1 * i_step) # i_step is current in A unit (negative to sink)
                time.sleep(0.25)
                i_dd_12 = abs(smu_handle.measure_current_scalar(LOAD_CHANNEL)) * 1000 # measure current, get abs value, convert to mA
                I_DD_OUT_1.append(i_dd_12)
                P_DD_OUT_1.append(smu_handle.measure_voltage_scalar(LOAD_CHANNEL) * i_dd_12) # measure voltage and calculate power

    except Exception as e:
        logging.error(f"An exception has occured during test: {repr(e)}")
        smu_handle.disable_smu_channel(LOAD_CHANNEL)
        psu_handle.disable_dc_output()
        assert False

    t_end = time.perf_counter()
    logging.info(f"Load Current Sweep Took: {(t_end - t_start):3f} sec")

    logging.info(f"{V_DD_LINE_UNDER_TEST} Max/Min power; Max: {max(P_DD_OUT_1):3f} mW, Min: {min(P_DD_OUT_1):3f} mW with V_INPUT: {V_INPUT}V")
    
    smu_handle.disable_smu_channel(LOAD_CHANNEL)
    psu_handle.disable_dc_output()
    
    # plot results of  load current vs. output power (@Vdd)
    axis.plot(I_DD_OUT_1, P_DD_OUT_1)    
    
    plt.legend()
    plt.grid(True, which="both", ls="-")
    plt.pause(3)