from dotenv import load_dotenv
from aiko2.tests import kb_test


def main():
    #kb_test.main()

    load_dotenv()

    print("Hello, world!")
    print("Testing pipeline")

    from aiko2.client import CLI
    from aiko2.discord import BasicDiscordBot

    # CLI.run()
    BasicDiscordBot.main()


if __name__ == "__main__":
    main()
