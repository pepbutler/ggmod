import argparse

def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help="variation of bruhs")
    bruh_parser = subparsers.add_parser("bruh")
    bruh2_parser = subparsers.add_parser("bruh2")

    bruh_parser.add_argument("a")

    parsed_args = parser.parse_args()
    print(vars(parsed_args))

if __name__ == "__main__":
    main()
