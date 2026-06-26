import time
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Header, Footer, Static, Label
from textual.reactive import reactive
from rich.table import Table
from rich.text import Text
from rich import box
from rich.console import Console
import io
from game import SudokuGame

LARGE_DIGITS = {
    1: " ╻ \n ┃ \n ╹ ",
    2: "╺━┓\n┏━┛\n┗━╸",
    3: "╺━┓\n╺━┫\n╺━┛",
    4: "╻ ╻\n┗━┫\n  ╹",
    5: "┏━╸\n┗━┓\n╺━┛",
    6: "┏━╸\n┣━┓\n┗━┛",
    7: "╺━┓\n  ┃\n  ╹",
    8: "┏━┓\n┣━┫\n┗━┛",
    9: "┏━┓\n┗━┫\n╺━┛",
}

THEMES = {
    "peach": {"bg": "#1A1A1A", "fg": "#E0E0E0", "heavy": "#CC7766", "fixed": "#CC7766", "sel": "#3A2A2A"},
    "blue": {"bg": "#0E1824", "fg": "#E0E0E0", "heavy": "#5588CC", "fixed": "#5588CC", "sel": "#182A40"},
    "green": {"bg": "#14241A", "fg": "#E0E0E0", "heavy": "#55AA77", "fixed": "#55AA77", "sel": "#1C3626"},
    "dracula": {"bg": "#282A36", "fg": "#F8F8F2", "heavy": "#BD93F9", "fixed": "#50FA7B", "sel": "#44475A"}
}

class StopwatchWidget(Static):
    start_time = reactive(0.0)
    running = reactive(False)
    elapsed_time = reactive(0.0)

    def on_mount(self) -> None:
        self.update_timer = self.set_interval(1 / 10, self.update_time, pause=True)

    def update_time(self) -> None:
        if self.running:
            self.elapsed_time = time.time() - self.start_time

    def start(self) -> None:
        self.start_time = time.time()
        self.running = True
        self.update_timer.resume()

    def stop(self) -> None:
        if self.running:
            self.running = False
            self.update_timer.pause()
            self.elapsed_time = time.time() - self.start_time
        
    def reset(self) -> None:
        self.running = False
        self.update_timer.pause()
        self.elapsed_time = 0.0

    def get_large_time(self, mins: int, secs: int) -> str:
        digits = {
            '1': [" ╻ ", " ┃ ", " ╹ "],
            '2': ["╺━┓", "┏━┛", "┗━╸"],
            '3': ["╺━┓", "╺━┫", "╺━┛"],
            '4': ["╻ ╻", "┗━┫", "  ╹"],
            '5': ["┏━╸", "┗━┓", "╺━┛"],
            '6': ["┏━╸", "┣━┓", "┗━┛"],
            '7': ["╺━┓", "  ┃", "  ╹"],
            '8': ["┏━┓", "┣━┫", "┗━┛"],
            '9': ["┏━┓", "┗━┫", "╺━┛"],
            '0': ["┏━┓", "┃ ┃", "┗━┛"],
            ':': [" ", "•", "•"]
        }
        
        time_str = f"{mins:02d}:{secs:02d}"
        lines = ["", "", ""]
        for i in range(3):
            lines[i] = " ".join(digits[char][i] for char in time_str)
        
        return "\n".join(lines)

    def render(self) -> str:
        mins, secs = divmod(int(self.elapsed_time), 60)
        large_time = self.get_large_time(mins, secs)
        return f"[b]⏱  Time:[/b]\n[#FFFFFF]{large_time}[/]"

