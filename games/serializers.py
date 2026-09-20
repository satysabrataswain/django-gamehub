from rest_framework import serializers

from .models import Game


class GameCreateSerializer(serializers.Serializer):
    game_type = serializers.ChoiceField(
        choices=Game.GameType.choices
    )
    mode = serializers.ChoiceField(
        choices=Game.Mode.choices
    )


class MoveSerializer(serializers.Serializer):
    move = serializers.IntegerField()


class GameSerializer(serializers.ModelSerializer):
    player1 = serializers.CharField(
        source="player1.username",
        read_only=True,
    )
    player2 = serializers.SerializerMethodField()
    winner = serializers.SerializerMethodField()
    your_role = serializers.SerializerMethodField()
    state = serializers.SerializerMethodField()

    class Meta:
        model = Game
        fields = [
            "id",
            "game_type",
            "mode",
            "player1",
            "player2",
            "your_role",
            "current_turn",
            "state",
            "status",
            "winner",
            "winner_is_computer",
            "created_at",
            "updated_at",
        ]

    def _request_user_id(self):
        request = self.context.get("request")
        if request is None:
            return None

        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated:
            return None

        return user.id

    def get_player2(self, obj: Game) -> str | None:
        if obj.mode == Game.Mode.PVC:
            return "COMPUTER"

        if obj.player2:
            return obj.player2.username

        return None

    def get_winner(self, obj: Game) -> str | None:
        if obj.winner_is_computer:
            return "COMPUTER"

        if obj.winner:
            return obj.winner.username

        return None

    def get_your_role(self, obj: Game) -> str | None:
        user_id = self._request_user_id()

        if user_id is None:
            return None

        if obj.player1_id == user_id:
            return Game.Turn.P1

        if obj.player2_id == user_id:
            return Game.Turn.P2

        return None

    def get_state(self, obj: Game) -> dict:
        """
        Return game state without leaking a live Bingo opponent board.

        Tic-Tac-Toe is a public board game, so its full state is safe.
        For Bingo, each player sees only their own board while the game
        is waiting/active. After the game ends, both boards are revealed.
        """
        state = dict(obj.state or {})

        if obj.game_type != Game.GameType.BINGO:
            return state

        if obj.status in {
            Game.Status.FINISHED,
            Game.Status.DRAW,
        }:
            return state

        role = self.get_your_role(obj)

        if role != Game.Turn.P1:
            state["p1_board"] = None

        if role != Game.Turn.P2:
            state["p2_board"] = None

        return state
