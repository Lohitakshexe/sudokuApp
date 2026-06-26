import random
import copy

class SudokuGame:
    def __init__(self):
        self.board = [[0 for _ in range(9)] for _ in range(9)]
        self.solution = []
        
    def generate(self, difficulty='easy'):
        # Empty the board
        self.board = [[0 for _ in range(9)] for _ in range(9)]
        # Fill diagonal 3x3 blocks first to speed up generation
        self._fill_diagonal()
        # Solve the rest to get a complete valid board
        self._solve(self.board)
        self.solution = copy.deepcopy(self.board)
        
        # Determine number of cells to remove
        remove_counts = {
            'easy': random.randint(30, 40),
            'medium': random.randint(41, 50),
            'hard': random.randint(51, 60),
            'expert': random.randint(61, 65)
        }
        
        count = remove_counts.get(difficulty.lower(), 40)
        self._remove_cells(count)
        
    def _fill_diagonal(self):
        for i in range(0, 9, 3):
            self._fill_box(i, i)
            
    def _fill_box(self, rowStart, colStart):
        num = 0
        for i in range(3):
            for j in range(3):
                while True:
                    num = random.randint(1, 9)
                    if self._is_safe_in_box(rowStart, colStart, num):
                        break
                self.board[rowStart + i][colStart + j] = num
                
    def _is_safe_in_box(self, rowStart, colStart, num):
        for i in range(3):
            for j in range(3):
                if self.board[rowStart + i][colStart + j] == num:
                    return False
        return True
        
    def _is_safe(self, board, row, col, num):
        # Check row
        for x in range(9):
            if board[row][x] == num:
                return False
        # Check col
        for x in range(9):
            if board[x][col] == num:
                return False
        # Check box
        startRow = row - row % 3
        startCol = col - col % 3
        for i in range(3):
            for j in range(3):
                if board[i + startRow][j + startCol] == num:
                    return False
        return True

    def _solve(self, board):
        for row in range(9):
            for col in range(9):
                if board[row][col] == 0:
                    nums = list(range(1, 10))
                    random.shuffle(nums)
                    for num in nums:
                        if self._is_safe(board, row, col, num):
                            board[row][col] = num
                            if self._solve(board):
                                return True
                            board[row][col] = 0
                    return False
        return True

    def _remove_cells(self, count):
        while count > 0:
            cellId = random.randint(0, 80)
            i = cellId // 9
            j = cellId % 9
            if self.board[i][j] != 0:
                self.board[i][j] = 0
                count -= 1

    def is_valid_move(self, row, col, num):
        if num == 0:
            return True
        # Check against the solution to be strict, or just check conflicts
        # A simple conflict check is often better for a player experience
        temp = self.board[row][col]
        self.board[row][col] = 0
        safe = self._is_safe(self.board, row, col, num)
        self.board[row][col] = temp
        return safe

    def check_win(self):
        for i in range(9):
            for j in range(9):
                if self.board[i][j] == 0:
                    return False
                if not self._is_safe(self.board, i, j, self.board[i][j]):
                    return False
        return True
