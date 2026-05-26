#!/usr/bin/env python3
"""Simple Tetris game using pygame."""

import random
import sys

import pygame

# Grid
COLS = 10
ROWS = 20
CELL = 30
SIDEBAR = 160

# Window
WIDTH = COLS * CELL + SIDEBAR
HEIGHT = ROWS * CELL

# Timing (ms)
DROP_INITIAL = 800
DROP_MIN = 120
DROP_STEP = 40

# Colors (R, G, B)
BLACK = (15, 15, 20)
GRID_COLOR = (35, 35, 45)
WHITE = (230, 230, 235)
GRAY = (120, 120, 130)

# Tetromino shapes: list of rotation states, each state is list of (x, y) offsets
SHAPES = {
    "I": [
        [(0, 1), (1, 1), (2, 1), (3, 1)],
        [(2, 0), (2, 1), (2, 2), (2, 3)],
    ],
    "O": [
        [(1, 0), (2, 0), (1, 1), (2, 1)],
    ],
    "T": [
        [(1, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (1, 2)],
        [(1, 0), (0, 1), (1, 1), (1, 2)],
    ],
    "S": [
        [(1, 0), (2, 0), (0, 1), (1, 1)],
        [(1, 0), (1, 1), (2, 1), (2, 2)],
    ],
    "Z": [
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        [(2, 0), (1, 1), (2, 1), (1, 2)],
    ],
    "J": [
        [(0, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (2, 2)],
        [(1, 0), (1, 1), (0, 2), (1, 2)],
    ],
    "L": [
        [(2, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (1, 2), (2, 2)],
        [(0, 1), (1, 1), (2, 1), (0, 2)],
        [(0, 0), (1, 0), (1, 1), (1, 2)],
    ],
}

COLORS = {
    "I": (0, 240, 240),
    "O": (240, 240, 0),
    "T": (160, 0, 240),
    "S": (0, 240, 0),
    "Z": (240, 0, 0),
    "J": (0, 80, 240),
    "L": (240, 160, 0),
}


class Piece:
    def __init__(self, kind: str):
        self.kind = kind
        self.rotations = SHAPES[kind]
        self.rotation = 0
        self.x = COLS // 2 - 2
        self.y = 0
        self.color = COLORS[kind]

    def cells(self) -> list[tuple[int, int]]:
        shape = self.rotations[self.rotation % len(self.rotations)]
        return [(self.x + dx, self.y + dy) for dx, dy in shape]


class Tetris:
    def __init__(self):
        self.board: list[list[str | None]] = [
            [None for _ in range(COLS)] for _ in range(ROWS)
        ]
        self.score = 0
        self.lines = 0
        self.level = 1
        self.game_over = False
        self.current = self._new_piece()
        self.next_piece = self._new_piece()
        self.drop_interval = DROP_INITIAL

    def _new_piece(self) -> Piece:
        return Piece(random.choice(list(SHAPES.keys())))

    def _valid(self, cells: list[tuple[int, int]]) -> bool:
        for x, y in cells:
            if x < 0 or x >= COLS or y >= ROWS:
                return False
            if y >= 0 and self.board[y][x] is not None:
                return False
        return True

    def _lock_piece(self) -> None:
        for x, y in self.current.cells():
            if y < 0:
                self.game_over = True
                return
            self.board[y][x] = self.current.kind

        cleared = self._clear_lines()
        if cleared:
            self.lines += cleared
            self.score += [0, 100, 300, 500, 800][cleared] * self.level
            self.level = 1 + self.lines // 10
            self.drop_interval = max(
                DROP_MIN, DROP_INITIAL - (self.level - 1) * DROP_STEP
            )

        self.current = self.next_piece
        self.next_piece = self._new_piece()
        if not self._valid(self.current.cells()):
            self.game_over = True

    def _clear_lines(self) -> int:
        new_board = [row for row in self.board if any(cell is None for cell in row)]
        cleared = ROWS - len(new_board)
        for _ in range(cleared):
            new_board.insert(0, [None for _ in range(COLS)])
        self.board = new_board
        return cleared

    def move(self, dx: int, dy: int) -> bool:
        self.current.x += dx
        self.current.y += dy
        if self._valid(self.current.cells()):
            return True
        self.current.x -= dx
        self.current.y -= dy
        return False

    def rotate(self) -> None:
        old = self.current.rotation
        self.current.rotation = (self.current.rotation + 1) % len(
            self.current.rotations
        )
        if not self._valid(self.current.cells()):
            for kick in (-1, 1, -2, 2):
                self.current.x += kick
                if self._valid(self.current.cells()):
                    return
                self.current.x -= kick
            self.current.rotation = old

    def hard_drop(self) -> None:
        while self.move(0, 1):
            self.score += 2
        self._lock_piece()

    def soft_drop(self) -> None:
        if self.move(0, 1):
            self.score += 1
        else:
            self._lock_piece()

    def tick(self) -> None:
        if self.game_over:
            return
        if not self.move(0, 1):
            self._lock_piece()

    def ghost_cells(self) -> list[tuple[int, int]]:
        ghost = Piece(self.current.kind)
        ghost.rotation = self.current.rotation
        ghost.x = self.current.x
        ghost.y = self.current.y
        while True:
            ghost.y += 1
            if not self._valid(ghost.cells()):
                ghost.y -= 1
                break
        return ghost.cells()


def draw_cell(
    surface: pygame.Surface, x: int, y: int, color: tuple[int, int, int]
) -> None:
    rect = pygame.Rect(x * CELL, y * CELL, CELL, CELL)
    pygame.draw.rect(surface, color, rect.inflate(-2, -2), border_radius=4)


def draw_board(screen: pygame.Surface, game: Tetris) -> None:
    board_surface = pygame.Surface((COLS * CELL, ROWS * CELL))
    board_surface.fill(BLACK)

    for y in range(ROWS):
        for x in range(COLS):
            pygame.draw.rect(
                board_surface,
                GRID_COLOR,
                (x * CELL, y * CELL, CELL, CELL),
                1,
            )
            kind = game.board[y][x]
            if kind:
                draw_cell(board_surface, x, y, COLORS[kind])

    for x, y in game.ghost_cells():
        if y >= 0:
            rect = pygame.Rect(x * CELL, y * CELL, CELL, CELL)
            pygame.draw.rect(board_surface, GRAY, rect.inflate(-2, -2), 2, border_radius=4)

    for x, y in game.current.cells():
        if y >= 0:
            draw_cell(board_surface, x, y, game.current.color)

    screen.blit(board_surface, (0, 0))


def draw_sidebar(screen: pygame.Surface, game: Tetris, font: pygame.font.Font) -> None:
    x0 = COLS * CELL + 16
    lines = [
        "俄罗斯方块",
        "",
        f"分数: {game.score}",
        f"行数: {game.lines}",
        f"等级: {game.level}",
        "",
        "下一块:",
        "",
        "← → 移动",
        "↑ 旋转",
        "↓ 加速下落",
        "空格 硬降",
        "P 暂停",
        "R 重新开始",
        "Esc 退出",
    ]
    for i, text in enumerate(lines):
        surf = font.render(text, True, WHITE)
        screen.blit(surf, (x0, 16 + i * 26))

    # Preview next piece
    preview_x = x0
    preview_y = 16 + 8 * 26
    for dx, dy in game.next_piece.rotations[0]:
        rect = pygame.Rect(
            preview_x + dx * 22,
            preview_y + dy * 22,
            20,
            20,
        )
        pygame.draw.rect(screen, game.next_piece.color, rect, border_radius=3)

    if game.game_over:
        overlay = font.render("游戏结束!", True, (255, 80, 80))
        screen.blit(overlay, (x0, HEIGHT - 80))


def main() -> None:
    pygame.init()
    pygame.display.set_caption("俄罗斯方块")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("pingfang sc,stheiti,arial", 18)

    game = Tetris()
    paused = False
    last_drop = pygame.time.get_ticks()

    while True:
        now = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit(0)
                if event.key == pygame.K_p:
                    paused = not paused
                if event.key == pygame.K_r:
                    game = Tetris()
                    paused = False
                    last_drop = now
                if paused or game.game_over:
                    continue
                if event.key == pygame.K_LEFT:
                    game.move(-1, 0)
                elif event.key == pygame.K_RIGHT:
                    game.move(1, 0)
                elif event.key == pygame.K_DOWN:
                    game.soft_drop()
                elif event.key == pygame.K_UP:
                    game.rotate()
                elif event.key == pygame.K_SPACE:
                    game.hard_drop()

        if not paused and not game.game_over:
            if now - last_drop >= game.drop_interval:
                game.tick()
                last_drop = now

        screen.fill(BLACK)
        draw_board(screen, game)
        draw_sidebar(screen, game, font)
        if paused:
            pause_text = font.render("已暂停", True, WHITE)
            screen.blit(pause_text, (COLS * CELL // 2 - 30, ROWS * CELL // 2))
        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()
