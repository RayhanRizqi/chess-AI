
class Piece:

    # Piece Types
    NoneType = 0
    Pawn = 1
    Knight = 2
    Bishop = 3
    Rook = 4
    Queen = 5
    King = 6

    # Piece Colors
    White = 0
    Black = 8

    # Pieces
    WhitePawn = Pawn | White
    WhiteKnight = Knight | White
    WhiteBishop = Bishop | White
    WhiteRook = Rook | White
    WhiteQueen = Queen | White
    WhiteKing = King | White

    BlackPawn = Pawn | Black
    BlackKnight = Knight | Black
    BlackBishop = Bishop | Black
    BlackRook = Rook | Black
    BlackQueen = Queen | Black
    BlackKing = King | Black

    MaxPieceIndex = BlackKing

    PieceIndices = [
        WhitePawn, WhiteKnight, WhiteBishop, WhiteRook, WhiteQueen, WhiteKing,
        BlackPawn, BlackKnight, BlackBishop, BlackRook, BlackQueen, BlackKing
    ]

    # Bit Masks
    typeMask = 0b0111
    colorMask = 0b1000

    @staticmethod
    def make_piece(piece_type, piece_color):
        return piece_type | piece_color

    @staticmethod
    def make_piece_by_color(piece_type, piece_is_white):
        return Piece.make_piece(piece_type, Piece.White if piece_is_white else Piece.Black)

    @staticmethod
    def is_color(piece, color):
        return (piece & Piece.colorMask) == color and piece != Piece.NoneType

    @staticmethod
    def is_white(piece):
        return Piece.is_color(piece, Piece.White)

    @staticmethod
    def piece_color(piece):
        return piece & Piece.colorMask

    @staticmethod
    def piece_type(piece):
        return piece & Piece.typeMask

    @staticmethod
    def is_orthogonal_slider(piece):
        return Piece.piece_type(piece) in (Piece.Rook, Piece.Queen)

    @staticmethod
    def is_diagonal_slider(piece):
        return Piece.piece_type(piece) in (Piece.Bishop, Piece.Queen)

    @staticmethod
    def is_sliding_piece(piece):
        return Piece.piece_type(piece) in (Piece.Bishop, Piece.Rook, Piece.Queen)

    @staticmethod
    def get_symbol(piece):
        piece_type = Piece.piece_type(piece)
        symbol = {
            Piece.Rook: 'R',
            Piece.Knight: 'N',
            Piece.Bishop: 'B',
            Piece.Queen: 'Q',
            Piece.King: 'K',
            Piece.Pawn: 'P'
        }.get(piece_type, ' ')
        return symbol if Piece.is_white(piece) else symbol.lower()

    @staticmethod
    def get_piece_type_from_symbol(symbol):
        symbol = symbol.upper()
        return {
            'R': Piece.Rook,
            'N': Piece.Knight,
            'B': Piece.Bishop,
            'Q': Piece.Queen,
            'K': Piece.King,
            'P': Piece.Pawn
        }.get(symbol, Piece.NoneType)