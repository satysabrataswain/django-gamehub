import uuid

from django.conf import settings
from django.db import models


class Game(models.Model):

    class GameType(models.TextChoices):
        TIC_TAC_TOE = "TIC_TAC_TOE", "Tic Tac Toe"
        BINGO = "BINGO", "Bingo"

    class Mode(models.TextChoices):
        PVP = "PVP", "Player vs Player"
        PVC = "PVC", "Player vs Computer"

    class Status(models.TextChoices):
        WAITING = "WAITING", "Waiting"
        ACTIVE = "ACTIVE", "Active"
        FINISHED = "FINISHED", "Finished"
        DRAW = "DRAW", "Draw"

    class Turn(models.TextChoices):
        P1 = "P1", "Player 1"
        P2 = "P2", "Player 2"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    game_type = models.CharField(
        max_length=30,
        choices=GameType.choices,
    )

    mode = models.CharField(
        max_length=10,
        choices=Mode.choices,
    )

    player1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="games_as_player1",
    )

    player2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="games_as_player2",
        null=True,
        blank=True,
    )

    current_turn = models.CharField(
        max_length=2,
        choices=Turn.choices,
        default=Turn.P1,
    )

    state = models.JSONField(
        default=dict,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.WAITING,
    )

    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="games_won",
        null=True,
        blank=True,
    )

    winner_is_computer = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self) -> str:
        return f"{self.game_type} - {self.id}"