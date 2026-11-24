"""
START

skapa fönster (16x16 rutor, 32 pixlar per ruta, 60 pixlar panel högst upp)
skapa typsnitt och färger 
skapa ett nytt spel med:
minor = 16x16 rutnät, alla False
öppnade = 16x16 rutnät, alla False
minor_utlagda = False
tillstånd = "spelar"
poäng = 0
starttid = None
sluttid = None 
exploderad = None

While running:
OM fönstret stängs eller ESC trycks: avsluta
OM R trycks: skapa nytt spel
OM vänsterklick på en ruta: öppna ruta
OM hgerklick på en ruta: sätt eller ta bort flagga

Rita allt på skärmen:
Fyll bakgrund
Rita panel (poäng, minor kvar, tid)
rita spelplanen:
  för varje ruta: 
    om rutan är öppnad eller ska visa mina:
      fyll med öppen färg (röd om exploderad)
      rita mina om det finns en
      annars rita siffra om granntal > 0
    annars:
      fyll med stängd färg och 3D kanter
    om flaggad: rita flagga
    om förlorad och fel flagga: rita rött kryss
om spelet är slut: rita slutskärm ("Du vann!" eller "BOOM")

vänta lite (60 bildrutor per sekund)

stäng fönstret 
slut


"""
import pygame
import random

# ---------- Inställningar ----------
COLS = 16              # antal kolumner
ROWS = 16              # antal rader
MINES = 40             # antal minor
CELL = 32              # storlek på en ruta i pixlar
TOP = 60               # höjd på infopanelen högst upp
WIDTH = COLS * CELL
HEIGHT = ROWS * CELL + TOP
FPS = 60

# ---------- Färger ----------
BG = (40, 44, 52)
PANEL = (30, 33, 40)
CLOSED = (170, 178, 189)
CLOSED_LIGHT = (210, 216, 224)
CLOSED_DARK = (110, 116, 126)
OPENED = (225, 228, 233)
GRID_LINE = (190, 194, 200)
RED = (220, 50, 50)
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)

# Färg för varje siffra (1-8), som i det klassiska spelet
NUMBER_COLORS = {
    1: (25, 118, 210),
    2: (56, 142, 60),
    3: (211, 47, 47),
    4: (123, 31, 162),
    5: (255, 143, 0),
    6: (0, 151, 167),
    7: (66, 66, 66),
    8: (120, 120, 120),
}

# ---------- Starta Pygame ----------
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Minröj")
clock = pygame.time.Clock()

font_number = pygame.font.Font(None, 30)
font_info = pygame.font.Font(None, 30)
font_big = pygame.font.Font(None, 64)
font_small = pygame.font.Font(None, 28)

# Rektangeln som spelplanen ligger i (allt under infopanelen)
board_rect = pygame.Rect(0, TOP, WIDTH, ROWS * CELL)


# ============================================================
#  Funktioner för spellogiken
# ============================================================

def create_grid(value):
    """Skapar en 2D-lista (ROWS x COLS) där alla rutor har samma startvärde."""
    return [[value for _ in range(COLS)] for _ in range(ROWS)]


def new_game():
    """Skapar ett nytt spel. All information om spelet sparas i en dictionary."""
    return {
        "mines": create_grid(False),     # True där det finns en mina
        "counts": create_grid(0),        # antal minor runt varje ruta
        "opened": create_grid(False),    # True om rutan är öppnad
        "flagged": create_grid(False),   # True om rutan har en flagga
        "mines_placed": False,           # minorna läggs ut först vid första klicket
        "state": "playing",              # "playing", "won" eller "lost"
        "score": 0,
        "start_time": None,
        "end_time": None,
        "exploded": None,                # rutan där man sprängdes
    }


def neighbours(row, col):
    """Returnerar en lista med alla grannrutor (upp till 8 st) runt en ruta."""
    result = []
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue  # hoppa över rutan själv
            r = row + dr
            c = col + dc
            if 0 <= r < ROWS and 0 <= c < COLS:
                result.append((r, c))
    return result


