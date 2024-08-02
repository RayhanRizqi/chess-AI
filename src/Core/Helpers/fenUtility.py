from collections import namedtuple
from Board.piece import Piece
from boardHelpers import BoardHelper
from Board.coord import Coord

# Helper class for dealing with FEN strings
class FenUtility:
    StartPositionFEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

    @staticmethod
    def position_from_fen(fen):
        """
        Load position from fen string
        """
        loaded_position_info = FenUtility.PositionInfo(fen)
        return loaded_position_info
    
    @staticmethod
    def current_fen(board, always_include_ep_square=True):
        """
        Get the fen string of the current position
        When always_include_ep_square is true, the en passant square will be included
        in the fen string even if no enemy pawn is in a position to capture it
        """

        fen = ""
        for rank in range(7, -1, -1):
            num_empty_files = 0
            for file in range(8):
                i = rank * 8 + file
                piece = board.squares[i]
                if piece != 0:
                    if num_empty_files != 0:
                        fen += str(num_empty_files)
                        num_empty_files = 0
                    is_black = Piece.is_color(piece, Piece.Black)
                    piece_type = Piece.piece_type(piece)
                    piece_char = ' '
                    if piece_type == Piece.Rook:
                        piece_char = 'R'
                    elif piece_type == Piece.Knight:
                        piece_char = 'N'
                    elif piece_type == Piece.Bishop:
                        piece_type = 'B'
                    elif piece_type == Piece.Queen:
                        piece_char = 'Q'
                    elif piece_type == Piece.King:
                        piece_char = 'K'
                    elif piece_type == Piece.Pawn:
                        piece_char = 'P'

                    fen += piece_char.lower() if is_black else piece_char.upper()
                else:
                    num_empty_files += 1
                
            if num_empty_files != 0:
                fen += str(num_empty_files)
            
            if rank != 0:
                fen += '/'

        # Side to move
        fen += ' '
        fen += 'w' if board.is_white_to_move else 'b'

        # Castling
        white_kingside = (board.current_game_state.castling_rights & 1) == 1
        white_queenside = (board.current_game_state.castling_rights >> 1 & 1) == 1
        black_kingside = (board.current_game_state.castling_rights >> 2 & 1) == 1
        black_queenside = (board.current_game_state.castling_rights >> 3 & 1) == 1
        fen += ' '
        fen += 'K' if white_kingside else ''
        fen += 'Q' if white_queenside else ''
        fen += 'k' if black_kingside else ''
        fen += 'q' if black_queenside else ''
        fen += '-' if board.current_game_state.castling_rights == 0 else ''

        # En passant
        fen += ' '
        ep_file_index = board.current_game_state.en_passant_file - 1
        ep_rank_index = 5 if board.is_white_to_move else 2

        is_en_passant = ep_file_index != -1
        include_ep = always_include_ep_square or FenUtility.en_passant_can_be_captured(ep_file_index, ep_rank_index, board)
        if is_en_passant and include_ep:
            fen += BoardHelper.square_name_from_coordinate(ep_file_index, ep_rank_index)
        else:
            fen += '-'

        # 50 move counter
        fen += ' '
        fen += str(board.current_game_state.fifty_move_counter)

        # Full-move count (should be one at start, and increase after each move by black)
        fen += ' '
        fen += str((board.ply_count // 2) + 1)

        return fen
    
    @staticmethod
    def en_passant_can_be_captured(ep_file_index, ep_rank_index, board):
        capture_from_a = Coord(ep_file_index - 1, ep_rank_index + (-1 if board.is_white_to_move else 1))
        capture_from_b = Coord(ep_file_index + 1, ep_rank_index + (-1 if board.is_white_to_move else 1))
        ep_capture_square = Coord(ep_file_index, ep_rank_index).square_index
        friendly_pawn = Piece.make_piece(Piece.Pawn, board.move_color)

        def can_capture(from_coord):
            if from_coord.is_valid_square() and board.squares[from_coord.square_index] == friendly_pawn:
                move = Move(from_coord.square_index, ep_capture_square, Move.EnPassantCaptureFlag)
                board.make_move(move)
                board.make_null_move()
                was_legal_move = not board.calculate_in_check_state()

                board.unmake_null_move()
                board.unmake_move(move)
                return was_legal_move
            return False
        
        return can_capture(capture_from_a) or can_capture(capture_from_b)
    
    @staticmethod
    def flip_fen(fen):
        flipped_fen = ""
        sections = fen.split(' ')

        inverted_fen_chars = []
        fen_ranks = sections[0].split('/')

        for i in range(len(fen_ranks) - 1, -1, -1):
            rank = fen_ranks[i]
            for c in rank:
                flipped_fen += invert_case(c)
            if i != 0:
                flipped_fen += '/'

        flipped_fen += " " + ('b' if sections[1][0] == 'w' else 'w')
        castling_rights = sections[2]
        flipped_rights = ""
        for c in "kqKQ":
            if c in castling_rights:
                flipped_rights += invert_case(c)
        flipped_fen += " " + ("-" if len(flipped_rights) == 0 else flipped_rights)

        ep = sections[3]
        flipped_ep = ep[0] + ""
        if len(ep) > 1:
            flipped_ep += '3' if ep[1] == '6' else '6'
        flipped_fen += " " + flipped_ep
        flipped_fen += " " + sections[4] + " " + sections[5]

        def invert_case(c):
            if c.islower():
                return c.upper()
            return c.lower()
        
        return flipped_fen
    
        
    class PositionInfo:
        """
        Read-only structure for storing detailed information about a chess position from a fen string
        """
        def __init__(self, fen):
            self.fen = fen
            square_pieces = [0] * 64

            sections = fen.split(' ')

            file = 0
            rank = 7

            for symbol in sections[0]:
                if symbol == '/':
                    file = 0
                    rank -= 1
                else:
                    if symbol.isdigit():
                        file += int(symbol)
                    else:
                        piece_color = Piece.White if symbol.isupper() else Piece.Black
                        piece_type = {
                            'k': Piece.King,
                            'p': Piece.Pawn,
                            'n': Piece.Knight,
                            'b': Piece.Bishop,
                            'r': Piece.Rook,
                            'q': Piece.Queen
                        }.get(symbol.lower(), Piece.NoneType)

                        square_pieces[rank * 8 + file] = piece_type | piece_color
                        file += 1

            self.squares = tuple(square_pieces)

            self.white_to_move = sections[1] == "w"

            castling_rights = sections[2]
            self.white_castle_kingside = 'K' in castling_rights
            self.white_castle_queenside = 'Q' in castling_rights
            self.black_castle_kingside = 'k' in castling_rights
            self.black_castle_queenside = 'q' in castling_rights

            # Default values
            self.ep_file = 0
            self.fifty_move_ply_count = 0
            self.move_count = 0

            if len(sections) > 3:
                en_passant_file_name = sections[3][0]
                if en_passant_file_name in BoardHelper.file_names:
                    self.ep_file = BoardHelper.file_names.index(en_passant_file_name) + 1

            # Half-move clock
            if len(sections) > 4:
                self.fifty_move_ply_count = int(sections[4])

            # Full move number
            if len(sections) > 5:
                self.move_count = int(sections[5])