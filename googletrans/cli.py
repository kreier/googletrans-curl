import argparse
import asyncio
import sys

from googletrans.client import Translator


async def _run_cli(args: argparse.Namespace) -> None:
    async with Translator() as translator:
        if args.detect:
            result = await translator.detect(args.text)
            print(f"[{result.lang}, {result.confidence}] {args.text}")
            return

        result = await translator.translate(args.text, dest=args.dest, src=args.src)
        output = f"""[{result.src}] {result.origin}
    ->
[{result.dest}] {result.text}
[pron.] {result.pronunciation}"""
        print(output)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Python Google Translator as a command-line tool"
    )
    parser.add_argument("text", help="The text you want to translate.")
    parser.add_argument(
        "-d",
        "--dest",
        default="en",
        help="The destination language you want to translate. (Default: en)",
    )
    parser.add_argument(
        "-s",
        "--src",
        default="auto",
        help="The source language you want to translate. (Default: auto)",
    )
    parser.add_argument(
        "-c", "--detect", action="store_true", default=False, help="Detect language"
    )
    args = parser.parse_args()
    asyncio.run(_run_cli(args))


if __name__ == "__main__":
    main()
