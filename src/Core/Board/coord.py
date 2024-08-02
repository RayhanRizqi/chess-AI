from Helpers.boardHelpers import BoardHelper

# Structure for representing squares on the chess board as file/rank integer pairs.
# (0, 0) = a1, (7, 7) = h8.
# Coords can also be used as offsets. For example, while a Coord of (-1, 0) is not
# a valid square, it can be used to represent the concept of moving 1 square left.

class Coord:
    def __init__(self, file_index, rank_index=None):
        """
        Initializes a Coord object.
        If only one argument is provided, it is assumed to be a square index.
        """
        if rank_index is None:
            # If rank_index is None, initialize using a single square index
            self.file_index = BoardHelper.file_index(file_index)
            self.rank_index = BoardHelper.rank_index(file_index)
            self.square_index = file_index
        else:
            self.file_index = file_index
            self.rank_index = rank_index
            self.square_index = BoardHelper.index_from_coord(self)
    
    def is_light_square(self):
        """Determines if the square is a light-colored square"""
        return (self.file_index + self.rank_index) % 2 != 0
    
    def compare_to(self, other):
        """Compares two coordinates"""
        if not isinstance(other, Coord):
            return NotImplemented
        return 0 if (self.file_index == other.file_index and self.rank_index == other.rank_index) else 1
    
    def is_valid_square(self):
        """Checks if the coordinate is within the valid chessboard range"""
        return 0 <= self.file_index < 8 and 0 <= self.rank_index < 8
    
    @property
    def __add__(self, other):
        """Defines the addition of two Coord objects"""
        if isinstance(other, Coord):
            return Coord(self.file_index + other.file_index, self.rank_index + other.rank_index)
        return NotImplemented
    
    def __sub__(self, other):
        """Defines the substraction of two Coord objects"""
        if isinstance(other, Coord):
            return Coord(self.file_index - other.file_index, self.rank_index - other.rank_index)
        return NotImplemented
    
    def __mul__(self, other):
        """Defines the multiplication of a Coord object with an integer"""
        if isinstance(other, int):
            return Coord(self.file_index * other, self.rank_index * other)
        return NotImplemented
    
    def __rmul__(self, other):
        """Defines the reverse multiplaction (int * Coord)"""
        return self.__mul__(other)
    
