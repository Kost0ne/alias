from __future__ import annotations

import random
import string
from typing import Dict, List, Optional

from nicegui import ui, app
from fastapi import FastAPI

app_instance = FastAPI()
app.native.fastapi_app.mount('/api', app_instance)

# Simple in-memory store for lobbies
lobbies: Dict[str, 'Lobby'] = {}

# Predefined word list (could be extended or loaded from file)
DEFAULT_WORDS = [
    'python', 'fastapi', 'framework', 'socket', 'database', 'server', 'client',
    'interface', 'package', 'function', 'variable', 'class', 'object', 'thread'
]


class Player:
    def __init__(self, name: str, sid: str):
        self.name = name
        self.sid = sid
        self.team: int | None = None


class Lobby:
    ROUND_DURATION = 60

    def __init__(self, lobby_id: str, host_sid: str) -> None:
        self.id = lobby_id
        self.host_sid = host_sid
        self.players: Dict[str, Player] = {}
        self.started = False
        self.current_team = 0
        self.scores = [0, 0]
        self.words = DEFAULT_WORDS.copy()
        random.shuffle(self.words)
        self.word_index = 0
        self.current_word: Optional[str] = None
        self.time_left = Lobby.ROUND_DURATION
        self.current_explainer: Optional[str] = None
        self.timer_handle: Optional[object] = None
        self.explainer_index = 0

    def next_word(self) -> str:
        if self.word_index >= len(self.words):
            self.word_index = 0
            random.shuffle(self.words)
        word = self.words[self.word_index]
        self.word_index += 1
        self.current_word = word
        return word

    def choose_explainer(self) -> None:
        team_players = [p.sid for p in self.players.values() if p.team == self.current_team]
        if not team_players:
            self.current_explainer = None
            return
        self.current_explainer = team_players[self.explainer_index % len(team_players)]
        self.explainer_index += 1

    def start_round(self) -> None:
        if self.started:
            return
        self.started = True
        self.time_left = Lobby.ROUND_DURATION
        self.choose_explainer()
        self.next_word()
        self.timer_handle = ui.timer(1.0, lambda: self.tick())

    def tick(self) -> None:
        self.time_left -= 1
        if self.time_left <= 0:
            self.end_round()

    def end_round(self) -> None:
        if self.timer_handle:
            self.timer_handle.cancel()
            self.timer_handle = None
        self.started = False
        self.current_word = None
        self.current_explainer = None
        self.time_left = Lobby.ROUND_DURATION
        self.current_team = 1 - self.current_team

    def guess(self) -> None:
        self.scores[self.current_team] += 1
        self.next_word()

    def skip(self) -> None:
        self.next_word()


@ui.page('/')
async def index_page() -> None:
    with ui.column().classes('w-full items-center justify-center'):
        ui.label('Alias Game').classes('text-2xl')
        ui.button('Create Lobby', on_click=create_lobby)


async def create_lobby() -> None:
    lobby_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    ui.navigate(f'/lobby/{lobby_id}')


def get_lobby(lobby_id: str) -> Lobby | None:
    return lobbies.get(lobby_id)


@ui.page('/lobby/{lobby_id}')
async def lobby_page(lobby_id: str) -> None:
    lobby = get_lobby(lobby_id)
    if lobby is None:
        # Create new lobby if not exists
        lobby = Lobby(lobby_id, ui.context.session_id)
        lobbies[lobby_id] = lobby

    if ui.context.session_id not in lobby.players:
        name_input = ui.input('Enter your name').classes('w-64')
        ui.button('Join', on_click=lambda: join_lobby(name_input.value, lobby))
        return
    player = lobby.players[ui.context.session_id]

    def start_round() -> None:
        lobby.start_round()

    def guess() -> None:
        if lobby.started and lobby.current_explainer == ui.context.session_id:
            lobby.guess()

    def skip() -> None:
        if lobby.started and lobby.current_explainer == ui.context.session_id:
            lobby.skip()

    word_label = ui.label('').classes('text-2xl')
    score_label = ui.label('')
    timer_label = ui.label('')

    def update() -> None:
        if lobby.started:
            if lobby.current_explainer == ui.context.session_id:
                word_label.text = lobby.current_word or ''
            else:
                word_label.text = 'Идет ход другой команды'
        else:
            word_label.text = 'Раунд не запущен'
        score_label.text = f'A: {lobby.scores[0]}  B: {lobby.scores[1]}'
        timer_label.text = f'Осталось: {lobby.time_left}s'

    ui.timer(1.0, update)

    with ui.column() as column:
        ui.label(f'Lobby {lobby_id}').classes('text-xl')
        ui.label(f'Player: {player.name}')
        ui.label(f'Team: {player.team}').bind_text_from(player, 'team')

        if not lobby.started and ui.context.session_id == lobby.host_sid:
            ui.button('Start Round', on_click=start_round)
        with ui.row():
            ui.button('Guess', on_click=guess)
            ui.button('Skip', on_click=skip)
        word_label
        score_label
        timer_label


async def join_lobby(name: str, lobby: Lobby) -> None:
    player = Player(name, ui.context.session_id)
    lobby.players[ui.context.session_id] = player
    # balance teams by assigning the player to the team with fewer members
    team_a = len([p for p in lobby.players.values() if p.team == 0])
    team_b = len([p for p in lobby.players.values() if p.team == 1])
    player.team = 0 if team_a <= team_b else 1
    await ui.navigate(f'/lobby/{lobby.id}')


ui.run(reload=False)
