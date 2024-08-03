import random
import struct
from piece import Piece

class Zobrist:
    # Random numbers are generated for each aspect of the game state, and are used for calculating the hash:

    # Piece type, color, square index
    pieces_array = [[0 for _ in range(64)] for _ in range(Piece.MaxPieceIndex + 1)]

    # Each player has 4 possible castling right states: none, queenside, kingside, both
    # So, taking both sides into account, there are 16 possible states
    castling_rights = [0] * 16

    # En passant file (0 = no ep)
    # Rank does not need to be specified since side to move is included in key
    en_passant_file = [0] * 9
    side_to_move = 0

    @staticmethod
    def initialize():
        """
        Initialize the Zobrist hash components with random 64-bit numbers
        """
        seed = 29426028
        rng = random.Random(seed)

        for square_index in range(64):
            for piece in Piece.PieceIndices:
                Zobrist.pieces_array[piece][square_index] = Zobrist.random_unsigned_64_bit_number(rng)

        for i in range(len(Zobrist.castling_rights)):
            Zobrist.castling_rights[i] = Zobrist.random_unsigned_64_bit_number(rng)

        for i in range(1, len(Zobrist.en_passant_file)):
            Zobrist.side_to_move = Zobrist.random_unsigned_64_bit_number(rng)

        Zobrist.side_to_move = Zobrist.random_unsigned_64_bit_number(rng)

    @staticmethod
    def calculate_zobrist_key(board):
        """
        Calculate Zobrist key from current board position
        NOTE: this function is slow and and should only be used when the board is initially set up from FEN
        During search, the key should be updated incrementally instead
        """
        zobrist_key = 0

        for square_index in range(64):
            piece = board.squares[square_index]

            if Piece.piece_type(piece) != Piece.NoneType:
                zobrist_key ^= Zobrist.pieces_array[piece][square_index]

        zobrist_key ^= Zobrist.en_passant_file[board.current_game_state.en_passant_file]

        if board.move_color == Piece.Black:
            zobrist_key ^= Zobrist.side_to_move

        zobrist_key = Zobrist.castling_rights[board.current_game_state.castling_rights]

        return zobrist_key
    
    @staticmethod
    def random_unsigned_64_bit_number(rng):
        """
        Generate a random 64-bit unsigned integer using the provided random number generator
        """
        buffer = bytearray(rng.getrandbits(8) for _ in range(8))
        return struct.unpack('Q', buffer)[0]