def place_mines(game, safe_row, safe_col):
    """Lägger ut minorna slumpmässigt, men aldrig på eller runt första klicket.
    Då kan man aldrig förlora på första draget."""
    safe = neighbours(safe_row, safe_col) + [(safe_row, safe_col)]

    # Gör en lista med alla rutor där en mina får ligga
    allowed = []
    for r in range(ROWS):
        for c in range(COLS):
            if (r, c) not in safe:
                allowed.append((r, c))

    # Välj MINES st olika rutor
    for r, c in random.sample(allowed, MINES):
        game["mines"][r][c] = True

    # Räkna hur många minor varje ruta har runt sig
    for r in range(ROWS):
        for c in range(COLS):
            count = 0
            for nr, nc in neighbours(r, c):
                if game["mines"][nr][nc]:
                    count += 1
            game["counts"][r][c] = count


def open_cell(game, row, col):
    """Öppnar en ruta. Om rutan har 0 minor runt sig öppnas grannarna också,
    så att ett helt tomt område öppnas på en gång."""
    if game["state"] != "playing":
        return
    if game["opened"][row][col] or game["flagged"][row][col]:
        return

    # Första klicket: lägg ut minorna och starta klockan
    if not game["mines_placed"]:
        place_mines(game, row, col)
        game["mines_placed"] = True
        game["start_time"] = pygame.time.get_ticks()

    # Träffade vi en mina? Då har vi förlorat.
    if game["mines"][row][col]:
        game["state"] = "lost"
        game["exploded"] = (row, col)
        game["end_time"] = pygame.time.get_ticks()
        return

    # "Flood fill" med en stack (lista) istället för rekursion
    stack = [(row, col)]
    while stack:
        r, c = stack.pop()
        if game["opened"][r][c] or game["flagged"][r][c]:
            continue
        game["opened"][r][c] = True
        game["score"] += 10
        if game["counts"][r][c] == 0:
            for nr, nc in neighbours(r, c):
                if not game["opened"][nr][nc]:
                    stack.append((nr, nc))

    if check_win(game):
        game["state"] = "won"
        game["score"] += 500
        game["end_time"] = pygame.time.get_ticks()


def toggle_flag(game, row, col):
    """Sätter eller tar bort en flagga på en oöppnad ruta."""
    if game["state"] != "playing":
        return
    if not game["opened"][row][col]:
        game["flagged"][row][col] = not game["flagged"][row][col]


def check_win(game):
    """Man vinner när alla rutor utan mina är öppnade."""
    for r in range(ROWS):
        for c in range(COLS):
            if not game["mines"][r][c] and not game["opened"][r][c]:
                return False
    return True


def count_flags(game):
    """Räknar hur många flaggor som är utsatta."""
    total = 0
    for r in range(ROWS):
        for c in range(COLS):
            if game["flagged"][r][c]:
                total += 1
    return total


def cell_at_pixel(x, y):
    """Räknar ut vilken ruta (rad, kolumn) en pixel ligger i.
    Returnerar None om pixeln är utanför spelplanen."""
    if not board_rect.collidepoint(x, y):
        return None
    col = x // CELL
    row = (y - TOP) // CELL
    return row, col


def get_time(game):
    """Returnerar hur många sekunder spelet har pågått."""
    if game["start_time"] is None:
        return 0
    if game["end_time"] is not None:
        return (game["end_time"] - game["start_time"]) // 1000
    return (pygame.time.get_ticks() - game["start_time"]) // 1000


# ============================================================
#  Funktioner för att rita
# ============================================================

def draw_flag(rect):
    """Ritar en liten flagga i en ruta."""
    pole_x = rect.x + 13
    pygame.draw.line(screen, BLACK, (pole_x, rect.y + 7), (pole_x, rect.y + 24), 2)
    pygame.draw.polygon(screen, RED, [(pole_x, rect.y + 7),
                                      (pole_x + 11, rect.y + 11),
                                      (pole_x, rect.y + 15)])
    pygame.draw.line(screen, BLACK, (rect.x + 8, rect.y + 25), (rect.x + 20, rect.y + 25), 3)


def draw_mine(rect):
    """Ritar en mina (en svart boll med taggar)."""
    cx, cy = rect.center
    for dx, dy in ((9, 0), (0, 9), (7, 7), (7, -7)):
        pygame.draw.line(screen, BLACK, (cx - dx, cy - dy), (cx + dx, cy + dy), 2)
    pygame.draw.circle(screen, BLACK, (cx, cy), 7)
    pygame.draw.circle(screen, WHITE, (cx - 2, cy - 2), 2)


