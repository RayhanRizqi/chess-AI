from piece import Piece

class Move:
    # Flags
    NoFlag = 0b0000
    EnPassantCaptureFlag = 0b0001
    CastleFlag = 0b0010
    PawnTwoUpFlag = 0b0011

    PromoteToQueenFlag = 0b0100
    PromoteToKnightFlag = 0b0101
    PromoteToRookFlag = 0b0110
    PromoteToBishopFlag = 0b0111

    # Masks
    start_square_mask = 0b0000000000111111
    target_square_mask = 0b0000111111000000
    flag_mask = 0b1111000000000000

    def __init__(self, start_square=None, target_square=None, flag=NoFlag, move_value=None):
        """
        Initialize a Move instance. A move can be created either by providing the start and target squares (with an optional flag)
        or dirtectly using a move value (ushort equivalent)
        """
        if move_value is not None:
            self.move_value = move_value
        else:
            self.move_value = (start_square | (target_square << 6) | (flag << 12))

    @property
    def value(self):
        return self.move_value
    
    @property
    def is_null(self):
        return self.move_value == 0
    
    @property
    def start_square(self):
        return self.move_value & self.start_square_mask
    
    @property
    def target_square(self):
        return (self.move_value & self.target_square_mask) >> 6
    
    @property
    def is_promotion(self):
        return self.move_flag >= Move.PromoteToQueenFlag
    
    @property
    def move_flag(self):
        return self.move_value >> 12
    
    @property
    def promotion_piece_type(self):
        """
        Determine the piece type for a promotion move
        """
        if self.move_flag == Move.PromoteToRookFlag:
            return Piece.Rook
        elif self.move_flag == Move.PromoteToKnightFlag:
            return Piece.Knight
        elif self.move_flag == Move.PromoteToBishopFlag:
            return Piece.Bishop
        elif self.move_flag == Move.PromoteToQueenFlag:
            return Piece.Queen
        else:
            return Piece.NoneType
        
    @staticmethod
    def null_move():
        return Move(move_value=0)
    
    @staticmethod
    def same_move(a, b):
        return a.move_value == b.move_value
    
    