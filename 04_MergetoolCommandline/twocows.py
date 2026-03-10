import cowsay
import cmd
import shlex


COWS = ['bud-frogs', 'kiss', 'dragon', 'supermilker', 'head-in', 'TuxStab', 'elephant-in-snake', 'kitty', 'tux', 'bong', 'cower', 'small', 'stimpy', 'ghostbusters', 'eyes', 'sheep', 'moose', 'three-eyes', 'stegosaurus', 'hellokitty', 'mutilated', 'elephant', 'cheese', 'ren', 'vader', 'turtle', 'turkey', 'frogs', 'default', 'kosh', 'luke-koala', 'koala', 'udder', 'surgery', 'milk', 'bunny', 'satanic', 'flaming-sheep', 'daemon', 'meow', 'dragon-and-cow', 'skeleton', 'www', 'beavis.zen', 'vader-koala', 'blowfish', 'moofasa']


class twocows(cmd.Cmd):
    prompt = "twocows> "

    def _two_cowsay(self, name_1, messenge_1, params_1, name_2, messenge_2, params_2, cowthink = False):
        """The realization of a dialogue between two cows"""

        fun = cowsay.cowthink if cowthink else cowsay.cowsay

        try:
            cow_1 = fun(
                messenge_1,
                cow=name_1,
                **params_1
            )

            cow_2 = fun(
                messenge_2,
                cow=name_2,
                **params_2
            )

        except Exception as er:
            print(er)
            return

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


    def do_list_cows(self, arg):
        """Print the list of available cows"""
        print(COWS)


    def _parse_1(self, arg):
        """Parse the input argument for 1 cows"""
        if not isinstance(arg, list):
            arg = shlex.split(arg)

        if len(arg) <= 0:
            print("Нет сообщения")
            return None
        
        messenge = arg[0]
        if len(arg) > 1 and arg[1] in COWS:
            name = arg[1]
            params = arg[2:]
        else:
            name = "default"
            params = arg[1:]

        params = dict(w.split("=", 1) for w in params if "=" in w)
        return name, messenge, params

    def _parse_2(self, arg):
        """Parse the input argument for 2 cows"""
        arg = shlex.split(arg)
        str_split = "reply"

        if str_split not in arg:
            print(f"Нет {str_split}")
            return

        pos = arg.index(str_split)
        cow_1 = arg[:pos]
        cow_2 = arg[pos + 1:]
        
        param_1 = self._parse_1(cow_1)
        param_2 = self._parse_1(cow_2)

        if param_1 is None or param_2 is None:
            return None

        return param_1 + param_2


    def do_cowsay(self, arg):
        """Using the two_cowsay module 
        сообщение [название {параметр=значение}] reply ответ [название {параметр=значение}]
        
        сообщение и ответ — это реплики двух персонажей
        название — это название коровы (должно поддерживаться достраивание)
        параметр=значение — это eyes и tongue, а значение — строк"""
        if param := self._parse_2(arg):
            self._two_cowsay(*param)
    
    def do_cowthink(self, arg):
        """Using the two_cowthink module
        сообщение [название {параметр=значение}] reply ответ [название {параметр=значение}]
        
        сообщение и ответ — это реплики двух персонажей
        название — это название коровы (должно поддерживаться достраивание)
        параметр=значение — это eyes и tongue, а значение — строк"""
        if param := self._parse_2(arg):
            self._two_cowsay(*param, cowthink=True)

    def do_make_bubble(self, arg):
        """Using the make_bubble module 
        сообщение {параметр=значение}
        """
        if param := self._parse_1(arg):
            try:
                print(cowsay.make_bubble(param[1], **param[2]))
            except Exception as er:
                print(er)
        


twocows().cmdloop()