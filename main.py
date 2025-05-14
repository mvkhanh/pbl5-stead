import random, sys, pygame, time, copy
from pygame.locals import *
import pygame.gfxdraw

# ------------------------- CẤU HÌNH -------------------------
FPS = 30
WINDOWWIDTH = 1080
WINDOWHEIGHT = 720
SPACESIZE = 80
BOARDWIDTH = 8
BOARDHEIGHT = 8

WHITE_TILE = 'WHITE_TILE'
BLACK_TILE = 'BLACK_TILE'
EMPTY_SPACE = 'EMPTY_SPACE'
HINT_TILE = 'HINT_TILE'
ANIMATIONSPEED = 5

XMARGIN = int((WINDOWWIDTH - (BOARDWIDTH * SPACESIZE)) / 2)
YMARGIN = int((WINDOWHEIGHT - (BOARDHEIGHT * SPACESIZE)) / 2)

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (70, 130, 180)
BRIGHTBLUE = (0, 50, 255)

TEXTBGCOLOR1 = BRIGHTBLUE
TEXTBGCOLOR2 = GREEN
GRIDLINECOLOR = BLACK
TEXTCOLOR = WHITE
HINTCOLOR = BLACK

# ------------------------- HÀM HỖ TRỢ -------------------------
def check_for_quit():
    for event in pygame.event.get((QUIT, KEYUP)):
        if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
            pygame.quit()
            sys.exit()

