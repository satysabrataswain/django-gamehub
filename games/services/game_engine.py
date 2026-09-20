from rest_framework.exceptions import (
    PermissionDenied,
    ValidationError,
)

from games.models import Game

from . import bingo
from . import tic_tac_toe


def create_initial_state(
    game_type: str,
) -> dict:

    if (
        game_type
        == Game.GameType.TIC_TAC_TOE
    ):
        return (
            tic_tac_toe.initial_state()
        )

    if (
        game_type
        == Game.GameType.BINGO
    ):
        return bingo.initial_state()

    raise ValidationError(
        "Invalid game type."
    )


def get_player_role(
    game: Game,
    user_id: int,
) -> str:

    if game.player1_id == user_id:
        return Game.Turn.P1

    if game.player2_id == user_id:
        return Game.Turn.P2

    raise PermissionDenied(
        "Aap is game ke player nahi ho."
    )


def finish_game(
    game: Game,
    result: str,
) -> None:

    game.winner = None
    game.winner_is_computer = False

    if result == "DRAW":

        game.status = Game.Status.DRAW

        return

    game.status = (
        Game.Status.FINISHED
    )

    if result == "P1":

        game.winner = game.player1

        return

    if result == "P2":

        if game.mode == Game.Mode.PVC:

            game.winner_is_computer = True

        else:

            game.winner = game.player2


def play_tic_tac_toe(
    game: Game,
    role: str,
    move: int,
) -> None:

    state = dict(
        game.state
    )

    state.pop(
        "last_cpu_move",
        None,
    )

    if role == Game.Turn.P1:
        mark = "X"
    else:
        mark = "O"

    try:

        state = (
            tic_tac_toe.place_mark(
                state,
                move,
                mark,
            )
        )

    except ValueError as error:

        raise ValidationError({
            "move": str(error),
        }) from error

    result = (
        tic_tac_toe.check_result(
            state
        )
    )

    game.state = state

    if result:

        finish_game(
            game,
            result,
        )

        return

    # Player vs Computer
    if game.mode == Game.Mode.PVC:

        cpu_move = (
            tic_tac_toe.best_computer_move(
                state
            )
        )

        if cpu_move is not None:

            state = (
                tic_tac_toe.place_mark(
                    state,
                    cpu_move,
                    "O",
                )
            )

            state[
                "last_cpu_move"
            ] = cpu_move

            game.state = state

            result = (
                tic_tac_toe.check_result(
                    state
                )
            )

            if result:

                finish_game(
                    game,
                    result,
                )

                return

        game.current_turn = (
            Game.Turn.P1
        )

        return

    # Player vs Player
    if role == Game.Turn.P1:

        game.current_turn = (
            Game.Turn.P2
        )

    else:

        game.current_turn = (
            Game.Turn.P1
        )


def play_bingo(
    game: Game,
    role: str,
    move: int,
) -> None:

    state = dict(
        game.state
    )

    state.pop(
        "last_cpu_move",
        None,
    )

    try:

        state = bingo.call_number(
            state,
            move,
        )

    except ValueError as error:

        raise ValidationError({
            "move": str(error),
        }) from error

    result = bingo.check_result(
        state
    )

    game.state = state

    if result:

        finish_game(
            game,
            result,
        )

        return

    # Player vs Computer
    if game.mode == Game.Mode.PVC:

        cpu_move = (
            bingo.best_computer_move(
                state
            )
        )

        if cpu_move is not None:

            state = bingo.call_number(
                state,
                cpu_move,
            )

            state[
                "last_cpu_move"
            ] = cpu_move

            game.state = state

            result = (
                bingo.check_result(
                    state
                )
            )

            if result:

                finish_game(
                    game,
                    result,
                )

                return

        game.current_turn = (
            Game.Turn.P1
        )

        return

    # Player vs Player
    if role == Game.Turn.P1:

        game.current_turn = (
            Game.Turn.P2
        )

    else:

        game.current_turn = (
            Game.Turn.P1
        )


def perform_move(
    game: Game,
    user_id: int,
    move: int,
) -> None:

    if game.status != Game.Status.ACTIVE:

        raise ValidationError(
            "Game active nahi hai."
        )

    role = get_player_role(
        game,
        user_id,
    )

    if role != game.current_turn:

        raise ValidationError(
            "Abhi aapki turn nahi hai."
        )

    if (
        game.mode == Game.Mode.PVC
        and role != Game.Turn.P1
    ):
        raise ValidationError(
            "Computer ki move server automatically karega."
        )

    if (
        game.game_type
        == Game.GameType.TIC_TAC_TOE
    ):

        play_tic_tac_toe(
            game,
            role,
            move,
        )

        return

    if (
        game.game_type
        == Game.GameType.BINGO
    ):

        play_bingo(
            game,
            role,
            move,
        )

        return

    raise ValidationError(
        "Unsupported game type."
    )