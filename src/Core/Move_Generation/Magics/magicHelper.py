from Helpers.boardHelpers import BoardHelper
from Board.coord import Coord
from Bitboards.bitBoardUtility import BitBoardUtility

class MagicHelper:
    @staticmethod
    def create_all_blocker_bitboards(movement_mask):
        """
        Create all possible blocker bitboards for a given movement mask
        """
        # Create a list of the indices of the bits that are set in the movement mask
        move_square_indices = []
        for i in range(64):
            if (movement_mask >> i) & 1 == 1:
                move_square_indices.append(i)
        
        # Calculate total number of different bitboards (one for each possible arrangement of pieces)
        num_patterns = 1 << len(move_square_indices) # 2^n
        blocker_bitboards = [0] * num_patterns

        # Create all bitboards
        for pattern_index in range(num_patterns):
            for bit_index, square_index in enumerate(move_square_indices):
                bit = (pattern_index >> bit_index) & 1
                blocker_bitboards[pattern_index] |= bit << square_index
        
        return blocker_bitboards
    
    @staticmethod
    def create_movement_mask(square_index, ortho):
        """
        Create a movement mask for a given square index and direction type (ortho for rook-like, else bishop-like)
        """
        mask = 0
        directions = BoardHelper.RookDirections if ortho else BoardHelper.BishopDirections
        start_coord = Coord(square_index)

        for dir in directions:
            for dst in range(1, 8):
                coord = start_coord + dir * dst
                next_coord = start_coord + dir * (dst + 1)

                if next_coord.is_valid_square():
                    mask = BitBoardUtility.set_square(mask, coord.square_index)
                else:
                    break
        
        return mask
    
    @staticmethod
    def legal_move_bitboard_from_blockers(start_square, blocker_bitboard, ortho):
        """
        Generate a legal move bitboard for a given start square and blocker bitboard
        """
        bitboard = 0

        directions = BoardHelper.RookDirections if ortho else BoardHelper.BishopDirections
        start_coord = Coord(start_square)

        for dir in directions:
            for dst in range(1, 8):
                coord = start_coord + dir * dst

                if coord.is_valid_square():
                    bitboard = BitBoardUtility.set_square(bitboard, coord.square_index)
                    if BitBoardUtility.contains_square(blocker_bitboard, coord.square_index):
                        break
                else:
                    break
        
        return bitboard