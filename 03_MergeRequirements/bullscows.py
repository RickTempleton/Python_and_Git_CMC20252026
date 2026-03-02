from collections import Counter
from random import choice
import argparse
from urllib.request import urlopen
from cowsay import cowsay

def bullscows(guess, secret):
    bulls = sum(g == s for g, s in zip(guess, secret))
    common = sum((Counter(guess) & Counter(secret)).values())
    cows = common - bulls
    return bulls, cows


def gameplay(ask, inform, WORDS):
    """
    запускает игру быки-коровы.
    """

    secret = choice(WORDS)
    attempts = 0

    while True:
        word = ask("Введите слово: ", WORDS)
        attempts += 1
        inform("Быки: {}, Коровы: {}", *bullscows(word, secret))
        if word == secret:
            return attempts



def ask(prompt, valid = None):
    while True:
        s = input(prompt).strip().lower()
        if valid is None or s in valid:
            return s
        print(cowsay("Недопустимое слово. Попробуйте снова."))

def inform(format_string, bulls, cows):
    print(cowsay(format_string.format(bulls, cows)))




def read_words(source: str, length: int = 5) -> list[str]:
    """
    source — локальный файл или URL
    length — длина слов (по умолчанию 5)
    """
    try:
        with open(source, "r") as f:
            text = f.read()
    except OSError:
        with urlopen(source) as r:
            text = r.read().decode()

    words = []
    for word in text.split():
        w = word.strip().lower()
        if len(w) == length:
            words.append(w)

    return list(set(words))



def main():
    parser = argparse.ArgumentParser(
        prog="bullscows",
        description=(
            "Игра «Быки и коровы».\n"
            "Пример запуска:\n"
            "python -m bullscows https://raw.githubusercontent.com/Harrix/Russian-Nouns/main/dist/russian_nouns.txt 6"
        ),
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "dictionary",
        help="Имя файла со словарём или URL"
    )
    parser.add_argument(
        "length",
        nargs="?",
        type=int,
        default=5,
        help="Длина слова (по умолчанию 5)"
    )
    args = parser.parse_args()

    words = read_words(args.dictionary, args.length)
    if not words:
        print("Нет слов подходящей длины.")
        return
    attempts = gameplay(ask, inform, words)
    print(attempts)


if __name__ == "__main__":
    main()













