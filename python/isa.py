"""Представление исходного и машинного кода.
"""

from __future__ import annotations

import json
from collections import namedtuple
from enum import Enum


class Opcode(str, Enum):
    """Opcode для инструкций."""

    # No argument
    INC = "inc"
    DEC = "dec"

    # Argument is a label (address saves to acc)
    MOV = "mov"

    # Argument is a label (address in data memory)
    LOAD = "load"
    STORE = "store"
    LD = "ld"
    ST = "st"
    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    DIV = "div"
    MOD = "mod"

    # Argument is an address in code memory
    JMP = "jmp"
    JZ = "jz"
    JNZ = "jnz"
    # No argument
    HALT = "halt"

    def __str__(self):
        """Переопределение стандартного поведения `__str__` для `Enum`"""
        return str(self.value)


class Term(namedtuple("Term", "line symbol")):
    """Описание выражения из исходного текста программы."""


def write_code(filename: str, code: list) -> None:
    """Записать машинный код в файл."""
    with open(filename, "w", encoding="utf-8") as file:
        buf = []
        for instr in code:
            buf.append(json.dumps(instr))
        file.write("[" + ",\n ".join(buf) + "]")


def read_code(filename: str) -> tuple[list[dict], list[int]]:
    """Прочесть машинный код из файла."""
    with open(filename, encoding="utf-8") as file:
        code_src = json.loads(file.read())
    data: list[int] = []
    code: list[dict] = []
    section = ""
    for instr in code_src:
        if instr == ".data":
            section = "data"
            continue
        if instr == ".text":
            section = "text"
            continue

        if section == "data":
            data.append(instr)
        elif section == "text":
            instr["opcode"] = Opcode(instr["opcode"])
            if "term" in instr:
                assert len(instr["term"]) == 2
                instr["term"] = Term(instr["term"][0], instr["term"][1])
            code.append(instr)
        else:
            raise ValueError()
    return code, data
