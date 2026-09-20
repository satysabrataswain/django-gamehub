(() => {
    "use strict";

    const state = {
        access: localStorage.getItem("gamehub_access") || "",
        refresh: localStorage.getItem("gamehub_refresh") || "",
        username: localStorage.getItem("gamehub_username") || "",
        currentGame: null,
        pollTimer: null,
        toastTimer: null,
        movePending: false,
    };

    const authEndpoints = {
        login: [
            "/api/auth/token/",
            "/api/auth/login/",
            "/api/token/",
        ],
        register: [
            "/api/auth/register/",
            "/api/accounts/register/",
            "/api/register/",
        ],
        refresh: [
            "/api/auth/token/refresh/",
            "/api/auth/refresh/",
            "/api/token/refresh/",
        ],
    };

    const $ = (id) => document.getElementById(id);

    const els = {
        authView: $("authView"),
        dashboardView: $("dashboardView"),
        gameView: $("gameView"),
        userBar: $("userBar"),
        usernameLabel: $("usernameLabel"),
        loginTab: $("loginTab"),
        registerTab: $("registerTab"),
        loginForm: $("loginForm"),
        registerForm: $("registerForm"),
        authMessage: $("authMessage"),
        waitingGames: $("waitingGames"),
        waitingCount: $("waitingCount"),
        myGames: $("myGames"),
        ticTacToeArea: $("ticTacToeArea"),
        bingoArea: $("bingoArea"),
        ticTacToeBoard: $("ticTacToeBoard"),
        bingoBoard: $("bingoBoard"),
        calledNumbers: $("calledNumbers"),
        bingoLineCount: $("bingoLineCount"),
        bingoLetters: $("bingoLetters"),
        gameTitle: $("gameTitle"),
        gameModeLabel: $("gameModeLabel"),
        gameTypeBadge: $("gameTypeBadge"),
        gameIdLabel: $("gameIdLabel"),
        statusBadge: $("statusBadge"),
        gameStatus: $("gameStatus"),
        playerOne: $("playerOne"),
        playerTwo: $("playerTwo"),
        yourRoleLabel: $("yourRoleLabel"),
        turnLabel: $("turnLabel"),
        toast: $("toast"),
    };

    function setTokens(data, username) {
        const access = data.access || data.token || data.access_token || "";
        const refresh = data.refresh || data.refresh_token || "";

        if (!access) {
            return false;
        }

        state.access = access;
        state.refresh = refresh;
        state.username = username;

        localStorage.setItem("gamehub_access", access);
        localStorage.setItem("gamehub_username", username);

        if (refresh) {
            localStorage.setItem("gamehub_refresh", refresh);
        }

        return true;
    }

    function clearSession() {
        state.access = "";
        state.refresh = "";
        state.username = "";
        state.currentGame = null;
        stopPolling();

        localStorage.removeItem("gamehub_access");
        localStorage.removeItem("gamehub_refresh");
        localStorage.removeItem("gamehub_username");
    }

    function flattenError(data) {
        if (!data) {
            return "Request failed.";
        }

        if (typeof data === "string") {
            return data;
        }

        if (data.detail) {
            return String(data.detail);
        }

        const parts = [];

        Object.entries(data).forEach(([key, value]) => {
            if (Array.isArray(value)) {
                parts.push(`${key}: ${value.join(" ")}`);
            } else if (value && typeof value === "object") {
                parts.push(`${key}: ${flattenError(value)}`);
            } else {
                parts.push(`${key}: ${value}`);
            }
        });

        return parts.join(" • ") || "Request failed.";
    }

    async function parseResponse(response) {
        const text = await response.text();

        if (!text) {
            return null;
        }

        try {
            return JSON.parse(text);
        } catch {
            return text;
        }
    }

    async function tryRefreshToken() {
        if (!state.refresh) {
            return false;
        }

        for (const endpoint of authEndpoints.refresh) {
            try {
                const response = await fetch(endpoint, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        refresh: state.refresh,
                    }),
                });

                const data = await parseResponse(response);

                if (
                    response.ok &&
                    data &&
                    (data.access || data.token || data.access_token)
                ) {
                    state.access =
                        data.access ||
                        data.token ||
                        data.access_token;

                    localStorage.setItem(
                        "gamehub_access",
                        state.access,
                    );

                    if (data.refresh) {
                        state.refresh = data.refresh;
                        localStorage.setItem(
                            "gamehub_refresh",
                            state.refresh,
                        );
                    }

                    return true;
                }
            } catch {
                // Try the next possible endpoint.
            }
        }

        return false;
    }

    async function api(
        url,
        options = {},
        retryAuth = true,
    ) {
        const headers = {
            ...(options.headers || {}),
        };

        if (
            options.body &&
            !(options.body instanceof FormData) &&
            !headers["Content-Type"]
        ) {
            headers["Content-Type"] = "application/json";
        }

        if (state.access) {
            headers.Authorization = `Bearer ${state.access}`;
        }

        let response;

        try {
            response = await fetch(url, {
                ...options,
                headers,
            });
        } catch {
            throw new Error(
                "Server se connection nahi hua. Django runserver check karo.",
            );
        }

        if (
            response.status === 401 &&
            retryAuth &&
            state.refresh
        ) {
            const refreshed = await tryRefreshToken();

            if (refreshed) {
                return api(url, options, false);
            }
        }

        const data = await parseResponse(response);

        if (!response.ok) {
            const error = new Error(flattenError(data));
            error.status = response.status;
            throw error;
        }

        return data;
    }

    async function callFirstEndpoint(
        endpoints,
        payload,
    ) {
        let lastError = null;

        for (const endpoint of endpoints) {
            try {
                const response = await fetch(endpoint, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify(payload),
                });

                const data = await parseResponse(response);

                if (response.ok) {
                    return {
                        endpoint,
                        data,
                    };
                }

                if (response.status !== 404) {
                    const error = new Error(
                        flattenError(data),
                    );
                    error.status = response.status;
                    throw error;
                }
            } catch (error) {
                lastError = error;

                if (
                    error.status &&
                    error.status !== 404
                ) {
                    throw error;
                }
            }
        }

        throw (
            lastError ||
            new Error(
                "Matching API endpoint nahi mila.",
            )
        );
    }

    function showToast(message) {
        clearTimeout(state.toastTimer);
        els.toast.textContent = message;
        els.toast.classList.remove("hidden");

        state.toastTimer = setTimeout(() => {
            els.toast.classList.add("hidden");
        }, 3200);
    }

    function showView(name) {
        els.authView.classList.toggle(
            "hidden",
            name !== "auth",
        );
        els.dashboardView.classList.toggle(
            "hidden",
            name !== "dashboard",
        );
        els.gameView.classList.toggle(
            "hidden",
            name !== "game",
        );
        els.userBar.classList.toggle(
            "hidden",
            name === "auth",
        );

        if (name !== "game") {
            stopPolling();
        }
    }

    function updateUserBar() {
        els.usernameLabel.textContent =
            state.username || "Player";
    }

    function setAuthTab(tab) {
        const login = tab === "login";

        els.loginTab.classList.toggle("active", login);
        els.registerTab.classList.toggle(
            "active",
            !login,
        );
        els.loginTab.setAttribute(
            "aria-selected",
            String(login),
        );
        els.registerTab.setAttribute(
            "aria-selected",
            String(!login),
        );
        els.loginForm.classList.toggle(
            "hidden",
            !login,
        );
        els.registerForm.classList.toggle(
            "hidden",
            login,
        );
        els.authMessage.textContent = "";
    }

    async function login(username, password) {
        const { data } = await callFirstEndpoint(
            authEndpoints.login,
            {
                username,
                password,
            },
        );

        if (!setTokens(data || {}, username)) {
            throw new Error(
                "Login response me JWT access token nahi mila.",
            );
        }

        updateUserBar();
        showView("dashboard");
        await loadDashboard();
    }

    async function register(
        username,
        email,
        password,
    ) {
        const payload = {
            username,
            password,
        };

        if (email) {
            payload.email = email;
        }

        await callFirstEndpoint(
            authEndpoints.register,
            payload,
        );

        await login(username, password);
        showToast("Account created. Welcome to GameHub!");
    }

    function gameName(type) {
        return type === "BINGO"
            ? "Bingo"
            : "Tic-Tac-Toe";
    }

    function modeName(mode) {
        return mode === "PVC"
            ? "VS COMPUTER"
            : "PLAYER VS PLAYER";
    }

    function formatStatus(status) {
        const map = {
            WAITING: "Waiting",
            ACTIVE: "Active",
            FINISHED: "Finished",
            DRAW: "Draw",
        };

        return map[status] || status || "Unknown";
    }

    function statusClass(status) {
        if (status === "ACTIVE") {
            return "status-active";
        }

        if (status === "WAITING") {
            return "status-waiting";
        }

        return "status-finished";
    }

    function normalizeList(data) {
        if (Array.isArray(data)) {
            return data;
        }

        if (data && Array.isArray(data.results)) {
            return data.results;
        }

        return [];
    }

    function roomRow(game, actionLabel, action) {
        const row = document.createElement("div");
        row.className = "room-row";

        const info = document.createElement("div");
        const title = document.createElement("strong");
        const sub = document.createElement("small");

        title.textContent =
            `${gameName(game.game_type)} · #${game.id}`;

        sub.textContent =
            `${game.player1 || "Player 1"} · ${formatStatus(game.status)}`;

        info.append(title, sub);
        row.append(info);

        if (actionLabel && action) {
            const button = document.createElement("button");
            button.type = "button";
            button.className =
                "button button-secondary button-small";
            button.textContent = actionLabel;
            button.addEventListener("click", action);
            row.append(button);
        }

        return row;
    }

    function emptyState(message) {
        const div = document.createElement("div");
        div.className = "empty-state";
        div.textContent = message;
        return div;
    }

    async function loadWaitingGames() {
        try {
            const data = await api(
                "/api/games/waiting/",
            );
            const games = normalizeList(data);

            els.waitingCount.textContent =
                String(games.length);
            els.waitingGames.replaceChildren();

            if (!games.length) {
                els.waitingGames.append(
                    emptyState(
                        "Abhi koi public waiting room nahi hai. PVP room create karo.",
                    ),
                );
                return;
            }

            games.forEach((game) => {
                const ownRoom =
                    game.player1 === state.username;

                els.waitingGames.append(
                    roomRow(
                        game,
                        ownRoom ? "Open" : "Join",
                        () => {
                            if (ownRoom) {
                                openGame(game.id);
                            } else {
                                joinGame(game.id);
                            }
                        },
                    ),
                );
            });
        } catch (error) {
            els.waitingGames.replaceChildren(
                emptyState(error.message),
            );
        }
    }

    async function loadMyGames() {
        try {
            const data = await api("/api/games/");
            const games = normalizeList(data)
                .filter((game) => (
                    game.player1 === state.username ||
                    game.player2 === state.username ||
                    game.player2 === "COMPUTER"
                ))
                .sort((a, b) => (
                    new Date(b.updated_at || b.created_at || 0) -
                    new Date(a.updated_at || a.created_at || 0)
                ))
                .slice(0, 6);

            els.myGames.replaceChildren();

            if (!games.length) {
                els.myGames.append(
                    emptyState(
                        "Tumhara koi game abhi nahi hai. Upar se start karo.",
                    ),
                );
                return;
            }

            games.forEach((game) => {
                els.myGames.append(
                    roomRow(
                        game,
                        "Open",
                        () => openGame(game.id),
                    ),
                );
            });
        } catch (error) {
            els.myGames.replaceChildren(
                emptyState(error.message),
            );
        }
    }

    async function loadDashboard() {
        await Promise.allSettled([
            loadWaitingGames(),
            loadMyGames(),
        ]);
    }

    async function createGame(
        gameType,
        mode,
    ) {
        try {
            const game = await api(
                "/api/games/",
                {
                    method: "POST",
                    body: JSON.stringify({
                        game_type: gameType,
                        mode,
                    }),
                },
            );

            showToast(
                mode === "PVP"
                    ? "PVP room created."
                    : "Game started.",
            );
            renderGame(game);
            showView("game");
            startPollingIfNeeded(game);
        } catch (error) {
            showToast(error.message);
        }
    }

    async function joinGame(id) {
        try {
            const game = await api(
                `/api/games/${id}/join/`,
                {
                    method: "POST",
                    body: JSON.stringify({}),
                },
            );

            showToast("Room joined.");
            renderGame(game);
            showView("game");
            startPollingIfNeeded(game);
        } catch (error) {
            showToast(error.message);
        }
    }

    async function openGame(id) {
        try {
            const game = await api(
                `/api/games/${id}/`,
            );

            renderGame(game);
            showView("game");
            startPollingIfNeeded(game);
        } catch (error) {
            showToast(error.message);
        }
    }

    function deriveRole(game) {
        if (game.your_role) {
            return game.your_role;
        }

        if (game.player1 === state.username) {
            return "P1";
        }

        if (game.player2 === state.username) {
            return "P2";
        }

        return null;
    }

    function isMyTurn(game) {
        if (!game || game.status !== "ACTIVE") {
            return false;
        }

        const role = deriveRole(game);
        return Boolean(
            role &&
            game.current_turn === role
        );
    }

    function gameStatusText(game) {
        if (game.status === "WAITING") {
            return "Friend ke join karne ka wait ho raha hai…";
        }

        if (game.status === "DRAW") {
            return "Match draw hua.";
        }

        if (game.status === "FINISHED") {
            if (game.winner_is_computer) {
                return "Computer won this match.";
            }

            if (game.winner) {
                return `${game.winner} won this match.`;
            }

            return "Match finished.";
        }

        if (isMyTurn(game)) {
            return "Your turn — make a move.";
        }

        if (
            game.mode === "PVC" &&
            game.current_turn === "P2"
        ) {
            return "Computer is thinking…";
        }

        return "Opponent's turn — waiting for move.";
    }

    function renderPlayers(game) {
        const role = deriveRole(game);
        const p1You = role === "P1";
        const p2You = role === "P2";

        els.playerOne.innerHTML = "";
        els.playerTwo.innerHTML = "";

        const p1Name = document.createElement("strong");
        const p1Meta = document.createElement("span");
        p1Name.textContent = game.player1 || "Player 1";
        p1Meta.textContent =
            p1You ? "Player 1 · You" : "Player 1";

        const p2Name = document.createElement("strong");
        const p2Meta = document.createElement("span");
        p2Name.textContent =
            game.player2 ||
            (game.mode === "PVC"
                ? "COMPUTER"
                : "Waiting…");
        p2Meta.textContent =
            p2You ? "Player 2 · You" : "Player 2";

        els.playerOne.append(p1Name, p1Meta);
        els.playerTwo.append(p2Name, p2Meta);
    }

    function renderGame(game) {
        state.currentGame = game;

        els.gameTitle.textContent =
            gameName(game.game_type);
        els.gameModeLabel.textContent =
            modeName(game.mode);
        els.gameTypeBadge.textContent =
            game.game_type === "BINGO"
                ? "BINGO"
                : "TIC-TAC-TOE";
        els.gameIdLabel.textContent =
            `Game #${game.id}`;

        els.statusBadge.className =
            `status-badge ${statusClass(game.status)}`;
        els.statusBadge.textContent =
            formatStatus(game.status);

        els.gameStatus.textContent =
            gameStatusText(game);

        const role = deriveRole(game);

        els.yourRoleLabel.textContent =
            role || "Spectator";
        els.turnLabel.textContent =
            game.current_turn || "—";

        renderPlayers(game);

        const isTtt =
            game.game_type === "TIC_TAC_TOE";

        els.ticTacToeArea.classList.toggle(
            "hidden",
            !isTtt,
        );
        els.bingoArea.classList.toggle(
            "hidden",
            isTtt,
        );

        if (isTtt) {
            renderTicTacToe(game);
        } else {
            renderBingo(game);
        }
    }

    function renderTicTacToe(game) {
        const board =
            game.state?.board || Array(9).fill(null);

        els.ticTacToeBoard.replaceChildren();

        for (let index = 0; index < 9; index += 1) {
            const value = board[index];
            const button = document.createElement("button");

            button.type = "button";
            button.className =
                `ttt-cell ${value ? value.toLowerCase() : ""}`;
            button.textContent = value || "";
            button.setAttribute(
                "aria-label",
                value
                    ? `Cell ${index + 1}: ${value}`
                    : `Cell ${index + 1}: empty`,
            );

            button.disabled = Boolean(
                value ||
                !isMyTurn(game) ||
                state.movePending,
            );

            button.addEventListener(
                "click",
                () => makeMove(index),
            );

            els.ticTacToeBoard.append(button);
        }
    }

    function bingoLines(board, calledNumbers) {
        if (!Array.isArray(board)) {
            return 0;
        }

        const called = new Set(calledNumbers || []);
        const lines = [];

        board.forEach((row) => lines.push(row));

        for (let column = 0; column < 5; column += 1) {
            lines.push(
                board.map((row) => row[column]),
            );
        }

        lines.push(
            board.map((row, index) => row[index]),
        );
        lines.push(
            board.map(
                (row, index) => row[4 - index],
            ),
        );

        return lines.filter((line) => (
            line.every((number) => called.has(number))
        )).length;
    }

    function getOwnBingoBoard(game) {
        const role = deriveRole(game);
        const gameState = game.state || {};

        if (role === "P2" && gameState.p2_board) {
            return gameState.p2_board;
        }

        if (role === "P1" && gameState.p1_board) {
            return gameState.p1_board;
        }

        return (
            gameState.p1_board ||
            gameState.p2_board ||
            null
        );
    }

    function renderBingo(game) {
        const board = getOwnBingoBoard(game);
        const called =
            game.state?.called_numbers || [];
        const calledSet = new Set(called);
        const lines = bingoLines(board, called);

        els.bingoLineCount.textContent =
            `${Math.min(lines, 5)} / 5 lines`;

        els.bingoLetters.replaceChildren();

        "BINGO".split("").forEach((letter, index) => {
            const span = document.createElement("span");
            span.className =
                `bingo-letter ${index < lines ? "done" : ""}`;
            span.textContent = letter;
            els.bingoLetters.append(span);
        });

        els.bingoBoard.replaceChildren();

        if (!board) {
            els.bingoBoard.append(
                emptyState(
                    "Board abhi available nahi hai.",
                ),
            );
        } else {
            board.flat().forEach((number) => {
                const isCalled = calledSet.has(number);
                const button =
                    document.createElement("button");

                button.type = "button";
                button.className =
                    `bingo-cell ${isCalled ? "called" : ""}`;
                button.textContent = String(number);
                button.disabled = Boolean(
                    isCalled ||
                    !isMyTurn(game) ||
                    state.movePending,
                );

                button.setAttribute(
                    "aria-label",
                    isCalled
                        ? `${number}, already called`
                        : `Call number ${number}`,
                );

                button.addEventListener(
                    "click",
                    () => makeMove(number),
                );

                els.bingoBoard.append(button);
            });
        }

        els.calledNumbers.replaceChildren();

        if (!called.length) {
            const span = document.createElement("span");
            span.className = "muted";
            span.textContent = "None yet";
            els.calledNumbers.append(span);
        } else {
            called.forEach((number) => {
                const span =
                    document.createElement("span");
                span.className = "called-number";
                span.textContent = String(number);
                els.calledNumbers.append(span);
            });
        }
    }

    async function makeMove(move) {
        const game = state.currentGame;

        if (
            !game ||
            !isMyTurn(game) ||
            state.movePending
        ) {
            return;
        }

        state.movePending = true;
        renderGame(game);

        try {
            const updated = await api(
                `/api/games/${game.id}/move/`,
                {
                    method: "POST",
                    body: JSON.stringify({ move }),
                },
            );

            renderGame(updated);
            startPollingIfNeeded(updated);
        } catch (error) {
            showToast(error.message);

            try {
                await refreshCurrentGame();
            } catch {
                // The original error is enough for the player.
            }
        } finally {
            state.movePending = false;

            if (state.currentGame) {
                renderGame(state.currentGame);
            }
        }
    }

    async function refreshCurrentGame() {
        if (!state.currentGame) {
            return;
        }

        const game = await api(
            `/api/games/${state.currentGame.id}/`,
        );

        renderGame(game);
        startPollingIfNeeded(game);
    }

    function stopPolling() {
        if (state.pollTimer) {
            clearInterval(state.pollTimer);
            state.pollTimer = null;
        }
    }

    function startPollingIfNeeded(game) {
        stopPolling();

        const shouldPoll =
            game &&
            game.mode === "PVP" &&
            (
                game.status === "WAITING" ||
                game.status === "ACTIVE"
            );

        if (!shouldPoll) {
            return;
        }

        state.pollTimer = setInterval(
            async () => {
                try {
                    await refreshCurrentGame();
                } catch (error) {
                    if (error.status === 401) {
                        clearSession();
                        showView("auth");
                    }
                }
            },
            1400,
        );
    }

    els.loginTab.addEventListener(
        "click",
        () => setAuthTab("login"),
    );

    els.registerTab.addEventListener(
        "click",
        () => setAuthTab("register"),
    );

    els.loginForm.addEventListener(
        "submit",
        async (event) => {
            event.preventDefault();
            els.authMessage.textContent = "";

            const username =
                $("loginUsername").value.trim();
            const password =
                $("loginPassword").value;

            try {
                await login(username, password);
            } catch (error) {
                els.authMessage.textContent =
                    error.message;
            }
        },
    );

    els.registerForm.addEventListener(
        "submit",
        async (event) => {
            event.preventDefault();
            els.authMessage.textContent = "";

            const username =
                $("registerUsername").value.trim();
            const email =
                $("registerEmail").value.trim();
            const password =
                $("registerPassword").value;

            try {
                await register(
                    username,
                    email,
                    password,
                );
            } catch (error) {
                els.authMessage.textContent =
                    error.message;
            }
        },
    );

    document
        .querySelectorAll(".create-game")
        .forEach((button) => {
            button.addEventListener(
                "click",
                () => createGame(
                    button.dataset.game,
                    button.dataset.mode,
                ),
            );
        });

    $("logoutButton").addEventListener(
        "click",
        () => {
            clearSession();
            setAuthTab("login");
            showView("auth");
        },
    );

    $("refreshLobbyButton").addEventListener(
        "click",
        loadDashboard,
    );

    $("manualRefreshButton").addEventListener(
        "click",
        async () => {
            try {
                await refreshCurrentGame();
            } catch (error) {
                showToast(error.message);
            }
        },
    );

    $("backButton").addEventListener(
        "click",
        async () => {
            state.currentGame = null;
            stopPolling();
            showView("dashboard");
            await loadDashboard();
        },
    );

    window.addEventListener(
        "beforeunload",
        stopPolling,
    );

    async function boot() {
        if (!state.access) {
            showView("auth");
            return;
        }

        updateUserBar();
        showView("dashboard");

        try {
            await loadDashboard();
        } catch {
            // Individual dashboard panels already render their own errors.
        }
    }

    boot();
})();
