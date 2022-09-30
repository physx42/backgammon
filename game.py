# game

from enum import Enum
from main import Board
from agent import Agent


class PlayersType(Enum):
    HumanVsHuman = 0
    HumanVsRandom = 1
    HumanVsAI = 2
    RandomVsAI = 3
    AIvsAI = 4


class Game:
    def __init__(self, play_type: PlayersType):
        self.board = Board()
        if play_type == PlayersType.HumanVsAI or \
                play_type == PlayersType.RandomVsAI:
            self.p2_agent_ai = Agent(0.1, 0.01, 0.1, 0.95)
        if play_type == PlayersType.AIvsAI:
            self.p1_agent_ai = Agent(0.1, 0.01, 0.1, 0.95)
            self.p2_agent_ai = self.p1_agent_ai