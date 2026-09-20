from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from .models import Game
from .services import bingo
from .services.game_engine import perform_move


class GameApiTests(APITestCase):
    def setUp(self):
        self.p1 = User.objects.create_user(
            username="player1",
            password="test-password-123",
        )
        self.p2 = User.objects.create_user(
            username="player2",
            password="test-password-123",
        )
        self.outsider = User.objects.create_user(
            username="outsider",
            password="test-password-123",
        )

    def test_create_pvc_tic_tac_toe(self):
        self.client.force_authenticate(self.p1)

        response = self.client.post(
            "/api/games/",
            {
                "game_type": Game.GameType.TIC_TAC_TOE,
                "mode": Game.Mode.PVC,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.data["status"],
            Game.Status.ACTIVE,
        )
        self.assertEqual(
            response.data["player2"],
            "COMPUTER",
        )
        self.assertEqual(
            response.data["state"]["board"],
            [None] * 9,
        )

    def test_pvp_game_can_be_joined(self):
        game = Game.objects.create(
            game_type=Game.GameType.TIC_TAC_TOE,
            mode=Game.Mode.PVP,
            player1=self.p1,
            state={"board": [None] * 9},
            status=Game.Status.WAITING,
        )

        self.client.force_authenticate(self.p2)

        response = self.client.post(
            f"/api/games/{game.id}/join/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        game.refresh_from_db()

        self.assertEqual(
            game.player2_id,
            self.p2.id,
        )
        self.assertEqual(
            game.status,
            Game.Status.ACTIVE,
        )

    def test_player_cannot_join_own_pvp_game(self):
        game = Game.objects.create(
            game_type=Game.GameType.TIC_TAC_TOE,
            mode=Game.Mode.PVP,
            player1=self.p1,
            state={"board": [None] * 9},
            status=Game.Status.WAITING,
        )

        self.client.force_authenticate(self.p1)

        response = self.client.post(
            f"/api/games/{game.id}/join/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_bingo_hides_opponent_board_while_active(self):
        state = bingo.initial_state()

        game = Game.objects.create(
            game_type=Game.GameType.BINGO,
            mode=Game.Mode.PVP,
            player1=self.p1,
            player2=self.p2,
            state=state,
            status=Game.Status.ACTIVE,
        )

        self.client.force_authenticate(self.p1)

        response = self.client.get(
            f"/api/games/{game.id}/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["state"]["p1_board"],
            state["p1_board"],
        )
        self.assertIsNone(
            response.data["state"]["p2_board"]
        )

    def test_waiting_bingo_does_not_leak_boards_to_outsider(self):
        Game.objects.create(
            game_type=Game.GameType.BINGO,
            mode=Game.Mode.PVP,
            player1=self.p1,
            state=bingo.initial_state(),
            status=Game.Status.WAITING,
        )

        self.client.force_authenticate(
            self.outsider
        )

        response = self.client.get(
            "/api/games/waiting/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertIsNone(
            response.data[0]["state"]["p1_board"]
        )
        self.assertIsNone(
            response.data[0]["state"]["p2_board"]
        )

    def test_outsider_cannot_make_move(self):
        game = Game.objects.create(
            game_type=Game.GameType.TIC_TAC_TOE,
            mode=Game.Mode.PVP,
            player1=self.p1,
            player2=self.p2,
            state={"board": [None] * 9},
            status=Game.Status.ACTIVE,
        )

        self.client.force_authenticate(
            self.outsider
        )

        response = self.client.post(
            f"/api/games/{game.id}/move/",
            {"move": 0},
            format="json",
        )

        self.assertEqual(response.status_code, 403)


class GameEngineTests(APITestCase):
    def setUp(self):
        self.p1 = User.objects.create_user(
            username="engine-player",
            password="test-password-123",
        )

    def test_tic_tac_toe_cpu_responds_after_player_move(self):
        game = Game.objects.create(
            game_type=Game.GameType.TIC_TAC_TOE,
            mode=Game.Mode.PVC,
            player1=self.p1,
            state={"board": [None] * 9},
            status=Game.Status.ACTIVE,
        )

        perform_move(
            game=game,
            user_id=self.p1.id,
            move=0,
        )

        board = game.state["board"]

        self.assertEqual(board[0], "X")
        self.assertIn("O", board)
        self.assertEqual(
            game.current_turn,
            Game.Turn.P1,
        )

    def test_bingo_cpu_returns_an_uncalled_number(self):
        state = bingo.initial_state()
        state["called_numbers"] = [1, 2, 3]

        move = bingo.best_computer_move(
            state
        )

        self.assertIsNotNone(move)
        self.assertNotIn(
            move,
            state["called_numbers"],
        )
        self.assertGreaterEqual(move, 1)
        self.assertLessEqual(move, 25)
