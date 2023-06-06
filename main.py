import sys

from app import processor_executor

if __name__ == "__main__":
    exit_code = processor_executor.execute()
    sys.exit(exit_code)
