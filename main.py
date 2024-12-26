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
            device.generate_packets(time, switch.packet_config)
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

    device_colors = {
        device_id: color
        for device_id, color in zip(switch.connected_devices.keys(), ['orange', 'blue', 'green', 'red'])
    }
    type_markers = {
        pkt_type: marker
        for pkt_type, marker in zip(switch.packet_config.keys(), ['o', '^', '^', 'd'])
    }

    for device in switch.connected_devices.values():
        device.track_buffer()
        for pkt_type, buffer_sizes in device.buffer_by_priority.items():
            plt.plot(
                range(finish_time + 1),
                buffer_sizes,
                label=f"Device {device.device_id} - Type {pkt_type}",
                color=device_colors[device.device_id],
                marker=type_markers[pkt_type],
                linestyle="-",
                linewidth=1.5,
                markersize=5
            )

    device_handles = [
        plt.Line2D([], [], color=color, marker='', linestyle='-', linewidth=2, label=f"Device {device_id}")
        for device_id, color in device_colors.items()
    ]
    type_handles = [
        plt.Line2D([], [], color='black', marker=marker, linestyle='', markersize=8, label=f"Type {pkt_type}")
        for pkt_type, marker in type_markers.items()
    ]

    plt.legend(handles=device_handles + type_handles, loc="upper right", title="Legend")
    plt.xlabel("Time")
    plt.ylabel("Buffer Size")
    plt.title("Input Buffer Utilization Over Time")
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
    packet_config = {pkt['packet_type']: pkt for pkt in config["packets"]}

    devices = [Device(**device, packet_config=packet_config) for device in config["devices"]]
    switch = Switch(**config["switches"][0], packet_config=packet_config)
    switch.connect_devices(devices)

    SIMULATION_DURATION = 20
    run_simulation(SIMULATION_DURATION, devices, switch)
    finish_time = run_cool_down_simulation(SIMULATION_DURATION, devices, switch)

    plot_input_buffer_utilization(switch, finish_time)
    plot_output_buffer_utilization(switch, finish_time)
    plot_dropped_packets(switch)