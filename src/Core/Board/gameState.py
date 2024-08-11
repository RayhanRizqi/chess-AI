class GameState():

    ClearWhiteKingsideMask = 0b1110
    ClearWhiteQueensideMask = 0b1101
    ClearBlackKingsideMask = 0b1011
    ClearBlackQueensideMask = 0b0111

    def __init__(self, captured_piece_type, en_passant_file, castling_rights, fifty_move_counter, zobrist_key):
        """
        Initialize a new GameState
        """
        self.captured_piece_type = captured_piece_type
        self.en_passant_file = en_passant_file
        self.castling_rights = castling_rights
        self.fifty_move_counter = fifty_move_counter
        self.zobrist_key = zobrist_key

    def has_kingside_castle_right(self, white):
        """
        Check if the given side has the right to castle kingside
        """
        mask = 1 if white else 4
        return (self.castling_rights & mask) != 0
    
    def has_queenside_castle_right(self, white):
        """
        Check if the given side has the right to castle queenside
        """
        mask = 2 if white else 8
        return (self.castling_rights & mask) != 0