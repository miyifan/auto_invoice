import tkinter as tk
from tkinter import messagebox
import json
import os
import itertools


# 定义 JSON 文件路径
JSON_FILE = "1.json"
def fullwidth_to_halfwidth(s):
        """将全角符号转换为半角符号"""
        return ''.join([chr(ord(char) - 0xFEE0) if 0xFF01 <= ord(char) <= 0xFF5E else char for char in s])
class NumberInputApp:
    def __init__(self, root):
        self.root = root
        self.root.title("发票报销系统")
         # 设置窗口大小
        window_width = 400
        window_height = 400
        self.root.geometry(f"{window_width}x{window_height}")

        # 计算居中位置
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        
        # 设置窗口位置
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # 定义输入验证规则：允许输入数字和小数点
        validate_cmd = self.root.register(self.validate_input)
        
        # 输入框
        self.input_entry = tk.Entry(root, validate="key", validatecommand=(validate_cmd, '%P'))
        self.input_entry.pack(pady=10)

        # 添加按钮
        self.add_button = tk.Button(root, text="添加发票金额", command=self.add_column)
        self.add_button.pack(pady=5)

        # 删除按钮
        self.delete_button = tk.Button(root, text="删除选中金额", command=self.delete_column)
        self.delete_button.pack(pady=5)

        # 进入报销计算页面的按钮
        self.go_to_reimbursement_button = tk.Button(root, text="进入报销计算", command=self.open_reimbursement_page)
        self.go_to_reimbursement_button.pack(pady=5)

        # 列表框显示输入的发票金额
        self.listbox = tk.Listbox(root)
        self.listbox.pack(pady=10, fill=tk.BOTH, expand=True)

        # 加载之前保存的发票金额
        self.load_numbers()

    

    def validate_input(self, new_value):
        """验证输入框的内容，允许输入数字和小数点，并将全角符号转换为半角"""
        new_value = fullwidth_to_halfwidth(new_value)  # 转换全角到半角
        # 检查新值是否为有效数字
        if new_value == "" or new_value.isdigit() or (new_value.count('.') == 1 and new_value.replace('.', '').isdigit()):
            return True
        else:
            return False

    def add_column(self):
        """添加发票金额并保存"""
        input_value = self.input_entry.get()
        input_value = fullwidth_to_halfwidth(input_value)  # 在这里转换全角到半角
        try:
            # 确保输入的数字为浮点数，可以包含小数点
            number = float(input_value)
            # 保留两位小数的格式
            formatted_number = f"{number:.2f}"
            self.listbox.insert(tk.END, formatted_number)
            self.input_entry.delete(0, tk.END)
            self.save_numbers()
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字。")

    def delete_column(self):
        """删除选中的发票金额并更新 JSON 文件"""
        selected_index = self.listbox.curselection()
        if not selected_index:
            messagebox.showwarning("警告", "请先选择要删除的金额")
            return
        self.listbox.delete(selected_index)
        self.save_numbers()

    def load_numbers(self):
        """从 JSON 文件加载发票金额"""
        if os.path.exists(JSON_FILE):
            with open(JSON_FILE, "r") as f:
                numbers = json.load(f)
                for number in numbers:
                    # 保留两位小数格式加载数字
                    formatted_number = f"{float(number):.2f}"
                    self.listbox.insert(tk.END, formatted_number)

    def save_numbers(self):
        """将发票金额保存到 JSON 文件"""
        numbers = self.listbox.get(0, tk.END)
        with open(JSON_FILE, "w") as f:
            json.dump([float(num) for num in numbers], f)

    def open_reimbursement_page(self):
        """打开报销计算页面"""
        new_window = tk.Toplevel(self.root)
        ReimbursementPage(new_window, self.load_invoice_numbers(), self)

    def load_invoice_numbers(self):
        """从列表框获取发票金额"""
        return [float(self.listbox.get(i)) for i in range(self.listbox.size())]

