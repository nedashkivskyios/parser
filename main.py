import tkinter as tk
import ui
import logic

if __name__ == "__main__":
    root = tk.Tk()
    app = ui.SitemapApp(root, logic)
    root.mainloop()
