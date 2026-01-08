"""
Demonstrates setting up stream-in with stream-out that continuously updates.

====================================================================
Make it a library for LAPP demonstration experiment Michelson-Virgo
====================================================================

old explanation :

Streams in while streaming out arbitrary values. These arbitrary stream-out
values act on DAC0 to alternate between increasing the voltage from 0 to 2.5 and
decreasing from 5.0 to 2.5 on (approximately). Though these values are initially
generated during the call to create_out_context, the values could be
dynamically generated, read from a file, etc. To convert this example file into
a program to suit your needs, the primary things you need to do are:

    1. Edit the global setup variables in this file
    2. Define your own create_out_context function or equivalent
    3. Define your own process_stream_results function or equivalent

You may also need to configure AIN, etc.

"""
import sys
from math import *
from labjack import ljm

import ljm_stream_util
import matplotlib.pyplot as plt


# Setup

IN_NAMES = ["AIN0"]
# could define more stream input channels : IN_NAMES = ["AIN0", "AIN1"]


"""
STREAM_OUTS = [
    {
        "target": str register name that stream-out values will be sent to,
        "buffer_num_bytes": int size in bytes for this stream-out buffer,

        "stream_out_index": int STREAM_OUT# offset. 0 would generate names like
            "STREAM_OUT0_BUFFER_STATUS", etc.

        "set_loop": int value to be written to STREAM_OUT#(0:3)_SET_LOOP
    },
    ...
]
"""
STREAM_OUTS = [
    {
        "target": "DAC0",
        "buffer_num_bytes": 512,
        "stream_out_index": 0,
        "set_loop": 3
    }]
#
# could define more output channels as in
#,
#    {
#        "target": "DAC1",
#        "buffer_num_bytes": 512,
#        "stream_out_index": 1,
#        "set_loop": 3
#    }
#]


# default scan rate, do not exceed 2000 Hz (approximately)
# well, you can try, depends on your hardware
INITIAL_SCAN_RATE_HZ = 2000 # speed limit : around 3000 Hz, be below 2048

# old comment :

# Note: This program does not work well for large scan rates because
# the value loops will start looping before new value loops can be written.
# While testing on USB with 512 bytes in one stream-out buffer, 2000 Hz worked
# without stream-out buffer loop repeating.
# (Other machines may have different results.)
# Increasing the size of the buffer_num_bytes will increase the maximum speed.
# Using an Ethernet connection type will increase the maximum speed.

NUM_CYCLES = 5
# I didn't understand yet what this was really for,
# probably the number of slices of the buffer ?
# never mind, let's be pragmatic, it works...

def print_register_value(handle, register_name):
    value = ljm.eReadName(handle, register_name)
    print("%s = %f" % (register_name, value))


def open_ljm_device(device_type, connection_type, identifier):
    try:
        handle = ljm.open(device_type, connection_type, identifier)
    except ljm.LJMError:
        print(
            "Error calling ljm.open(" +
            "device_type=" + str(device_type) + ", " +
            "connection_type=" + str(connection_type) + ", " +
            "identifier=" + identifier + ")"
        )
        raise

    return handle


def print_device_info(handle):
    info = ljm.getHandleInfo(handle)
    print(
        "Opened a LabJack with Device type: %i, Connection type: %i,\n"
        "Serial number: %i, IP address: %s, Port: %i,\nMax bytes per MB: %i\n" %
        (info[0], info[1], info[2], ljm.numberToIP(info[3]), info[4], info[5])
    )

def inject_detect(
    injection_signal,
    scan_rate_hz=INITIAL_SCAN_RATE_HZ,
    verbose = 0
):
# injection and detection on the Michelson
# injects signal injection_signal on the DAC0 channel (in volts)
# returns the detected signal on AIN0 (in volts)
    in_names=IN_NAMES
    stream_outs=STREAM_OUTS
    num_cycles=NUM_CYCLES
    
    injection_signal_samples = len(injection_signal)

    detection_signal = main_in_out(injection_signal, scan_rate_hz, in_names, stream_outs, num_cycles, verbose=verbose)
    return detection_signal

