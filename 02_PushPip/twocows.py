from cowsay import cowsay
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Визуализирует диалогов двух 'коров'")

    parser.add_argument("-e", help="Глаза для первой 'коровы'")
    parser.add_argument("-f", help="Первая 'корова'")
    parser.add_argument("-n", help="Сообщение первой коровы в 1 строку", action="store_true")

    parser.add_argument("-E", help="Глаза для второй 'коровы'")
    parser.add_argument("-F", help="Вторая 'корова'")
    parser.add_argument("-N", help="Сообщение второй коровы в 1 строку", action="store_true")

    parser.add_argument("args", nargs=2, help="Два сообщения")

    args = vars(parser.parse_args())

    massage_1 = args["args"][0]
    massage_2 = args["args"][1]

    cow_1 = cowsay(
        massage_1,
        cow=args.get("f") or "default",
        eyes=args.get("e") or "oo",
        wrap_text=(not args.get("n", False)),
    )

    cow_2 = cowsay(
        massage_2,
        cow=args.get("F") or "default",
        eyes=args.get("E") or "oo",
        wrap_text=(not args.get("N", False)),
    )

    lines_1 = cow_1.splitlines()
    lines_2 = cow_2.splitlines()

    w1 = max((len(s) for s in lines_1), default=0)
    h1 = len(lines_1)
    h2 = len(lines_2)

    if h1 < h2:
        lines_1 = ([" " * w1] * (h2 - h1)) + lines_1
    if h2 < h1:
        lines_2 = ""

    eps = "  "
    for a, b in zip(lines_1, lines_2):
        print(a.ljust(w1) + eps + b)