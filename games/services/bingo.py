import random
from typing import Any


BOARD_SIZE = 5
LINES_TO_WIN = 5


def generate_board() -> list[list[int]]:
    numbers = list(range(1, 26))
    random.shuffle(numbers)

    board = []

    for i in range(0, 25, BOARD_SIZE):
        board.append(
            numbers[i:i + BOARD_SIZE]
        )

    return board


def initial_state() -> dict[str, Any]:
    return {
        "p1_board": generate_board(),
        "p2_board": generate_board(),
        "called_numbers": [],
    }


def call_number(
    state: dict[str, Any],
    number: int,
) -> dict[str, Any]:
    if number < 1 or number > 25:
        raise ValueError(
            "Bingo number 1 se 25 ke beech hona chahiye."
        )

    called_numbers = list(
        state.get(
            "called_numbers",
            [],
        )
    )

    if number in called_numbers:
        raise ValueError(
            "Ye number already call ho chuka hai."
        )

    called_numbers.append(number)

    new_state = dict(state)
    new_state["called_numbers"] = called_numbers

    return new_state


def _all_lines(
    board: list[list[int]],
) -> list[list[int]]:
    lines: list[list[int]] = []

    # Rows
    for row in board:
        lines.append(row)

    # Columns
    for column in range(BOARD_SIZE):
        lines.append([
            board[row][column]
            for row in range(BOARD_SIZE)
        ])

    # Left diagonal
    lines.append([
        board[i][i]
        for i in range(BOARD_SIZE)
    ])

    # Right diagonal
    lines.append([
        board[i][BOARD_SIZE - 1 - i]
        for i in range(BOARD_SIZE)
    ])

    return lines


def line_count(
    board: list[list[int]],
    called_numbers: list[int],
) -> int:
    called = set(called_numbers)
    count = 0

    for line in _all_lines(board):
        if all(
            number in called
            for number in line
        ):
            count += 1

    return count


def check_result(
    state: dict[str, Any],
) -> str | None:
    called_numbers = state[
        "called_numbers"
    ]

    p1_lines = line_count(
        state["p1_board"],
        called_numbers,
    )

    p2_lines = line_count(
        state["p2_board"],
        called_numbers,
    )

    if (
        p1_lines >= LINES_TO_WIN
        and p2_lines >= LINES_TO_WIN
    ):
        return "DRAW"

    if p1_lines >= LINES_TO_WIN:
        return "P1"

    if p2_lines >= LINES_TO_WIN:
        return "P2"

    return None


def _board_score(
    board: list[list[int]],
    called_numbers: list[int],
) -> int:
    called = set(called_numbers)
    score = 0

    for line in _all_lines(board):
        marked = sum(
            1
            for number in line
            if number in called
        )

        # Squared score rewards moves that get close to
        # completing a line more than scattered marks.
        score += marked * marked

    return score


def best_computer_move(
    state: dict[str, Any],
) -> int | None:
    """
    Choose a sensible CPU move.

    Priority:
    1. Take an immediate CPU win.
    2. Avoid a move that immediately makes P1 win.
    3. Prefer moves that improve P2's board more than P1's.
    4. If every move ends the game, prefer a draw over a loss.
    """
    called_numbers = set(
        state["called_numbers"]
    )

    available_numbers = [
        number
        for number in range(1, 26)
        if number not in called_numbers
    ]

    if not available_numbers:
        return None

    winning_moves: list[int] = []
    drawing_moves: list[int] = []
    safe_moves: list[tuple[int, int]] = []
    losing_moves: list[int] = []

    for number in available_numbers:
        test_called_numbers = (
            list(called_numbers)
            + [number]
        )

        test_state = dict(state)
        test_state["called_numbers"] = test_called_numbers

        result = check_result(test_state)

        if result == "P2":
            winning_moves.append(number)
            continue

        if result == "DRAW":
            drawing_moves.append(number)
            continue

        if result == "P1":
            losing_moves.append(number)
            continue

        p2_score = _board_score(
            state["p2_board"],
            test_called_numbers,
        )
        p1_score = _board_score(
            state["p1_board"],
            test_called_numbers,
        )

        safe_moves.append(
            (p2_score - p1_score, number)
        )

    if winning_moves:
        return random.choice(winning_moves)

    if safe_moves:
        best_score = max(
            score
            for score, _ in safe_moves
        )

        best_numbers = [
            number
            for score, number in safe_moves
            if score == best_score
        ]

        return random.choice(best_numbers)

    if drawing_moves:
        return random.choice(drawing_moves)

    return random.choice(losing_moves)
