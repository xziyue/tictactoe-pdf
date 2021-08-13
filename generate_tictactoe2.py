import os
import numpy as np
import pickle

tictactoe_states = np.genfromtxt(os.path.join('generate_tictactoe', 'tictactoe.txt'), dtype=np.int16)

boards = tictactoe_states[:, :9]
winners = tictactoe_states[:, 13]

print(f'total number of boards: {len(boards)}')

# degree of freedom of each board
dog = np.count_nonzero(boards == 0, axis=1)

# see whose turn it is for each undecided game
# -1, 0, 1 (O, decided, X)
# remember X goes first
x_count = np.count_nonzero(boards == 1, axis=1)
o_count = np.count_nonzero(boards == -1, axis=1)
x_turn_mask = x_count <= o_count
o_turn_mask = np.logical_not(x_turn_mask)
decided_turn_mask = np.logical_or(dog == 0, winners != 0)
turns = np.zeros(boards.shape[0], np.int32)
turns[x_turn_mask] = 1
turns[o_turn_mask] = -1
turns[decided_turn_mask] = 0

# for each board that is not decided, compute possible moves
moves = []
for i in range(len(turns)):
    if turns[i] != 0:
        moves.append(np.where(boards[i, ...] == 0)[0].tolist())
    else:
        moves.append([])

jump_table = [dict() for _ in range(len(boards))]
for i in range(len(moves)):
    move = moves[i]
    if len(move) > 0:
        jump = jump_table[i]
        for item in move:
            jump[item] = []

hash_arr = np.power(3, np.arange(9, dtype=np.int64))


def hash_board(board):
    return np.sum(hash_arr * (board + 1))


# compute the hash code for all states
board_hash = [hash_board(boards[i, ...]) for i in range(boards.shape[0])]
board_inv_lookup = dict()
for i, hash_code in enumerate(board_hash):
    board_inv_lookup[hash_code] = i


def find_board_index(board):
    hash_code = hash_board(board)
    return board_inv_lookup[hash_code]


# # gather a list of must lose boards
# must_lose_boards = []
#
#
# def find_must_lost_board(board):
#     board_ind = find_board_index(board)
#
#     if board_ind in must_lose_boards:
#         return False
#
#     if winners[board_ind] == 1:
#         return False  # a losing state
#     elif winners[board_ind] == -1:
#         return True  # a winning state
#     elif dog[board_ind] == 0:
#         return True  # a non-losing state
#     else:
#         # if the board is still playable...
#         possible_moves = np.where(board == 0)[0]
#         var = False
#
#         symbol = turns[board_ind]
#         assert symbol != 0
#         for move in possible_moves:
#             assert board[move] == 0
#             board[move] = symbol
#             var = var or find_must_lost_board(board)
#             board[move] = 0
#             if var:
#                 return var
#
#         # returns false only when all children are all false!
#         return var
#
#
# o_turns = np.where(turns == -1)[0]
# for board_ind in o_turns:
#     board = boards[board_ind, ...]
#     if not find_must_lost_board(board):
#         must_lose_boards.append(board_ind)



def find_all_children_helper(board, moves):
    board_ind = find_board_index(board)
    if turns[board_ind] == 0:
        return

    symbol = turns[board_ind]
    possible_moves = np.where(board == 0)[0]
    for move in possible_moves:
        assert board[move] == 0
        board[move] = symbol
        moves.append(move)
        yield (moves, find_board_index(board))
        find_all_children_helper(board, moves)
        moves.pop()
        board[move] = 0


def apply_to_all_children_helper(board, func, moves, result):
    board_ind = find_board_index(board)

    result.append(func(moves, board_ind))

    if turns[board_ind] == 0:
        return

    symbol = turns[board_ind]
    possible_moves = np.where(board == 0)[0]
    for move in possible_moves:
        assert board[move] == 0
        board[move] = symbol
        moves.append(move)
        apply_to_all_children_helper(board, func, moves, result)
        moves.pop()
        board[move] = 0

