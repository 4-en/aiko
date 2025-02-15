from dotenv import load_dotenv
from aiko2.tests import kb_test

import time

class Stopwatch:
    def __init__(self):
        self.start_time = time.time()
        self.step_time = self.start_time

    def reset(self):
        self.start_time = time.time()

    def elapsed(self):
        return time.time() - self.start_time
    
    def step(self):
        elapsed = time.time() - self.step_time
        self.step_time = time.time()
        return elapsed

    def __str__(self):
        return f"{self.elapsed()}s"

    def __repr__(self):
        return f"Stopwatch({self.elapsed()}s)"


def main():

    print("Hello, world!")
    print("Testing pipeline")
    stopwatch = Stopwatch()
    from aiko2.client import CLI
    print(f"CLI loaded in {stopwatch}")
    from aiko2.discord import BasicDiscordBot
    print(f"Discord loaded in {stopwatch}")

    # CLI.run()
    BasicDiscordBot.main()


if __name__ == "__main__":
    main()
