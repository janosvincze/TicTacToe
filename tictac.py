import random

class TicTacToe(object):
    """ Game Environment Class"""

    def __init__(self, board=[]):
        """ Initialize the environment variables """
        # Generate a new board if the passed board is empty
        if len(board) == 0:
            self.board = [' ' for square in range(9)]
        # Set new board as old board
        else:
            self.board = board

        self.winning_streaks = (
        [0,1,2], [3,4,5], [6,7,8],
        [0,3,6], [1,4,7], [2,5,8],
        [0,4,8], [2,4,6])

    def output(self):
        """ Print the board"""
        return ''.join(self.board)

    def legal_moves(self):
        """ Get the empty spaces """
        return [index for index, square in enumerate(self.board) if square == ' ']

    def leaf(self):
        """ Is the board full or has someone won the game """
        if ' ' not in [square for square in self.board]:
            return True
        if self.winner() != None:
            return True
        return False

    def X_won(self):
        """ Did player X win """
        return self.winner() == 'X'

    def O_won(self):
        """ Did player O win """
        return self.winner() == 'O'

    def tied(self):
        """ Is the game a tie? """
        return self.leaf() == True and self.winner() is None

    def winner(self):
        """ Get the winner of the board """
        for player in ('X', 'O'):
            positions = self.get_squares(player)
            for streak in self.winning_streaks:
                win = True
                for pos in streak:
                    if pos not in positions:
                        win = False
                if win:
                    return player
        return None

    def get_squares(self, player):
        """ Get a list of all squares taken by a certain player """
        return [index for index, square in enumerate(self.board) if square == player]

    def move(self, position, player):
        """ Move player to position """
        self.board[position] = player

def get_opponent(player):
    """ Gives us the opponent of player """
    if player == 'O':
        return 'X'
    else:
        return 'O'

def minimax(node, player, alpha, beta, depth):
    if node.leaf():
        if node.X_won:
            return -1
        elif node.tied():
            return 0
        elif node.O_won:
            return 1

    for move in node.legal_moves():
        node.move(move, player)
        score = minimax(node, get_opponent(player), alpha, beta, depth-1)
        node.move(move, ' ')
        if player == 'O':
            if score > alpha:
                alpha = score
            if alpha >= beta:
                return beta
        else:
            if score < beta:
                beta = score
            if beta <= alpha:
                return alpha
    if player == 'O':
        return alpha
    else:
        return beta

def computer_move(board, player):
    best_moves = [0,1,2,3,4,5,6]
    o_player = get_opponent(player)

    # If computer can win: play there
    for move in board.legal_moves():
        board.move(move, player)
        if board.winner() == player:
            print('Computer will play at square: {}'.format(move+1))
            return move
        # Undo the move
        board.move(move, ' ')

    # If player can win: block the move
    for move in board.legal_moves():
        board.move(move, o_player)
        if board.winner() == o_player:
            print('Computer will block at square: {}'.format(move+1))
            return move
        # Undo the move
        board.move(move, ' ')

    best = -2
    choices = []

    if len(board.legal_moves()) == 9:
        return 4 #random.choice([0,2,6,8])

    for move in board.legal_moves():
        board.move(move, player)
        score = minimax(board, get_opponent(player), -2, 2, 6)
        board.move(move, ' ')
        print("Move: ",move+1," has a score of: ",score)
        if score > best:
            best = score
            choices = [move]
        elif score == best:
            choices.append(move)
    choice = random.choice(choices)
    print("[+] Selected move: ",choice+1)
    return choice