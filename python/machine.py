#!/usr/bin/python3
"""Модель процессора, позволяющая выполнить машинный код полученный из программы
на языке ассемблера.
"""
from __future__ import annotations

import logging
import sys

from python.isa import Opcode, read_code


class DataPath:
    """Тракт данных (пассивный), включая: ввод/вывод, память и арифметику."""

    data_memory_size: int = None
    "Размер памяти данных."

    data_memory: list[int] = None
    "Память данных. Инициализируется нулевыми значениями."

    data_address: int = None
    "Адрес в памяти данных. Инициализируется нулём."

    acc: int = None
    "Аккумулятор. Инициализируется нулём."

    input_buffer: list = None
    "Буфер входных данных. Инициализируется входными данными конструктора."

    output_buffer: list = None
    "Буфер выходных данных."

    def __init__(self, data_memory_size: int, data: list[int], input_buffer: list):
        assert data_memory_size > 0, "Data_memory size should be non-zero"
        self.data_memory_size = data_memory_size
        self.data_memory = [0] * data_memory_size
        for i, v in enumerate(data):
            self.data_memory[i] = v
        self.data_address = 0
        self.acc = 0
        self.input_buffer = input_buffer
        self.output_buffer = []

    def correct_number(self, number: int) -> int:
        """Корректировка числа."""
        if number > 2**31 - 1:
            number = -(2**32) + number
        elif number < -(2**31):
            number = 2**32 + number
        return number

    def signal_latch_data_addr(self, addr: int):
        """Защёлкнуть адрес в памяти данных."""
        self.data_address = addr
        assert 0 <= self.data_address < self.data_memory_size, "Address out of range"

    def signal_latch_acc(self):
        """Защёлкнуть слово из памяти (`oe` от Output Enable) и защёлкнуть его в
        аккумулятор.
        """
        if self.data_address == 0:
            if len(self.input_buffer) == 0:
                raise EOFError()
            symbol = self.input_buffer.pop(0)
            self.acc = ord(symbol)
            logging.debug("input: %s ", repr(symbol))

        else:
            self.acc = self.data_memory[self.data_address]

    def signal_wr(self):
        """wr (от WRite), сохранить в память."""
        if self.data_address == 1:
            symbol = chr(self.acc)
            self.output_buffer.append(symbol)
            logging.debug("output: %s << %s", repr("".join(self.output_buffer)), repr(symbol))
        else:
            self.data_memory[self.data_address] = self.acc

    def signal_noarg(self, opcode: str):
        """Базовая операция без аргумента."""
        match opcode:
            case "inc":
                self.acc += 1
            case "dec":
                self.acc -= 1
            case _:
                raise ValueError()
        self.acc = self.correct_number(self.acc)

    def signal_set_acc(self, value):
        """Установить значение аккумулятора."""
        self.acc = value

    def signal_addr_by_addr(self):
        """Установить адрес по адресу."""
        self.data_address = self.data_memory[self.data_address]

    def signal_arg(self, opcode: str):
        """Базовая операция с аргументом."""
        match opcode:
            case "mul":
                self.acc *= self.data_memory[self.data_address]
            case "div":
                self.acc //= self.data_memory[self.data_address]
            case "add":
                self.acc += self.data_memory[self.data_address]
            case "sub":
                self.acc -= self.data_memory[self.data_address]
            case "mod":
                self.acc %= self.data_memory[self.data_address]
            case _:
                raise ValueError()
        self.acc = self.correct_number(self.acc)

    def zero(self):
        """Флаг нуля. Необходим для условных переходов."""
        return self.acc == 0


