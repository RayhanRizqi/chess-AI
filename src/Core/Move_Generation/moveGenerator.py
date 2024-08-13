from enum import Enum
from Board.piece import Piece
from Bitboards.bitBoardUtility import BitBoardUtility
from Board.move import Move
from Bitboards.bits import Bits
from Helpers.boardHelpers import BoardHelper
from Magics.magic import Magic
from precomputedMoveData import PrecomputedMoveData

class PromotionMode(Enum):
    ALL = 1
    QUEEN_ONLY = 2
    QUEEN_AND_KNIGHT = 3

class MoveGenerator():
    MAX_MOVES = 218
    
    def __init__(self):
        self.promotions_to_generate = PromotionMode.ALL
        self.is_white_to_move = False
        self.friendly_color = 0
        self.opponent_color = 0
        self.friendly_king_square = 0
        self.friendly_index = 0
        self.enemy_index = 0
        self.in_check = False
        self.in_double_check = False
        self.check_ray_bitmask = 0
        self.pin_rays = 0
        self.not_pin_rays = 0
        self.opponent_attack_map_no_pawns = 0
        self.opponent_attack_map = 0
        self.opponent_pawn_attack_map = 0
        self.opponent_sliding_attack_map = 0
        self.generate_quiet_moves = True
        self.board = None
        self.curr_move_index = 0
        self.enemy_pieces = 0
        self.friendly_pieces = 0
        self.all_pieces = 0
        self.empty_squares = 0
        self.empty_or_enemy_squares = 0
        self.move_type_mask = 0

    def generate_moves(self, board, captures_only=False):
        moves = []
        self._generate_moves(board, moves, captures_only)
        return moves
    
    def _generate_moves(self, board, moves, captures_only=False):
        self.board = board
        self.generate_quiet_moves = not captures_only

        self._init()

        self._generate_king_moves(moves)

        if not self.in_double_check:
            self._generate_sliding_moves(moves)
            self._generate_knight_moves(moves)
            self._generate_pawn_moves(moves)

        return len(moves)
    
    def is_in_check(self):
        return self.in_check
    
    def _init(self):
        self.curr_move_index = 0
        self.in_check = False
        self.in_double_check = False
        self.check_ray_bitmask = 0
        self.pin_rays = 0

        self.is_white_to_move = self.board.move_color == Piece.White
        self.friendly_color = self.board.move_color
        self.opponent_color = self.board.opponent_color
        self.friendly_king_square = self.board.king_square[self.board.move_color_index]
        self.friendly_index = self.board.move_color_index
        self.enemy_index = 1 - self.friendly_index

        self.enemy_pieces = self.board.color_bitboards[self.enemy_index]
        self.friendly_pieces = self.board.color_bitboards[self.friendly_index]
        self.all_pieces = self.board.all_pieces_bitboard
        self.empty_squares = ~self.all_pieces
        self.empty_or_enemy_squares = self.empty_squares | self.enemy_pieces
        self.move_type_mask = self.generate_quiet_moves and 0xFFFFFFFFFFFFFFFF or self.enemy_pieces

        self._calculate_attack_data()

    def _generate_king_moves(self, moves):
        legal_mask = ~(self.opponent_attack_map | self.friendly_pieces)
        king_moves = BitBoardUtility.KingMoves[self.friendly_king_square] & legal_mask & self.move_type_mask
        while king_moves:
            target_square = BitBoardUtility.pop_lsb(king_moves)
            moves.append(Move(self.friendly_king_square, target_square))
        
        # Castling
        if not self.in_check and self.generate_quiet_moves:
            castle_blockers = self.opponent_attack_map | self.board.all_pieces_bitboard
            if self.board.current_game_state.has_kingside_castle_rights(self.board.is_white_to_move):
                castle_mask = Bits.WhiteKingsideMask if self.board.is_white_to_move else Bits.BlackKingsideMask
                if (castle_mask & castle_blockers) == 0:
                    target_square = BoardHelper.c1 if self.board.is_white_to_move else BoardHelper.c8
                    moves.append(Move(self.friendly_king_square, target_square, Move.CastleFlag))

    def _generate_sliding_moves(self, moves):
        move_mask = self.empty_or_enemy_squares & self.check_ray_bitmask & self.move_type_mask

        orthogonal_sliders = self.board.friendly_orthogonal_sliders
        diagonal_sliders = self.board.friendly_diagonal_sliders

        if self.in_check:
            orthogonal_sliders &= ~self.pin_rays
            diagonal_sliders &= ~self.pin_rays

        while orthogonal_sliders:
            start_square = BitBoardUtility.pop_lsb(orthogonal_sliders)
            move_squares = Magic.get_rook_attacks(start_square, self.all_pieces) & move_mask

            if self._is_pinned(start_square):
                move_squares &= PrecomputedMoveData.align_mask[start_square, self.friendly_king_square]

            while move_squares:
                target_square = BitBoardUtility.pop_lsb(move_squares)
                moves.append(Move(start_square, target_square))

        while diagonal_sliders:
            start_square = BitBoardUtility.pop_lsb(diagonal_sliders)
            move_squares = Magic.get_bishop_attacks(start_square, self.all_pieces) & move_mask

            if self._is_pinned(start_square):
                move_squares &= PrecomputedMoveData.align_mask[start_square, self.friendly_king_square]

            while move_squares:
                target_square = BitBoardUtility.pop_lsb(move_squares)
                moves.append(Move(start_square, target_square))

    def _generate_knight_moves(self, moves):
        friendly_knight_piece = Piece.make_piece(Piece.Knight, self.board.move_color)
        knights = self.board.piece_bitboards[friendly_knight_piece] & self.not_pin_rays
        move_mask = self.empty_or_enemy_squares & self.check_ray_bitmask & self.move_type_mask

        while knights:
            knight_square = BitBoardUtility.pop_lsb(knights)
            move_squares = BitBoardUtility.KnightAttacks[knight_square] & move_mask

            while move_squares:
                target_square = BitBoardUtility.pop_lsb(move_squares)
                moves.append(Move(knight_square, target_square))
    
    def _generate_pawn_moves(self, moves):
        push_dir = 1 if self.board.is_white_to_move else -1
        push_offset = push_dir * 8

        friendly_pawn_piece = Piece.make_piece(Piece.Pawn, self.board.move_color)
        pawns = self.board.piece_bitboards[friendly_pawn_piece]

        promotion_rank_mask = BitBoardUtility.Rank8 if self.board.is_white_to_move else BitBoardUtility.Rank1

        single_push = BitBoardUtility.shift(pawns, push_offset) & self.empty_squares

        push_promotions = single_push & promotion_rank_mask & self.check_ray_bitmask

        capture_edge_file_mask = BitBoardUtility.notAFile if self.board.is_white_to_move else BitBoardUtility.notHFile
        capture_edge_file_mask2 = BitBoardUtility.notHFile if self.board.is_white_to_move else BitBoardUtility.notAFile
        capture_a = BitBoardUtility.shift(pawns & capture_edge_file_mask, push_dir * 7) & self.enemy_pieces
        capture_b = BitBoardUtility.shift(pawns & capture_edge_file_mask2, push_dir * 9) & self.enemy_pieces

        single_push_no_promotions = single_push & ~promotion_rank_mask & self.check_ray_bitmask

        capture_promotions_a = capture_a & promotion_rank_mask & self.check_ray_bitmask
        capture_promotions_b = capture_b & promotion_rank_mask & self.check_ray_bitmask

        capture_a &= self.check_ray_bitmask & ~promotion_rank_mask
        capture_b &= self.check_ray_bitmask & promotion_rank_mask

        if self.generate_quiet_moves:
            while single_push_no_promotions:
                target_square = BitBoardUtility.pop_lsb(single_push_no_promotions)
                start_square = target_square - push_offset
                if not self._is_pinned(start_square) or PrecomputedMoveData.align_mask[start_square, self.friendly_king_square] == PrecomputedMoveData.align_mask[target_square, self.friendly_king_square]:
                    moves.append(Move(start_square, target_square))

            double_push_target_rank_mask = BitBoardUtility.Rank4 if self.board.is_white_to_move else BitBoardUtility.Rank5
            double_push = BitBoardUtility.shift(single_push, push_offset) & self.empty_squares & double_push_target_rank_mask & self.check_ray_bitmask

            while double_push:
                target_square = BitBoardUtility.pop_lsb(double_push)
                start_square = target_square - push_offset * 2
                if not self.is_pinned(start_square) or PrecomputedMoveData.align_mask[start_square, self.friendly_king_square] == PrecomputedMoveData.align_mask[target_square, self.friendly_king_square]:
                    moves.append(Move(start_square, target_square, Move.PawnTwoUpFlag))
        
        # Captures
        while capture_a:
            target_square = BitBoardUtility.pop_lsb(capture_a)
            start_square = target_square - push_dir * 7

            if not self._is_pinned(start_square) or PrecomputedMoveData.align_mask[start_square, self.friendly_king_square] == PrecomputedMoveData.align_mask[target_square, self.friendly_king_square]:
                moves.append(Move(start_square, target_square))
        
        while capture_b:
            target_square = BitBoardUtility.pop_lsb(capture_b)
            start_square = target_square - push_dir * 9

            if not self._is_pinned(start_square) or PrecomputedMoveData.align_mask[start_square, self.friendly_king_square] == PrecomputedMoveData.align_mask[target_square, self.friendly_king_square]:
                moves.append(Move(start_square, target_square))
        
        # Promotions
        while push_promotions:
            target_square = BitBoardUtility.pop_lsb(push_promotions)
            start_square = target_square - push_offset
            if not self._is_pinned(start_square):
                self._generate_promotions(start_square, target_square, moves)
        
        while capture_promotions_a:
            target_square = BitBoardUtility.pop_lsb(capture_promotions_a)
            start_square = target_square - push_dir * 7

            if not self._is_pinned(start_square) or PrecomputedMoveData.align_mask[start_square, self.friendly_king_square] == PrecomputedMoveData.align_mask[target_square, self.friendly_king_square]:
                self._generate_promotions(start_square, target_square, moves)
        
        while capture_promotions_b:
            target_square = BitBoardUtility.pop_lsb(capture_promotions_b)
            start_square = target_square - push_dir * 9

            if not self._is_pinned(start_square) or PrecomputedMoveData.align_mask[start_square, self.friendly_king_square] == PrecomputedMoveData.align_mask[target_square, self.friendly_king_square]:
                self._generate_promotions(start_square, target_square, moves)

        # En passant
        if self.board.current_game_state.en_passant_file > 0:
            ep_file_index = self.board.current_game_state.en_passant_file - 1
            ep_rank_index = 5 if self.board.is_white_to_move else 2
            target_square = ep_rank_index * 8 + ep_file_index
            captured_pawn_square = target_square - push_offset

            if BitBoardUtility.contains_square(self.check_ray_bitmask, captured_pawn_square):
                pawns_that_can_capture_ep = pawns & BitBoardUtility.pawn_attacks(1 << target_square, not self.board.is_white_to_move)

                while pawns_that_can_capture_ep:
                    start_square = BitBoardUtility.pop_lsb(pawns_that_can_capture_ep)
                    if not self._is_pinned(start_square) or PrecomputedMoveData.align_mask[start_square, self.friendly_king_square] == PrecomputedMoveData.align_mask[target_square, self.friendly_king_square]:
                        if not self._in_check_after_en_passant(start_square, target_square, captured_pawn_square):
                            moves.append(Move(start_square, target_square, Move.EnPassantCaptureFlag))
    
    def _generate_promotions(self, start_square, target_square, moves):
        moves.append(Move(start_square, target_square, Move.PromoteToQueenFlag))
        if self.generate_quiet_moves:
            if self.promotions_to_generate == PromotionMode.ALL:
                moves.append(Move(start_square, target_square, Move.PromoteToKnightFlag))
                moves.append(Move(start_square, target_square, Move.PromoteToRookFlag))
                moves.append(Move(start_square, target_square, Move.PromoteToBishopFlag))
            elif self.promotions_to_generate == PromotionMode.QUEEN_AND_KNIGHT:
                moves.append(Move(start_square, target_square, Move.PromoteToKnightFlag))

    def _is_pinned(self, square):
        return (self.pin_rays >> square) & 1 != 0
    
    def _generate_sliding_attack_map(self):
        self.opponent_sliding_attack_map = 0

        def update_slide_attack(piece_board, ortho):
            blockers = self.board.all_pieces_bitboard & ~(1 << self.friendly_king_square)

            while piece_board:
                start_square = BitBoardUtility.pop_lsb(piece_board)
                move_board = Magic.get_slider_attacks(start_square, blockers, ortho)
                self.opponent_sliding_attack_map |= move_board
        
        update_slide_attack(self.board.enemy_orthogonal_sliders, True)
        update_slide_attack(self.board.enemy_diagonal_sliders, False)

    def _calculate_attack_data(self):
        self._generate_sliding_attack_map()

        start_dir_index = 0
        end_dir_index = 8

        if not self.board.queens[self.enemy_index]:
            start_dir_index = 0 if self.board.rooks[self.enemy_index] else 4
            end_dir_index = 8 if self.board.bishops[self.enemy_index] else 4

        for dir in range(start_dir_index, end_dir_index):
            is_diagonal = dir > 3
            slider = self.board.enemy_diagonal_sliders if is_diagonal else self.board.enemy_orthogonal_sliders
            if not (PrecomputedMoveData.dir_ray_mask[dir][self.friendly_king_square] & slider):
                continue

            n = PrecomputedMoveData.num_squares_to_edge[self.friendly_king_square][dir]
            direction_offset = PrecomputedMoveData.direction_offsets[dir]
            is_friendly_piece_along_ray = False
            ray_mask = 0

            for i in range(n):
                square_index = self.friendly_king_square + direction_offset * (i + 1)
                ray_mask |= 1 << square_index
                piece = self.board.square[square_index]

                # Square contains a piece
                if piece != Piece.NoneType:
                    if Piece.is_color(piece, self.friendly_color):
                        # First friendly piece we have come across in this direction, so it might be pinned
                        if not is_friendly_piece_along_ray:
                            is_friendly_piece_along_ray = True
                        
                        # Second friendly piece we've found in this direction, therefore pin is not possible
                        else:
                            break

                    # This square contains an enemy piece
                    else:
                        piece_type = Piece.piece_type(piece)
                        
                        # Check if piece is in bitmask of pieces able to move in current direction
                        if (is_diagonal and Piece.is_diagonal_slider(piece_type)) or (not is_diagonal and Piece.is_orthogonal_slider(piece_type)):
                            
                            # Friendly piece blocks the check, so this is a pin
                            if is_friendly_piece_along_ray:
                                self.pin_rays |= ray_mask

                            # No friendly piece blocking the attack, so this is a check
                            else:
                                self.check_ray_bitmask |= ray_mask
                                self.in_double_check = self.in_check
                                self.in_check = True
                            break
                        else:
                            # This enemy piece is not able to move in the current direction, and so is blocking any checks/pins
                            break

            # Stop searching for pins if in double check, as the king is the only piece able to move in that case anyway
            if self.in_double_check:
                break
        
        self.not_pin_rays = ~self.pin_rays

        opponent_knight_attacks = 0
        knights = self.board.piece_bitbooards[Piece.make_piece(Piece.Knight, self.board.opponent_color)]
        friendly_king_board = self.board.piece_bitboards[Piece.make_piece(Piece.King, self.board.move_color)]

        while knights:
            knight_square = BitBoardUtility.pop_lsb(knights)
            knight_attacks = BitBoardUtility.KnightAttacks[knight_square]
            opponent_knight_attacks |= knight_attacks

            if knight_attacks & friendly_king_board:
                self.in_double_check = self.in_check
                self.in_check = True
                self.check_ray_bitmask |= 1 << knight_square

        # Pawn attacks
        opponent_pawn_attack_map = BitBoardUtility.pawn_attacks(self.board.piece_bitboards[Piece.make_piece(Piece.Pawn, self.board.opponent_color)], not self.is_white_to_move)

        if BitBoardUtility.contains_square(opponent_pawn_attack_map, self.friendly_king_square):
            self.in_double_check = self.in_check
            self.in_check = True
            possible_pawn_attack_origins = BitBoardUtility.WhitePawnAttacks[self.friendly_king_square] if self.is_white_to_move else BitBoardUtility.BlackPawnAttacks[self.friendly_king_square]
            pawn_check_map = self.board.piece_bitboards[Piece.make_piece(Piece.Pawn, self.board.opponent_color)] & possible_pawn_attack_origins
            self.check_ray_bitmask |= pawn_check_map

        enemy_king_square = self.board.king_square[self.enemy_index]

        self.opponent_attack_map_no_pawns = self.opponent_sliding_attack_map | opponent_knight_attacks | BitBoardUtility.KingMoves[enemy_king_square]
        self.opponent_attack_map = self.opponent_attack_map_no_pawns | opponent_pawn_attack_map

        if not self.in_check:
            self.check_ray_bitmask = 0xFFFFFFFFFFFFFFFF
    
    def _in_check_after_en_passant(self, start_square, target_square, ep_capture_square):
        enemy_ortho = self.board.enemy_orthogonal_sliders

        if enemy_ortho:
            masked_blockers = (self.all_pieces ^ (1 << ep_capture_square | 1 << start_square | 1 << target_square))
            rook_attacks = Magic.get_rook_attacks(self.friendly_king_square, masked_blockers)
            return (rook_attacks & enemy_ortho) != 0
        
        return False