class ReimbursementPage:
    def __init__(self, root, invoice_numbers, parent_app):
        self.root = root
        self.root.title("报销计算页面")
        self.root.geometry("400x400")

        self.invoice_numbers = invoice_numbers
        self.parent_app = parent_app
        self.projects = []  # 存储报销项目的目标金额

        # 创建新的报销项目
        self.target_entry = tk.Entry(root)
        self.target_entry.pack(pady=10)

        self.add_project_button = tk.Button(root, text="添加报销项目", command=self.add_project)
        self.add_project_button.pack(pady=5)

        # 计算按钮
        self.calculate_button = tk.Button(root, text="计算发票组合", command=self.calculate_reimbursement)
        self.calculate_button.pack(pady=5)

        # 报销完成按钮
        self.complete_button = tk.Button(root, text="报销完成", command=self.complete_reimbursement)
        self.complete_button.pack(pady=5)

        # 显示添加的报销项目
        self.project_listbox = tk.Listbox(root, selectmode=tk.MULTIPLE)  # 允许多选
        self.project_listbox.pack(pady=10, fill=tk.BOTH, expand=True)

        # 用于存储每个项目的最优发票组合
        self.project_combinations = {}

    def add_project(self):
        """添加报销项目"""
        try:
            target_value = float(self.target_entry.get())
            self.projects.append(target_value)
            self.project_listbox.insert(tk.END, f"报销项目: {target_value:.2f}")
            self.target_entry.delete(0, tk.END)
        except ValueError:
            messagebox.showerror("错误", "请输入有效的金额。")

    def calculate_reimbursement(self):
        """计算最接近报销金额的发票组合"""
        if not self.projects:
            messagebox.showwarning("警告", "请添加至少一个报销项目")
            return

        selected_projects = [float(self.project_listbox.get(i).split(": ")[1]) for i in self.project_listbox.curselection()]
        if not selected_projects:
            messagebox.showwarning("警告", "请选中至少一个报销项目")
            return

        available_invoices = self.invoice_numbers.copy()  # 可用的发票金额
        self.project_combinations.clear()  # 清空之前的组合记录

        results = []
        for project in selected_projects:
            best_combination = self.find_best_combinations(project, available_invoices)
            if best_combination:
                result = f"报销目标 {project:.2f} 的最佳组合: {best_combination}, 总金额: {sum(best_combination):.2f}"
                results.append(result)
                self.project_combinations[project] = best_combination
                # 删除已使用的发票金额
                for num in best_combination:
                    available_invoices.remove(num)
            else:
                result = f"报销目标 {project:.2f} 无法找到合适的组合"
                results.append(result)

        messagebox.showinfo("计算结果", "\n".join(results))


    def find_best_combinations(self, target, invoices):
        best_below_target = None
        best_below_diff = float('inf')

        for r in range(1, len(invoices) + 1):
            for combination in itertools.combinations(invoices, r):
                total = sum(combination)
                if total <= target:
                    diff = target - total
                    if diff < best_below_diff:
                        best_below_diff = diff
                        best_below_target = combination

        return best_below_target  # 只返回最接近的组合



        
    def complete_reimbursement(self):
        """报销完成，删除已使用的发票金额"""
        used_invoices = []
        for combination in self.project_combinations.values():
            used_invoices.extend(combination)

        # 从父窗口的发票列表中删除使用过的发票
        self.parent_app.listbox.delete(0, tk.END)  # 清空当前发票列表框
        remaining_invoices = [inv for inv in self.invoice_numbers if inv not in used_invoices]
        for invoice in remaining_invoices:
            self.parent_app.listbox.insert(tk.END, f"{invoice:.2f}")

        # 更新 JSON 文件
        self.parent_app.save_numbers()

        messagebox.showinfo("提示", "报销完成，已删除使用过的发票金额。")
        self.root.destroy()  # 关闭报销页面

if __name__ == "__main__":
    root = tk.Tk()
    app = NumberInputApp(root)
    root.mainloop()