class BoardWidget(Static):
    def start_snake(self):
        buf = io.StringIO()
        console = Console(file=buf, force_terminal=True, color_system="truecolor", width=120)
        console.print(self.render_table())
        ansi_str = buf.getvalue()
        
        t = Text.from_ansi(ansi_str)
        self.cached_lines = [line for line in t.split("\n") if len(line) > 0]
        
        height = len(self.cached_lines)
        width = len(self.cached_lines[0]) if height > 0 else 0
        
        self.perimeter = []
        for c in range(width): self.perimeter.append((0, c))
        for r in range(1, height): self.perimeter.append((r, width - 1))
        for c in range(width - 2, -1, -1): self.perimeter.append((height - 1, c))
        for r in range(height - 2, 0, -1): self.perimeter.append((r, 0))
            
        self.animating = True
        self.snake_pos = 0
        self.snake_timer = self.set_interval(0.015, self.update_snake)

    def update_snake(self):
        self.snake_pos += 1
        if self.snake_pos > len(self.perimeter) + 20:
            self.snake_timer.stop()
        self.refresh()

    def render(self):
        if getattr(self, 'animating', False):
            import copy
            lines = copy.deepcopy(self.cached_lines)
            snake_head = self.snake_pos
            snake_tail = max(0, snake_head - 10)
            
            snake_cells = set()
            for p in range(snake_tail, snake_head):
                if 0 <= p < len(self.perimeter):
                    snake_cells.add(self.perimeter[p])
                    
            traversed = set()
            for p in range(0, snake_head):
                if 0 <= p < len(self.perimeter):
                    traversed.add(self.perimeter[p])
            
            theme = THEMES[self.app.current_theme_name]
            for r, c in traversed:
                if 0 <= r < len(lines) and 0 <= c < len(lines[r]):
                    if (r, c) in snake_cells:
                        lines[r].stylize("bold #FFFFFF", c, c+1)
                    else:
                        lines[r].stylize(f"bold {theme['heavy']}", c, c+1)
            
            return Text("\n").join(lines)
        return self.render_table()

    def render_table(self):
        theme = THEMES[self.app.current_theme_name]
        heavy_color = theme["heavy"]
        bg_color = theme["bg"]
        fg_color = theme["fg"]
        fixed_color = theme["fixed"]
        sel_color = theme["sel"]
        err_color = "#FFFFFF on #883333"

        use_large = self.app.size.height >= 46

        outer = Table(show_header=False, box=box.HEAVY, padding=(0,0), style=heavy_color, show_lines=True)
        for _ in range(3): outer.add_column()

        for br in range(3):
            row_tables = []
            for bc in range(3):
                inner = Table(show_header=False, box=box.SQUARE, padding=(0,0), style="#444444", show_lines=use_large)
                for _ in range(3): inner.add_column(width=7 if use_large else 3, justify="center")

                for r in range(3):
                    cells_render = []
                    for c in range(3):
                        row = br * 3 + r
                        col = bc * 3 + c
                        cell_data = self.app.cells_state[row][col]
                        
                        if cell_data['error']:
                            c_style = err_color
                        elif cell_data['selected']:
                            c_style = f"{fg_color} on {sel_color}"
                        elif cell_data['fixed']:
                            c_style = f"{fixed_color} on {bg_color}"
                        else:
                            c_style = f"{fg_color} on {bg_color}"

                        if cell_data['value'] != 0:
                            if use_large:
                                content = LARGE_DIGITS[cell_data['value']]
                            else:
                                content = str(cell_data['value'])
                        elif cell_data['notes']:
                            if use_large:
                                lines = []
                                for nr in range(3):
                                    line = ""
                                    for nc in range(3):
                                        n = nr * 3 + nc + 1
                                        line += str(n) if n in cell_data['notes'] else " "
                                        if nc < 2: line += " "
                                    lines.append(line)
                                content = "\n".join(lines)
                            else:
                                notes_str = "".join(str(n) for n in sorted(cell_data['notes']))
                                if len(notes_str) > 3:
                                    content = notes_str[:2] + "."
                                else:
                                    content = notes_str
                            c_style = f"#888888 on {sel_color if cell_data['selected'] else bg_color}"
                        else:
                            content = " \n \n " if use_large else " "

                        cells_render.append(Text(content, style=c_style, justify="center", no_wrap=True))
                    inner.add_row(*cells_render)
                row_tables.append(inner)
            outer.add_row(*row_tables)
            
        return outer

    def on_click(self, event) -> None:
        use_large = self.app.size.height >= 46
        if use_large:
            col = self._get_index(event.x, [2, 10, 18, 28, 36, 44, 54, 62, 70], 7)
            row = self._get_index(event.y, [2, 6, 10, 16, 20, 24, 30, 34, 38], 3)
        else:
            col = self._get_index(event.x, [2, 6, 10, 16, 20, 24, 30, 34, 38], 3)
            row = self._get_index(event.y, [2, 3, 4, 8, 9, 10, 14, 15, 16], 1)
        if row is not None and col is not None:
            self.app.select_cell(row, col)

    def _get_index(self, pos, starts, length):
        for i, start in enumerate(starts):
            if start <= pos < start + length:
                return i
        return None

