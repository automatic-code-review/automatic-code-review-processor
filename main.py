import sys
import logging

from app import processor_executor


class AutoFlush:
    def __init__(self, stream):
        self.stream = stream

    def write(self, data):
        self.stream.write(data)
        self.stream.flush()

    def flush(self):
        self.stream.flush()



if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )
    sys.stdout = AutoFlush(sys.stdout)
    exit_code = processor_executor.execute()
    sys.exit(exit_code)
