"""models.py - This file contains the class definitions for the Datastore
entities used by the Game. Because these classes are also regular Python
classes they can include methods (such as 'to_form' and 'new_game')."""

import random
from tictac import TicTacToe
from tictac import computer_move
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb


class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email =ndb.StringProperty()
    score = ndb.IntegerProperty(required=True, default=0)
    played_game = ndb.IntegerProperty(required=True, default=0)
    performance = ndb.FloatProperty(required=True, default=0)

    def to_form(self):
        """Returns user's name and performance"""
        form = RankForm()
        form.user_name = self.name
        form.performance = self.performance
        return form


class TicTac(ndb.Model):
    """A Tic Tac Toe game object"""
    board = ndb.StringProperty(required=True, default='         ')
    user_start = ndb.BooleanProperty(required=True, default=True)
    game_over = ndb.BooleanProperty(required=True, default=False)
    user_steps = ndb.IntegerProperty(required=True, default=0)
    user = ndb.KeyProperty(required=True, kind='User')
    cancelled = ndb.BooleanProperty(required=True, default=False)
    winner = ndb.IntegerProperty()
    last_step = ndb.DateTimeProperty(auto_now=True)

    @classmethod
    def new_game(cls, user, user_start, board='         '):
        """Creates and returns a new game"""
        tic = TicTac(user=user,
                     user_start=user_start,
                     user_steps=(9 - board.count(' ')),
                     board=board,
                     game_over=False,
                     cancelled=False,
                     winner=0)
        if not user_start:
            tictac = TicTacToe(list(board))
            tictac.move(computer_move(tictac,'O'), 'O')
            tic.board = tictac.output()
            tic.user_steps +=1
        tic.put()
        return tic

    def legal_moves_str(self, board):
        """ Get the empty spaces """
        return ' '.join(str(index) for index,
                square in enumerate(list(board)) if square == ' ')

    def is_legal_moves(self, board, move):
        """ Is the move is legal? """
        return move in [index for index,
                square in enumerate(list(board)) if square == ' ']

    def make_a_move(self, position):
        board = TicTacToe(list(self.board))

        if (self.game_over or self.cancelled):
            return self.to_form('Game is already over!')
        else:
            if self.is_legal_moves(self.board, position):
                board.move(position,'X')
                self.board = board.output()

                history = History(game=self.key,
                                    is_human=True,
                                    position=position,
                                    board=self.board,
                                    msg='',
                                    steps=self.user_steps)
                history.put()

                self.user_steps += 1
                if board.X_won():
                    self.end_game(1)
                    msg = 'Congratulation! You win!'
                elif self.user_steps == 9:
                    msg = 'It is tied! Game Over'
                    self.end_game(0)
                else:
                    comp_position = computer_move(board,'O')
                    board.move(comp_position, 'O')
                    self.board = board.output()

                    history = History(game=self.key,
                                    is_human=False,
                                    position=comp_position,
                                    board=self.board,
                                    msg='',
                                    steps=self.user_steps)
                    history.put()

                    self.user_steps +=1
                    if board.O_won():
                        self.end_game(-1)
                        msg = 'You lose it!'
                    elif board.leaf():
                        self.end_game(0)
                        msg = 'It is tied! Game Over'
                    else:
                        msg = 'Your turn'
            else:
                msg = 'Invalid move! Choose from the following: %s' %\
                      self.legal_moves_str(self.board)
            self.put()

        return self.to_form(msg)


    def to_form(self, message=''):
        """Returns a GameForm representation of the Game"""
        form = TicTacForm()
        form.urlsafe_key = self.key.urlsafe()
        form.user_name = self.user.get().name
        form.game_over = self.game_over
        form.message = message
        form.board = self.board[0:3] + '|' + self.board[3:6] + '|' +\
                     self.board[6:]
        form.steps = self.user_steps
        form.cancelled = self.cancelled
        form.winner = self.winner
        return form

    def end_game(self, winner=0):
        """Ends the game - if won is True, the player won. - if won is False,
        the player lost."""
        self.game_over = True
        self.winner = winner
        self.put()

        if winner == 1:
            msg = 'User win!'
        elif winner == 0:
            msg = 'Tied'
        else:
            msg = 'Computer win!'

        history = History(game=self.key,
                            is_human=False,
                            position=-1,
                            board=self.board,
                            msg='Game over! %s' % msg,
                            steps=10)
        history.put()

        # Add the game to the score 'board'
        score = Score(user=self.user, date=date.today(), winner=winner,
                      user_steps=self.user_steps)
        score.put()

        user =self.user.get()
        if user.played_game:
            user.played_game += 1
        else:
            user.played_game = 1
        if self.user_start:
            user.score += winner
        else:
            if winner > 0:
                user.score += 2
            else:
                user.score += winner
        user.performance = user.score / user.played_game
        user.put()

class History(ndb.Model):
    """Games' history"""
    game = ndb.KeyProperty(required=True, kind='TicTac')
    is_human = ndb.BooleanProperty(required=True)
    position = ndb.IntegerProperty(required=True)
    board = ndb.StringProperty(required=True)
    msg = ndb.StringProperty(required=True)
    steps = ndb.IntegerProperty(required=True)

    def to_form(self):
        form = HistoryForm()
        form.is_human = self.is_human
        form.position = self.position
        form.board = self.board
        form.msg = self.msg
        form.steps = self.steps

        return form



class Score(ndb.Model):
    """Score object"""
    user = ndb.KeyProperty(required=True, kind='User')
    date = ndb.DateProperty(required=True)
    winner = ndb.IntegerProperty(required=True)
    user_steps = ndb.IntegerProperty(required=True)

    def to_form(self):
        return ScoreForm(user_name=self.user.get().name, winner=self.winner,
                         date=str(self.date), user_steps=self.user_steps)


class TicTacForm(messages.Message):
    """TicTacForm for outbound game state information"""
    urlsafe_key = messages.StringField(1, required=True)
    game_over = messages.BooleanField(3, required=True)
    message = messages.StringField(4, required=True)
    board = messages.StringField(5, required=True)
    steps = messages.IntegerField(6, required=True)
    user_name = messages.StringField(7, required=True)
    cancelled = messages.BooleanField(8, required=True)
    winner = messages.IntegerField(9, required=True)


class GamesForm(messages.Message):
    games = messages.MessageField(TicTacForm, 1, repeated=True)


class NewTicTacForm(messages.Message):
    """Used to create a new game"""
    user_name = messages.StringField(1, required=True)
    user_start = messages.BooleanField(2, default=True)
    board = messages.StringField(3, default='         ')


class MakeTicTacMoveForm(messages.Message):
    """Used to make a move in an existing game"""
    position = messages.IntegerField(1, required=True)


class ScoreForm(messages.Message):
    """ScoreForm for outbound Score information"""
    user_name = messages.StringField(1, required=True)
    date = messages.StringField(2, required=True)
    winner = messages.IntegerField(3, required=True)
    user_steps = messages.IntegerField(4, required=True)


class ScoreForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(ScoreForm, 1, repeated=True)


class RankForm(messages.Message):
    """Employee rank"""
    user_name = messages.StringField(1, required=True)
    performance = messages.FloatField(2, required=True)


class RankForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(RankForm, 1, repeated=True)


class HistoryForm(messages.Message):
    is_human = messages.BooleanField(1, required=True)
    position = messages.IntegerField(2, required=True)
    board = messages.StringField(3, required=True)
    msg = messages.StringField(4, required=True)
    steps = messages.IntegerField(5, required=True)


class HistoryForms(messages.Message):
    items = messages.MessageField(HistoryForm, 1, repeated=True)


class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)
