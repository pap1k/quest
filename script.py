import re

__version = 0.2


class script_func:
    name = ""
    arglist = []
    has_func = False
    func = None
    stack = ""

    def __init__(self, name, func=None) -> None:
        self.name = name
        self.stack = ""
        self.arglist = []
        if func != None:
            self.has_func = True
            self.func = func

    def add_arg(self, *args):
        for arg in args:
            self.arglist.append(arg)

    def execute(self, *arglist):
        if self.has_func:
            return self.func(*arglist)
        s = self.stack
        for i in range(len(arglist)):
            s = s.replace(f"%{self.arglist[i]}%", arglist[i])

        return s


def function_input_comp(*args):
    return "--special_action input_comp " + args[0]


def function_input(*args):
    return "--special_action input"


def function_photo_request(*args):
    return "--special_action photo_request"


def function_video_request(*args):
    return "--special_action video_request"


default_functions = {
    "input": function_input,
    "photo_request": function_photo_request,
    "video_request": function_video_request,
    "input_comp": function_input_comp,
}


class Line:
    id = -1
    text: list[str] = []

    def __init__(self, id, *text) -> None:
        self.id = id
        self.text = text


class Script:
    filename: str = ""
    functions: list[script_func] = []
    errors: list[str] = []
    script: list[str] = []
    status = True

    def __init__(self, file: str) -> None:
        self.errors = []
        self.script = []
        self.functions = []
        self.status = False

        if file.endswith(".qs"):
            self.filename = file
        else:
            self.filename = file + ".qs"

        for k in default_functions:
            self.functions.append(script_func(k, default_functions[k]))

        self.status = self.load()

    def get_line(self, line: int) -> Line:
        texts = []
        nextline = 0
        for i in range(line, len(self.script)):
            line = self.script[i]
            linefuncs = re.findall(r"\%(\w+)\((.+)?\)\%", line, re.M)
            if len(linefuncs) > 0:
                for func in linefuncs:
                    for f in self.functions:
                        if f.name == func[0]:
                            if func[1] != "":
                                texts.append(f.execute(func[1]))
                                if texts[-1].startswith("--special_action"):
                                    return Line(i + 1, *texts)
                            else:
                                texts.append(f.execute())
                                if texts[-1].startswith("--special_action"):
                                    return Line(i + 1, *texts)
            else:
                texts.append(line)
        return Line(nextline, *texts)

    def has_func(self, funcname):
        for f in self.functions:
            if f.name == funcname:
                return True
        return False

    def load(self) -> bool:
        with open(self.filename, "r", encoding="utf-8") as file:
            filedata = file.read()
            filedata = re.sub(r"\#(.*)\n", "", filedata)
            if filedata == "":
                return False

            # СОЗДАЕМ ФУНКЦИИ
            marks = re.findall(r"^\:(\w+)\b ?(\w+)?\n(.*)", filedata, re.M)
            if len(marks) < 1 and "start" not in marks:
                self.errors.append("Не найдена точка входа 'start'")
            for mark in marks:
                f = script_func(mark[0])
                if mark[1] != "":
                    f.add_arg(mark[1])
                if mark[0] != "start":
                    f.stack = mark[2]
                self.functions.append(f)

            # проверяем вызовы фукций
            funcs = re.findall(r"\%(.+)\((.*)\)\%", filedata, re.M)
            if len(funcs) > 0:
                for func in funcs:
                    if self.has_func(func[0]):
                        if func[1] != "":
                            if func[1].startswith("%") and func[1].endswith("%"):
                                param = re.findall(r"\%(.+)\%", func[1])[0]
                                if not self.has_func(param):
                                    self.errors.append(
                                        f"Обнаружена неизвестная функция {param}, перданная в качестве параметра '{func[0]}'"
                                    )
                    else:
                        self.errors.append(
                            f"Обнаружена неизвестная функция '{func[0]}'"
                        )

            if len(self.errors) > 0:
                return False

            self.script = filedata.split(":start")[1].split("\n")[1:]

            if self.script[-1] == "":
                self.script[-1] = "--special_action end"
            else:
                self.script.append("--special_action end")

            return True
