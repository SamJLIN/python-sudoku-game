import tkinter as tk
from tkinter import messagebox
import random
import sqlite3
import time

class SudokuGame:
    def __init__(self):
        # 初始化主視窗和遊戲設置
        self.root = tk.Tk()
        self.root.title("9x9 數獨遊戲")

        # 儲存遊戲盤面和解答
        self.board = []
        self.solution = []
        
        # 儲存所有 9x9 的格子元件
        self.cells = [[None for _ in range(9)] for _ in range(9)]
        
        # 計時器起始時間
        self.start_time = None

        # 初始化 SQLite 資料庫
        self.db_conn = sqlite3.connect("sudoku_records.db")
        self.init_database()

        # 建立遊戲介面
        self.create_ui()
        
        # 預設生成一個中等難度的遊戲
        self.generate_new_game("中等")
        self.root.mainloop()

    def init_database(self):
        # 初始化 SQLite 資料表以保存玩家記錄
        cursor = self.db_conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                difficulty TEXT,
                time REAL,
                completion_count INTEGER
            )
            """
        )
        self.db_conn.commit()

    def create_ui(self):
        # 建立主要遊戲介面，包括格子和按鈕
        for i in range(9):
            for j in range(9):
                # 每個格子為一個 Entry 小部件
                cell = tk.Entry(self.root, width=2, font=("Arial", 18), justify="center")
                cell.grid(row=i, column=j, padx=1, pady=1)
                self.cells[i][j] = cell

        # 難度選擇下拉選單
        self.difficulty_var = tk.StringVar(value="中等")
        tk.OptionMenu(self.root, self.difficulty_var, "簡單", "中等", "困難").grid(row=9, column=0, columnspan=3)

        # 功能按鈕
        tk.Button(self.root, text="檢查", command=self.check_board).grid(row=9, column=3, columnspan=2)
        tk.Button(self.root, text="新遊戲", command=self.new_game).grid(row=9, column=5, columnspan=2)
        tk.Button(self.root, text="最佳成績", command=self.show_records).grid(row=9, column=7, columnspan=2)

        # 計時器顯示
        self.timer_label = tk.Label(self.root, text="計時: 0 秒", font=("Arial", 14))
        self.timer_label.grid(row=10, column=0, columnspan=9)
        
        # 每秒更新計時器
        self.update_timer()

    def generate_new_game(self, difficulty):
        # 根據難度生成新的遊戲盤面
        self.board, self.solution = self.generate_sudoku_board(difficulty)
        
        # 將生成的盤面填入格子
        for i in range(9):
            for j in range(9):
                cell = self.cells[i][j]
                cell.config(state="normal")  # 解鎖格子
                cell.delete(0, tk.END)  # 清空格子
                if self.board[i][j] != 0:
                    # 如果是預設數字，顯示並鎖定格子
                    cell.insert(0, str(self.board[i][j]))
                    cell.config(state="disabled")
        
        # 重置計時器
        self.start_time = time.time()

    def generate_sudoku_board(self, difficulty):
        # 生成完整解答（簡化為固定結構）
        full_solution = [[(i * 3 + i // 3 + j) % 9 + 1 for j in range(9)] for i in range(9)]
        random.shuffle(full_solution)
        
        # 創建題目盤面
        board = [row[:] for row in full_solution]

        # 根據難度設定移除的數字數量
        difficulty_levels = {"簡單": 40, "中等": 30, "困難": 20}
        remove_count = 81 - difficulty_levels.get(difficulty, 30)

        # 隨機清除數字
        for _ in range(remove_count):
            x, y = random.randint(0, 8), random.randint(0, 8)
            while board[x][y] == 0:
                x, y = random.randint(0, 8), random.randint(0, 8)
            board[x][y] = 0

        return board, full_solution

    def check_board(self):
        # 驗證玩家輸入是否正確
        current_board = [[int(self.cells[i][j].get()) if self.cells[i][j].get().isdigit() else 0 for j in range(9)] for i in range(9)]
        if current_board == self.solution:
            elapsed_time = round(time.time() - self.start_time, 2)
            messagebox.showinfo("恭喜", f"解答正確！用時: {elapsed_time} 秒")
            self.save_record(elapsed_time)
        else:
            messagebox.showwarning("錯誤", "答案不正確，請檢查後再試！")

    def save_record(self, elapsed_time):
        # 將遊戲記錄保存到 SQLite
        difficulty = self.difficulty_var.get()
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT * FROM records WHERE difficulty=?", (difficulty,))
        record = cursor.fetchone()

        if record:
            # 更新最佳時間和完成次數
            best_time = min(record[2], elapsed_time)
            completion_count = record[3] + 1
            cursor.execute(
                "UPDATE records SET time=?, completion_count=? WHERE difficulty=?",
                (best_time, completion_count, difficulty)
            )
        else:
            # 插入新記錄
            cursor.execute(
                "INSERT INTO records (difficulty, time, completion_count) VALUES (?, ?, ?)",
                (difficulty, elapsed_time, 1)
            )
        self.db_conn.commit()

    def show_records(self):
        # 顯示最佳成績
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT * FROM records ORDER BY time ASC")
        records = cursor.fetchall()

        if records:
            # 格式化記錄內容以顯示
            records_text = "\n".join(
                [f"難度: {r[1]} - 最快時間: {r[2]} 秒 - 完成次數: {r[3]}" for r in records]
            )
            messagebox.showinfo("最佳成績", records_text)
        else:
            messagebox.showinfo("最佳成績", "目前沒有記錄。")

    def new_game(self):
        # 開始新遊戲
        self.generate_new_game(self.difficulty_var.get())

    def update_timer(self):
        # 更新計時器
        if self.start_time:
            elapsed_time = int(time.time() - self.start_time)
            self.timer_label.config(text=f"計時: {elapsed_time} 秒")
        self.root.after(1000, self.update_timer)

if __name__ == "__main__":
    SudokuGame()