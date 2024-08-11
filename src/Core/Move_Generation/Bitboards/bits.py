import numpy as np
from math import clamp
from Helpers.boardHelpers import BoardHelper
from bitBoardUtility import BitBoardUtility

class Bits:
    # Constants representing file masks and kingside/queenside masks
    FileA = 0x101010101010101

    WhiteKingsideMask = (1 << BoardHelper.f1) | (1 << BoardHelper.g1)
    BlackKingsideMask = (1 << BoardHelper.f8) | (1 << BoardHelper.g8)

    WhiteQueensideMask2 = (1 << BoardHelper.d1) | (1 << BoardHelper.c1)
    BlackQueensideMask2 = (1 << BoardHelper.d8) | (1 << BoardHelper.c8)

    WhiteQueensideMask = WhiteQueensideMask2 | (1 << BoardHelper.b1)
    BlackQueensideMask = BlackQueensideMask2 | (1 << BoardHelper.b8)

    # Static variables for various bitboard masks
    WhitePassedPawnMask = [0] * 64
    BlackPassedPawnMask = [0] * 64
    WhitePawnSupportMask = [0] * 64
    BlackPawnSupportMask = [0] * 64
    FileMask = [0] * 8
    AdjacentFileMasks = [0] * 8
    KingSafetyMask = [0] * 64
    WhiteForwardFileMask = [0] * 64
    BlackForwardFileMask = [0] * 64
    TripleFileMask = [0] * 8

    @staticmethod
    def initialize():
        # Initialize file masks and adjacent file masks
        for i in range(8):
            Bits.FileMask[i] = Bits.FileA << i
            left = Bits.FileA << (i - 1) if i > 0 else 0
            right = Bits.FileA << (i + 1) if i < 7 else 0
            Bits.AdjacentFileMasks[i] = left | right

        # Initialize triple file masks
        for i in range(8):
            clamped_file = clamp(i, 1, 6)
            Bits.TripleFileMask[i] = Bits.FileMask[clamped_file] | Bits.AdjacentFileMasks[clamped_file]

        # Initialize passed pawn masks, pawn support masks, and forward file masks
        for square in range(64):
            file = BoardHelper.file_index(square)
            rank = BoardHelper.rank_index(square)
            adjacent_files = Bits.FileA << max(0, file - 1) | Bits.FileA << min(7, file + 1)

            # Passed pawn mask
            white_forward_mask = ~((1 << (64 - 8 * (rank + 1))) - 1)
            black_forward_mask = (1 << (8 * rank)) - 1

            Bits.WhitePassedPawnMask[square] = (Bits.FileA << file | adjacent_files) & white_forward_mask
            Bits.BlackPassedPawnMask[square] = (Bits.FileA << file | adjacent_files) & black_forward_mask

            # Pawn support mask
            adjacent = ((1 << (square - 1)) | (1 << (square + 1))) & adjacent_files
            Bits.WhitePawnSupportMask[square] = adjacent | BitBoardUtility.shift(adjacent, -8)
            Bits.BlackPawnSupportMask[square] = adjacent | BitBoardUtility.shift(adjacent, 8)

            Bits.WhiteForwardFileMask[square] = white_forward_mask & Bits.FileMask[file]
            Bits.BlackForwardFileMask[square] = black_forward_mask & Bits.FileMask[file]

        # Initialize king safety masks
        for i in range(64):
            Bits.KingSafetyMask[i] = BitBoardUtility.KingMoves[i] | (1 << i)

# Initialize the bitboard masks
Bits.initialize()