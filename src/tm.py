import typing
import sys
import itertools
import os
from description import TuringMachineDescription
from error import assert_property, TuringMachineError
from abc import ABC, abstractmethod
import numpy as np


class TuringMachineResult:
    def __init__(self, num_steps: int, accepted: bool, tape: typing.Union[typing.List[str], None]):
        self.num_steps = num_steps
        self.accepted = accepted
        if tape is None:
            self.tape = None
        else:
            for i, letter in enumerate(reversed(tape)):
                if letter != "_":
                    break
            self.tape = tape[:-i] if i > 0 else tape
            if self.tape == []:
                self.tape = ["_"]

    def __str__(self):
        return ("accepted" if self.accepted else "not accepted") + os.linesep + str(self.num_steps) + ((os.linesep + "".join(self.tape)) if self.tape is not None else "")


class TuringMachineConfiguration:
    def __init__(self, state: int, tape: np.array, position: int):
        self.state = state
        self.tape = tape
        self.position = position

    def duplicate(self):
        return TuringMachineConfiguration(self.state, self.tape.copy(), self.position)

    def print(self, description: TuringMachineDescription):
        print(" {:5s} ".format(description.states[self.state]), end="")
        for i, letter in enumerate(self.tape):
            if i == self.position:
                print('\033[91m', end="")
            print(description.alphabet[letter], end=" ")
            if i == self.position:
                print('\033[0m', end="")
        print()


class DeterministicTuringMachine:

    def __init__(self, description: TuringMachineDescription):
        self.description = description

    def process_input(self, input: list, verbose: bool = False) -> TuringMachineResult:
        if len(input) == 0:
            input = ["_"]
        try:
            tape = np.array([self.description.alphabet.index(x)
                             for x in input], dtype=np.uint8)
        except ValueError:
            raise TuringMachineError("input contains invalid characters")
        configuration = TuringMachineConfiguration(0, tape, 0)
        num_steps = 0
        if verbose:
            configuration.print(self.description)
        while True:
            self.perform_step(configuration)
            if verbose:
                configuration.print(self.description)
            if configuration.state == self.description.accepting:
                return TuringMachineResult(num_steps, True, [self.description.alphabet[x] for x in configuration.tape])
            if configuration.state == self.description.rejecting:
                return TuringMachineResult(num_steps, False, [self.description.alphabet[x] for x in configuration.tape])
            num_steps += 1

    def perform_step(self, configuration: TuringMachineConfiguration):
        # read
        tape_input = configuration.tape[configuration.position]
        state = self.description.transitions[configuration.state]
        if tape_input in state:
            to_state, tape_output, move_right = state[tape_input]
            # write
            configuration.tape[configuration.position] = tape_output
            # move head
            if move_right:
                configuration.position += 1
                if configuration.position == len(configuration.tape):
                    configuration.tape.resize(
                        configuration.position + 1, refcheck=False)
            elif configuration.position > 0:
                configuration.position -= 1
            # change state
            configuration.state = to_state
        else:
            # move head right
            configuration.position += 1
            # go to rejecting state
            configuration.state = self.description.rejecting


class NondeterministicTuringMachine:
    def __init__(self, description: TuringMachineDescription):
        self.description = description

    def process_input(self, input: list, verbose: bool = False) -> TuringMachineResult:
        if len(input) == 0:
            input = ["_"]
        try:
            tape = np.array([self.description.alphabet.index(x)
                             for x in input], dtype=np.uint8)
        except ValueError:
            raise TuringMachineError("input contains invalid characters")
        configurations = [TuringMachineConfiguration(0, tape, 0)]
        num_steps = 0
        if verbose:
            for configuration in configurations:
                configuration.print(self.description)
            print()
        while True:
            new_configurations = []
            for configuration in itertools.chain.from_iterable(self.perform_step(c) for c in configurations):
                if configuration.state == self.description.accepting:
                    return TuringMachineResult(num_steps, True, None)
                elif configuration.state != self.description.rejecting:
                    new_configurations.append(configuration)
            if len(new_configurations) == 0:
                return TuringMachineResult(num_steps, False, None)
            if verbose:
                for configuration in configurations:
                    configuration.print(self.description)
                print()
            num_steps += 1

    def perform_step(self, configuration: TuringMachineConfiguration) -> typing.List[TuringMachineConfiguration]:
        # read
        tape_input = configuration.tape[configuration.position]
        state = self.description.transitions[configuration.state]
        if tape_input in state:
            transitions = state[tape_input]
            for i, (to_state, tape_output, move_right) in enumerate(transitions):
                conf = configuration if i == len(
                    transitions) else configuration.duplicate()
                # write
                conf.tape[conf.position] = tape_output
                # move head
                if move_right:
                    conf.position += 1
                    if conf.position == len(conf.tape):
                        conf.tape.resize(
                            conf.position + 1, refcheck=False)
                elif conf.position > 0:
                    conf.position -= 1
                # change state
                conf.state = to_state
                yield conf
