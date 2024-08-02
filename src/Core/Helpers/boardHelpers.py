from Board.coord import Coord
from Board.piece import Piece
from fenUtility import FenUtility

class BoardHelper:
    # Directional coordinates for Rook and Bishop moves
    RookDirections = [Coord(-1, 0), Coord(1, 0), Coord(0, 1), Coord(0, -1)]
    BishopDirections = [Coord(-1, 1), Coord(1, 1), Coord(1, -1), Coord(-1, -1)]

    file_names = 'abcdefgh'
    rank_names = "12345678"

    # Constants for specific squares
    a1, b1, c1, d1, e1, f1, g1, h1 = range(8)
    a8, b8, c8, d8, e8, f8, g8, h8 = range(56, 64)

    @staticmethod
    def rank_index(square_index):
        """Returns the rank index (0 to 7) of a given square index (0 to 63)"""
        return square_index >> 3
    
    @staticmethod
    def file_index(square_index):
        """Returns the file index (0 to 7) of a given square index (0 to 63)"""
        return square_index & 0b000111
    
    @staticmethod
    def index_from_coord(file_index, rank_index):
        """Returns the square index from given file and rank indices"""
        return rank_index * 8 + file_index
    
    @staticmethod
    def index_from_coord(coord):
        """Returns the square index from a Coord object"""
        return BoardHelper.index_from_coord(coord.file_index, coord.rank_index)
    
    @staticmethod
    def coord_from_index(square_index):
        """Creates a Coord object from a given square index"""
        return Coord(BoardHelper.file_index(square_index), BoardHelper.rank_index(square_index))
    
    @staticmethod
    def light_square(file_index, rank_index):
        """Determines if the given file and rank represent a light square"""
        return (file_index + rank_index) % 2 != 0
    
    @staticmethod
    def light_square(square_index):
        return BoardHelper.light_square(BoardHelper.file_index(square_index), BoardHelper.rank_index(square_index))
    
    @staticmethod
    def square_name_from_coordinate(file_index, rank_index):
        return BoardHelper.file_names[file_index] + str(rank_index + 1)
    
    @staticmethod
    def square_name_from_index(square_index):
        coord = BoardHelper.coord_from_index(square_index)
        return BoardHelper.square_name_from_coordinate(coord.file_index, coord.rank_index)
    
    @staticmethod
    def square_name_from_coordinate(coord):
        return BoardHelper.square_name_from_coordinate(coord.file_index, coord.rank_index)
    
    @staticmethod
    def square_index_from_name(name):
        file_name = name[0]
        rank_name = name[1]
        file_index = BoardHelper.file_names.index(file_name)
        rank_index = BoardHelper.rank_names.index(rank_name)
        return BoardHelper.index_from_coord(file_index, rank_index)
    
    @staticmethod
    def is_valid_coordinate(x, y):
        return 0 <= x < 8 and 0 <= y < 8
    
    @staticmethod
    def create_diagram(board, black_at_top=True, include_fen=True, include_zobrist_key=True):
        """Creates ASCII diagram of the current board position"""
        result = []
        last_move_square = board.all_game_moves[-1].target_square if board.all_game_moves else -1

        for y in range(8):
            rank_index = 7 - y if black_at_top else y
            result.append("+---+---+---+---+---+---+---+---+")

            for x in range(8):
                file_index = x if black_at_top else 7 - x
                square_index = BoardHelper.index_from_coord(file_index, rank_index)
                highlight = square_index == last_move_square
                piece = board.squares[square_index]
                symbol = Piece.get_symbol(piece)

                if highlight:
                    result.append(f"|({symbol})")
                else:
                    result.append(f"| {symbol} ")

                if x == 7:
                    # Show rank number
                    result.append(f"| {rank_index + 1}")
            
            result.append("")

            if y == 7:
                # Show file names
                result.append("+---+---+---+---+---+---+---+---+")
                file_names = "  a   b   c   d   e   f   g   h  "
                file_names_rev = "  h   g   f   e   d   c   b   a  "
                result.append(file_names if black_at_top else file_names_rev)
                result.append("")

                if include_fen:
                    result.append(f"Fen         : {FenUtility.current_fen(board)}")

                if include_zobrist_key:
                    result.append(f"Zobrist Key : {board.zobrist_key}")
        
        return "\n".join(result)