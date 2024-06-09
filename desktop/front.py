import tkinter as tk
from math import ceil, acos, degrees
import unicodedata


MAP_RADIUS = 30

def vector_size(vector):
    return (vector[0]**2 + vector[1]**2)**0.5

def get_angle_of_vectors(vectorA, vecotrB):
    cosalpha = (vectorA[0]*vecotrB[0] + vectorA[1]*vecotrB[1])/(vector_size(vectorA) * vector_size(vecotrB))
    return acos(cosalpha)

def determine_area(point: tuple[int, int], middle: tuple[int, int]) -> int:
    vectorA = (point[0] - middle[0], point[1] - middle[1])
    vectorB = (1, 0)

    angle = degrees(get_angle_of_vectors(vectorA, vectorB))
    print(angle)
    if not point[1] >= middle[1]:
        return angle // 60
    else:
        return 5 - (angle // 60)
    
print(determine_area((0, 0), (300, 300)))
print(determine_area((280, 0), (300, 300)))
print(determine_area((320, 310), (300, 300)))
print(determine_area((300, 350), (300, 300)))

print(determine_area((250, 310), (300, 300)))


def remove_diacritics(input_str):
    normalized_str = unicodedata.normalize('NFKD', input_str)
    return ''.join([c for c in normalized_str if not unicodedata.combining(c)])


def compare_strings(str1, str2):
    processed_str1 = remove_diacritics(str1).lower()
    processed_str2 = remove_diacritics(str2).lower()
    return processed_str1 == processed_str2

class Front:
    def __init__(self, actions):
        self.actions = actions
        self.window = tk.Tk()

        window_height = self.window.winfo_screenheight() # - 200 # - 200 only for easier testing
        window_width = self.window.winfo_screenwidth() # - 200 # - 200 only for easier testing


        self.map_canvas_size = {"x": window_width - (window_height / 2), "y": window_height}
        self.menu_canvas_size = {"x": window_height / 2, "y": window_height}

        self.font_size = int(window_height / 60)

        # line below makes window completely fullscreen (annoying to test with)
        # self.window.overrideredirect(True)
        # self.window.geometry(f"{window_width}x{window_height}+0+0")

        self.map_canvas = tk.Canvas(self.window, bg="green2")
        self.map_canvas.place(y=0, width=self.map_canvas_size["x"], relheight=1)

        self.menu_canvas = tk.Canvas(self.window, bg="grey")
        self.menu_canvas.place(y=0, x=self.map_canvas_size["x"], width=self.menu_canvas_size["x"], relheight=1)

        self.zoom = 60 # describes how many rows of tiles will be displayed
        self.selected_pos = []
        self.status = {}

        self.map_canvas.bind("<MouseWheel>", self.scroll_response)
        # matus sprta to kodu
        self.map_canvas.bind('<Button-1>', self.select_hex)
        self.menu_canvas.bind('<Button-1>', self.menu_click)
        self.buttons = []
        self.polygons = []
        self.tkinter_to_map_cords = {}

        self.center_hexagon_cords = {"x": 0, "y": 0} # defining on which hexagon the map is centered

        self.draw_map()

        # inventory
        self.inventory_window = None

        # trades
        self.trade_page_number = 0
        self.trade_window = None
        self.disposable_trade_labels = []

        self.make_trade_window = None
        self.make_trade_objects = {}


    def update(self): # call this function rapidly to make everything work
        self.map_canvas.update()


    def scroll_response(self, event):
        if event.num == 5 or event.delta == -120:
            self.zoom += 1
        if event.num == 4 or event.delta == 120:
            if self.zoom > 1:
                self.zoom -= 1
        self.polygons = []
        self.selected_pos = []
        self.draw_map()
    
    # matus sprta to kodu
    def select_hex(self, event):
        id = min(self.polygons, key=lambda l: ((l[1][0]-event.x)**2 + (l[1][1]-event.y)**2)**0.5)
        if self.selected_pos == id:
            self.map_canvas.itemconfig(self.selected_pos[0], fill='red')
            self.selected_pos = []
        else:
            if self.selected_pos != []:
                self.map_canvas.itemconfig(self.selected_pos[0], fill='red')
            self.selected_pos = id
            map_cords = self.tkinter_to_map_cords[id[1]]
            self.status = self.actions.possible_actions(list(map_cords))
            print(map_cords)
            self.draw_menu()
            # tu pride daco co bude zo statusu pisat veci na sidebar
            self.map_canvas.create_text(id[1][0], id[1][1], text=f"{map_cords[0]}, {map_cords[1]}")
            self.map_canvas.itemconfig(self.selected_pos[0], fill='blue')
        self.update()
    

    def create_inventory_window(self):
        if self.inventory_window:
            try:
                self.inventory_window.destroy()
            except tk.TclError:
                pass
        self.inventory_window = tk.Tk()
        self.update_inventory_window()
        self.inventory_window.title("Inventár")

    
    def update_inventory_window(self):
        if self.inventory_window:
            try:
                inv = self.actions.inventory
                inv = dict(sorted(inv.items(), key=lambda item: item[1]))

                num_of_rows = 20

                tk.Label(self.inventory_window, text=f"people: {inv['people']}", width=30, font=("smili", 20)).grid(row=0, column=0, columnspan=1000)
                tk.Label(self.inventory_window, text=f"money: {inv['money']}", width=30, font=("smili", 20)).grid(row=1, column=0, columnspan=1000)

                counter = 0
                for item in inv.keys():
                    if item != "money" and item != "people":

                        tk.Label(self.inventory_window, text=f"{item}: {inv[item]}", width=30, font=("smili", 20)).grid(row=counter % num_of_rows + 2, column=counter // num_of_rows)
                        counter += 1
            except tk.TclError:
                pass
    
    def change_trade_page(self, value):
        self.trade_page_number += value
        self.trade_page_number %= ceil(len(self.actions.trades) / 10)
        self.show_trades()

    def create_trade_window(self):
        if self.trade_window:
            try:
                self.trade_window.destroy()
            except tk.TclError:
                pass
        self.trade_window = tk.Tk()

        tk.Label(self.trade_window, width=30, text="Čo dám", font=("smili", self.font_size)).grid(row=0, column=0)
        tk.Label(self.trade_window, width=30, text="Čo dostanem", font=("smili", self.font_size)).grid(row=0, column=1)

        tk.Button(self.trade_window, text="<-", width=30, command=lambda: self.change_trade_page(-1), font=("smili", self.font_size)).grid(row=11, column=0)
        tk.Button(self.trade_window, text="->", width=30, command=lambda: self.change_trade_page(1), font=("smili", self.font_size)).grid(row=11, column=2)

        tk.Button(self.trade_window, text="Pridat ponuku", width=90, command=self.add_trade, font=("smili", self.font_size)).grid(row=12, columnspan=3)

        self.show_trades()
    
    def show_trades(self):
        if self.trade_window is None:
            return
        try:
            self.trade_window.winfo_exists()
        except tk.TclError:
            return

        while self.trade_page_number > len(self.actions.trades) * 10:
            self.trade_page_number -= 1

        for label in self.disposable_trade_labels:
            try:
                label.destroy()
            except tk.TclError:
                pass

        trades = list(reversed(sorted(list(self.actions.trades))))
        for i, id in enumerate(trades[self.trade_page_number * 10:]):
            if i >= 10:
                break
            self.disposable_trade_labels.append(tk.Label(self.trade_window, width=30, text=f"{self.actions.trades[id]['cost']}", font=("smili", self.font_size)))
            self.disposable_trade_labels[-1].grid(row=i + 1, column=(self.actions.trades[id]["type"] + 1) % 2)
            self.disposable_trade_labels.append(tk.Label(self.trade_window, width=30, text=f"{self.actions.trades[id]['count']} - {self.actions.trades[id]['item']}", font=("smili", self.font_size)))
            self.disposable_trade_labels[-1].grid(row=i + 1, column=self.actions.trades[id]["type"])

            self.disposable_trade_labels.append(tk.Button(self.trade_window, command=lambda x = id: self.buy(x), width=30, bg="green2", text="✔", font=("smili", self.font_size)))
            self.disposable_trade_labels[-1].grid(row=i + 1, column=2)

            if self.actions.trades[id]['type'] == 0:
                if self.actions.inventory[self.actions.trades[id]['item']] < self.actions.trades[id]['count']:
                    self.disposable_trade_labels[-1].config(bg="grey", state="disabled")
            else:
                if self.actions.inventory['money'] < self.actions.trades[id]['cost']:
                    self.disposable_trade_labels[-1].config(bg="grey", state="disabled")

        self.disposable_trade_labels.append(tk.Label(self.trade_window, text=f"{self.trade_page_number + 1} / {ceil(len(self.actions.trades) / 10)}", font=("smili", self.font_size)))
        self.disposable_trade_labels[-1].grid(row=11, column=1)

    def add_trade(self):
        # TODO redesign...        ...sure

        # 🔁
        if self.make_trade_window:
            try:
                self.make_trade_window.destroy()
            except tk.TclError:
                pass
        
        self.make_trade_window = tk.Tk()
        tk.Label(self.make_trade_window, text="Čo dám", font=("smili", self.font_size)).grid(row=0, column=0, columnspan=2)
        tk.Label(self.make_trade_window, text="Čo dostanem", font=("smili", self.font_size)).grid(row=0, column=2, columnspan=2)

        tk.Label(self.make_trade_window, text="Koľko:", width=30, font=("smili", self.font_size)).grid(row=2, column=0)
        tk.Label(self.make_trade_window, text="Koľko:", width=30, font=("smili", self.font_size)).grid(row=2, column=2)

        self.make_trade_objects = {
            "money_amount": tk.Entry(self.make_trade_window, width=30, font=("smili", self.font_size)),
            "item_amount": tk.Entry(self.make_trade_window, width=30, font=("smili", self.font_size)),
            "item": tk.Entry(self.make_trade_window, width=30, font=("smili", self.font_size)),
            "money_label": tk.Label(self.make_trade_window, text="Peniaze", width=30, font=("smili", self.font_size)),
            "item_label": tk.Label(self.make_trade_window, text="Tovar:", width=30, font=("smili", self.font_size)),
            "direction": True
        }

        self.grid_make_trade_objects()

        tk.Button(self.make_trade_window, text="🔁", font=("smili", self.font_size * 2), width=60, command=self.grid_make_trade_objects).grid(row=3, columnspan=4)
        tk.Button(self.make_trade_window, text="Zverejniť", font=("smili", self.font_size * 2), width=60, command=self.publish_trade).grid(row=4, columnspan=4)

    def grid_make_trade_objects(self):
        if self.make_trade_objects["direction"]:
            self.make_trade_objects["money_amount"].grid(row=2, column=3)
            self.make_trade_objects["item_amount"].grid(row=2, column=1)
            self.make_trade_objects["item"].grid(row=1, column=1)
            self.make_trade_objects["money_label"].grid(row=1, column=2, columnspan=2)
            self.make_trade_objects["item_label"].grid(row=1, column=0)
        else:
            self.make_trade_objects["money_amount"].grid(row=2, column=1)
            self.make_trade_objects["item_amount"].grid(row=2, column=3)
            self.make_trade_objects["item"].grid(row=1, column=3)
            self.make_trade_objects["money_label"].grid(row=1, column=0, columnspan=2)
            self.make_trade_objects["item_label"].grid(row=1, column=2)
        self.make_trade_objects["direction"] = not self.make_trade_objects["direction"]

    def publish_trade(self):
        trade = {"item": self.make_trade_objects["item"].get(),
                 "count": self.make_trade_objects["item_amount"].get(),
                 "cost": self.make_trade_objects["money_amount"].get(),
                 }
        exists = False
        for key in self.actions.inventory.keys():
            if compare_strings(trade["item"], key) and key != "people":
                exists = True
                break
        if not exists:
            # e-ee
            return
        if trade["count"].isnumeric():
            trade["count"] = int(trade["count"])
            if trade["count"] < 0:
                # e-ee
                return
        else:
            # e-ee
            return
        if trade["cost"].isnumeric():
            trade["cost"] = int(trade["cost"])
            if trade["cost"] < 0:
                # e-ee
                return
        else:
            # e-ee
            return
        
        if not self.make_trade_objects["direction"]:
            if self.actions.inventory["money"] < trade["cost"]:
                # e-ee
                return
        else:
            if self.actions.inventory[trade["item"]] < trade["count"]:
                # e-ee
                return
        
        self.actions.place_trade(int(not self.make_trade_objects["direction"]), trade["item"], trade["count"], trade["cost"])

        # cink


    def buy(self, id):
        if self.actions.take_trade(id):
            pass # cink
        else:
            pass # e-eee

    def create_army_window(self):
        pass

    def draw_menu(self, ceiling=0):
        self.menu_canvas.delete('all')
        self.buttons = []
        x = self.menu_canvas_size['x']
        y = self.menu_canvas_size['y']
        print(self.status)

        infos = self.status['info']
        self.menu_canvas.create_rectangle(0, ceiling, x, ceiling+len(infos)*20, fill='yellow')
        for i, info in enumerate(infos.keys()):
            self.menu_canvas.create_text(x/2, ceiling+i*20+10, text=f'{info} : {infos[info]}')
        ceiling += len(infos)*20

        for action in self.status['actions']:
            ceiling += self.draw_button(action, ceiling)
        
        inv = self.actions.inventory
        self.menu_canvas.create_rectangle(0, ceiling, x, ceiling+len(inv)*20, fill='yellow')
        for i, item in enumerate(inv.keys()):
            self.menu_canvas.create_text(x/2, ceiling+i*20+10, text=f'{item} : {inv[item]}')

        tk.Button(text="Armáda", command=self.create_army_window, borderwidth=4, font=("smili", self.font_size)).\
            place(rely=0.76, x=self.map_canvas_size["x"], width=self.menu_canvas_size["x"], relheight=0.08)
        tk.Button(text="Obchodovanie", command=self.create_trade_window, borderwidth=4, font=("smili", self.font_size)).\
            place(rely=0.84, x=self.map_canvas_size["x"], width=self.menu_canvas_size["x"], relheight=0.08)
        tk.Button(text="Inventár", command=self.create_inventory_window, borderwidth=4, font=("smili", self.font_size)).\
            place(rely=0.92, x=self.map_canvas_size["x"], width=self.menu_canvas_size["x"], relheight=0.08)


    def draw_button(self, action, ceiling):# button = (id, (x, y), (action))
        self.buttons.append((self.menu_canvas.create_rectangle(0, ceiling, self.menu_canvas_size['x'], ceiling+30, fill='grey'), (self.menu_canvas_size['x']/2, ceiling+15), action))
        self.menu_canvas.create_text(self.menu_canvas_size['x']/2, ceiling+10, text=action[0])
        self.menu_canvas.create_text(self.menu_canvas_size['x']/2, ceiling+20, text=action[2])
        return 30


    def menu_click(self, event):
        button = min(self.buttons, key=lambda l: ((l[1][0]-event.x)**2 + (l[1][1]-event.y)**2)**0.5)
        print(button[2][1])
        button[2][1][0](*button[2][1][1])
        map_cords = self.tkinter_to_map_cords[self.selected_pos[1]]
        self.status = self.actions.possible_actions(list(map_cords))
        print(self.status)
        self.draw_menu()


    def menu_scroll(self, event):
        self.draw_menu()


    def draw_map(self):
        self.map_canvas.delete("all")

        side_length = (2 * self.map_canvas_size["y"]) / (3 * self.zoom + 1)
        hexagon_width = ((3) ** 0.5) * side_length
        full_num_of_columns = int(self.map_canvas_size["x"] / hexagon_width)

        center_piece_row = self.zoom // 2
        center_piece_column = full_num_of_columns // 2

        for row in range(self.zoom):
            center_pos_y = side_length + side_length * 1.5 * row
            if row % 2 == center_piece_row % 2: # checking if it's an even or odd row
                num_of_columns = full_num_of_columns
                center_pos_x = (((3) ** 0.5) / 2) * side_length
            else:
                num_of_columns = full_num_of_columns - 1
                center_pos_x = (((3) ** 0.5) / 2) * side_length * 2

            for column in range(num_of_columns):
                self.draw_hexagon(center_pos_x, center_pos_y, 0.95 * side_length)

                # calculating where the hexagon is in map coordinates, (keep in mind tkinter has reversed y axis)
                y_cord_difference = center_piece_row - row
                x_cord_difference = column - center_piece_column - (y_cord_difference // 2)

                self.tkinter_to_map_cords[(center_pos_x, center_pos_y)] = (self.center_hexagon_cords["x"] + x_cord_difference, self.center_hexagon_cords["y"] + y_cord_difference)
                center_pos_x += (((3) ** 0.5) / 2) * side_length * 2
    
    def draw_hexagon(self, x, y, side_length):
        x_shift = (((3) ** 0.5) / 2) * side_length
        y_shift = side_length / 2
        self.polygons.append((self.map_canvas.create_polygon(
            x, y + side_length,
            x - x_shift, y + y_shift,
            x - x_shift, y - y_shift,
            x, y - side_length,
            x + x_shift, y - y_shift,
            x + x_shift, y + y_shift,
            fill="red"
        ), (x, y)))


if __name__ == "__main__":
    front = Front(None)
    front.window.mainloop()
