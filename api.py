# -*- coding: utf-8 -*-`
"""api.py - Create and configure the Game API exposing the resources.
This can also contain game logic. For more complex games it would be wise to
move game logic to another file. Ideally the API will be simple, concerned
primarily with communication to/from the API's users."""


import logging
import endpoints
import random
from protorpc import remote, messages
from google.appengine.api import memcache
from google.appengine.api import taskqueue

from tictac import TicTacToe
from tictac import computer_move

from models import User, Score, TicTac
from models import StringMessage, ScoreForms, NewTicTacForm, TicTacForm
from models import MakeTicTacMoveForm, GamesForm
from models import RankForm, RankForms
from models import History, HistoryForm, HistoryForms
from utils import get_by_urlsafe


USER_REQUEST = endpoints.ResourceContainer(user_name=messages.StringField(1),
                                           email=messages.StringField(2))

NEW_TICTAC_REQUEST = endpoints.ResourceContainer(NewTicTacForm)
GET_TICTAC_REQUEST = endpoints.ResourceContainer(
        urlsafe_game_key=messages.StringField(1),)
MAKE_TICTAC_MOVE_REQUEST = endpoints.ResourceContainer(
    MakeTicTacMoveForm,
    urlsafe_game_key=messages.StringField(1),)
NUMBER_OF_RESULTS = endpoints.ResourceContainer(
    number_of_results=messages.IntegerField(1),)

MEMCACHE_MOVES_REMAINING = 'MOVES_REMAINING'

