from enum import Enum

class GameResult(Enum):
    NotStarted = 0
    InProgress = 1
    WhiteIsMated = 2
    BlackIsMated = 3
    Stalemate = 4
    Repetition = 5
    FiftyMoveRule = 6
    InsufficientMaterial = 7
    DrawByArbiter = 8
    WhiteTimeout = 9
    BlackTimeout = 10
    WhiteIllegalMove = 11
    BlackIllegalMove = 12