class PieceList:
    def __init__(self, max_piece_count=16):
        # Indices of squares occupied by a given piece type
        self.occupied_squares = [None] * max_piece_count # List to store occupied squares
        self.map = [None] * 64 # Map to go from index of a squares to the index in occupied_squares
        self.num_pieces = 0 # Number of pieces currently in the list

    @property
    def count(self):
        return self.num_pieces
    
    def add_piece_at_square(self, square):
        """Add a piece at the given square"""
        self.occupied_squares[self.num_pieces] = square
        self.map[square] = self.num_pieces
        self.num_pieces += 1

    def remove_piece_at_square(self, square):
        """Remove a piece at the given square"""
        piece_index = self.map[square]
        # Move the last element to the place of the removed element
        last_square = self.occupied_squares[self.num_pieces - 1]
        self.occupied_squares[piece_index] = last_square
        self.map[last_square] = piece_index
        self.num_pieces -= 1

    def move_piece(self, start_square, target_square):
        """Move a piece from startSquare to targetSquare"""
        piece_index = self.map[start_square]
        self.occupied_squares[piece_index] = target_square
        self.map[target_square] = piece_index

    def __getitem__(self, index):
        return self.occupied_squares[index]