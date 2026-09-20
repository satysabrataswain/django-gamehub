from rest_framework import serializers

from .models import Game


class GameCreateSerializer(
    serializers.Serializer
):

    game_type = (
        serializers.ChoiceField(
            choices=Game.GameType.choices
        )
    )

    mode = serializers.ChoiceField(
        choices=Game.Mode.choices
    )


class MoveSerializer(
    serializers.Serializer
):

    move = serializers.IntegerField()


class GameSerializer(
    serializers.ModelSerializer[Game]
):

    player1 = serializers.CharField(
        source="player1.username",
        read_only=True,
    )

    player2 = (
        serializers.SerializerMethodField()
    )

    winner = (
        serializers.SerializerMethodField()
    )

    your_role = (
        serializers.SerializerMethodField()
    )

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

    def get_player2(
        self,
        obj: Game,
    ) -> str | None:

        if obj.mode == Game.Mode.PVC:
            return "COMPUTER"

        if obj.player2:
            return obj.player2.username

        return None

    def get_winner(
        self,
        obj: Game,
    ) -> str | None:

        if obj.winner_is_computer:
            return "COMPUTER"

        if obj.winner:
            return obj.winner.username

        return None

    def get_your_role(
        self,
        obj: Game,
    ) -> str | None:

        request = self.context.get(
            "request"
        )

        if request is None:
            return None

        if (
            obj.player1_id
            == request.user.id
        ):
            return "P1"

        if (
            obj.player2_id
            == request.user.id
        ):
            return "P2"

        return None