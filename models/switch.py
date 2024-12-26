from utils.logger import logger

class Switch:
    def __init__(self, switch_id: str, connected_devices_ids: list):
        self.switch_id = switch_id
        self.connected_devices_ids = connected_devices_ids
        self.connected_devices = {}

    def connect_devices(self, devices):
        for device in devices:
            if device.device_id in self.connected_devices_ids:
                device.connect_to_switch(self)
                self.connected_devices[device.device_id] = device
                logger.info(f"Switch {self.switch_id} connected to device {device.device_id}")

    def init_credits(self):
        for device in self.connected_devices.values():
            receive_rates = {}
            for conn_dvc in device.send_rates.keys():
                receive_rates[conn_dvc] = self.connected_devices[conn_dvc].send_rates[device.device_id]
            if sum(receive_rates.values()) == 0:
                for conn_dvc in device.send_rates.keys():
                    device.credits[conn_dvc] = 0
                return
            for conn_dvc in device.send_rates.keys():
                device.credits[conn_dvc] = (device.buffer_capacity * receive_rates[conn_dvc]) // (sum(receive_rates.values()))
            for conn_dvc in device.send_rates.keys():
                if device.buffer_capacity - sum(device.credits.values()) > 0:
                    device.credits[conn_dvc] += 1

    def init_target_credits(self):
        for device in self.connected_devices.values():
            for conn_dvc in device.send_rates.keys():
                device.target_credits[conn_dvc] = self.connected_devices[conn_dvc].credits[device.device_id]

    def forward_packet(self, packet, time: int):
        self.connected_devices[packet.destination_device_id].receive_packet(packet, time)
        logger.info(f"Packet forwarded from {packet.source_device_id} to {packet.destination_device_id}")
    