def apply_to_all_children(board, func):
    moves = []
    lst = []
    apply_to_all_children_helper(board, func, moves, lst)
    return lst


blank_board_index = find_board_index(np.zeros(9))

corner_cases_inds = dict()
corner_placement_inds = [0, 2, 6, 8]
corner_response_inds = [8, 6, 2, 0]
for ind, corner_ind in enumerate(corner_placement_inds):
    board = np.zeros(9)
    board[corner_ind] = 1
    corner_cases_inds[find_board_index(board)] = corner_response_inds[ind]

hardcode_case1 = np.zeros(9)
hardcode_case1[2] = hardcode_case1[6] = 1
hardcode_case1[4] = -1
hardcode_case1_ind = find_board_index(hardcode_case1)

hardcode_case2 = np.zeros(9)
hardcode_case2[0] = hardcode_case2[8] = 1
hardcode_case2[4] = -1
hardcode_case2_ind = find_board_index(hardcode_case2)

def score_function(moves, board_ind):
    if winners[board_ind] == -1:
        sign = 2
    elif winners[board_ind] == 1:
        sign = -1.0e3
    elif turns[board_ind] == 0:
        sign = 1
    else:
        sign = 0

    weight = np.power(0.6, len(moves) // 2)
    score = sign * weight

    return score

def danger_function(moves, board_ind):
    if len(moves) == 1 and winners[board_ind] == 1:
        return True
    return False

# find optimal move for O=-1
def find_optimal_move(board):
    board_ind = find_board_index(board)
    assert turns[board_ind] == -1
    possible_moves = np.where(board == 0)[0]

    symbol = turns[board_ind]
    moves = []

    # hard code a strategy: when the user starts on the corners, we take the center position
    if board_ind in corner_cases_inds:
        return 4

    # hard code two more cases to make sure the player cannot win
    if board_ind == hardcode_case1_ind or board_ind == hardcode_case2_ind:
        return 3

    for move in possible_moves:
        assert board[move] == 0
        board[move] = symbol
        new_board_ind = find_board_index(board)

        if winners[new_board_ind] == -1:
            moves.append((move, 1.0))
        else:
            # compute a score for each move
            scores = np.asarray(apply_to_all_children(board, score_function))
            dangers = any(apply_to_all_children(board, danger_function))  # look for imminent threat
            non_zero_loc = np.where(np.abs(scores) >= 1.0e-6)[0]
            non_zero_scores = scores[non_zero_loc]
            mean_score = non_zero_scores.mean()
            if dangers:
                mean_score -= 1.0e9
            moves.append((move, mean_score))

        board[move] = 0

    moves.sort(key=lambda x: x[1])
    best_move, best_winrate = moves[-1]
    # if best_winrate < 0.0:
    #     print('a bad case is found')

    return best_move


def generate_jump_table(board, jump_table):
    board_ind = find_board_index(board)

    my_turn = turns[board_ind]
    if my_turn == 0:
        jump_table[board_ind] = dict()
        return
    assert my_turn == 1

    move_dict = dict()
    possible_moves = np.where(board == 0)[0]

    # for each user move
    for move in possible_moves:
        symbol = my_turn
        other_symbol = -symbol

        assert board[move] == 0
        board[move] = symbol
        new_board_ind = find_board_index(board)

        if turns[new_board_ind] != 0:
            # if the board is still playable after this move
            my_best_move = find_optimal_move(board)
            assert board[my_best_move] == 0
            board[my_best_move] = other_symbol
            next_board_index = find_board_index(board)
            move_dict[move] = (my_best_move, next_board_index)
            generate_jump_table(board, jump_table)
            board[my_best_move] = 0
        else:
            # after this user move, the game stops
            move_dict[move] = (None, new_board_ind)
            generate_jump_table(board, jump_table)

        board[move] = 0

    jump_table[board_ind] = move_dict


# save_filename = 'ttt2.pickle'


jump_table = dict()
generate_jump_table(np.zeros(9), jump_table)


print(f'number of states: {len(jump_table)}')

# state_template = r'''
# \begin{{center}}
# \begin{{minipage}}[t][2.5cm][t]{{\linewidth}}
# \begin{{center}}
# \hypertarget{{{l:}}}{{\Large\scshape Tic-Tac-Toe}}\\
# {{\huge {msg:}}}
# \end{{center}}
# \end{{minipage}}
# \drawtictactoe{{{x:}}}{{{o:}}}{{{t:}}}
# \end{{center}}
# \vfill
# \begin{{flushright}}
# \scriptsize\hyperlink{{{sz:}}}{{Restart}}
# \end{{flushright}}
# \clearpage
# '''

state_template = r'''
\begin{center}
\begin{minipage}[t][2.5cm][t]{\linewidth}
\begin{center}
\hypertarget{%(l)s}{\Large\scshape Tic-Tac-Toe}\\
{\huge %(msg)s}
\end{center}
\end{minipage}
\drawtictactoe{%(x)s}{%(o)s}{%(t)s}
\end{center}
\vfill
\begin{flushright}
\scriptsize
\hyperlink{homepage}{$\rightarrow$Home}
\quad\hyperlink{%(sz)s}{$\rightarrow$Restart}
\end{flushright}
\clearpage
'''.strip()


def get_label_name(l):
    return 'state{}'.format(l)


tex_pages = []

user_won = pdf_won = draw = 0

for key, val in jump_table.items():
    board = boards[key, ...]
    xs = np.array2string(np.where(board == 1)[0], separator=',').lstrip('[').rstrip(']')
    os = np.array2string(np.where(board == -1)[0], separator=',').lstrip('[').rstrip(']')
    jump_arr = []
    for user_move, (my_move, next_state) in val.items():
        jump_arr.append('{}={}'.format(user_move, get_label_name(next_state)))
    jump = ','.join(jump_arr)

    msg = ''
    if turns[key] == 0:
        if winners[key] == 1:
            msg = 'You have won!'
            user_won += 1
        elif winners[key] == -1:
            msg = 'The PDF has won!'
            pdf_won += 1
        else:
            msg = 'It\'s a draw!'
            draw += 1

    page_str = state_template % {
        'l': get_label_name(key),
        'x': xs,
        'o': os,
        'sz': get_label_name(blank_board_index),
        'msg': msg,
        't': jump
    }

    tex_pages.append(page_str)

print(f'{user_won, pdf_won, draw}')

# for i in range(len(all_states)):
#     state = all_states[i]
#     board = boards[state.state_index]
#     xs = np.array2string(np.where(board == 1)[0], separator=',').lstrip('[').rstrip(']')
#     os = np.array2string(np.where(board == -1)[0], separator=',').lstrip('[').rstrip(']')
#     jump_table_arr = []
#     for key, val in state.jumps.items():
#         jump_table_arr.append('{}={}'.format(key, get_label_name(val)))
#     jump = ','.join(jump_table_arr)
#
#     msg = ''
#     if state.winner == -1:
#         msg = 'The PDF has won!'
#     elif state.winner == 1:
#         msg = 'You have won!'
#     elif state.winner == 0:
#         msg = 'It\'s a draw!'
#
#     page_str = state_template.format(
#         l = get_label_name(i),
#         x = xs,
#         o = os,
#         t = jump,
#         sz = get_label_name(0),
#         msg = msg
#     )
#     tex_pages.append(page_str)
#
#

# generate latex output
with open('template2.tex', 'r') as infile:
    tex_template = infile.read()

tex_output = tex_template.replace('%%content', '\n'.join(tex_pages)).replace('%%fp', get_label_name(blank_board_index))
with open('tic-tac-toe2.tex', 'w') as outfile:
    outfile.write(tex_output)
