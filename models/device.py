from utils.logger import logger
from models.packet import Packet
from models.switch import Switch

class Device:

    def __init__(self, device_id: str, buffer_capacity: int, send_rates: dict, process_rate: int):
        self.device_id = device_id
        self.buffer_capacity = buffer_capacity * 2
        self.send_rates = send_rates
        self.in_buffer = []
        self.out_buffer = {rcvr: list() for rcvr in send_rates.keys()}
        self.process_rate = process_rate
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
                pkt = self.in_buffer.pop(0)
                self.switch.connected_devices[pkt.source_device_id].target_credits[self.device_id] = min (
                    self.switch.connected_devices[pkt.source_device_id].target_credits[self.device_id] + 1,
                    self.credits[pkt.source_device_id]
                )
                logger.info(f"Packet processed by {self.device_id}")
            else:
                break

    def generate_packets(self, time: int):
        for dvc, rate in self.send_rates.items():
            for _ in range(rate):
                pkt = Packet(packet_type="1", size=0.5, source_device_id=self.device_id, destination_device_id=dvc, time=time)
                self.out_buffer[dvc].append(pkt)
                logger.info(f"Packet generated from {self.device_id} to {dvc}")

    def send_packets(self, time: int, cooldown=False):
        for dvc, rate in self.send_rates.items():
            for _ in range(rate):
                pkt = None
                if self.target_credits[dvc] > 0:
                    if len(self.out_buffer[dvc]) > 0:
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
        self.buffer_occupancy.append(len(self.in_buffer))

    def track_output_buffer(self):
        total_out_buffer = sum(len(buf) for buf in self.out_buffer.values())
        self.output_buffer_size.append(total_out_buffer)