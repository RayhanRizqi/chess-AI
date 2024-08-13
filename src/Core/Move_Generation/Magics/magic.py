from PrecomputedMagics import PrecomputedMagics
from magicHelper import MagicHelper

RookShifts = PrecomputedMagics.RookShifts
BishopShifts = PrecomputedMagics.BishopShifts
RookMagics = PrecomputedMagics.RookMagics
BishopMagics = PrecomputedMagics.BishopMagics

class Magic:
    # Rook and bishop mask bitboards for each origin square
    RookMask = [0] * 64
    BishopMask = [0] * 64

    RookAttacks = [None] * 64
    BishopAttacks = [None] * 64

    @staticmethod
    def get_slider_attacks(square, blockers, ortho):
        """
        Get attacks for sliders (rooks and bishops) depending on the direction
        """
        return Magic.get_rook_attacks(square, blockers) if ortho else Magic.get_bishop_attacks(square, blockers)
    
    @staticmethod
    def get_rook_attacks(square, blockers):
        """
        Get rook attacks for a given square and blocker bitboard
        """
        key = ((blockers & Magic.RookMask[square]) * RookMagics[square]) >> RookShifts[square]
        return Magic.RookAttacks[square][key]
    
    @staticmethod
    def get_bishop_attacks(square, blockers):
        """
        Get bishop attacks for a given square and blocker bitboard
        """
        key = ((blockers & Magic.BishopMask[square]) * BishopMagics[square]) >> BishopShifts[square]
        return Magic.BishopAttacks[square][key]
    
    @staticmethod
    def initialize():
        """
        Initialize masks and attack tables for all squares on the board
        """
        for square_index in range(64):
            Magic.RookMask[square_index] = MagicHelper.create_movement_mask(square_index, True)
            Magic.BishopMask[square_index] = MagicHelper.create_movement_mask(square_index, False)

        for i in range(64):
            Magic.RookAttacks[i] = Magic.create_table(i, True, RookMagics[i], RookShifts[i])
            Magic.BishopAttacks[i] = Magic.create_table(i, False, BishopMagics[i], BishopShifts[i])

    @staticmethod
    def create_table(square, rook, magic, left_shift):
        """
        Create the attack table for a given square using the specified magic number
        """
        num_bits = 64 - left_shift
        lookup_size = 1 << num_bits
        table = [0] * lookup_size

        movement_mask = MagicHelper.create_movement_mask(square, rook)
        blocker_patterns = MagicHelper.create_all_blocker_bitboards(movement_mask)

        for pattern in blocker_patterns:
            index = (pattern * magic) >> left_shift
            moves = MagicHelper.legal_move_bitboard_from_blockers(square, pattern, rook)
            table[index] = moves

        return table
    
# Initialize the Magic class (this mimics the static constructor in C#)
Magic.initialize()