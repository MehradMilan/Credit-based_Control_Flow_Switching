from models.device import Device
from models.switch import Switch
from utils.logger import logger
from utils.config_loader import load_config
import matplotlib.pyplot as plt

def run_simulation(duration: int, devices: list, switch: Switch):
    logger.info("Starting simulation")
    switch.init_credits()
    switch.init_target_credits()
    time = 0
    while time < duration:
        for device in switch.connected_devices.values():
            device.generate_packets(time)
            device.send_packets(time=time)
            device.track_buffer()       
            device.track_output_buffer()
            device.process_packets()
        time += 1    
    logger.info(f"Simulation complete at time: {time}")

def run_cool_down_simulation(start: int, devices: list, switch: Switch):
    logger.info("Starting cool down simulation")
    switch.init_credits()
    switch.init_target_credits()
    time = start
    complete = False
    while True:
        if complete:
            break
        for device in switch.connected_devices.values():
            device.send_packets(cooldown=True, time=time)
            device.track_buffer()
            device.track_output_buffer()
            device.process_packets()
        time += 1
        complete = True
        for device in switch.connected_devices.values():
            for out_buffer_devices in device.out_buffer:
                if len(device.out_buffer[out_buffer_devices]) > 0:
                    complete = False
    logger.info(f"Cool down simulation complete at time: {time}")
    return time

def plot_input_buffer_utilization(switch: Switch, finish_time: int):
    plt.figure(figsize=(12, 6))
    for device in switch.connected_devices.values():
        device.track_buffer()
        plt.plot(range(finish_time+1), device.buffer_occupancy, label=f"{device.device_id} - Input Buffer")
    plt.xlabel("Time")
    plt.ylabel("Input Buffer Size")
    plt.title("Input Buffer Utilization Over Time")
    plt.legend()
    plt.grid(True)
    plt.show()

def plot_output_buffer_utilization(switch: Switch, finish_time: int):
    plt.figure(figsize=(12, 6))
    for device in switch.connected_devices.values():
        device.track_output_buffer()
        plt.plot(range(finish_time+1), device.output_buffer_size, label=f"{device.device_id} - Output Buffer", linestyle="--")
    plt.xlabel("Time")
    plt.ylabel("Output Buffer Size")
    plt.title("Output Buffer Utilization Over Time")
    plt.legend()
    plt.grid(True)
    plt.show()

def plot_dropped_packets(switch: Switch):
    plt.figure(figsize=(12, 6))
    for device in switch.connected_devices.values():
        times = sorted(device.dropped_packets.keys())
        dropped_counts = [device.dropped_packets[time] for time in times]
        plt.plot(times, dropped_counts, label=f"{device.device_id} - Dropped Packets", linestyle="--")
    plt.xlabel("Time")
    plt.ylabel("Dropped Packets")
    plt.title("Dropped Packets Over Time")
    plt.legend()
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    config = load_config("config/config.json")
    devices = [Device(**device) for device in config["devices"]]
    switch = [Switch(**switch) for switch in config["switches"]][0]
    switch.connect_devices(devices)
    SIMULATION_DURATION = 20
    run_simulation(SIMULATION_DURATION, devices, switch)
    finish_time = run_cool_down_simulation(SIMULATION_DURATION, devices, switch)

    plot_input_buffer_utilization(switch, finish_time)
    plot_output_buffer_utilization(switch, finish_time)
    plot_dropped_packets(switch)