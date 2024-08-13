from gameResult import GameResult
from Move_Generation.moveGenerator import MoveGenerator
from Board.board import Board
from Helpers.boardHelpers import BoardHelper

class Arbiter:

    @staticmethod
    def is_draw_result(result):
        return result in {GameResult.DrawByArbiter, GameResult.FiftyMoveRule,
                          GameResult.Repetition, GameResult.Stalemate, GameResult.InsufficientMaterial}
    
    @staticmethod
    def is_win_result(result):
        return Arbiter.is_white_wins_result(result) or Arbiter.is_black_wins_result(result)
    
    @staticmethod
    def is_white_wins_result(result):
        return result in {GameResult.BlackIsMated, GameResult.BlackTimeout, GameResult.BlackIllegalMove}
    
    @staticmethod
    def is_black_wins_result(result):
        return result in {GameResult.WhiteIsMated, GameResult.WhiteTimeout, GameResult.WhiteIllegalMove}

    @staticmethod
    def get_game_state(board):
        move_generator = MoveGenerator()
        moves = move_generator.generate_moves(board)

        # Look for mate/stalemate
        if len(moves) == 0:
            if move_generator.is_in_check():
                return GameResult.WhiteIsMated if board.is_white_to_move else GameResult.BlackIsMated
            return GameResult.Stalemate
        
        # Fifty move rule
        if board.fifty_move_counter >= 100:
            return GameResult.FiftyMoveRule
        
        # Threefold repetition
        rep_count = sum(1 for x in board.repetition_position_history if x == board.zobrist_key)
        if rep_count == 3:
            return GameResult.Repetition
        
        # Look for insufficient material
        if Arbiter.insufficient_material(board):
            return GameResult.InsufficientMaterial
        
        return GameResult.InProgress
    
    @staticmethod
    def insufficient_material(board):
        # Can't have insufficient material with pawns on the board
        if board.pawns[Board.WhiteIndex].count > 0 or board.pawns[Board.BlackIndex].count > 0:
            return False
        
        # Can't have insufficient material with queens/rooks on the board
        if board.friendly_orthogonal_sliders != 0 or board.enemy_orthogonal_sliders != 0:
            return False
        
        # If no pawns, queens, or rooks on the board, then consider knight and bishop cases
        num_white_bishops = board.bishops[Board.WhiteIndex].count
        num_black_bishops = board.bishops[Board.BlackIndex].count
        num_white_knights = board.knights[Board.WhiteIndex].count
        num_black_knights = board.knights[Board.BlackIndex].count
        num_white_minors = num_white_bishops + num_white_knights
        num_black_minors = num_black_bishops + num_black_knights
        num_minors = num_white_minors + num_black_minors

        # Lone kings or King vs King + single minor: is insufficient
        if num_minors <= 1:
            return True
        
        # Bishop vs Bishop: is insufficient when bishops are same color complex
        if num_minors == 2 and num_white_bishops == 1 and num_black_bishops == 1:
            white_bishop_is_light_square = BoardHelper.light_square(board.bishops[Board.WhiteIndex][0])
            black_bishop_is_light_square = BoardHelper.light_square(board.bishops[Board.BlackIndex][0])
            return white_bishop_is_light_square == black_bishop_is_light_square
        
        return False