def draw_board(game):
    """Ritar alla rutor på spelplanen."""
    for r in range(ROWS):
        for c in range(COLS):
            rect = pygame.Rect(c * CELL, TOP + r * CELL, CELL, CELL)
            is_mine = game["mines"][r][c]
            show_mine = game["state"] == "lost" and is_mine and not game["flagged"][r][c]

            if game["opened"][r][c] or show_mine:
                # Öppnad ruta
                color = RED if game["exploded"] == (r, c) else OPENED
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, GRID_LINE, rect, 1)
                if show_mine:
                    draw_mine(rect)
                elif game["counts"][r][c] > 0:
                    number = game["counts"][r][c]
                    text = font_number.render(str(number), True, NUMBER_COLORS[number])
                    screen.blit(text, text.get_rect(center=rect.center))
            else:
                # Oöppnad ruta med lite 3D-effekt
                pygame.draw.rect(screen, CLOSED, rect)
                pygame.draw.line(screen, CLOSED_LIGHT, rect.topleft, (rect.right - 1, rect.top), 2)
                pygame.draw.line(screen, CLOSED_LIGHT, rect.topleft, (rect.left, rect.bottom - 1), 2)
                pygame.draw.line(screen, CLOSED_DARK, (rect.left, rect.bottom - 1), (rect.right - 1, rect.bottom - 1), 2)
                pygame.draw.line(screen, CLOSED_DARK, (rect.right - 1, rect.top), (rect.right - 1, rect.bottom - 1), 2)
                if game["flagged"][r][c]:
                    draw_flag(rect)
                    # Fel flagga när man förlorat -> rött kryss
                    if game["state"] == "lost" and not is_mine:
                        pygame.draw.line(screen, RED, (rect.x + 5, rect.y + 5), (rect.right - 5, rect.bottom - 5), 3)
                        pygame.draw.line(screen, RED, (rect.right - 5, rect.y + 5), (rect.x + 5, rect.bottom - 5), 3)


def draw_panel(game):
    """Ritar infopanelen med poäng, minor kvar och tid."""
    pygame.draw.rect(screen, PANEL, (0, 0, WIDTH, TOP))

    score_text = font_info.render(f"Poäng: {game['score']}", True, WHITE)
    mines_text = font_info.render(f"Minor: {MINES - count_flags(game)}", True, WHITE)
    time_text = font_info.render(f"Tid: {get_time(game)}", True, WHITE)

    screen.blit(score_text, (12, 20))
    screen.blit(mines_text, mines_text.get_rect(center=(WIDTH // 2, TOP // 2)))
    screen.blit(time_text, time_text.get_rect(topright=(WIDTH - 12, 20)))


def draw_end_screen(game):
    """Visar ett meddelande när man har vunnit eller förlorat."""
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 140))
    screen.blit(overlay, (0, 0))

    if game["state"] == "won":
        title = font_big.render("Du vann!", True, (120, 230, 120))
    else:
        title = font_big.render("BOOM!", True, RED)

    info = font_small.render(f"Poäng: {game['score']}   Tid: {get_time(game)} s", True, WHITE)
    hint = font_small.render("Tryck R för att spela igen", True, WHITE)

    screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40)))
    screen.blit(info, info.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 10)))
    screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 45)))


# ============================================================
#  Spelloopen
# ============================================================

game = new_game()
running = True

while running:
    # ----- 1. Hantera händelser (tangenter, mus, stäng fönstret) -----
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_r:
                game = new_game()  # starta om

        elif event.type == pygame.MOUSEBUTTONDOWN:
            cell = cell_at_pixel(*event.pos)
            if cell is not None:
                if event.button == 1:      # vänsterklick
                    open_cell(game, cell[0], cell[1])
                elif event.button == 3:    # högerklick
                    toggle_flag(game, cell[0], cell[1])

    # ----- 2. Rita allt -----
    screen.fill(BG)
    draw_panel(game)
    draw_board(game)
    if game["state"] != "playing":
        draw_end_screen(game)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()