def main_in_out(
    injection_signal,
    initial_scan_rate_hz=INITIAL_SCAN_RATE_HZ,
    in_names=IN_NAMES,
    stream_outs=STREAM_OUTS,
    num_cycles=NUM_CYCLES,
    verbose=0
):
# main injection and detection loop
# adapted from the ljm example in_stream_with_non_looping_out_stream.py
    injection_signal_samples = len(injection_signal)
    detection_signal = []
    
    print("Beginning...")
    handle = open_ljm_device(ljm.constants.dtANY, ljm.constants.ctANY, "ANY")
    print_device_info(handle)

    print("Initializing stream out buffers...")
    out_contexts = []
    for stream_out in stream_outs:
        out_context = create_out_context_from_signal(stream_out,injection_signal)
        ljm_stream_util.initialize_stream_out(handle, out_context)
        out_contexts.append(out_context)

    print("")

    for out_context in out_contexts:
        print_register_value(handle, out_context["names"]["buffer_status"])

    for out_context in out_contexts:
        update_str = "Updating %(stream_out)s buffer whenever " \
            "%(buffer_status)s is greater or equal to " % out_context["names"]
        print(update_str + str(out_context["state_size"]))

    scans_per_read = int(min([context["state_size"] for context in out_contexts]))
    print("scans per read = %i" % scans_per_read)
    buffer_status_names = [out["names"]["buffer_status"] for out in out_contexts]
    print(buffer_status_names)
    try:
        scan_list = ljm_stream_util.create_scan_list(
            in_names=in_names,
            out_contexts=out_contexts
        )
        print("scan_list: " + str(scan_list))
        print("scans_per_read: " + str(scans_per_read))
        
        # set the number of slices/cycles
        out_context=out_contexts[0]
        num_cycles = int(injection_signal_samples/out_context["state_size"])
        print("out_context state size %i" % out_context["state_size"])
 #       test_plot = []
 #       for i in range(num_cycles):
 #          test_plot.extend(out_context["states"][i]["values"])

        scan_rate = ljm.eStreamStart(handle, scans_per_read, len(scan_list),
                                     scan_list, initial_scan_rate_hz)
        print("\nStream started with a scan rate of %0.0f Hz." % scan_rate)
        print("\nPerforming %i buffer updates." % num_cycles)

        iteration = 0
        total_num_skipped_scans = 0
        while iteration < num_cycles:
            buffer_statuses = [0]
            infinity_preventer = 0
            while max(buffer_statuses) < 0.5*out_context["state_size"]:
                buffer_statuses = ljm.eReadNames(
                    handle,
                    len(buffer_status_names),
                    buffer_status_names
                )
                if(verbose > 0):
                    print(str(out_context["state_size"])+"   :::   "+str(max(buffer_statuses))+" :::  "+str(infinity_preventer))
                infinity_preventer = infinity_preventer + 1
                if infinity_preventer > scan_rate:
                    raise ValueError(
                        "Buffer statuses don't appear to be updating:" +
                        str(buffer_status_names) + str(buffer_statuses)
                    )

            for out_context in out_contexts:
                ljm_stream_util.update_stream_out_buffer(handle, out_context)

            # ljm.eStreamRead will sleep until data has arrived
            stream_read = ljm.eStreamRead(handle)
            if(verbose > 0) :
                print("length of result : %i" % len(stream_read[0]))
#            print("result :" + str(stream_read[0]))

            num_skipped_scans = ljm_stream_util.process_stream_results(
                iteration,
                stream_read,
                in_names,
                device_threshold=out_context["state_size"],
                ljm_threshold=out_context["state_size"]
            )
            total_num_skipped_scans += num_skipped_scans
            # if no skipped scans, nothing is printed, else the "process_stream" function will do
            
            # build the detection signal, append the results read from the input stream
            detection_signal.extend(stream_read[0][:scans_per_read])

            iteration = iteration + 1
    except ljm.LJMError:
        ljm_stream_util.prepare_for_exit(handle)
        raise
    except Exception:
        ljm_stream_util.prepare_for_exit(handle)
        raise
    ljm_stream_util.prepare_for_exit(handle)

    print("Total number of skipped scans: %d" % total_num_skipped_scans)
    
    return detection_signal