@endpoints.api(name='tic_tac_toe', version='v1')
class TicTacToeApi(remote.Service):
    """Tic Tac Toe API"""


    def legal_moves_str(self, board):
        """ Get the empty spaces """
        return ' '.join(str(index) for index,
                square in enumerate(list(board)) if square == ' ')

    def is_legal_moves(self, board, move):
        """ Is the move is legal? """
        return move in [index for index,
                square in enumerate(list(board)) if square == ' ']


    @endpoints.method(request_message=USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='create_user',
                      http_method='POST')
    def create_user(self, request):
        """Create a User. Requires a unique username"""
        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException(
                    'A User with that name already exists!')
        user = User(name=request.user_name, email=request.email)
        user.put()
        return StringMessage(message='User {} created!'.format(
                request.user_name))

    @endpoints.method(request_message=NEW_TICTAC_REQUEST,
                      response_message=TicTacForm,
                      path='game',
                      name='new_game',
                      http_method='POST')
    def new_game(self, request):
        """Creates new game"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        try:
            game = TicTac.new_game(user.key, request.user_start, '         ')

        except ValueError:
            raise endpoints.BadRequestException('Maximum must be greater '
                                                'than minimum!')

        # Use a task queue to update the average user steps.
        # This operation is not needed to complete the creation of a new game
        # so it is performed out of sequence.
        taskqueue.add(url='/tasks/cache_average_steps')
        msg = 'Choose your next move: %s' % self.legal_moves_str(game.board)
        return game.to_form(msg)


    @endpoints.method(request_message=USER_REQUEST,
                      response_message=GamesForm,
                      path='games/user/{user_name}',
                      name='get_user_games',
                      http_method='GET')
    def get_user_games(self, request):
        """Returns all of an individual User's scores"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        games = TicTac.query(TicTac.user == user.key,
                             TicTac.game_over == False,
                             TicTac.cancelled == False)
        return GamesForm(games=[game.to_form() for game in games])
        # user_name = user.name,


    @endpoints.method(request_message=GET_TICTAC_REQUEST,
                      response_message=TicTacForm,
                      path='game/cancel/{urlsafe_game_key}',
                      name='cancel_game',
                      http_method='GET')
    def cancel_game(self, request):
        """Return the current game state."""
        game = get_by_urlsafe(request.urlsafe_game_key, TicTac)
        if game:
            if game.cancelled:
                msg = 'This game has already cancelled!'
            else:
                game.cancelled = True
                game.put()
                msg = 'The game is canelled!'
            return game.to_form(msg)
        else:
            raise endpoints.NotFoundException('Game not found!')


    @endpoints.method(request_message=GET_TICTAC_REQUEST,
                      response_message=TicTacForm,
                      path='game/{urlsafe_game_key}',
                      name='get_game',
                      http_method='GET')
    def get_game(self, request):
        """Return the current game state."""
        game = get_by_urlsafe(request.urlsafe_game_key, TicTac)
        if game:
            msg = 'Choose your next move: %s' % self.legal_moves_str(game.board)
            return game.to_form(msg)
        else:
            raise endpoints.NotFoundException('Game not found!')


    @endpoints.method(request_message=MAKE_TICTAC_MOVE_REQUEST,
                      response_message=TicTacForm,
                      path='game/{urlsafe_game_key}',
                      name='make_move',
                      http_method='PUT')
    def make_move(self, request):
        """Makes a move. Returns a game state with message"""
        game = get_by_urlsafe(request.urlsafe_game_key, TicTac)
        if not game:
            raise endpoints.NotFoundException('Game not found!')

        return game.make_a_move(request.position)

    @endpoints.method(response_message=ScoreForms,
                      path='scores',
                      name='get_scores',
                      http_method='GET')
    def get_scores(self, request):
        """Return all scores"""
        return ScoreForms(items=[score.to_form() for score in Score.query()])


    @endpoints.method(request_message=NUMBER_OF_RESULTS,
                      response_message=ScoreForms,
                      path='high_scores',
                      name='get_high_scores',
                      http_method='GET')
    def get_high_scores(self, request):
        """Return high scores"""
        if request.number_of_results:
            return ScoreForms(items=[score.to_form() for score in
                    Score.query().order(-Score.winner, -Score.user_steps).\
                      fetch(request.number_of_results)])
        else:
            return ScoreForms(items=[score.to_form() for score in
                      Score.query().order(-Score.winner, -Score.user_steps)])


    @endpoints.method(request_message=USER_REQUEST,
                      response_message=ScoreForms,
                      path='scores/user/{user_name}',
                      name='get_user_scores',
                      http_method='GET')
    def get_user_scores(self, request):
        """Returns all of an individual User's scores"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        scores = Score.query(Score.user == user.key)
        return ScoreForms(items=[score.to_form() for score in scores])


    @endpoints.method(response_message=RankForms,
                      path='user_rankings',
                      name='get_user_rankings',
                      http_method='GET')
    def get_user_rankings(self, request):
        """Return users ranking"""
        return RankForms(items=[rank.to_form() for rank in
                          User.query().order(-User.performance)])


    @endpoints.method(request_message=GET_TICTAC_REQUEST,
                      response_message=HistoryForms,
                      path='game/history/{urlsafe_game_key}',
                      name='get_game_history',
                      http_method='GET')
    def get_game_history(self, request):
        """Return a game's history."""
        game = get_by_urlsafe(request.urlsafe_game_key, TicTac)
        if game:
            histories = History.query(History.game == game.key).\
                                order(History.steps)
            return HistoryForms(items=[history.to_form() for history in histories])
        else:
            raise endpoints.NotFoundException('Game not found!')


    @endpoints.method(response_message=StringMessage,
                      path='games/average_steps',
                      name='get_average_steps',
                      http_method='GET')
    def get_average_steps(self, request):
        """Get the cached average moves remaining"""
        return StringMessage(message=memcache.get(MEMCACHE_MOVES_REMAINING) or '')

    @staticmethod
    def _cache_average_steps():
        """Populates memcache with the average moves of Games"""
        games = TicTac.query(TicTac.game_over == False,
                             TicTac.cancelled == False).fetch()
        if games:
            count = len(games)
            total_user_steps = sum([game.user_steps
                                        for game in games])
            average = float(total_user_steps)/count
            memcache.set(MEMCACHE_MOVES_REMAINING,
                         'The average moves is {:.2f}'.format(average))


api = endpoints.api_server([TicTacToeApi])
