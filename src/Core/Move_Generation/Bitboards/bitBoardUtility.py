import numpy as np

class BitBoardUtility:
    # Constants representing files and ranks
    FileA = 0x101010101010101

    Rank1 = 0b11111111
    Rank2 = Rank1 << 8
    Rank3 = Rank2 << 8
    Rank4 = Rank3 << 8
    Rank5 = Rank4 << 8
    Rank6 = Rank5 << 8
    Rank7 = Rank6 << 8
    Rank8 = Rank7 << 8

    notAFile = ~FileA & ((1 << 64) - 1) # Masking to ensure 64-bit
    notHFile = ~(FileA << 7) & ((1 << 64) - 1) # Masking to ensure 64 bit

    # Static variables for attack bitboards
    KnightAttacks = [0] * 64
    KingMoves = [0] * 64
    WhitePawnAttacks = [0] * 64
    BlackPawnAttacks = [0] * 64

    @staticmethod
    def pop_lsb(bitboard):
        """
        Get index of least significant set bit in given 64bit value. Also clears the bit to zero
        """
        if bitboard == 0:
            return -1
        
        lsb_index = (bitboard & -bitboard).bit_length() - 1
        bitboard &= bitboard - 1
        return lsb_index
    
    @staticmethod
    def set_square(bitboard, square_index):
        """
        Set the bit at the square index
        """
        return bitboard | (1 << square_index)
    
    @staticmethod
    def clear_square(bitboard, square_index):
        """
        Clear the bit at the square index
        """
        return bitboard & ~(1 << square_index)
    
    @staticmethod
    def toggle_square(bitboard, square_index):
        """
        Toggle the bit at the square index
        """
        return bitboard ^ (1 << square_index)
    
    @staticmethod
    def toggle_squares(bitboard, square_a, square_b):
        """
        Toggle the bits at the two square indices
        """
        return bitboard ^ ((1 << square_a) | (1 << square_b))
    
    @staticmethod
    def contains_square(bitboard, square):
        """
        Check if the bitboard contains the given square
        """
        return ((bitboard >> square) & 1) != 0
    
    @staticmethod
    def pawn_attacks(pawn_bitboard, is_white):
        """
        Calculate pawn attacks
        """
        if is_white:
            return ((pawn_bitboard << 9) & BitBoardUtility.notAFile) | ((pawn_bitboard << 7) & BitBoardUtility.notHFile)
        else:
            return ((pawn_bitboard >> 7) & BitBoardUtility.notAFile) | ((pawn_bitboard >> 9) & BitBoardUtility.notHFile)
    
    @staticmethod
    def shift(bitboard, num_squares_to_shift):
        """
        Shift the bitboard by the specified number of squares
        """
        if num_squares_to_shift > 0:
            return bitboard << num_squares_to_shift
        else:
            return bitboard >> -num_squares_to_shift
        
    @staticmethod
    def initialize():
        """
        Initialize the attack bitboards for knights, kings, and pawns
        """
        ortho_dir = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        diag_dir = [(-1, -1), (-1, 1), (1, 1), (1, -1)]
        knight_jumps = [(-2, -1), (-2, 1), (-1, 2), (1, 2), (2, 1), (2, -1), (1, -2), (-1, -2)]

        for y in range(8):
            for x in range(8):
                BitBoardUtility.process_square(x, y, ortho_dir, diag_dir, knight_jumps)
    
    @staticmethod
    def process_square(x, y, ortho_dir, diag_dir, knight_jumps):
        """
        Process each square to set up the attack bitboards
        """
        square_index = y * 8 + x

        for dir_index in range(4):
            # Orthogonal and diagonal directions
            for dst in range(1, 8):
                ortho_x = x + ortho_dir[dir_index][0] * dst
                ortho_y = y + ortho_dir[dir_index][1] * dst
                diag_x = x + diag_dir[dir_index][0] * dst
                diag_y = y + diag_dir[dir_index][1] * dst

                if BitBoardUtility.valid_square_index(ortho_x, ortho_y):
                    ortho_target_index = ortho_y * 8 + ortho_x
                    if dst == 1:
                        BitBoardUtility.KingMoves[square_index] |= 1 << ortho_target_index

                if BitBoardUtility.valid_square_index(diag_x, diag_y):
                    diag_target_index = diag_y * 8 + diag_x
                    if dst == 1:
                        BitBoardUtility.KingMoves[square_index] |= 1 << diag_target_index

            # Knight jumps
            for jump in knight_jumps:
                knight_x = x + jump[0]
                knight_y = y + jump[1]
                if BitBoardUtility.valid_square_index(knight_x, knight_y):
                    knight_target_square = knight_y * 8 + knight_x
                    BitBoardUtility.KnightAttacks[square_index] |= 1 << knight_target_square

            # Pawn attacks
            if BitBoardUtility.valid_square_index(x + 1, y + 1):
                white_pawn_right = (y + 1) * 8 + (x + 1)
                BitBoardUtility.WhitePawnAttacks[square_index] |= 1 << white_pawn_right

            if BitBoardUtility.valid_square_index(x - 1, y + 1):
                white_pawn_left = (y + 1) * 8 + (x - 1)
                BitBoardUtility.WhitePawnAttacks[square_index] |= 1 << white_pawn_left

            if BitBoardUtility.valid_square_index(x + 1, y - 1):
                black_pawn_attack_right = (y - 1) * 8 + (x + 1)
                BitBoardUtility.BlackPawnAttacks[square_index] |= 1 << black_pawn_attack_right

            if BitBoardUtility.valid_square_index(x - 1, y - 1):
                black_pawn_attack_left = (y - 1) * 8 + (x - 1)
                BitBoardUtility.BlackPawnAttacks[square_index] |= 1 << black_pawn_attack_left

    def valid_square_index(x, y):
        """
        Check if the given coordinates correspond to a valid square index
        """
        return 0 <= x < 8 and 0 <= y < 8
    
# Initialize the bitboards
BitBoardUtility.initialize()