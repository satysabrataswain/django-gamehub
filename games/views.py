from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Game
from .serializers import (
    GameCreateSerializer,
    GameSerializer,
    MoveSerializer,
)
from .services.game_engine import (
    create_initial_state,
    perform_move,
)


class GameViewSet(
    ModelViewSet
):

    permission_classes = [
        IsAuthenticated
    ]

    http_method_names = [
        "get",
        "post",
        "head",
        "options",
    ]

    def get_queryset(self):

        user = self.request.user

        return (
            Game.objects
            .filter(
                Q(player1=user)
                | Q(player2=user)
            )
            .select_related(
                "player1",
                "player2",
                "winner",
            )
            .order_by(
                "-created_at"
            )
        )

    def get_serializer_class(self):

        if self.action == "create":
            return GameCreateSerializer

        return GameSerializer

    def create(
        self,
        request: Request,
        *args,
        **kwargs,
    ) -> Response:

        serializer = (
            GameCreateSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        game_type = (
            serializer.validated_data[
                "game_type"
            ]
        )

        mode = (
            serializer.validated_data[
                "mode"
            ]
        )

        initial_state = (
            create_initial_state(
                game_type
            )
        )

        if mode == Game.Mode.PVC:

            game_status = (
                Game.Status.ACTIVE
            )

        else:

            game_status = (
                Game.Status.WAITING
            )

        game = Game.objects.create(
            game_type=game_type,
            mode=mode,
            player1=request.user,
            state=initial_state,
            current_turn=Game.Turn.P1,
            status=game_status,
        )

        output = GameSerializer(
            game,
            context={
                "request": request
            },
        )

        return Response(
            output.data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=False,
        methods=["get"],
    )
    def waiting(
        self,
        request: Request,
    ) -> Response:

        games = (
            Game.objects
            .filter(
                mode=Game.Mode.PVP,
                status=Game.Status.WAITING,
                player2__isnull=True,
            )
            .exclude(
                player1=request.user
            )
            .select_related(
                "player1"
            )
            .order_by(
                "-created_at"
            )
        )

        serializer = GameSerializer(
            games,
            many=True,
            context={
                "request": request
            },
        )

        return Response(
            serializer.data
        )

    @action(
        detail=True,
        methods=["post"],
    )
    def join(
        self,
        request: Request,
        pk: str | None = None,
    ) -> Response:

        with transaction.atomic():

            game = get_object_or_404(
                Game.objects
                .select_for_update()
                .select_related(
                    "player1",
                    "player2",
                ),
                pk=pk,
            )

            if (
                game.mode
                != Game.Mode.PVP
            ):

                raise ValidationError(
                    "Sirf PVP game join ki ja sakti hai."
                )

            if (
                game.status
                != Game.Status.WAITING
            ):

                raise ValidationError(
                    "Game join ke liye available nahi hai."
                )

            if (
                game.player1_id
                == request.user.id
            ):

                raise ValidationError(
                    "Aap apni game ko second player ke roop me join nahi kar sakte."
                )

            if game.player2 is not None:

                raise ValidationError(
                    "Game already full hai."
                )

            game.player2 = (
                request.user
            )

            game.status = (
                Game.Status.ACTIVE
            )

            game.current_turn = (
                Game.Turn.P1
            )

            game.save()

        output = GameSerializer(
            game,
            context={
                "request": request
            },
        )

        return Response(
            output.data
        )

    @action(
        detail=True,
        methods=["post"],
    )
    def move(
        self,
        request: Request,
        pk: str | None = None,
    ) -> Response:

        serializer = MoveSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        move = (
            serializer.validated_data[
                "move"
            ]
        )

        with transaction.atomic():

            game = get_object_or_404(
                Game.objects
                .select_for_update()
                .select_related(
                    "player1",
                    "player2",
                    "winner",
                ),
                pk=pk,
            )

            perform_move(
                game=game,
                user_id=request.user.id,
                move=move,
            )

            game.save()

        output = GameSerializer(
            game,
            context={
                "request": request
            },
        )

        return Response(
            output.data
        )