import os
import pathlib
import re


class WikiPage:
    def __init__(self, name: str):
        self.name: str = name
        self.content = list()

    def __str__(self):
        return self.name + self._build_page()

    def _build_page(self):
        return "\n".join(self.content)

    def add_row(self, row: str):
        self.content.append(row)

    def add_table_header(self, *args):
        column_separator = " | "
        header = column_separator + column_separator.join(args).replace(":", "")
        divider = column_separator
        for arg in args:
            d = ["----"]
            for pos in re.finditer(r":", arg):
                if pos.start() == 0:
                    d.insert(0, ":")
                if pos.start() == len(arg) - 1:
                    d.append(":")
            divider += "".join(d) + column_separator
        self.content.append(header)
        self.content.append(divider)

    def add_table_row(self, *args):
        column_separator = " | "
        if args:
            row = column_separator + column_separator.join(args)
            self.content.append(row)

    def add_section_break(self):
        self.content.append("")

    def output_page(self):
        separator = "-"
        file_name = separator.join(self.name.split()) + ".md"
        dump_dir = "wiki"
        pathlib.Path(dump_dir).mkdir(parents=True, exist_ok=True)
        output_file = open(os.path.join(dump_dir, file_name), "w+")
        output_file.write(self._build_page())
        output_file.close()