class ControlUnit:
    """Блок управления процессора. Выполняет декодирование инструкций и
    управляет состоянием модели процессора, включая обработку данных (DataPath).
    """

    program: list[dict] = None
    "Память команд."

    program_counter: int = None
    "Счётчик команд. Инициализируется нулём."

    data_path: DataPath = None
    "Блок обработки данных."

    _tick: int = None
    "Текущее модельное время процессора (в тактах). Инициализируется нулём."

    def __init__(self, program: list[dict], data_path: DataPath):
        self.program = program
        self.program_counter = 0
        self.data_path = data_path
        self._tick = 0

    def tick(self):
        """Продвинуть модельное время процессора вперёд на один такт."""
        self._tick += 1

    def current_tick(self):
        """Текущее модельное время процессора (в тактах)."""
        return self._tick

    def signal_latch_program_counter(self, sel_next: bool):
        """Защёлкнуть новое значение счётчика команд."""
        if sel_next:
            self.program_counter += 1
        else:
            instr = self.program[self.program_counter]
            assert "arg" in instr, "internal error"
            self.program_counter = instr["arg"]

    def decode_and_execute_control_flow_instruction(self, instr: dict, opcode: Opcode):
        """Декодировать и выполнить инструкцию управления потоком исполнения."""
        if opcode is Opcode.HALT:
            raise StopIteration()

        if opcode is Opcode.JMP:
            addr = instr["arg"]
            self.program_counter = addr
            self.tick()
            return True

        if opcode is Opcode.JZ:
            addr = instr["arg"]

            if self.data_path.zero():
                self.signal_latch_program_counter(sel_next=False)
            else:
                self.signal_latch_program_counter(sel_next=True)
            self.tick()
            return True

        if opcode is Opcode.JNZ:
            addr = instr["arg"]

            if not self.data_path.zero():
                self.signal_latch_program_counter(sel_next=False)
            else:
                self.signal_latch_program_counter(sel_next=True)
            self.tick()
            return True

        return False

    def _ld(self, addr: int):
        self.data_path.signal_latch_data_addr(addr)
        self.tick()
        self.data_path.signal_addr_by_addr()
        self.tick()
        self.data_path.signal_latch_acc()
        self.signal_latch_program_counter(sel_next=True)
        self.tick()

    def _st(self, addr: int):
        self.data_path.signal_latch_data_addr(addr)
        self.tick()
        self.data_path.signal_addr_by_addr()
        self.tick()
        self.data_path.signal_wr()
        self.signal_latch_program_counter(sel_next=True)
        self.tick()

    def _store(self, addr: int):
        self.data_path.signal_latch_data_addr(addr)
        self.tick()
        self.data_path.signal_wr()
        self.signal_latch_program_counter(sel_next=True)
        self.tick()

    def _load(self, addr: int):
        self.data_path.signal_latch_data_addr(addr)
        self.tick()
        self.data_path.signal_latch_acc()
        self.signal_latch_program_counter(sel_next=True)
        self.tick()

    def _noarg(self, opcode: Opcode):
        self.data_path.signal_noarg(str(opcode))
        self.signal_latch_program_counter(sel_next=True)
        self.tick()

    def _arg(self, opcode: Opcode, arg: int):
        self.data_path.signal_latch_data_addr(arg)
        self.tick()
        self.data_path.signal_arg(str(opcode))
        self.signal_latch_program_counter(sel_next=True)
        self.tick()

    def _mov(self, arg: int):
        self.data_path.signal_set_acc(arg)
        self.signal_latch_program_counter(sel_next=True)
        self.tick()

    def _sigbyopcode(self, opcode: Opcode, instr: dict):
        match opcode:
            case Opcode.LD:
                self._ld(instr["arg"])
            case Opcode.ST:
                self._st(instr["arg"])
            case Opcode.STORE:
                self._store(instr["arg"])
            case Opcode.LOAD:
                self._load(instr["arg"])
            case Opcode.INC | Opcode.DEC:
                self._noarg(opcode)
            case Opcode.ADD | Opcode.SUB | Opcode.MUL | Opcode.DIV | Opcode.MOD:
                self._arg(opcode, instr["arg"])
            case Opcode.MOV:
                self._mov(instr["arg"])
            case _:
                raise ValueError()

    def decode_and_execute_instruction(self):
        """Основной цикл процессора. Декодирует и выполняет инструкцию."""
        instr = self.program[self.program_counter]
        opcode = instr["opcode"]

        if self.decode_and_execute_control_flow_instruction(instr, opcode):
            return
        self._sigbyopcode(opcode, instr)

    def __repr__(self):
        """Вернуть строковое представление состояния процессора."""
        state_repr = f"TICK: {self._tick} PC: {self.program_counter} ADDR: {self.data_path.data_address} MEM_OUT: {self.data_path.data_memory[self.data_path.data_address]} ACC: {self.data_path.acc}"

        instr = self.program[self.program_counter]
        opcode = instr["opcode"]
        instr_repr = str(opcode)

        if "arg" in instr:
            instr_repr += f" {instr['arg']}"

        if "term" in instr:
            term = instr["term"]
            instr_repr += f"  ('{term.symbol}'@{term.line})"

        return f"{state_repr} \t{instr_repr}"


def simulation(
    code: list,
    data: list[int],
    input_tokens: list[str],
    data_memory_size: int,
    limit: int,
):
    """Подготовка модели и запуск симуляции процессора."""
    data_path = DataPath(data_memory_size, data, input_tokens)
    control_unit = ControlUnit(code, data_path)
    instr_counter = 0

    logging.debug("%s", control_unit)
    try:
        while instr_counter < limit:
            control_unit.decode_and_execute_instruction()
            instr_counter += 1
            logging.debug("%s", control_unit)
    except EOFError:
        logging.warning("Input buffer is empty!")
    except StopIteration:
        pass

    if instr_counter >= limit:
        logging.warning("Limit exceeded!")
    logging.info("output_buffer: %s", repr("".join(data_path.output_buffer)))
    return "".join(data_path.output_buffer), instr_counter, control_unit.current_tick()


def main(code_file: str, input_file: str):
    """Функция запуска модели процессора."""
    code, data = read_code(code_file)
    with open(input_file, encoding="utf-8") as file:
        input_text = file.read()
        input_token = []
        for char in input_text:
            input_token.append(char)

    output, instr_counter, ticks = simulation(
        code,
        data,
        input_tokens=input_token,
        data_memory_size=200,
        limit=2000,
    )

    print("".join(output))
    print("instr_counter: ", instr_counter, "ticks:", ticks)


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    assert len(sys.argv) == 3, "Wrong arguments: machine.py <code_file> <input_file>"
    _, code_file, input_file = sys.argv
    main(code_file, input_file)
