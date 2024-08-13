import numpy as np
from math import abs, max
from Helpers.boardHelpers import BoardHelper
from Board.coord import Coord

class PrecomputedMoveData:
    align_mask = np.zeros((64, 64), dtype=np.uint64)
    dir_ray_mask = np.zeros((8, 64), dtype=np.uint64)
    direction_offsets = [8, -8, -1, 1, 7, -7, 9, -9]

    dir_offsets_2d = [
        (0, 1), # N
        (0, -1), # S
        (-1, 0), # W
        (1, 0), #E
        (-1, 1), # NW
        (1, -1), #SE
        (1, 1), #NE
        (-1, -1) # SW
    ]

    num_squares_to_edge = np.zeros((64, 8), dtype=int)
    knight_moves = [[] for i in range(64)]
    king_moves = [[] for i in range(64)]
    pawn_attack_directions = [[4, 6], [7, 5]]
    pawn_attacks_white = [[] for _ in range(64)]
    pawn_attacks_black = [[] for _ in range(64)]
    direction_lookup = np.zeros(127, dtype=int)
    king_attack_bitboards = np.zeros(64, dtype=np.uint64)
    knight_attack_bitboards = np.zeros(64, dtype=np.uint64)
    pawn_attack_bitboards = [np.zeros(2, dtype=np.uint64) for _ in range(64)]
    rook_moves = np.zeros(64, dtype=np.uint64)
    bishop_moves = np.zeros(64, dtype=np.uint64)
    queen_moves = np.zeros(64, dtype=np.uint64)
    orthogonal_distance = np.zeros((64, 64), dtype=int)
    king_distance = np.zeros((64, 64), dtype=int)
    centre_manhattan_distance = np.zeros(64, dtype=int)

    @staticmethod
    def num_rook_moves_to_reach_square(start_square, target_square):
        return PrecomputedMoveData.orthogonal_distance[start_square, target_square]
    
    @staticmethod
    def num_king_moves_to_reach_square(start_square, target_square):
        return PrecomputedMoveData.king_distance[start_square, target_square]
    
    @staticmethod
    def initialize():
        all_knight_jumps = [15, 17, -17, -15, 10, -6, 6, -10]

        for square_index in range(64):
            y = square_index // 8
            x = square_index % 8

            north = 7 - y
            south = y
            west = x
            east = 7 - x

            PrecomputedMoveData.num_squares_to_edge[square_index][0] = north
            PrecomputedMoveData.num_squares_to_edge[square_index][1] = south
            PrecomputedMoveData.num_squares_to_edge[square_index][2] = west
            PrecomputedMoveData.num_squares_to_edge[square_index][3] = east
            PrecomputedMoveData.num_squares_to_edge[square_index][4] = min(north, west)
            PrecomputedMoveData.num_squares_to_edge[square_index][5] = min(south, east)
            PrecomputedMoveData.num_squares_to_edge[square_index][6] = min(north, east)
            PrecomputedMoveData.num_squares_to_edge[square_index][7] = min(south, west)

            # Calculate all squares knight can jump to from current square
            legal_knight_jumps = []
            knight_bitboard = 0
            for knight_jump_delta in all_knight_jumps:
                knight_jump_square = square_index + knight_jump_delta
                if 0 <= knight_jump_square < 64:
                    knight_square_y = knight_jump_square // 8
                    knight_square_x = knight_jump_square % 8
                    max_coord_move_dst = max(abs(x - knight_square_x), abs(y - knight_square_y))
                    if max_coord_move_dst == 2:
                        legal_knight_jumps.append(knight_jump_square)
                        knight_bitboard |= 1 << knight_jump_square
            
            PrecomputedMoveData.knight_moves[square_index] = legal_knight_jumps
            PrecomputedMoveData.knight_attack_bitboards[square_index] = knight_bitboard

            # Calculate all squares king can move to from current square (not including castling)
            legal_king_moves = []
            for king_move_delta in PrecomputedMoveData.direction_offsets:
                king_move_square = square_index + king_move_delta
                if 0 <= king_move_square < 64:
                    king_square_y = king_move_square // 8
                    king_square_x = king_move_square % 8
                    max_coord_move_dst = max(abs(x - king_square_x), abs(y - king_square_y))
                    if max_coord_move_dst == 1:
                        legal_king_moves.append(king_move_square)
                        PrecomputedMoveData.king_attack_bitboards[square_index] |= 1 << king_move_square

            PrecomputedMoveData.king_moves[square_index] = legal_king_moves

            # Calculate legal pawn captures for white and black
            pawn_captures_white = []
            pawn_captures_black = []
            if x > 0:
                if y < 7:
                    pawn_captures_white.append(square_index + 7)
                    PrecomputedMoveData.pawn_attack_bitboards[square_index][0] |= 1 << (square_index + 7)
                if y > 0:
                    pawn_captures_black.append(square_index - 9)
                    PrecomputedMoveData.pawn_attack_bitboards[square_index][1] |= 1 << (square_index - 9)
            if x < 7:
                if y < 7:
                    pawn_captures_white.append(square_index + 9)
                    PrecomputedMoveData.pawn_attack_bitboards[square_index][0] |= 1 << (square_index + 9)
                if y > 0:
                    pawn_captures_black.append(square_index - 7)
                    PrecomputedMoveData.pawn_attack_bitboards[square_index][1] |= 1 << (square_index - 7)

            PrecomputedMoveData.pawn_attacks_white[square_index] = pawn_captures_white
            PrecomputedMoveData.pawn_attacks_black[square_index] = pawn_captures_black

            # Rook moves
            for direction_index in range(4):
                current_dir_offset = PrecomputedMoveData.direction_offsets[direction_index]
                for n in range(PrecomputedMoveData.num_squares_to_edge[square_index][direction_index]):
                    target_square = square_index + current_dir_offset * (n + 1)
                    PrecomputedMoveData.rook_moves[square_index] |= 1 << target_square

            # Bishop moves
            for direction_index in range(4, 8):
                current_dir_offset = PrecomputedMoveData.direction_offsets[direction_index]
                for n in range(PrecomputedMoveData.num_squares_to_edge[square_index][direction_index]):
                    target_square = square_index + current_dir_offset * (n + 1)
                    PrecomputedMoveData.bishop_moves[square_index] |= 1 << target_square

            PrecomputedMoveData.queen_moves[square_index] = (
                PrecomputedMoveData.rook_moves[square_index] | PrecomputedMoveData.bishop_moves[square_index]
            )

        # Direction lookup initialization
        for i in range(127):
            offset = i - 63
            abs_offset = abs(offset)
            abs_dir = 1
            if abs_offset % 9 == 0:
                abs_dir = 9
            elif abs_offset % 8 == 0:
                abs_dir = 8
            elif abs_offset % 7 == 0:
                abs_dir = 7

            PrecomputedMoveData.direction_lookup[i] = abs_dir * np.sign(offset)

        # Distance lookup initialization
        for square_a in range(64):
            coord_a = BoardHelper.coord_from_index(square_a)
            file_dst_from_centre = max(3 - coord_a.file_index, coord_a.file_index - 4)
            rank_dst_from_centre = max(3 - coord_a.rank_index, coord_a.rank_index - 4)
            PrecomputedMoveData.centre_manhattan_distance[square_a] = file_dst_from_centre + rank_dst_from_centre

            for square_b in range(64):
                coord_b = BoardHelper.coord_from_index(square_b)
                rank_distance = abs(coord_a.rank_index - coord_b.rank_index)
                file_distance = abs(coord_a.file_index - coord_b.file_index)
                PrecomputedMoveData.orthogonal_distance[square_a, square_b] = file_distance + rank_distance
                PrecomputedMoveData.king_distance[square_a, square_b] = max(file_distance, rank_distance)

        # Align mask initialization
        for square_a in range(64):
            for square_b in range(64):
                coord_a = BoardHelper.coord_from_index(square_a)
                coord_b = BoardHelper.coord_from_index(square_b)
                delta = coord_b - coord_a
                dir = Coord(np.sign(delta.file_index), np.sign(delta.rank_index))

                for i in range(-8, 8):
                    coord = coord_a + dir * i
                    if coord.is_valid_square():
                        PrecomputedMoveData.align_mask[square_a, square_b] |= 1 << BoardHelper.index_from_coord(coord)

        # Dir ray mask initialization
        for dir_index, dir_offset_2d in enumerate(PrecomputedMoveData.dir_offsets_2d):
            for square_index in range(64):
                square = BoardHelper.coord_from_index(square_index)

                for i in range(8):
                    coord = square + dir_offset_2d * i
                    if coord.is_valid_square():
                        PrecomputedMoveData.dir_ray_mask[dir_index, square_index] |= 1 << BoardHelper.index_from_coord(coord)
                    else:
                        break

# Initialize PrecomputedMoveData
PrecomputedMoveData.initialize()