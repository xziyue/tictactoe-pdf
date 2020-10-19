import os
import numpy as np

tictactoe_states = np.genfromtxt(os.path.join('generate_tictactoe', 'tictactoe.txt'), dtype=np.int16)

boards = tictactoe_states[:, :9]
winners = tictactoe_states[:, 13]
# degree of freedom of each board
dog = np.count_nonzero(boards == 0, axis=1)

row_indices = [
    np.array([0, 1, 2]),
    np.array([3, 4, 5]),
    np.array([6, 7, 8])
]

col_indices = [
    np.array([0, 3, 6]),
    np.array([1, 4, 7]),
    np.array([2, 5, 8])
]

diag_indices = [
    np.array([0, 4, 8]),
    np.array([6, 7, 8])
]

all_indices = [row_indices, col_indices, diag_indices]

def find_board_index(board):
    ret = np.where(np.all(boards == board, axis=1))[0]
    assert len(ret) == 1
    return ret[0]

def find_optimal_move(board_id):
    assert winners[board_id] == 0
    assert dog[board_id] > 0
    possible_moves = np.where(boards[board_id] == 0)[0]

    # for each possible move, analyze all of its descendents
    move_arr = []
    for move in possible_moves:
        new_board = np.copy(boards[board_id])
        new_board[move] = -1
        # find the index of new board
        new_board_id = find_board_index(new_board)
        # if this is a winning move, return this move
        if winners[new_board_id] == -1:
            return move
        # otherwise, choose the move that has the greatest probability to succeed
        board_mask = np.where(new_board != 0)[0]
        # find all descendents
        similar_boards = np.where(np.all((boards == new_board)[:,board_mask], axis=1))[0]
        # filter out intermediate states
        finished_boards_ind = np.where(dog[similar_boards] == 0)[0]
        finished_boards = similar_boards[finished_boards_ind]
        # calculate losing rate
        num_lost_boards = np.count_nonzero(winners[finished_boards] == 1)
        lose_rate = num_lost_boards / (finished_boards.size + 0.01)
        move_arr.append((lose_rate, move))

    board = boards[board_id]
    # if there is an imminent threat, eliminate that threat
    for indices in all_indices:
        for i in range(len(indices)):
            mask = indices[i]
            if np.count_nonzero(board[mask] == 1) == 2 and np.count_nonzero(board[mask] == 0) > 0:
                return mask[np.where(board[mask] == 0)[0]]

    move_arr.sort(key=lambda x : x[0])
    return move_arr[0][1]


blank_board_ind = find_board_index(np.zeros(9, np.int16))

class State:

    _counter = 0

    def __init__(self, **kwargs):
        self.counter = State._counter
        State._counter += 1

        self.state_index = kwargs.get('state_index', 0)
        self.winner = kwargs.get('winner', None)
        # opponent move
        self.jumps = dict()

blank_state = State(state_index=blank_board_ind)
all_states = [blank_state]

state_stack = [blank_state]

# fill the jump table for each state that awaits user input
def fill_state(state_stack):
    state = state_stack.pop()
    # see if there is a winner or it's a draw
    if winners[state.state_index] != 0:
        state.winner = winners[state.state_index]
        return
    # find all valid moves for the user
    board = boards[state.state_index]
    user_moves = np.where(board == 0)[0]

    # create a new state for each user move
    for move in user_moves:
        new_board = np.copy(board)
        new_board[move] = 1
        # find index of the new board
        new_board_ind = find_board_index(new_board)
        if winners[new_board_ind] != 0 or dog[new_board_ind] == 0:
            # the search reaches an end
            new_state = State(state_index=new_board_ind, winner=winners[new_board_ind])
            state.jumps[move] = new_state.counter
            all_states.append(new_state)
        else:
            # find optimal move for this board
            optimal_move = find_optimal_move(new_board_ind)
            # find index of the board after optimal move
            new_board[optimal_move] = -1
            optimal_move_board_ind = find_board_index(new_board)
            # create new state
            new_state = State(state_index=optimal_move_board_ind)
            state.jumps[move] = new_state.counter
            all_states.append(new_state)
            # keep investigating this state until an end is reached
            state_stack.append(new_state)

while len(state_stack) > 0:
    fill_state(state_stack)

# generate latex output
with open('template.tex', 'r') as infile:
    tex_template = infile.read()

state_template = r'''
\begin{{center}}
\begin{{minipage}}[t][2.5cm][t]{{\linewidth}}
\begin{{center}}
\hypertarget{{{l:}}}{{\Large\scshape Tic-Tac-Toe}}\\
{{\huge {msg:}}}
\end{{center}}
\end{{minipage}}
\drawtictactoe{{{x:}}}{{{o:}}}{{{t:}}}
\end{{center}}
\vfill
\begin{{flushright}}
\scriptsize\hyperlink{{{sz:}}}{{Restart}}
\end{{flushright}}
\clearpage
'''

def get_label_name(l):
    return 'state{}'.format(l)

tex_pages = []

for i in range(len(all_states)):
    state = all_states[i]
    board = boards[state.state_index]
    xs = np.array2string(np.where(board == 1)[0], separator=',').lstrip('[').rstrip(']')
    os = np.array2string(np.where(board == -1)[0], separator=',').lstrip('[').rstrip(']')
    jump_table_arr = []
    for key, val in state.jumps.items():
        jump_table_arr.append('{}={}'.format(key, get_label_name(val)))
    jump = ','.join(jump_table_arr)

    msg = ''
    if state.winner == -1:
        msg = 'The PDF has won!'
    elif state.winner == 1:
        msg = 'You have won!'
    elif state.winner == 0:
        msg = 'It\'s a draw!'

    page_str = state_template.format(
        l = get_label_name(i),
        x = xs,
        o = os,
        t = jump,
        sz = get_label_name(0),
        msg = msg
    )
    tex_pages.append(page_str)


tex_output = tex_template.replace('%%content', '\n'.join(tex_pages))
with open('tic-tac-toe.tex', 'w') as outfile:
    outfile.write(tex_output)