class Packet:
    pkt_counter = 0

    def __init__(self, packet_type: int, size: int, source_device_id: int, destination_device_id: int, time: int):
        self.packet_type = packet_type
        self.size = size
        self.source_device_id = source_device_id
        self.time = time
        self.destination_device_id = destination_device_id
        self.packet_id = Packet.pkt_counter
        Packet.pkt_counter += 1