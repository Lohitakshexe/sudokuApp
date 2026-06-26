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

    def _count_solutions(self, board, count=0):
        for row in range(9):
            for col in range(9):
                if board[row][col] == 0:
                    for num in range(1, 10):
                        if self._is_safe(board, row, col, num):
                            board[row][col] = num
                            count = self._count_solutions(board, count)
                            board[row][col] = 0
                            if count > 1:
                                return count
                    return count
        return count + 1

    def _remove_cells(self, count):
        cells = list(range(81))
        random.shuffle(cells)
        removed = 0
        for cellId in cells:
            if removed >= count:
                break
            i = cellId // 9
            j = cellId % 9
            if self.board[i][j] != 0:
                temp = self.board[i][j]
                self.board[i][j] = 0
                
                # Check if there is still a unique solution
                if self._count_solutions(self.board, 0) == 1:
                    removed += 1
                else:
                    self.board[i][j] = temp

    def is_valid_move(self, row, col, num):
        if num == 0:
            return True
        # Strict validation: Check directly against the true mathematical solution
        return self.solution[row][col] == num

    def check_win(self):
        for i in range(9):
            for j in range(9):
                if self.board[i][j] != self.solution[i][j]:
                    return False
        return True
