from piece import Piece
from pieceList import PieceList
from gameState import GameState
from Helpers.fenUtility import FenUtility
from move import Move
from Move_Generation.Bitboards.bitBoardUtility import BitBoardUtility
from zobrist import Zobrist
from Helpers.boardHelpers import BoardHelper
from Move_Generation.Magics.magic import Magic

class Board:
    """
    Represents the current state of the board during a game
    The state includes things such as: positions of all pieces, side to move,
    castling rights, en-passant square, etc. Some extra information is included
    as well to help with evaluation and move generation.

    The initial state of the board can be set from a FEN string, and mvoes are 
    subsequently made (or undone) using the make_move and unmake_move functions.
    """
    WhiteIndex = 0
    BlackIndex = 1

    def __init__(self):
        # Stores piece code for each square on the board
        self.square = [Piece.NoneType] * 64

        # Square index of white and black king
        self.king_square = [0, 0]

        # Bitboards
        # Bitboards for each piece type and color (white pawns, white knights, ... black pawns, etc.)
        self.piece_bitboards = [0] * (Piece.MaxPieceIndex + 1)

        # Bitboards for all pieces of either color (all white pieces, all black pieces)
        self.color_bitboards = [0, 0]
        self.all_pieces_bitboard = 0
        self.friendly_orthogonal_sliders = 0
        self.friendly_diagonal_sliders = 0
        self.enemy_orthogonal_sliders = 0
        self.enemy_diagonal_sliders = 0

        # Piece count excluding pawns and kings
        self.total_piece_count_without_pawns_and_kings = 0

        # Piece lists
        self.rooks = [PieceList(10), PieceList(10)]
        self.bishops = [PieceList(10), PieceList(10)]
        self.queens = [PieceList(9), PieceList(9)]
        self.knights = [PieceList(10), PieceList(10)]
        self.pawns = [PieceList(8), PieceList(8)]

        # Side to move info
        self.is_white_to_move = True
        self.repetition_position_history = []

        # Total plies (half-moves) played in game
        self.ply_count = 0
        self.all_game_moves = []

        # Private stuff
        self.all_piece_lists = [None] * (Piece.MaxPieceIndex + 1)
        self.game_state_history = []
        self.start_position_info = None
        self.cached_in_check_value = False
        self.has_cached_in_check_value = False

        # Initialize the piece lists
        self.all_piece_lists[Piece.WhitePawn] = self.pawns[self.WhiteIndex]
        self.all_piece_lists[Piece.WhiteKnight] = self.knights[self.WhiteIndex]
        self.all_piece_lists[Piece.WhiteBishop] = self.bishops[self.WhiteIndex]
        self.all_piece_lists[Piece.WhiteRook] = self.rooks[self.WhiteIndex]
        self.all_piece_lists[Piece.WhiteQueen] = self.queens[self.WhiteIndex]
        self.all_piece_lists[Piece.WhiteKing] = PieceList(1)

        self.all_piece_lists[Piece.BlackPawn] = self.pawns[self.BlackIndex]
        self.all_piece_lists[Piece.BlackKnight] = self.knights[self.BlackIndex]
        self.all_piece_lists[Piece.BlackBishop] = self.bishops[self.BlackIndex]
        self.all_piece_lists[Piece.BlackRook] = self.rooks[self.BlackIndex]
        self.all_piece_lists[Piece.BlackQueen] = self.queens[self.BlackIndex]
        self.all_piece_lists[Piece.BlackKing] = PieceList(1)

        # Initialize bitboards
        self.piece_bitboards = [0] * (Piece.MaxPieceIndex + 1)
        self.color_bitboards = [0, 0]
        self.all_pieces_bitboard = 0

        # Initialize game state
        self.current_game_state = GameState()
        self.initialize()

    @property
    def move_color(self):
        return Piece.White if self.is_white_to_move else Piece.Black
    
    @property
    def opponent_color(self):
        return Piece.Black if self.is_white_to_move else Piece.White
    
    @property
    def move_color_index(self):
        return self.WhiteIndex if self.is_white_to_move else self.BlackIndex
    
    @property
    def opponent_color_index(self):
        return self.BlackIndex if self.is_white_to_move else self.WhiteIndex
    
    @property
    def fifty_move_counter(self):
        return self.current_game_state.fifty_move_counter
    
    @property
    def zobrist_key(self):
        return self.current_game_state.zobrist_key
    
    @property
    def current_fen(self):
        return FenUtility.current_fen(self)
    
    @property
    def game_start_fen(self):
        return self.start_position_info.fen
    
    def make_move(self, move, in_search=False):
        """
        Make a move on the board.
        The inSearch parameter controls whether this move should be recorded in the game history
        (for detecting three-fold repetition)
        """
        # Get info about move
        start_square = move.start_square
        target_square = move.target_square
        move_flag = move.move_flag
        is_promotion = move.is_promotion
        is_en_passant = move_flag == Move.EnPassantCaptureFlag

        moved_piece = self.square[start_square]
        moved_piece_type = Piece.piece_type(moved_piece)
        captured_piece = self.square[target_square] if not is_en_passant else Piece.make_piece(Piece.Pawn, self.opponent_color)
        captured_piece_type = Piece.piece_type(captured_piece)

        prev_castle_state = self.current_game_state.castling_rights
        prev_en_passant_file = self.current_game_state.en_passant_file
        new_zobrist_key = self.current_game_state.zobrist_key
        new_castling_rights = self.current_game_state.castling_rights
        new_en_passant_file = 0

        # Update bitboard of moved piece (pawn promotion is a special case and is corrected later)
        self.move_piece(moved_piece, start_square, target_square)

        # Handle captures
        if captured_piece_type != Piece.NoneType:
            capture_square = target_square

            if is_en_passant:
                capture_square = target_square + (-8 if self.is_white_to_move else 8)
                self.square[capture_square] = Piece.NoneType

            if captured_piece_type != Piece.Pawn:
                self.total_piece_count_without_pawns_and_kings -= 1

            # Remove captured piece from bitboards/piece list
            self.all_piece_lists[captured_piece].remove_piece_at_square(capture_square)
            BitBoardUtility.toggle_square(self.piece_bitboards, captured_piece, capture_square)
            BitBoardUtility.toggle_square(self.color_bitboards, self.opponent_color_index, capture_square)
            new_zobrist_key ^= Zobrist.pieces_array[captured_piece][capture_square]

        # Handle King
        if moved_piece_type == Piece.King:
            self.king_square[self.move_color_index] = target_square
            new_castling_rights &= 0b1100 if self.is_white_to_move else 0b0011

            # Handle castling
            if move_flag == Move.CastleFlag:
                rook_piece = Piece.make_piece(Piece.Rook, self.move_color)
                kingside = target_square in (BoardHelper.g1, BoardHelper.g8)
                castling_rook_from_index = target_square + 1 if kingside else target_square - 2
                castling_rook_to_index = target_square - 1 if kingside else target_square + 1

                # Update rook position
                BitBoardUtility.toggle_squares(self.piece_bitboards, rook_piece, castling_rook_from_index, castling_rook_to_index)
                BitBoardUtility.toggle_squares(self.color_bitboards, self.move_color_index, castling_rook_from_index, castling_rook_to_index)
                self.all_piece_lists[rook_piece].move_piece(castling_rook_from_index, castling_rook_to_index)
                self.square[castling_rook_from_index] = Piece.NoneType
                self.square[castling_rook_to_index] = Piece.Rook | self.move_color

                new_zobrist_key ^= Zobrist.pieces_array[rook_piece][castling_rook_from_index]
                new_zobrist_key ^= Zobrist.pieces_array[rook_piece][castling_rook_to_index]
        
        # Handle promotion
        if is_promotion:
            self.total_piece_count_without_pawns_and_kings += 1
            promotion_piece_type = {
                Move.PromoteToQueenFlag: Piece.Queen,
                Move.PromoteToRookFlag: Piece.Rook, 
                Move.PromoteToKnightFlag: Piece.Knight,
                Move.PromoteToBishopFlag: Piece.Bishop
            }.get(move_flag, 0)

            promotion_piece = Piece.make_piece(promotion_piece_type, self.move_color)

            # Remove pawn from promotion square and add promoted piece instead
            BitBoardUtility.toggle_square(self.piece_bitboards, moved_piece, target_square)
            BitBoardUtility.toggle_square(self.piece_bitboards, promotion_piece, target_square)
            self.all_piece_lists[moved_piece].remove_piece_at_square(target_square)
            self.all_piece_lists[promotion_piece].add_piece_at_square(target_square)
            self.square[target_square] = promotion_piece

        # Pawn has moved two forwards, mark file with en-passant flag
        if move_flag == Move.PawnTwoUpFlag:
            file = BoardHelper.file_index(start_square) + 1
            new_en_passant_file = file
            new_zobrist_key ^= Zobrist.en_passant_file[file]

        # Update castling rights
        if prev_castle_state != 0:
            # Any piece moving to/from rook square removes castling right for that side
            if target_square in (BoardHelper.h1, start_square == BoardHelper.h1):
                new_castling_rights &= GameState.ClearWhiteKingsideMask
            elif target_square in (BoardHelper.a1, start_square == BoardHelper.a1):
                new_castling_rights &= GameState.ClearWhiteQueensideMask
            if target_square in (BoardHelper.h8, start_square == BoardHelper.h8):
                new_castling_rights &= GameState.ClearBlackKingsideMask
            elif target_square in (BoardHelper.a8, start_square == BoardHelper.a8):
                new_castling_rights &= GameState.ClearBlackQueensideMask

        # Update zobrist key with new piece position and side to move
        new_zobrist_key ^= Zobrist.side_to_move
        new_zobrist_key ^= Zobrist.pieces_array[moved_piece][start_square]
        new_zobrist_key ^= Zobrist.pieces_array[self.square[target_square]][target_square]
        new_zobrist_key ^= Zobrist.en_passant_file[prev_en_passant_file]

        if new_castling_rights != prev_castle_state:
            new_zobrist_key ^= Zobrist.castling_rights[prev_castle_state] # remove old castling rights state
            new_zobrist_key ^= Zobrist.castling_rights[new_castling_rights] # add new castling rights state

        # Change side to move
        self.is_white_to_move = not self.is_white_to_move

        self.ply_count += 1
        new_fifty_move_counter = self.current_game_state.fifty_move_counter + 1

        # Update extra bitboards
        self.all_pieces_bitboard = self.color_bitboards[self.WhiteIndex] | self.color_bitboards[self.BlackIndex]
        self.update_slider_bitboards()

        # Pawn moves and captures reset the fifty move counter and clear 3-fold repetition history
        if moved_piece_type == Piece.Pawn or captured_piece_type != Piece.NoneType:
            if not in_search:
                self.repetition_position_history.clear()
            new_fifty_move_counter = 0

        # Create and save the new game state
        new_state = GameState(captured_piece_type, new_en_passant_file, new_castling_rights, new_fifty_move_counter, new_zobrist_key)
        self.game_state_history.append(new_state)
        self.current_game_state = new_state
        self.has_cached_in_check_value = False

        if not in_search:
            self.repetition_position_history.append(new_state.zobrist_key)
            self.all_game_moves.append(move)

    def unmake_move(self, move, in_search=False):
        """
        Undo a move previously made on the board
        The in_search parameter controls whether this move should be recorded in game history
        """
        # Swap color to move
        self.is_white_to_move = not self.is_white_to_move

        undoing_white_move = self.is_white_to_move

        # Get move info
        moved_from = move.start_square
        moved_to = move.target_square
        move_flag = move.move_flag

        undoing_en_passant = move_flag == Move.EnPassantCaptureFlag
        undoing_promotion = move.is_promotion
        undoing_capture = self.current_game_state.captured_piece_type != Piece.NoneType

        moved_piece = Piece.make_piece(Piece.Pawn, self.move_color) if undoing_promotion else self.square[moved_to]
        moved_piece_type = Piece.piece_type(moved_piece)
        captured_piece_type = self.current_game_state.captured_piece_type

        # If undoing promotion, then remove piece from promotion square and replace with pawn
        if undoing_promotion:
            promoted_piece = self.square[moved_to]
            pawn_piece = Piece.make_piece(Piece.Pawn, self.move_color)
            self.total_piece_count_without_pawns_and_kings -= 1

            self.all_piece_lists[promoted_piece].remove_piece_at_square(moved_to)
            self.all_piece_lists[moved_piece].add_piece_at_square(moved_to)
            self.piece_bitboards[promoted_piece] = BitBoardUtility.toggle_square(self.piece_bitboards[promoted_piece], moved_to)
            self.piece_bitboards[pawn_piece] = BitBoardUtility.toggle_square(self.piece_bitboards[pawn_piece], moved_to)

        # Move the piece back to its original square
        self.move_piece(moved_piece, moved_to, moved_from)

        # Undo capture
        if undoing_capture:
            capture_square = moved_to
            captured_piece = Piece.make_piece(captured_piece_type, self.opponent_color)

            if undoing_en_passant:
                capture_square = moved_to + (-8 if undoing_white_move else 8)

            if captured_piece_type != Piece.Pawn:
                self.total_piece_count_without_pawns_and_kings += 1

            # Add back captured piece
            self.piece_bitboards[captured_piece] = BitBoardUtility.toggle_square(self.piece_bitboards[captured_piece], capture_square)
            self.colour_bitboards[self.opponent_colour_index] = BitBoardUtility.toggle_square(self.colour_bitboards[self.opponent_colour_index], capture_square)
            self.all_piece_lists[captured_piece].add_piece_at_square(capture_square)
            self.square[capture_square] = captured_piece

        # Update king's position
        if moved_piece_type == Piece.King:
            self.king_square[self.move_color_index] = moved_from

            # Undo castling
            if move_flag == Move.CastleFlag:
                rook_piece = Piece.make_piece(Piece.Rook, self.move_color)
                kingside = moved_to in (BoardHelper.g1, BoardHelper.g8)
                rook_square_before_castling = moved_to + 1 if kingside else moved_to - 2
                rook_square_after_castling = moved_to - 1 if kingside else moved_to + 1

                # Undo castling by returning rook to original square
                self.piece_bitboards[rook_piece] == BitBoardUtility.toggle_squares(
                    self.piece_bitboards[rook_piece], rook_square_after_castling, rook_square_before_castling
                )
                self.color_bitboards[self.move_color_index] = BitBoardUtility.toggle_squares(
                    self.color_bitboards[self.move_color_index], rook_square_after_castling, rook_square_before_castling
                )
                self.square[rook_square_after_castling] = Piece.NoneType
                self.square[rook_square_before_castling] = rook_piece
                self.all_piece_lists[rook_piece].move_piece(rook_square_after_castling, rook_square_before_castling)

        # Update all pieces bitboard and slider bitboards
        self.all_pieces_bitboard = self.color_bitboards[self.WhiteIndex] | self.color_bitboards[self.BlackIndex]
        self.update_slider_bitboards()

        if not in_search and self.repetition_position_history:
            self.repetition_position_history.pop()

        if not in_search:
            self.all_game_moves.pop()

        # Go back to the previous state
        self.game_state_history.pop()
        self.current_game_state = self.game_state_history[-1]
        self.ply_count -= 1
        self.has_cached_in_check_value = False

    def make_null_move(self):
        """
        Switch side to play without making a move (NOTE: must not be in check when called)
        """
        self.is_white_to_move = not self.is_white_to_move

        self.ply_count += 1

        new_zobrist_key = self.current_game_state.zobrist_key
        new_zobrist_key ^= Zobrist.side_to_move
        new_zobrist_key ^= Zobrist.en_passant_file[self.current_game_state.en_passant_file]

        new_state = GameState(Piece.NoneType, 0, self.current_game_state.castling_rights, 
                              self.current_game_state.fifty_move_counter + 1, new_zobrist_key)
        self.current_game_state = new_state
        self.game_state_history.append(self.current_game_state)
        self.update_slider_bitboards()
        self.has_cached_in_check_value = True
        self.cached_in_check_value = False

    def unmake_null_move(self):
        """
        Undo the null move and restore the previous game state
        """
        self.is_white_to_move = not self.is_white_to_move
        self.ply_count -= 1
        self.game_state_history.pop()
        self.current_game_state = self.game_state_history[-1]
        self.update_slider_bitboards()
        self.has_cached_in_check_value = True
        self.cached_in_check_value = False

    def is_in_check(self):
        """
        Check if the current player is in check
        """
        if self.has_cached_in_check_value:
            return self.cached_in_check_value
        
        self.cached_in_check_value = self.calculate_in_check_state()
        self.has_cached_in_check_value = True
        return self.cached_in_check_value
    
    def calculate_in_check_state(self):
        """
        Calculate if the current player is in check. Call is_in_check instead for automatic caching
        """
        king_square = self.king_square[self.move_color_index]
        blockers = self.all_pieces_bitboard

        if self.enemy_orthogonal_sliders:
            rook_attacks = Magic.get_rook_attacks(king_square, blockers)
            if rook_attacks & self.enemy_orthogonal_sliders:
                return True
            
        if self.enemy_diagonal_sliders:
            bishop_attacks = Magic.get_bishop_attacks(king_square, blockers)
            if bishop_attacks & self.enemy_diagonal_sliders:
                return True
            
        enemy_knights = self.piece_bitboards[Piece.make_piece(Piece.Knight, self.opponent_color)]
        if BitBoardUtility.KnightAttacks[king_square] & enemy_knights:
            return True
        
        enemy_pawns = self.piece_bitboards[Piece.make_piece(Piece.Pawn, self.opponent_color)]
        pawn_attack_mask = BitBoardUtility.WhitePawnAttacks[king_square] if self.is_white_to_move else BitBoardUtility.BlackPawnAttacks[king_square]
        if pawn_attack_mask & enemy_pawns:
            return True
        
        return False
    
    def load_start_position(self):
        """
        Load the starting position on the board
        """
        self.load_position(FenUtility.StartPositionFEN)

    def load_position(self, fen):
        """
        Load the position on the board from a FEN string
        """
        pos_info = FenUtility.position_from_fen(fen)
        self.load_position_info(pos_info)

    def load_position_info(self, pos_info):
        """
        Load the position on the board from a PositionInfo object
        """
        self.start_position_info = pos_info
        self.initialize()

        # Load pieces into board array and piece lists
        for square_index in range(64):
            piece = pos_info.squares[square_index]
            piece_type = Piece.piece_type(piece)
            color_index = Board.WhiteIndex if Piece.is_white(piece) else Board.BlackIndex
            self.square[square_index] = piece

            if piece != Piece.NoneType:
                BitBoardUtility.set_square(self.piece_bitboards[piece], square_index)
                BitBoardUtility.set_square(self.color_bitboards[color_index], square_index)

                if piece_type == Piece.King:
                    self.king_square[color_index] = square_index
                else:
                    self.all_piece_lists[piece].add_piece_at_square(square_index)

                self.total_piece_count_without_pawns_and_kings += (0 if piece_type in (Piece.Pawn, Piece.King) else 1)

        # Side to move
        self.is_white_to_move = pos_info.white_to_move

        # Set extra bitboards
        self.all_pieces_bitboard = self.color_bitboards[Board.WhiteIndex] | self.color_bitboards[Board.BlackIndex]
        self.update_slider_bitboards()

        # Create gamestate
        white_castle = ((1 << 0) if pos_info.white_castle_kingside else 0) | ((1 << 1) if pos_info.white_castle_queenside else 0)
        black_castle = ((1 << 2) if pos_info.black_castle_kingside else 0) | ((1 << 3) if pos_info.black_castle_queenside else 0)
        castling_rights = white_castle | black_castle

        self.ply_count = (pos_info.move_count - 1) * 2 + (0 if self.is_white_to_move else 1)

        # Set game state (note: calculating zobrist key relies on current game state)
        self.current_game_state = GameState(Piece.NoneType, pos_info.ep_file, castling_rights, pos_info.fifty_move_ply_count, 0)
        zobrist_key = Zobrist.calculate_zobrist_key(self)
        self.current_game_state = GameState(Piece.NoneType, pos_info.ep_file, castling_rights, pos_info.fifty_move_ply_count, zobrist_key)

        self.repetition_position_history.append(zobrist_key)
        self.game_state_history.append(self.current_game_state)

    def __str__(self):
        """
        Return a string representation of the board
        """
        return BoardHelper.create_diagram(self, self.is_white_to_move)
    
    @staticmethod
    def create_board(fen=FenUtility.StartPositionFEN):
        """
        Create a new board initialized with the given FEN string
        """
        board = Board()
        board.load_position(fen)
        return board
    
    @staticmethod
    def create_board_from_source(source):
        """
        Create a new board initialized as a copy of another board
        """
        board = Board()
        board.load_position_info(source.start_position_info)

        for move in source.all_game_moves:
            board.make_move(move)

        return board
    
    def move_piece(self, piece, start_square, target_square):
        """
        Update piece lists / bitboards based on the given move info
        Note that this does not account for:
        1. Removal of a captured piece
        2. Movement of rook when castling
        3. Removal of pawn from 1st/8th rank during pawn promotion
        4. Addition of promoted piece during pawn promotion
        """
        self.piece_bitboards[piece] = BitBoardUtility.toggle_squares(self.piece_bitboards[piece], start_square, target_square)
        self.colour_bitboards[self.move_colour_index] = BitBoardUtility.toggle_squares(self.colour_bitboards[self.move_colour_index], start_square, target_square)

        self.all_piece_lists[piece].move_piece(start_square, target_square)
        self.square[start_square] = Piece.NoneType
        self.square[target_square] = piece

    def update_slider_bitboards(self):
        """
        Update the bitboards for sliding pieces (rooks, bishops, queens)
        """
        friendly_rook = Piece.make_piece(Piece.Rook, self.move_color)
        friendly_queen = Piece.make_piece(Piece.Queen, self.move_color)
        friendly_bishop = Piece.make_piece(Piece.Bishop, self.move_color)
        self.friendly_orthogonal_sliders = self.piece_bitboards[friendly_rook] | self.piece_bitboards[friendly_queen]
        self.friendly_diagonal_sliders = self.piece_bitboards[friendly_bishop] | self.piece_bitboards[friendly_queen]

        enemy_rook = Piece.make_piece(Piece.Rook, self.opponent_color)
        enemy_queen = Piece.make_piece(Piece.Queen, self.opponent_color)
        enemy_bishop = Piece.make_piece(Piece.Bishop, self.opponent_color)
        self.enemy_orthogonal_sliders = self.piece_bitboards[enemy_rook] | self.piece_bitboards[enemy_queen]
        self.enemy_diagonal_sliders = self.piece_bitboards[enemy_bishop] | self.piece_bitboards[enemy_queen]

    def initialize(self):
        """
        Initialize the board, setting up the necessary data structures and bitboards
        """
        self.all_game_moves = []
        self.king_square = [0, 0]
        self.square = [Piece.NoneType] * 64

        self.repetition_position_history = []
        self.game_state_history = []

        self.current_game_state = GameState()
        self.ply_count = 0

        self.knights = [PieceList(10), PieceList(10)]
        self.pawns = [PieceList(8), PieceList(8)]
        self.rooks = [PieceList(10), PieceList(10)]
        self.bishops = [PieceList(10), PieceList(10)]
        self.queens = [PieceList(9), PieceList(9)]

        self.all_piece_lists = [None] * (Piece.MaxPieceIndex + 1)
        self.all_piece_lists[Piece.WhitePawn] = self.pawns[self.WhiteIndex]
        self.all_piece_lists[Piece.WhiteKnight] = self.knights[self.WhiteIndex]
        self.all_piece_lists[Piece.WhiteBishop] = self.bishops[self.WhiteIndex]
        self.all_piece_lists[Piece.WhiteRook] = self.rooks[self.WhiteIndex]
        self.all_piece_lists[Piece.WhiteQueen] = self.queens[self.WhiteIndex]
        self.all_piece_lists[Piece.WhiteKing] = PieceList(1)

        self.all_piece_lists[Piece.BlackPawn] = self.pawns[self.BlackIndex]
        self.all_piece_lists[Piece.BlackKnight] = self.knights[self.BlackIndex]
        self.all_piece_lists[Piece.BlackBishop] = self.bishops[self.BlackIndex]
        self.all_piece_lists[Piece.BlackRook] = self.rooks[self.BlackIndex]
        self.all_piece_lists[Piece.BlackQueen] = self.queens[self.BlackIndex]
        self.all_piece_lists[Piece.BlackKing] = PieceList(1)

        self.total_piece_count_without_pawns_and_kings = 0

        # Initialize bitboards
        self.piece_bitboards = [0] * (Piece.MaxPieceIndex + 1)
        self.colour_bitboards = [0, 0]
        self.all_pieces_bitboard = 0