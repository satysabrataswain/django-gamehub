from typing import Any


WIN_LINES = [
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),

    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),

    (0, 4, 8),
    (2, 4, 6),
]


def initial_state() -> dict[str, Any]:
    return {
        "board": [None] * 9,
    }


def place_mark(
    state: dict[str, Any],
    position: int,
    mark: str,
) -> dict[str, Any]:

    if position < 0 or position > 8:
        raise ValueError(
            "Position 0 se 8 ke beech honi chahiye."
        )

    board = list(state["board"])

    if board[position] is not None:
        raise ValueError(
            "Ye position already occupied hai."
        )

    board[position] = mark

    new_state = dict(state)
    new_state["board"] = board

    return new_state


def check_result(
    state: dict[str, Any],
) -> str | None:

    board = state["board"]

    for a, b, c in WIN_LINES:

        if (
            board[a] is not None
            and board[a] == board[b] == board[c]
        ):
            if board[a] == "X":
                return "P1"

            return "P2"

    if all(
        cell is not None
        for cell in board
    ):
        return "DRAW"

    return None


def _winner(
    board: list[Any],
) -> str | None:

    for a, b, c in WIN_LINES:

        if (
            board[a] is not None
            and board[a] == board[b] == board[c]
        ):
            return str(board[a])

    return None


def _minimax(
    board: list[Any],
    maximizing: bool,
) -> int:

    winner = _winner(board)

    if winner == "O":
        return 1

    if winner == "X":
        return -1

    if all(
        cell is not None
        for cell in board
    ):
        return 0

    if maximizing:

        best_score = -100

        for i in range(9):

            if board[i] is None:

                board[i] = "O"

                score = _minimax(
                    board,
                    False,
                )

                board[i] = None

                best_score = max(
                    best_score,
                    score,
                )

        return best_score

    best_score = 100

    for i in range(9):

        if board[i] is None:

            board[i] = "X"

            score = _minimax(
                board,
                True,
            )

            board[i] = None

            best_score = min(
                best_score,
                score,
            )

    return best_score


def best_computer_move(
    state: dict[str, Any],
) -> int | None:

    board = list(state["board"])

    best_score = -100
    best_move: int | None = None

    for i in range(9):

        if board[i] is None:

            board[i] = "O"

            score = _minimax(
                board,
                False,
            )

            board[i] = None

            if score > best_score:

                best_score = score
                best_move = i

    return best_move