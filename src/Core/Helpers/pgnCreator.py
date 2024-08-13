from Board.board import Board
from moveUtility import MoveUtility
from fenUtility import FenUtility
from enum import Enum
from io import StringIO
from Game_Result.gameResult import GameResult

class PGNCreator:

    @staticmethod
    def create_pgn(moves, result=None, start_fen=None, white_name="", black_name=""):
        # Set default values if not provided
        if result is None:
            result = GameResult.InProgress
        if start_fen is None:
            start_fen = FenUtility.StartPositionFEN

        start_fen = start_fen.replace("\n", "").replace("\r", "")

        pgn = StringIO()
        board = Board()
        board.load_position(start_fen)

        # Headers
        if white_name:
            pgn.write(f'[White "{white_name}]\n')
        if black_name:
            pgn.write(f'[Black "{black_name}]\n')

        if start_fen != FenUtility.StartPositionFEN:
            pgn.write(f'[FEN "{start_fen}]\n')
        if result not in {GameResult.NotStarted, GameResult.InProgress}:
            pgn.write(f'[Result "{result.name}]\n')

        # Move
        for ply_count, move in enumerate(moves):
            move_string = MoveUtility.get_move_from_san(move, board)
            board.make_move(move)

            if ply_count % 2 == 0:
                pgn.write(f'{(ply_count // 2) + 1}. ')
            pgn.write(f'{move_string} ')

        return pgn.getvalue()
    
    @staticmethod
    def create_pgn_from_board(board, result, white_name="", black_name=""):
        return PGNCreator.create_pgn(
            board.all_game_moves, result, board.game_start_fen, white_name, black_name
        )