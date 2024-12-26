import logging

def initialize_logger():
    logging.basicConfig(
        filename="simulation.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger("SimulationLogger")

logger = initialize_logger()