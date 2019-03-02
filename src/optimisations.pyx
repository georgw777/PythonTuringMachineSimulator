import cython
import numpy as np
cimport numpy as np

LETTER = np.uint32
ctypedef np.uint32_t LETTER_t

class Accept(Exception):
    pass

def create_initial_configuration(tape, accepting, rejecting):
    return np.array([0, 0, accepting, rejecting] + [x for x in tape], dtype=LETTER)

@cython.boundscheck(False)
@cython.wraparound(False) 
def read_state(LETTER_t[:] tape not None):
    return (tape[1], tape[tape[0] + 4])

@cython.boundscheck(False)
@cython.wraparound(False) 
def apply_transitions(np.ndarray configuration not None, LETTER_t[:, :] transitions):
    cdef LETTER_t position = configuration[0]
    cdef LETTER_t accepting = configuration[2]
    cdef LETTER_t rejecting = configuration[3]
    cdef ssize_t I = transitions.shape[0]

    cdef LETTER_t to_state
    cdef LETTER_t tape_output
    cdef LETTER_t move_right
    for i in range(I):
        to_state = transitions[i, 0]
        if to_state == rejecting:
            continue
        if to_state == accepting:
            raise Accept()
        tape_output = transitions[i, 1]
        move_right = transitions[i, 2]
        conf = configuration if i == I - 1 else configuration.copy()
        conf[position + 4] = tape_output
        conf[1] = to_state
        if move_right == 1:
            conf[0] = position + 1
            if conf.shape[0] == position + 5:
                conf.resize(conf.shape[0] * 2, refcheck=False)
        elif position > 0:
            conf[0] = position - 1
        yield conf