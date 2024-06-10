import tkinter as tk
from math import ceil, acos, degrees
import unicodedata


MAP_RADIUS = 30

def vector_size(vector):
    return (vector[0]**2 + vector[1]**2)**0.5


def get_angle_of_vectors(vectorA, vecotrB):
    cosalpha = (vectorA[0]*vecotrB[0] + vectorA[1]*vecotrB[1])/(vector_size(vectorA) * vector_size(vecotrB))
    return acos(cosalpha)


def determine_area(point: tuple[int, int], middle: tuple[int, int]) -> float:
    vectorA = (point[0] - middle[0], point[1] - middle[1])
    vectorB = (1, 0)

    angle = degrees(get_angle_of_vectors(vectorA, vectorB))
    if not point[1] >= middle[1]:
        return angle // 60
    else:
        return 5 - (angle // 60)
    

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

        self.zoom = 30 # describes how many rows of tiles will be displayed
        self.zoom_strength = 3
        self.selected_pos = []
        self.status = {}

        self.map_canvas.bind("<MouseWheel>", self.scroll_response)
        self.window.bind_all("<Left>", lambda event: self.arrow_click("left"))
        self.window.bind_all("<Right>", lambda event: self.arrow_click("right"))
        self.window.bind_all("<Up>", lambda event: self.arrow_click("up"))
        self.window.bind_all("<Down>", lambda event: self.arrow_click("down"))
        self.last_move_up_was_right = True
        # matus sprta to kodu
        self.map_canvas.bind('<Button-1>', self.select_hex)
        self.menu_canvas.bind('<Button-1>', self.menu_click)
        self.buttons = []
        self.polygons = []
        self.tkinter_to_map_cords = {}

        self.center_hexagon_cords = {"x": 0, "y": 0} # defining on which hexagon the map is centered

        self.clicked_hexagons = []  # na test zoomovania
        self.draw_map()

        # inventory
        self.inventory_window = None

        # trades
        self.trade_page_number = 0
        self.trade_window = None
        self.disposable_trade_labels = []

        self.make_trade_window = None
        self.make_trade_objects = {}

        # building
        self.build_window = None

    def update(self): # call this function rapidly to make everything work
        self.map_canvas.update()

    def scroll_response(self, event):
        mid_x = self.map_canvas_size["x"] / 2
        mid_y = self.map_canvas_size["y"] / 2

        distance_from_middle = vector_size((mid_x - event.x, mid_y - event.y))
        hexagon_size = (self.map_canvas_size["y"] / self.zoom) * 0.7
        mid_shift_size = int(((self.zoom_strength / self.zoom) * distance_from_middle) // hexagon_size)

        mid_shift_directions = {0: (-1, 0), 1: (0, -1), 2: (1, -1), 3: (1, 0), 4: (0, 1), 5: (-1, 1)}

        if event.num == 5 or event.delta == -120:
            self.zoom += self.zoom_strength
            mid_shift_size *= -1
        if event.num == 4 or event.delta == 120:
            if self.zoom > 1:
                self.zoom -= self.zoom_strength

        direction = mid_shift_directions[int(determine_area((event.x, event.y), (mid_x, mid_y)))]
        self.center_hexagon_cords["x"] -= direction[0] * mid_shift_size
        self.center_hexagon_cords["y"] -= direction[1] * mid_shift_size

        self.polygons = []
        self.selected_pos = []
        self.draw_map()
        self.zoom_strength = self.zoom // 15 + 1

    def arrow_click(self, arrow):
        if arrow == "left":
            self.center_hexagon_cords["x"] -= 1
        elif arrow == "right":
            self.center_hexagon_cords["x"] += 1
        elif arrow == "up":
            self.center_hexagon_cords["y"] += 1
            if self.last_move_up_was_right:
                self.center_hexagon_cords["x"] -= 1
            self.last_move_up_was_right = not self.last_move_up_was_right
        elif arrow == "down":
            self.center_hexagon_cords["y"] -= 1
            if self.last_move_up_was_right:
                self.center_hexagon_cords["x"] += 1
            self.last_move_up_was_right = not self.last_move_up_was_right
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
            print(map_cords)

            self.clicked_hexagons.append(map_cords)  # na test zoomovania

            self.status = self.actions.possible_actions(list(map_cords))
            self.draw_menu()
            # tu pride daco co bude zo statusu pisat veci na sidebar
            # self.map_canvas.create_text(id[1][0], id[1][1], text=f"{map_cords[0]}, {map_cords[1]}")
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
            print("eeee")
            return
        if trade["count"].isnumeric():
            trade["count"] = int(trade["count"])
            if trade["count"] < 0:
                # e-ee
                print("eeee")
                return
        else:
            # e-ee
            print("eeee")
            return
        if trade["cost"].isnumeric():
            trade["cost"] = int(trade["cost"])
            if trade["cost"] < 0:
                # e-ee
                print("eeee")
                return
        else:
            # e-ee
            print("eeee")
            return
        
        if not self.make_trade_objects["direction"]:
            if self.actions.inventory["money"] < trade["cost"]:
                # e-ee
                print("eeee")
                return
        else:
            if self.actions.inventory[trade["item"]] < trade["count"]:
                # e-ee
                print("eeee")
                return
        
        self.actions.place_trade(int(not self.make_trade_objects["direction"]), trade["item"], trade["count"], trade["cost"])

        # cink
        print("cink")

    def buy(self, id):
        if self.actions.take_trade(id):
            pass # cink
            print('cink')
        else:
            pass # e-eee
            print('eeee')

    def create_army_window(self):
        pass

    def create_build_window(self):
        if self.build_window:
            try:
                self.build_window.destroy()
            except tk.TclError:
                pass
        self.build_window = tk.Tk()

        # map_cords = self.tkinter_to_map_cords[self.selected_pos[1]]
        # self.status = self.actions.possible_actions(list(map_cords))

        # [['Postav road', (<bound method actions.build_new of <__main__.actions object at 0x000001E85F83A210>>, ('road', [-1, 1])), {'stone': 1, 'wood': 1}], ['Postav berry picker', (<bound method actions.build_new of <__main__.actions object at 0x000001E85F83A210>>, ('berry picker', [-1, 1])), {'people': 1, 'wood': 1, 'stone': 1}]]

        for i, building in enumerate(self.actions.buildings.keys()):
            cost_text = ""
            for material in self.actions.buildings[building]["cost"][0].keys():
                cost_text += f'{self.actions.buildings[building]["cost"][0][material]} {material}, '
            cost_text = cost_text[:-2]

            requirement_text = self.actions.buildings[building]["requrement"]
            if not requirement_text:
                requirement_text = "Môže byť kdekoľvek"
            else:
                requirement_text = "Musí byť pri: " + requirement_text

            if self.actions.buildings[building]["generating"]:
                input_text = ""
                for material in self.actions.buildings[building]["input"][0].keys():
                    input_text += f'{self.actions.buildings[building]["input"][0][material]} {material}, '
                if input_text:
                    input_text = output_text[:-2]
                else:
                    input_text = "Z ničoho"

                output_text = ""
                for material in self.actions.buildings[building]["output"][0].keys():
                    output_text += f'{self.actions.buildings[building]["output"][0][material]} {material}, '
                if output_text:
                    output_text = output_text[:-2]
                else:
                    output_text = "-"
                
                time_text = f"{self.actions.buildings[building]['ticks per item'][0]} ⌛"
            else:
                input_text = "-"
                output_text = "-"
                time_text = "0 ⌛"
            

            tk.Label(self.build_window, text=building, width=25, font=("smili", self.font_size)).grid(row=2 * i, column=0)
            tk.Label(self.build_window, text=cost_text, width=45, font=("smili", int(self.font_size * 0.7))).grid(row=2 * i, column=1)
            tk.Label(self.build_window, text=requirement_text, width=25, font=("smili", self.font_size)).grid(row=2 * i, column=2)
            button = tk.Button(self.build_window, text="✔", bg="green2", width=15, font=("smili", self.font_size))
            button.grid(row=2 * i, column=3)

            tk.Label(self.build_window, text=input_text, width=25, font=("smili", self.font_size)).grid(row=2 * i + 1, column=0)
            tk.Label(self.build_window, text="------->", font=("smili", self.font_size * 2)).grid(row=2 * i + 1, column=1)
            tk.Label(self.build_window, text=output_text, width=25, font=("smili", self.font_size)).grid(row=2 * i + 1, column=2)
            tk.Label(self.build_window, text=time_text, width=15, font=("smili", self.font_size)).grid(row=2 * i + 1, column=3)





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
        
        '''
        inv = self.actions.inventory
        self.menu_canvas.create_rectangle(0, ceiling, x, ceiling+len(inv)*20, fill='yellow')
        for i, item in enumerate(inv.keys()):
            self.menu_canvas.create_text(x/2, ceiling+i*20+10, text=f'{item} : {inv[item]}')
        '''

        if True: # TODO eventualne check ci sa tu da stavat
            tk.Button(text="Stavať", command=self.create_build_window, borderwidth=4, font=("smili", self.font_size)).\
                place(rely=0.68, x=self.map_canvas_size["x"], width=self.menu_canvas_size["x"], relheight=0.08)
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
                # calculating where the hexagon is in map coordinates
                y_cord_difference = center_piece_row - row
                x_cord_difference = column - center_piece_column - (y_cord_difference // 2)

                self.tkinter_to_map_cords[(center_pos_x, center_pos_y)] = (self.center_hexagon_cords["x"] + x_cord_difference, self.center_hexagon_cords["y"] + y_cord_difference)

                color = "red"
                if self.tkinter_to_map_cords[(center_pos_x, center_pos_y)] in self.clicked_hexagons:
                    color = "blue"

                self.draw_hexagon(center_pos_x, center_pos_y, 0.95 * side_length, color)

                center_pos_x += (((3) ** 0.5) / 2) * side_length * 2

    def draw_hexagon(self, x, y, side_length, color="red"):
        x_shift = (((3) ** 0.5) / 2) * side_length
        y_shift = side_length / 2
        self.polygons.append((self.map_canvas.create_polygon(
            x, y + side_length,
            x - x_shift, y + y_shift,
            x - x_shift, y - y_shift,
            x, y - side_length,
            x + x_shift, y - y_shift,
            x + x_shift, y + y_shift,
            fill=color
        ), (x, y)))


if __name__ == "__main__":
    front = Front(None)
    front.window.mainloop()
