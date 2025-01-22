from dotenv import load_dotenv

if __name__ == "__main__":

    load_dotenv()

    print("Hello, world!")
    print("Testing pipeline")

    from aiko2.client import CLI
    from aiko2.discord import BasicDiscordBot

    CLI.run()
    # BasicDiscordBot.main()