def create_out_context_from_signal(stream_out, out_signal):
    """Create an object wich describes some stream-out buffer states.
       starting from an arbitrary signal

    Create dict which will look something like this:
    out_context = {
        "current_index": int tracking which is the current state,
        "states": [
            {
                "state_name": str describing this state,
                "values": iterable over float values
            },
            ...
        ],
        "state_size": int describing how big each state's "values" list is,
        "target_type_str": str used to generate this dict's "names" list,
        "target": str name of the register to update during stream-out,
        "buffer_num_bytes": int number of bytes of this stream-out buffer,
        "stream_out_index": int number of this stream-out,
        "set_loop": int number to be written to to STREAM_OUT#(0:3)_SET_LOOP,
        "names": dict of STREAM_OUT# register names. For example, if
            "stream_out_index" is 0 and "target_type_str" is "F32", this would be
        {
            "stream_out": "STREAM_OUT0",
            "target": "STREAM_OUT0_TARGET",
            "buffer_size": "STREAM_OUT0_BUFFER_SIZE",
            "loop_size": "STREAM_OUT0_LOOP_SIZE",
            "set_loop": "STREAM_OUT0_SET_LOOP",
            "buffer_status": "STREAM_OUT0_BUFFER_STATUS",
            "enable": "STREAM_OUT0_ENABLE",
            "buffer": "STREAM_OUT0_BUFFER_F32"
        }
    }
    """
    BYTES_PER_VALUE = 2
    out_buffer_num_values = stream_out["buffer_num_bytes"] / BYTES_PER_VALUE

    # The size of all the states in out_context. This must be half of the
    # out buffer or less. (Otherwise, values in a given loop would be getting
    # overwritten during a call to update_stream_out_buffer.)
    state_size = int(out_buffer_num_values / 2)

    target_type = ljm_stream_util.convert_name_to_out_buffer_type_str(stream_out["target"])
    out_context = {
        "current_index": 0,
        "states": [],
        "state_size": state_size,
        "target_type_str": target_type
    }
    out_context.update(stream_out)

    out_context["names"] = ljm_stream_util.create_stream_out_names(out_context)
    
    num_signal_slices = int(len(out_signal)/state_size)
    print("Number of signal slices : "+str(num_signal_slices))
    if (len(out_signal)%state_size != 0):
       num_complete_signal = state_size - (len(out_signal)%state_size)
       out_signal.extend([0]*num_complete_signal)
    for i_signal_slice in range(num_signal_slices):
       out_context["states"].append(
          {
            "state_name": "slice"+str(i_signal_slice),
            "values": out_signal[i_signal_slice*state_size:(i_signal_slice+1)*state_size]
          }
       )

    print(len(out_context["states"][0]["values"]))
    return out_context

def process_stream_results(
    iteration,
    stream_read,
    in_names,
    device_threshold=0,
    ljm_threshold=0
):
    
    """
    Adapted from the LJM example in ljm_stream_util library

    in the old example, Print ljm.eStreamRead results and count the number of skipped samples."""
    data = stream_read[0]
    device_num_backlog_scans = stream_read[1]
    ljm_num_backlog_scans = stream_read[2]
    num_addresses = len(in_names)
    num_scans = len(data) / num_addresses

    # Count the skipped samples which are indicated by -9999 values. Missed
    # samples occur after a device's stream buffer overflows and are
    # reported after auto-recover mode ends.
    num_skipped_samples = data.count(-9999.0)

    print("\neStreamRead %i" % iteration)
    result_strs = []
    for index in range(len(in_names)):
        result_strs.append("%s = %0.5f" % (in_names[index], data[index]))

    if result_strs:
        print("  1st scan out of %i: %s" % (num_scans, ", ".join(result_strs)))

    # This is a test to ensure that 2 in channels are synchronized
    # def print_if_not_equiv_floats(index, a, b, delta=0.01):
    #     diff = abs(a - b)
    #     if diff > delta:
    #         print("index: %d, a: %0.5f, b: %0.5f, diff: %0.5f, delta: %0.5f" % \
    #             (index, a, b, diff, delta)
    #         )

    # for index in range(0, len(data), 2):
    #     print_if_not_equiv_floats(index, data[index], data[index + 1])

    if num_skipped_samples:
        print(
            "  **** Samples skipped = %i (of %i) ****" %
            (num_skipped_samples, len(data))
        )

    status_strs = []
    if device_num_backlog_scans > device_threshold:
        status_strs.append("Device scan backlog = %i" % device_num_backlog_scans)
    if ljm_num_backlog_scans > ljm_threshold:
        status_strs.append("LJM scan backlog = %i" % ljm_num_backlog_scans)

    if status_strs:
        status_str = "  " + ",".join(status_strs)
        print(status_str)

    return num_skipped_samples