class SudokuApp(App):
    CSS = """
    Screen {
        align: center middle;
    }
    
    #main-container {
        align: center middle;
    }
    
    #theme-controls {
        dock: right;
        width: 14;
        height: auto;
        margin: 1;
    }

    #controls {
        height: 3;
        width: 100%;
        align: center middle;
        margin-bottom: 1;
    }
    
    Button {
        border: none;
        margin: 0 1;
        min-width: 12;
    }
    
    #board-container {
        align: center middle;
        height: auto;
        width: 100%;
    }
    
    #left-spacer { width: 24; }
    #board-and-status { height: auto; align: left top; }
    #timer-container { width: 24; height: auto; align: center top; }
    .timer-btn { margin-top: 1; width: 100%; }
    #stopwatch {
        width: 24;
        height: 7;
        content-align: center middle;
        background: #222222;
        color: #E0E0E0;
        border: solid #888888;
    }

    BoardWidget {
        width: auto;
        height: auto;
    }
    
    #status-label {
        text-style: bold;
        margin: 1 0;
        text-align: left;
        width: 100%;
    }

    .theme-peach { background: #111111; color: #E0E0E0; }
    .theme-peach Header { background: #CC7766; color: #111111; }
    .theme-peach Button { background: #222222; color: #CC7766; }
    .theme-peach Button:hover { background: #333333; }
    .theme-peach Button.active { background: #CC7766; color: #111111; text-style: bold; }
    .theme-peach #status-label { color: #CC7766; }
    .theme-peach #stopwatch { border: solid #CC7766; background: #222222; color: #CC7766; }

    .theme-blue { background: #0A111A; color: #E0E0E0; }
    .theme-blue Header { background: #5588CC; color: #0A111A; }
    .theme-blue Button { background: #112233; color: #5588CC; }
    .theme-blue Button:hover { background: #1A334D; }
    .theme-blue Button.active { background: #5588CC; color: #0A111A; text-style: bold; }
    .theme-blue #status-label { color: #5588CC; }
    .theme-blue #stopwatch { border: solid #5588CC; background: #112233; color: #5588CC; }

    .theme-green { background: #0F1A13; color: #E0E0E0; }
    .theme-green Header { background: #55AA77; color: #0F1A13; }
    .theme-green Button { background: #152A1D; color: #55AA77; }
    .theme-green Button:hover { background: #1E3E2B; }
    .theme-green Button.active { background: #55AA77; color: #0F1A13; text-style: bold; }
    .theme-green #status-label { color: #55AA77; }
    .theme-green #stopwatch { border: solid #55AA77; background: #152A1D; color: #55AA77; }

    .theme-dracula { background: #282A36; color: #F8F8F2; }
    .theme-dracula Header { background: #FF79C6; color: #282A36; }
    .theme-dracula Button { background: #44475A; color: #FF79C6; }
    .theme-dracula Button:hover { background: #6272A4; color: #F8F8F2; }
    .theme-dracula Button.active { background: #FF79C6; color: #282A36; text-style: bold; }
    .theme-dracula #status-label { color: #8BE9FD; }
    .theme-dracula #stopwatch { border: solid #FF79C6; background: #44475A; color: #FF79C6; }
    """
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("n", "toggle_notes", "Toggle Notes"),
        ("1", "input('1')", "1"),
        ("2", "input('2')", "2"),
        ("3", "input('3')", "3"),
        ("4", "input('4')", "4"),
        ("5", "input('5')", "5"),
        ("6", "input('6')", "6"),
        ("7", "input('7')", "7"),
        ("8", "input('8')", "8"),
        ("9", "input('9')", "9"),
        ("backspace", "input('0')", "Clear"),
        ("delete", "input('0')", "Clear"),
        ("up", "move('up')", "Up"),
        ("down", "move('down')", "Down"),
        ("left", "move('left')", "Left"),
        ("right", "move('right')", "Right"),
    ]

    notes_mode = reactive(False)
    current_theme_name = "peach"

    def on_resize(self, event) -> None:
        try:
            is_large = event.size.height >= 46
            board_width = 79 if is_large else 43
            self.query_one("#board-and-status").styles.width = board_width
            
            # Vertically center the stopwatch relative to the board
            stopwatch_margin = 16 if is_large else 7
            self.query_one("#timer-container").styles.margin = (stopwatch_margin, 0, 0, 0)
        except:
            pass

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="main-container"):
            with Vertical(id="theme-controls"):
                yield Button("Peach", id="theme-peach")
                yield Button("Blue", id="theme-blue")
                yield Button("Green", id="theme-green")
                yield Button("Dracula", id="theme-dracula")
            with Horizontal(id="controls"):
                yield Button("Easy", id="btn-easy")
                yield Button("Medium", id="btn-medium")
                yield Button("Hard", id="btn-hard")
                yield Button("Expert", id="btn-expert")
                yield Button("Notes: OFF", id="btn-notes")
            
            with Horizontal(id="board-container"):
                yield Static(id="left-spacer")
                with Vertical(id="board-and-status"):
                    yield BoardWidget()
                    yield Label("", id="status-label")
                with Vertical(id="timer-container"):
                    yield StopwatchWidget(id="stopwatch")
                    yield Button("Start", id="btn-start", classes="timer-btn")
        yield Footer()

    def on_mount(self) -> None:
        self.game = SudokuGame()
        self.cells_state = [[{'value': 0, 'notes': set(), 'fixed': False, 'error': False, 'selected': False} for _ in range(9)] for _ in range(9)]
        
        self.selected_row = -1
        self.selected_col = -1
        self.start_time = time.time()
        
        self.change_theme("peach")
        self.start_game("easy")

    def change_theme(self, theme_name: str) -> None:
        for t in ["peach", "blue", "green", "dracula"]:
            self.screen.remove_class(f"theme-{t}")
            btn = self.query_one(f"#theme-{t}", Button)
            btn.remove_class("active")
            
        self.current_theme_name = theme_name
        self.screen.add_class(f"theme-{theme_name}")
        self.query_one(f"#theme-{theme_name}", Button).add_class("active")
        self.query_one(BoardWidget).refresh()

    def watch_notes_mode(self, notes_mode: bool) -> None:
        btn = self.query_one("#btn-notes", Button)
        if notes_mode:
            btn.label = "Notes: ON"
            btn.add_class("active")
        else:
            btn.label = "Notes: OFF"
            btn.remove_class("active")

    def update_difficulty_buttons(self, difficulty: str) -> None:
        for d in ["easy", "medium", "hard", "expert"]:
            btn = self.query_one(f"#btn-{d}", Button)
            if d == difficulty:
                btn.add_class("active")
            else:
                btn.remove_class("active")

    def start_game(self, difficulty: str) -> None:
        board = self.query_one(BoardWidget)
        board.animating = False
        board.styles.visibility = "visible"
        self.query_one("#stopwatch").reset()
        self.update_difficulty_buttons(difficulty)
        self.game.generate(difficulty)
        self.start_time = time.time()
        self.query_one("#status-label").update(f"Difficulty: {difficulty.capitalize()}")
        for r in range(9):
            for c in range(9):
                val = self.game.board[r][c]
                self.cells_state[r][c] = {
                    'value': val,
                    'notes': set(),
                    'fixed': val != 0,
                    'error': False,
                    'selected': False
                }
        self.selected_row = -1
        self.selected_col = -1
        self.query_one(BoardWidget).refresh()

    def select_cell(self, row: int, col: int) -> None:
        if self.selected_row != -1 and self.selected_col != -1:
            self.cells_state[self.selected_row][self.selected_col]['selected'] = False
        self.selected_row = row
        self.selected_col = col
        self.cells_state[row][col]['selected'] = True
        self.query_one(BoardWidget).refresh()

    def action_move(self, direction: str) -> None:
        if self.selected_row == -1 or self.selected_col == -1:
            self.select_cell(4, 4)
            return
            
        r, c = self.selected_row, self.selected_col
        if direction == "up":
            r = max(0, r - 1)
        elif direction == "down":
            r = min(8, r + 1)
        elif direction == "left":
            c = max(0, c - 1)
        elif direction == "right":
            c = min(8, c + 1)
            
        self.select_cell(r, c)

    def action_toggle_notes(self) -> None:
        self.notes_mode = not self.notes_mode

    def start_win_animation(self) -> None:
        self.blink_count = 0
        self.blink_timer = self.set_interval(0.3, self.do_blink)

    def do_blink(self) -> None:
        board = self.query_one(BoardWidget)
        if self.blink_count % 2 == 0:
            board.styles.visibility = "hidden"
        else:
            board.styles.visibility = "visible"
        self.blink_count += 1
        
        if self.blink_count >= 4:
            self.blink_timer.stop()
            board.styles.visibility = "visible"
            board.start_snake()

    def action_input(self, digit: str) -> None:
        if self.selected_row == -1 or self.selected_col == -1:
            return
        
        cell = self.cells_state[self.selected_row][self.selected_col]
        if cell['fixed']:
            return
            
        num = int(digit)
        if num == 0:
            self.game.board[self.selected_row][self.selected_col] = 0
            cell['value'] = 0
            cell['error'] = False
            cell['notes'] = set()
        else:
            if self.notes_mode:
                if num in cell['notes']:
                    cell['notes'].remove(num)
                else:
                    cell['notes'].add(num)
                
                if cell['value'] != 0:
                    self.game.board[self.selected_row][self.selected_col] = 0
                    cell['value'] = 0
                    cell['error'] = False
            else:
                is_valid = self.game.is_valid_move(self.selected_row, self.selected_col, num)
                self.game.board[self.selected_row][self.selected_col] = num
                cell['value'] = num
                cell['error'] = not is_valid
                
                if self.game.check_win():
                    self.query_one("#stopwatch").stop()
                    self.query_one("#status-label").update(f"🎉 YOU WIN! 🎉 Select a difficulty to play again.")
                    self.start_win_animation()
        
        self.query_one(BoardWidget).refresh()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-start":
            self.query_one("#stopwatch").start()
        elif event.button.id == "btn-notes":
            self.action_toggle_notes()
        elif event.button.id and event.button.id.startswith("btn-"):
            diff = event.button.id.split("-")[1]
            self.start_game(diff)
        elif event.button.id and event.button.id.startswith("theme-"):
            theme = event.button.id.split("-")[1]
            self.change_theme(theme)

if __name__ == "__main__":
    app = SudokuApp()
    app.run()
