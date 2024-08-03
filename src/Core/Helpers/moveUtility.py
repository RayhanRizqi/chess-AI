from boardHelpers import BoardHelper
from Board.piece import Piece
from Board.coord import Coord
from Board.move import Move
from Move_Generation.moveGenerator import MoveGenerator

class MoveUtility:
    """
    Helper class for handling chess moves, including conversion between
    UCI/SAN notations and internal move representations
    """

    @staticmethod
    def get_move_from_uci_name(move_name, board):
        """
        Converts a moveName into internal move representation
        Name is expected in format: "e2e4".
        Promotions can be written with or without an equals sign, 
        for example: "e7e8=q" or "e7e8q"
        """
        start_square = BoardHelper.square_index_from_name(move_name[:2])
        target_square = BoardHelper.square_index_from_name(move_name[2:4])

        moved_piece_type = Piece.piece_type(board.squares[start_square])
        start_coord = Coord(start_square)
        target_coord = Coord(target_square)

        # Figure out move flag
        flag = Move.NoFlag

        if moved_piece_type == Piece.Pawn:
            # Promotion
            if len(move_name) > 4:
                flag = {
                    'q': Move.PromoteToQueenFlag,
                    'r': Move.PromoteToRookFlag,
                    'n': Move.PromoteToKnightFlag,
                    'b': Move.PromoteToBishopFlag
                }.get(move_name[-1], Move.NoFlag)

            # Double pawn push
            elif abs(target_coord.rank_index - start_coord.rank_index) == 2:
                flag = Move.PawnTwoUpFlag

            # En-passant
            elif start_coord.file_index != target_coord.file_index and board.squares[target_square] == Piece.NoneType:
                flag = Move.EnPassantCaptureFlag

        elif moved_piece_type == Piece.King:
            if abs(start_coord.file_index - target_coord.file_index) > 1:
                flag = Move.CastleFlag

        return Move(start_square, target_square, flag)

    @staticmethod
    def get_move_name_uci(move):
        """
        Get algebraic name of move (with promotion specified)
        Examples: "e2e4", "e7e8q"
        """
        start_square_name = BoardHelper.square_name_from_index(move.start_square)
        end_square_name = BoardHelper.square_name_from_index(move.target_square)
        move_name = start_square_name + end_square_name

        if move.is_promotion:
            move_name += {
                Move.PromoteToRookFlag: "r",
                Move.PromoteToKnightFlag: "n",
                Move.PromoteToBishopFlag: "b",
                Move.PromoteToQueenFlag: "q"
            }.get(move.move_flag, "")

        return move_name
    
    @staticmethod
    def get_move_name_san(move, board):
        """
        Get name of move in Standard Algebraic Notation (SAN)
        Examples: "e4", "Bxf7+", "O-O", "Rh8#", "Nfd2"
        Note, the move must not yet have been made on the board
        """
        if move.is_null:
            return "Null"
        
        move_piece_type = Piece.piece_type(board.squares[move.start_square])
        captured_piece_type = Piece.piece_type(board.squares[move.target_square])

        if move.move_flag == Move.CastleFlag:
            delta = move.target_square - move.start_square
            if delta == 2:
                return "O-O"
            elif delta == -2:
                return "O-O-O"
            
        move_gen = MoveGenerator()
        move_notation = Piece.get_symbol(move_piece_type).upper() if move_piece_type != Piece.Pawn else ""

        # Check if ambiguity exists in notation (e.g., if e2 can be reached via Nfe2 and Nbe2)
        if move_piece_type != Piece.Pawn and move_piece_type != Piece.King:
            all_moves = move_gen.generate_moves(board)

            for alt_move in all_moves:
                if alt_move.start_square != move.start_square and alt_move.target_square == move.target_square:
                    if Piece.piece_type(board.squares[alt_move.start_square]) == move_piece_type:
                        from_file_index = BoardHelper.file_index(move.start_square)
                        alternate_from_file_index = BoardHelper.file_index(alt_move.start_square)
                        from_rank_index = BoardHelper.rank_index(move.start_square)
                        alternate_from_rank_index = BoardHelper.rank_index(alt_move.start_square)

                        if from_file_index != alternate_from_file_index:
                            move_notation += BoardHelper.file_names[from_file_index]
                            break # Ambiguity resolved
                        
                        elif from_rank_index != alternate_from_rank_index:
                            move_notation += BoardHelper.rank_names[from_rank_index]
                            break # Ambiguity resolved
        
        if captured_piece_type != 0:
            # Add 'x' to indicate capture
            if move_piece_type == Piece.Pawn:
                move_notation += BoardHelper.file_names[BoardHelper.file_index(move.start_square)] + "x"
            move_notation += "x"
        else:
            # Check if capturing en passant
            if move.move_flag == Move.EnPassantCaptureFlag:
                move_notation += BoardHelper.file_names[BoardHelper.file_index(move.start_square)] + "x"

        move_notation += BoardHelper.file_names[BoardHelper.file_index(move.target_square)]
        move_notation += BoardHelper.rank_names[BoardHelper.rank_index(move.target_square)]

        # Add promotion piece
        if move.is_promotion:
            promotion_piece_type = move.promotion_piece_type
            move_notation += "=" + Piece.get_symbol(promotion_piece_type).upper()

        board.make_move(move, in_search=True)
        legal_responses = move_gen.generate_moves(board)
        # Add check/mate symbol if applicable
        if move_gen.in_check():
            move_notation += "#" if not legal_responses else "+"

        board.unmake_move(move, in_search=True)

        return move_notation
    
    @staticmethod
    def get_move_from_san(board, algebraic_move):
        """
        Get move from the given name in SAN notation (e.g., "Nxf3", "Rad1", "O-O", etc.).
        The given board must contain the position from before the move was made.
        """
        move_generator = MoveGenerator()

        # Remove unrequired info from move string
        algebraic_move = algebraic_move.replace("+", "").replace("#", "").replace("x", "").replace("-", "")
        all_moves = move_generator.generate_moves(board)

        move = Move()

        for move_to_test in all_moves:
            move = move_to_test

            move_from_index = move.start_square
            move_to_index = move.target_square
            move_piece_type = Piece.piece_type(board.squares[move_from_index])
            from_coord = BoardHelper.coord_from_index(move_from_index)
            to_coord = BoardHelper.coord_from_index(move_to_index)

            if algebraic_move == "OO":
                # Castle kingside
                if move_piece_type == Piece.King and move_to_index - move_from_index == 2:
                    return move
            elif algebraic_move == "OOO":
                # Castle queenside
                if move_piece_type == Piece.King and move_to_index - move_from_index == -2:
                    return move
            # Is pawn move if starts with any file indicator (e.g., 'e'4. Note that uppercase B is used for bishops)
            elif algebraic_move[0] in BoardHelper.file_names:
                if move_piece_type != Piece.Pawn:
                    continue
                if BoardHelper.file_names.index(algebraic_move[0]) == from_coord.file_index:
                    # Correct starting file
                    if '=' in algebraic_move:
                        # Is promotion
                        if to_coord.rank_index == 0 or to_coord.rank_index == 7:
                            if len(algebraic_move) == 5:  # Pawn is capturing to promote
                                target_file = algebraic_move[1]
                                if BoardHelper.file_names.index(target_file) != to_coord.file_index:
                                    # Skip if not moving to correct file
                                    continue

                            promotion_char = algebraic_move[-1]

                            if move.promotion_piece_type != Piece.get_piece_type_from_symbol(promotion_char):
                                continue  # Skip this move, incorrect promotion type

                            return move
                    else:
                        target_file = algebraic_move[-2]
                        target_rank = algebraic_move[-1]

                        if BoardHelper.file_names.index(target_file) == to_coord.file_index:
                            # Correct ending file
                            if target_rank == str(to_coord.rank_index + 1):
                                # Correct ending rank
                                break
            else:
                # Regular piece move
                move_piece_char = algebraic_move[0]
                if Piece.get_piece_type_from_symbol(move_piece_char) != move_piece_type:
                    continue  # Skip this move, incorrect move piece type

                target_file = algebraic_move[-2]
                target_rank = algebraic_move[-1]
                if BoardHelper.file_names.index(target_file) == to_coord.file_index:
                    # Correct ending file
                    if target_rank == str(to_coord.rank_index + 1):
                        # Correct ending rank
                        if len(algebraic_move) == 4:
                            # Additional char present for disambiguation (e.g., Nbd7 or R7e2)
                            disambiguation_char = algebraic_move[1]

                            if disambiguation_char in BoardHelper.file_names:
                                # Is file disambiguation
                                if BoardHelper.file_names.index(disambiguation_char) != from_coord.file_index:
                                    # Incorrect starting file
                                    continue
                            else:
                                # Is rank disambiguation
                                if disambiguation_char != str(from_coord.rank_index + 1):
                                    # Incorrect starting rank
                                    continue

                        return move  # Move has been found

        return move  # Return the found move or a default move if not found