#!/usr/bin/python3
"""Транслятор Asm в машинный код.
"""

from __future__ import annotations

import sys

from python.isa import Opcode, Term, write_code


def get_meaningful_token(line):
    """Извлекаем из строки содержательный токен (метка или инструкция), удаляем
    комментарии и пробелы в начале/конце строки.
    """
    return line.split(";", 1)[0].strip()


def add_to_data(data: list, data_labels: list, token: str):
    """Добавление токена в секцию данных."""
    pc = len(data)
    if token.endswith(":"):  # токен содержит метку
        label = token.strip(":")
        assert label not in data_labels, f"Redefinition of label: {label}"
        data_labels[label] = pc
    elif token.startswith('"') and token.endswith('"'):
        data.append(len(token) - 2)
        data.extend(list(map(ord, token[1:-1])))
    else:
        data.append(int(token))


def add_to_code(code: list, code_labels: list, token: str, line_num: int):
    pc = len(code)
    if token.endswith(":"):  # токен содержит метку
        label = token.strip(":")
        assert label not in code_labels, f"Redefinition of label: {label}"
        code_labels[label] = pc
    elif " " in token:
        sub_tokens = token.split(" ")
        assert len(sub_tokens) == 2, f"Invalid instruction: {token}"
        mnemonic, arg = sub_tokens
        opcode = Opcode(mnemonic)
        assert opcode in (
            Opcode.JZ,
            Opcode.JNZ,
            Opcode.JMP,
            Opcode.LOAD,
            Opcode.STORE,
            Opcode.ST,
            Opcode.LD,
            Opcode.ADD,
            Opcode.SUB,
            Opcode.MUL,
            Opcode.DIV,
            Opcode.MOD,
            Opcode.MOV,
        ), f"{opcode} doesn't support arguments"
        code.append(
            {
                "index": pc,
                "opcode": opcode,
                "arg": arg,
                "term": Term(line_num, token),
            }
        )
    else:  # токен содержит инструкцию без операндов
        opcode = Opcode(token)
        code.append({"index": pc, "opcode": opcode, "term": Term(line_num, token)})


def get_section(token: str) -> str:
    """Определение секции, в которую добавляется токен."""
    if token == ".data":
        return "data"
    if token == ".text":
        return "text"
    raise ValueError()


def translate_stage_1(
    text: str,
) -> tuple[dict[str, int], dict[str, int], list[dict], list[int]]:
    """Первый проход транслятора. Преобразование текста программы в список
    инструкций и определение адресов меток.
    """
    data = []
    data_labels = {}
    code = []
    code_labels = {}

    section = ""
    for line_num, raw_line in enumerate(text.splitlines(), 1):
        token = get_meaningful_token(raw_line)
        if token == "":
            continue

        if token.startswith("."):
            section = get_section(token)
            continue

        if section == "data":
            add_to_data(data, data_labels, token)
        elif section == "text":
            add_to_code(code, code_labels, token, line_num)
        else:
            raise ValueError()

    return code_labels, data_labels, code, data


def translate_stage_2(code_labels: dict[str, int], data_labels: dict[str, int], code: list[dict]):
    """Второй проход транслятора. В уже определённые инструкции подставляются
    адреса меток."""
    for instruction in code:
        if "arg" in instruction:
            if instruction["opcode"] in (
                Opcode.LOAD,
                Opcode.STORE,
                Opcode.ST,
                Opcode.LD,
                Opcode.ADD,
                Opcode.SUB,
                Opcode.MUL,
                Opcode.DIV,
                Opcode.MOD,
                Opcode.MOV,
            ):
                label = instruction["arg"]
                assert instruction["arg"] in data_labels, "Label not defined: " + label
                instruction["arg"] = data_labels[label]

            elif instruction["opcode"] in (Opcode.JMP, Opcode.JZ, Opcode.JNZ):
                label = instruction["arg"]
                assert instruction["arg"] in code_labels, "Label not defined: " + label
                instruction["arg"] = code_labels[label]
            else:
                raise ValueError()

    return code


def translate(text: str) -> list:
    """Трансляция текста программы на Asm в машинный код."""
    code_labels, data_labels, code, data = translate_stage_1(text)
    code = translate_stage_2(code_labels, data_labels, code)

    result = []
    result.append(".data")
    result.extend(data)
    result.append(".text")
    result.extend(code)
    return result


def main(source: str, target: str):
    """Функция запуска транслятора. Параметры -- исходный и целевой файлы."""
    with open(source, encoding="utf-8") as f:
        source = f.read()

    code = translate(source)

    write_code(target, code)
    print("source LoC:", len(source.split("\n")), "code instr:", len(code))


if __name__ == "__main__":
    assert len(sys.argv) == 3, "Wrong arguments: translator.py <input_file> <target_file>"
    _, source, target = sys.argv
    main(source, target)
