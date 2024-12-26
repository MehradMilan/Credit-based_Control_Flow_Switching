from utils.logger import logger
from models.packet import Packet
from models.switch import Switch

class Device:
    def __init__(self, device_id: str, buffer_capacity: int, send_rates: dict, process_rate: int, packet_config: dict):
        self.device_id = device_id
        self.buffer_capacity = buffer_capacity * 2
        self.send_rates = send_rates
        self.process_rate = process_rate
        self.packet_config = packet_config
        self.in_buffer = []
        self.out_buffer = {rcvr: list() for rcvr in send_rates.keys()}
        self.credits = {}
        self.target_credits = {}
        self.buffer_occupancy = []
        self.output_buffer_size = []
        self.retransmitted_packets = []
        self.dropped_packets = {}

    def connect_to_switch(self, switch: Switch):
        self.switch = switch
        logger.info(f"Device {self.device_id} connected to switch {switch.switch_id}")

    def receive_packet(self, packet, time: int):
        current_time = time
        if len(self.in_buffer) < self.buffer_capacity:
            self.in_buffer.append(packet)
            logger.info(f"Packet received by {self.device_id}")
            self.dropped_packets[current_time] = 0
        else:
            if current_time not in self.dropped_packets:
                self.dropped_packets[current_time] = 1
            else:
                self.dropped_packets[current_time] += 1

            self.switch.connected_devices[packet.source_device_id].out_buffer[self.device_id].append(packet)
            logger.info(f"Packet dropped for retransmission by {self.device_id}")

    def process_packets(self):
        for _ in range(self.process_rate):
            if len(self.in_buffer) > 0:
                self.in_buffer.sort(key=lambda pkt: pkt.priority, reverse=True)
                pkt = self.in_buffer.pop(0)
                self.switch.connected_devices[pkt.source_device_id].target_credits[self.device_id] = min(
                    self.switch.connected_devices[pkt.source_device_id].target_credits[self.device_id] + 1,
                    self.credits[pkt.source_device_id]
                )
                logger.info(f"Packet with priority {pkt.priority} processed by {self.device_id}")
            else:
                break

    def generate_packets(self, time: int, packet_config: dict):
        for packet_type, config in packet_config.items():
            frequency = config['packet_freq']
            priority = config['packet_priority']
            for dvc in self.send_rates.keys():
                for _ in range(frequency):
                    pkt = Packet(
                        packet_type=packet_type,
                        size=config['packet_size'],
                        source_device_id=self.device_id,
                        destination_device_id=dvc,
                        priority=priority,
                        time=time
                    )
                    self.out_buffer[dvc].append(pkt)
                    logger.info(f"Packet of type {packet_type} generated from {self.device_id} to {dvc} with priority {priority}")

    def send_packets(self, time: int, cooldown=False):
        for dvc, rate in self.send_rates.items():
            for _ in range(rate):
                pkt = None
                if self.target_credits[dvc] > 0:
                    if len(self.out_buffer[dvc]) > 0:
                        self.out_buffer[dvc].sort(key=lambda p: self.packet_config[p.packet_type]['packet_priority'], reverse=True)
                        pkt = self.out_buffer[dvc].pop(0)
                        self.target_credits[dvc] -= 1
                        self.switch.forward_packet(pkt, time)
                        logger.info(f"Packet sent from {self.device_id} to {dvc}")
                    elif cooldown:
                        self.freeze_send_rate(dvc)
                        logger.info(f"Device {self.device_id} is in cooldown from sending packets to {dvc}")
                        break

    def freeze_send_rate(self, dvc):
        self.send_rates[dvc] = 0
        self.switch.init_credits()
        self.switch.init_target_credits()

    def track_buffer(self):
        priority_count = {pkt_type: 0 for pkt_type in self.packet_config}
        for pkt in self.in_buffer:
            priority_count[pkt.packet_type] += 1
        if not hasattr(self, 'buffer_by_priority'):
            self.buffer_by_priority = {pkt_type: [] for pkt_type in self.packet_config}
        for pkt_type in self.packet_config:
            self.buffer_by_priority[pkt_type].append(priority_count[pkt_type])


    def track_output_buffer(self):
        total_out_buffer = sum(len(buf) for buf in self.out_buffer.values())
        self.output_buffer_size.append(total_out_buffer)