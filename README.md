# Tic Tac Toe game in Google App Engine with Endpoints

## API availability 
You can explore the API at [Google App Engine](http://jv-tictactoe.appspot.com/_ah/api/explorer).

## Set-Up Instructions:
1. Clone this repository 
```
git clone https://github.com/janosvincze/TicTacToe YOUR_DIRECTORY
```
2.  Update the value of application in app.yaml to the app ID you have registered
 in the App Engine admin console and would like to use to host your instance of this sample.
3.  Run the app with the devserver using dev_appserver.py DIR, and ensure it's
 running by visiting the API Explorer - by default localhost:8080/_ah/api/explorer.
4.  (Optional) Generate your client library(ies) with the endpoints tool.
 Deploy your application.



## Game Description:
Tic Tac Toe is a simple two player game. Player can hold places one-by-one in a 3x3 grid. Who can place three in a row, will be the winner.
In this application players can play with 'the computer'. After every step the applictaion move automatically and write out the actual state.
Many different Tic Tac Toe games can be played by many different Users at any given time. Each game can be retrieved or played by using the path parameter
`urlsafe_game_key`.

## Files:
 - tictac.py: TicTacToe class representing the game.
 - api.py: Contains endpoints and game playing logic.
 - app.yaml: App configuration.
 - cron.yaml: Cronjob configuration.
 - main.py: Handler for taskqueue handler.
 - models.py: Entity and message definitions including helper methods.
 - utils.py: Helper function for retrieving ndb.Models by urlsafe Key string.

## Endpoints:
 - **create_user**
    - Path: 'user'
    - Method: POST
    - Parameters: user_name, email (optional)
    - Returns: Message confirming creation of the User.
    - Description: Creates a new User. user_name provided must be unique. Will
    raise a ConflictException if a User with that user_name already exists.

 - **new_game**
    - Path: 'game'
    - Method: POST
    - Parameters: user_name, min, max, attempts
    - Returns: GameForm with initial game state.
    - Description: Creates a new Game. user_name provided must correspond to an
    existing user - will raise a NotFoundException if not. Min must be less than
    max. Also adds a task to a task queue to update the average moves remaining
    for active games.

 - **get_game**
    - Path: 'game/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameForm with current game state.
    - Description: Returns the current state of a game.

 - **get_user_games**
    - Path: 'games/user/{user_name}'
    - Method: GET
    - Parameters: user_name
    - Returns: GamesForm with the given user's games.
    - Description: Returns the given user's games.

 - **cancel_game**
    - Path: 'game/cancel/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameForm with the last game state.
    - Description: Cancel an active game.

 - **make_move**
    - Path: 'game/{urlsafe_game_key}'
    - Method: PUT
    - Parameters: urlsafe_game_key, position of the next step
    - Returns: GameForm with new game state.
    - Description: Accepts a 'position' and returns the updated state of the game. The new states of the game will be added to the history of game.
    If this causes a game to end, a corresponding Score entity will be created.

 - **get_scores**
    - Path: 'scores'
    - Method: GET
    - Parameters: None
    - Returns: ScoreForms.
    - Description: Returns all Scores in the database (unordered).

 - **get_high_scores**
    - Path: 'high_scores'
    - Method: GET
    - Parameters: Optionally the number_of_result
    - Returns: ScoreForms.
    - Description: Returns the Scores from the database in the order of scores.

 - **get_user_scores**
    - Path: 'scores/user/{user_name}'
    - Method: GET
    - Parameters: user_name
    - Returns: ScoreForms.
    - Description: Returns all Scores recorded by the provided player (unordered).
    Will raise a NotFoundException if the User does not exist.

 - **get_user_rankings**
    - Path: 'user_rankings'
    - Method: GET
    - Parameters: None
    - Returns: HistoryForms.
    - Description: Returns the game's history in states.

 - **get_game_history**
    - Path: 'game/history/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameForm with the last game state.
    - Description: Cancel an active game.

 - **get_average_steps**
    - Path: 'games/average_steps'
    - Method: GET
    - Parameters: None
    - Returns: StringMessage
    - Description: Gets the average steps for all games
    from a previously cached memcache key.

##Models Included:
 - **User**
    - Stores unique user_name and (optional) email address.

 - **TicTac**
    - Stores unique game states. Associated with User model via KeyProperty.

 - **Score**
    - Records completed games. Associated with Users model via KeyProperty.

 - **History**
    - Records the states of games. Associated with TicTac model via KeyProperty.

##Forms Included:
 - **TicTacForm**
    - Representation of a TicTac's state (urlsafe_key, game_over,
    message, board, steps, user_name, cancelled, winner).
 - **GamesForms**
    - Multiple TicTacForm container.
 - **NewTicTacForm**
    - Used to create a new game (user_name, user_start, board)
 - **MakeTicTacMoveForm**
    - Inbound make move form (position).
 - **ScoreForm**
    - Representation of a completed game's Score (user_name, date, winner, user_steps).
 - **ScoreForms**
    - Multiple ScoreForm container.
 - **RankForm**
    - Representation of a user's performance (user_name, performance)
 - **RankForms**
    - Multiple RankForm container.
 - **HistoryForm**
    - Representation of a game's state (is_human, position, board, msg, steps)
 - **HistoryForms**
    - Multiple HistoryForm container.
 - **StringMessage**
    - General purpose String container.