# ------------------------- LỚP BOARD -------------------------
class Board:
    def __init__(self):
        self.width = BOARDWIDTH
        self.height = BOARDHEIGHT
        self.board = self.get_new_board()
        self.reset_board()

    def get_new_board(self):
        return [[EMPTY_SPACE for _ in range(self.height)] for _ in range(self.width)]
    
    def reset_board(self):
        for x in range(self.width):
            for y in range(self.height):
                self.board[x][y] = EMPTY_SPACE
        self.board[3][3] = WHITE_TILE
        self.board[3][4] = BLACK_TILE
        self.board[4][3] = BLACK_TILE
        self.board[4][4] = WHITE_TILE

    def is_on_board(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def is_valid_move(self, tile, xstart, ystart):
        if not self.is_on_board(xstart, ystart) or self.board[xstart][ystart] != EMPTY_SPACE:
            return False

        self.board[xstart][ystart] = tile  # Đánh dấu tạm thời
        otherTile = WHITE_TILE if tile == BLACK_TILE else BLACK_TILE
        tilesToFlip = []
        for dx, dy in [(0, 1), (1, 1), (1, 0), (1, -1),
                       (0, -1), (-1, -1), (-1, 0), (-1, 1)]:
            x, y = xstart + dx, ystart + dy
            if not self.is_on_board(x, y) or self.board[x][y] != otherTile:
                continue
            x, y = x + dx, y + dy
            while self.is_on_board(x, y) and self.board[x][y] == otherTile:
                x, y = x + dx, y + dy
            if not self.is_on_board(x, y):
                continue
            if self.board[x][y] == tile:
                while True:
                    x, y = x - dx, y - dy
                    if x == xstart and y == ystart:
                        break
                    tilesToFlip.append([x, y])
        self.board[xstart][ystart] = EMPTY_SPACE
        return tilesToFlip if tilesToFlip else False

    def get_valid_moves(self, tile):
        moves = []
        for x in range(self.width):
            for y in range(self.height):
                if self.is_valid_move(tile, x, y):
                    moves.append((x, y))
        return moves

    def get_board_with_valid_moves(self, tile):
        dup = copy.deepcopy(self.board)
        for x, y in self.get_valid_moves(tile):
            dup[x][y] = HINT_TILE
        return dup

    def get_score(self):
        whiteScore = sum(row.count(WHITE_TILE) for row in self.board)
        blackScore = sum(row.count(BLACK_TILE) for row in self.board)
        return {WHITE_TILE: whiteScore, BLACK_TILE: blackScore}

    def make_move(self, tile, xstart, ystart, display_obj=None, real_move=False):
        tilesToFlip = self.is_valid_move(tile, xstart, ystart)
        if not tilesToFlip:
            return False
        self.board[xstart][ystart] = tile
        if real_move and display_obj:
            display_obj.animate_tile_change(tilesToFlip, tile, (xstart, ystart))
        for x, y in tilesToFlip:
            self.board[x][y] = tile
        return True

# ------------------------- LỚP DISPLAY -------------------------
class Display:
    def __init__(self):
        pygame.init()
        self.surface = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
        pygame.display.set_caption('Flippy')
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Segoe UI", 24, bold=True)
        self.bigfont = pygame.font.SysFont("Segoe UI", 32, bold=True)
        self.load_images()

    def load_images(self):
        self.boardImage = pygame.image.load('009b77.png').convert()
        self.boardImage = pygame.transform.smoothscale(self.boardImage, (BOARDWIDTH * SPACESIZE, BOARDHEIGHT * SPACESIZE))
        self.boardImageRect = self.boardImage.get_rect()
        self.boardImageRect.topleft = (XMARGIN, YMARGIN)
        self.bgImage = pygame.image.load('Untitled.png').convert()
        self.bgImage = pygame.transform.smoothscale(self.bgImage, (WINDOWWIDTH, WINDOWHEIGHT))
        self.bgImage.blit(self.boardImage, self.boardImageRect)

    def translate_board_to_pixel(self, x, y):
        return XMARGIN + x * SPACESIZE + SPACESIZE // 2, YMARGIN + y * SPACESIZE + SPACESIZE // 2

    def draw_board(self, board_matrix):
        self.surface.blit(self.bgImage, self.bgImage.get_rect())
        for x in range(BOARDWIDTH + 1):
            pygame.draw.line(self.surface, GRIDLINECOLOR, (x * SPACESIZE + XMARGIN, YMARGIN),
                             (x * SPACESIZE + XMARGIN, YMARGIN + BOARDHEIGHT * SPACESIZE))
        for y in range(BOARDHEIGHT + 1):
            pygame.draw.line(self.surface, GRIDLINECOLOR, (XMARGIN, y * SPACESIZE + YMARGIN),
                             (XMARGIN + BOARDWIDTH * SPACESIZE, y * SPACESIZE + YMARGIN))
        for x in range(BOARDWIDTH):
            for y in range(BOARDHEIGHT):
                center = self.translate_board_to_pixel(x, y)
                if board_matrix[x][y] in (WHITE_TILE, BLACK_TILE):
                    color = WHITE if board_matrix[x][y] == WHITE_TILE else BLACK
                    radius = SPACESIZE // 2 - 4
                    pygame.gfxdraw.filled_circle(self.surface, center[0], center[1], radius, color)
                    pygame.gfxdraw.aacircle(self.surface, center[0], center[1], radius, BLACK)
                elif board_matrix[x][y] == HINT_TILE:
                    pygame.gfxdraw.aacircle(self.surface, center[0], center[1], SPACESIZE//2 - 4, BLACK)

    def animate_tile_change(self, tilesToFlip, tileColor, additionalTile):
        color_base = WHITE if tileColor == WHITE_TILE else BLACK
        add_center = self.translate_board_to_pixel(additionalTile[0], additionalTile[1])
        pygame.draw.circle(self.surface, color_base, add_center, SPACESIZE // 2 - 4)
        pygame.display.update()
        for rgb in range(0, 255, int(ANIMATIONSPEED * 2.55)):
            rgb = max(0, min(255, rgb))
            color = (rgb, rgb, rgb) if tileColor == WHITE_TILE else (255 - rgb, 255 - rgb, 255 - rgb)
            for x, y in tilesToFlip:
                center = self.translate_board_to_pixel(x, y)
                pygame.draw.circle(self.surface, color, center, SPACESIZE // 2 - 4)
            pygame.display.update()
            self.clock.tick(FPS)
            check_for_quit()

    def draw_button(self, rect, text, base_color, hover_color, mouse_pos):
        is_hover = rect.collidepoint(mouse_pos)
        color = hover_color if is_hover else base_color
        pygame.draw.rect(self.surface, color, rect, border_radius=12)
        text_surf = self.font.render(text, True, TEXTCOLOR)
        text_rect = text_surf.get_rect(center=rect.center)
        self.surface.blit(text_surf, text_rect)
        return is_hover

    def draw_info(self, board_obj, playerTile, computerTile, turn):
        scores = board_obj.get_score()
        info_text = f"Player Score: {scores[playerTile]}    Computer Score: {scores[computerTile]}    {turn.title()}'s Turn"
        info_surf = self.font.render(info_text, True, TEXTCOLOR)
        info_rect = info_surf.get_rect()
        info_rect.bottomleft = (10, WINDOWHEIGHT - 5)
        self.surface.blit(info_surf, info_rect)

    def get_space_clicked(self, mousex, mousey):
        for x in range(BOARDWIDTH):
            for y in range(BOARDHEIGHT):
                if XMARGIN + x * SPACESIZE < mousex < XMARGIN + (x+1)*SPACESIZE and \
                   YMARGIN + y * SPACESIZE < mousey < YMARGIN + (y+1)*SPACESIZE:
                    return (x, y)
        return None

    def show_end_game_screen(self, result_text):
        clock = pygame.time.Clock()
        yes_color = GREEN
        yes_hover = (100, 160, 220)
        no_color = (150, 50, 50)
        no_hover = (200, 80, 80)
        while True:
            self.surface.blit(self.bgImage, (0, 0))
            def render_shadow(text, font, color, shadow_color, center):
                shadow = font.render(text, True, shadow_color)
                text_surf = font.render(text, True, color)
                shadow_rect = shadow.get_rect(center=(center[0]+2, center[1]+2))
                text_rect = text_surf.get_rect(center=center)
                self.surface.blit(shadow, shadow_rect)
                self.surface.blit(text_surf, text_rect)
            render_shadow(result_text, self.bigfont, TEXTCOLOR, BLACK, (WINDOWWIDTH//2, WINDOWHEIGHT//2 - 60))
            render_shadow("Play again?", self.font, TEXTCOLOR, BLACK, (WINDOWWIDTH//2, WINDOWHEIGHT//2))
            button_width = 120
            button_height = 50
            button_radius = 15
            yes_rect = pygame.Rect(0, 0, button_width, button_height)
            yes_rect.center = (WINDOWWIDTH//2 - 100, WINDOWHEIGHT//2 + 60)
            no_rect = pygame.Rect(0, 0, button_width, button_height)
            no_rect.center = (WINDOWWIDTH//2 + 100, WINDOWHEIGHT//2 + 60)
            mx, my = pygame.mouse.get_pos()
            yes_hovered = yes_rect.collidepoint(mx, my)
            no_hovered = no_rect.collidepoint(mx, my)
            pygame.draw.rect(self.surface, yes_hover if yes_hovered else yes_color, yes_rect, border_radius=button_radius)
            pygame.draw.rect(self.surface, no_hover if no_hovered else no_color, no_rect, border_radius=button_radius)
            yes_text = self.font.render("Yes", True, TEXTCOLOR)
            no_text = self.font.render("No", True, TEXTCOLOR)
            self.surface.blit(yes_text, yes_text.get_rect(center=yes_rect.center))
            self.surface.blit(no_text, no_text.get_rect(center=no_rect.center))
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == MOUSEBUTTONUP:
                    if yes_hovered:
                        pygame.event.clear()
                        return True
                    elif no_hovered:
                        pygame.quit()
                        sys.exit()
            pygame.display.update()
            clock.tick(FPS)

# ------------------------- LỚP PLAYER -------------------------
class Player:
    def __init__(self, tile, display_obj):
        self.tile = tile
        self.display = display_obj

    def get_move(self, board_obj, newGameRect, hintsRect):
        valid_moves = board_obj.get_valid_moves(self.tile)
        if not valid_moves:
            return None
        move = None
        # Chỉ xử lý sự kiện click vào ô bàn cờ; nút đã được xử lý từ Game.run()
        while move is None:
            check_for_quit()
            for event in pygame.event.get():
                if event.type == MOUSEBUTTONUP:
                    mousex, mousey = event.pos
                    move = self.display.get_space_clicked(mousex, mousey)
                    if move and move not in valid_moves:
                        move = None
            board_to_draw = board_obj.get_board_with_valid_moves(self.tile)
            self.display.draw_board(board_to_draw)
            self.display.draw_info(board_obj, self.tile, WHITE_TILE if self.tile == BLACK_TILE else BLACK_TILE, "player")
            pygame.display.update()
            self.display.clock.tick(FPS)
        return move


# ------------------------- LỚP COMPUTERPLAYER -------------------------
class ComputerPlayer(Player):
    def __init__(self, tile, display_obj):
        super().__init__(tile, display_obj)

    def get_move(self, board_obj):
        valid_moves = board_obj.get_valid_moves(self.tile)
        if not valid_moves:
            return None
        pause_time = time.time() + random.randint(5,15) * 0.1
        while time.time() < pause_time:
            pygame.display.update()
        return self.get_computer_move(board_obj.board)

    @staticmethod
    def evaluate_board(board_state, aiTile):
        whiteScore = sum(row.count(WHITE_TILE) for row in board_state)
        blackScore = sum(row.count(BLACK_TILE) for row in board_state)
        return (blackScore - whiteScore) if aiTile == BLACK_TILE else (whiteScore - blackScore)

    @staticmethod
    def minimax_ab(board_state, depth, alpha, beta, maximizing, aiTile):
        # Khởi tạo đối tượng Board tạm thời
        tmp = Board()
        tmp.board = board_state
        current_tile = aiTile if maximizing else (WHITE_TILE if aiTile == BLACK_TILE else BLACK_TILE)
        valid_moves = tmp.get_valid_moves(current_tile)
        if depth == 0 or not valid_moves:
            return ComputerPlayer.evaluate_board(board_state, aiTile), None
        best_move = None
        if maximizing:
            maxEval = -float('inf')
            for move in valid_moves:
                new_board_state = copy.deepcopy(board_state)
                tmp2 = Board()
                tmp2.board = new_board_state
                tmp2.make_move(aiTile, move[0], move[1])
                eval_score, _ = ComputerPlayer.minimax_ab(tmp2.board, depth - 1, alpha, beta, False, aiTile)
                if eval_score > maxEval:
                    maxEval = eval_score
                    best_move = move
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return maxEval, best_move
        else:
            minEval = float('inf')
            opponentTile = WHITE_TILE if aiTile == BLACK_TILE else BLACK_TILE
            for move in valid_moves:
                new_board_state = copy.deepcopy(board_state)
                tmp2 = Board()
                tmp2.board = new_board_state
                tmp2.make_move(opponentTile, move[0], move[1])
                eval_score, _ = ComputerPlayer.minimax_ab(tmp2.board, depth - 1, alpha, beta, True, aiTile)
                if eval_score < minEval:
                    minEval = eval_score
                    best_move = move
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return minEval, best_move

    def get_computer_move(self, board_state):
        _, move = ComputerPlayer.minimax_ab(board_state, 3, -float('inf'), float('inf'), True, self.tile)
        return move

# ------------------------- LỚP GAME -------------------------
class Game:
    def __init__(self):
        self.display = Display()
        self.board = Board()
        self.player_tile, self.computer_tile = self.enter_player_tile()
        # Nếu người chơi chọn Black thì được đi trước (giống escape.py)
        self.turn = 'player' if self.player_tile == BLACK_TILE else 'computer'
        self.human = Player(self.player_tile, self.display)
        self.computer = ComputerPlayer(self.computer_tile, self.display)
        self.button_width = 140
        self.button_height = 40
        self.padding = 10
        self.newGameRect = pygame.Rect(WINDOWWIDTH - self.button_width - self.padding, self.padding,
                                        self.button_width, self.button_height)
        self.hintsRect = pygame.Rect(WINDOWWIDTH - self.button_width - self.padding,
                                     self.padding + self.button_height + 10,
                                     self.button_width, self.button_height)
        self.showHints = False

    def enter_player_tile(self):
        clock = pygame.time.Clock()
        question = 'Do you want to be white or black?'
        white_text = 'White'
        black_text = 'Black'
        button_width = 150
        button_height = 60
        button_radius = 15
        while True:
            self.display.surface.blit(self.display.bgImage, (0, 0))
            mx, my = pygame.mouse.get_pos()
            def render_shadow(text, font, color, shadow_color, center):
                shadow = font.render(text, True, shadow_color)
                text_surf = font.render(text, True, color)
                shadow_rect = shadow.get_rect(center=(center[0]+2, center[1]+2))
                text_rect = text_surf.get_rect(center=center)
                self.display.surface.blit(shadow, shadow_rect)
                self.display.surface.blit(text_surf, text_rect)
            render_shadow(question, self.display.font, TEXTCOLOR, BLACK, (WINDOWWIDTH//2, WINDOWHEIGHT//4))
            white_rect = pygame.Rect(0, 0, button_width, button_height)
            white_rect.center = (WINDOWWIDTH//2 - 120, WINDOWHEIGHT//2)
            black_rect = pygame.Rect(0, 0, button_width, button_height)
            black_rect.center = (WINDOWWIDTH//2 + 120, WINDOWHEIGHT//2)
            white_hover = white_rect.collidepoint(mx, my)
            black_hover = black_rect.collidepoint(mx, my)
            pygame.draw.rect(self.display.surface, (100, 160, 220) if white_hover else (70, 130, 180), white_rect, border_radius=button_radius)
            pygame.draw.rect(self.display.surface, (100, 160, 220) if black_hover else (70, 130, 180), black_rect, border_radius=button_radius)
            white_text_surf = self.display.bigfont.render(white_text, True, TEXTCOLOR)
            white_text_rect = white_text_surf.get_rect(center=white_rect.center)
            self.display.surface.blit(white_text_surf, white_text_rect)
            black_text_surf = self.display.bigfont.render(black_text, True, TEXTCOLOR)
            black_text_rect = black_text_surf.get_rect(center=black_rect.center)
            self.display.surface.blit(black_text_surf, black_text_rect)
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == MOUSEBUTTONDOWN:
                    if white_hover:
                        pygame.time.wait(150)
                        pygame.event.clear()
                        return [WHITE_TILE, BLACK_TILE]
                    elif black_hover:
                        pygame.time.wait(150)
                        pygame.event.clear()
                        return [BLACK_TILE, WHITE_TILE]
            pygame.display.update()
            clock.tick(FPS)

    def run(self):
        running = True
        while running:
            self.board.reset_board()
            game_over = False
            while not game_over:
                check_for_quit()
                # Nếu bật gợi ý thì lấy bảng có gợi ý, ngược lại lấy bảng bình thường.
                board_to_draw = self.board.board
                if self.showHints:
                    board_to_draw = self.board.get_board_with_valid_moves(self.human.tile)
                # Vẽ bàn cờ, thông tin và nút
                self.display.draw_board(board_to_draw)
                self.display.draw_info(self.board, self.human.tile, self.computer.tile, self.turn)
                mouse_pos = pygame.mouse.get_pos()
                hover_new = self.display.draw_button(self.newGameRect, "New Game", TEXTBGCOLOR2, (100,160,220), mouse_pos)
                hover_hints = self.display.draw_button(self.hintsRect, "Hints", TEXTBGCOLOR2, (100,160,220), mouse_pos)
                pygame.display.update()
                self.display.clock.tick(FPS)

                # Xử lý sự kiện cho toàn bộ giao diện trong vòng lặp chính:
                for event in pygame.event.get():
                    if event.type == MOUSEBUTTONUP:
                        mx, my = event.pos
                        if self.newGameRect.collidepoint(mx, my):
                            return True   # Khởi động lại game
                        if self.hintsRect.collidepoint(mx, my):
                            self.showHints = not self.showHints
                            pygame.time.wait(150)
                            pygame.event.clear()
                            continue

                # Sau khi xử lý nút, nếu lượt người chơi thì lấy nước đi từ bàn cờ
                if self.turn == 'player':
                    if not self.board.get_valid_moves(self.human.tile):
                        game_over = True
                        break
                    move = self.human.get_move(self.board)  
                    # Ở đây, get_move chỉ xử lý click lên bàn cờ (không vẽ nút)
                    if move:
                        self.board.make_move(self.human.tile, move[0], move[1],
                                            display_obj=self.display, real_move=True)
                        if self.board.get_valid_moves(self.computer.tile):
                            self.turn = 'computer'
                else:
                    # Xử lý lượt máy (vẫn như cũ)
                    if not self.board.get_valid_moves(self.computer.tile):
                        game_over = True
                        break
                    self.display.draw_board(self.board.board)
                    self.display.draw_info(self.board, self.human.tile, self.computer.tile, self.turn)
                    pygame.display.update()
                    move = self.computer.get_move(self.board)
                    if move:
                        self.board.make_move(self.computer.tile, move[0], move[1],
                                            display_obj=self.display, real_move=True)
                        if self.board.get_valid_moves(self.human.tile):
                            self.turn = 'player'
                            pygame.event.clear()
            # Hiển thị màn hình kết thúc game, sau đó hỏi chơi lại
            self.display.draw_board(self.board.board)
            scores = self.board.get_score()
            if scores[self.human.tile] > scores[self.computer.tile]:
                result_text = 'You win!'
            elif scores[self.human.tile] < scores[self.computer.tile]:
                result_text = 'You lose!'
            else:
                result_text = "It's a tie!"
            if self.display.show_end_game_screen(result_text):
                running = True
            else:
                running = False

# ------------------------- CHẠY CHƯƠNG TRÌNH -------------------------
if __name__ == '__main__':
    while True:
        game = Game()
        if not game.run():
            break
