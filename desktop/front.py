import tkinter as tk
from math import ceil, acos, degrees
import unicodedata
import winsound


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
        self.hexagon_color = "ivory2"
        self.clicked_hexagon_color = "gold"

        self.map_canvas_size = {"x": window_width - (window_height / 2), "y": window_height}
        self.menu_canvas_size = {"x": window_height / 2, "y": window_height}

        self.font_size = int(window_height / 60)

        # line below makes window completely fullscreen (annoying to test with)
        # self.window.overrideredirect(True)
        # self.window.geometry(f"{window_width}x{window_height}+0+0")

        self.map_canvas = tk.Canvas(self.window, bg="deep sky blue")
        self.map_canvas.place(y=0, width=self.map_canvas_size["x"], relheight=1)

        self.menu_canvas = tk.Canvas(self.window, bg="grey")
        self.menu_canvas.place(y=0, x=self.map_canvas_size["x"], width=self.menu_canvas_size["x"], relheight=1)

        self.zoom = 6 # describes how many rows of tiles will be displayed
        self.zoom_strength = 3
        self.selected_pos = []
        self.map_cords = []
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

        self.draw_map()

        # inventory
        self.inventory_window = None

        # trades
        self.trade_page_number = 0
        self.trade_window = None
        self.disposable_trade_labels = []

        self.make_trade_window = None
        self.make_trade_objects = {}

        # army building
        self.army_building_win = None

        # building
        self.build_window = None
        self.build_page_number = 0
        self.disposable_build_labels = []
        self.build_confirm_window = None

        # menu
        self.disposable_menu_buttons = []

        # upgrading
        self.upgrade_window = None

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
            if self.zoom <= 0:
                self.zoom = 1

        direction = mid_shift_directions[int(determine_area((event.x, event.y), (mid_x, mid_y)))]
        self.center_hexagon_cords["x"] -= direction[0] * mid_shift_size
        self.center_hexagon_cords["y"] -= direction[1] * mid_shift_size

        self.polygons = []
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
        
        self.polygons = []
        self.draw_map()
    
    # matus sprta to kodu
    def select_hex(self, event):
        id = min(self.polygons, key=lambda l: ((l[1][0]-event.x)**2 + (l[1][1]-event.y)**2)**0.5)

        if self.selected_pos != []:
            self.map_canvas.itemconfig(self.selected_pos[0], fill=self.get_hexagon_color(self.map_cords))
        self.selected_pos = id
        map_cords = self.tkinter_to_map_cords[id[1]]
        print(map_cords)
        self.map_cords = [map_cords[0], map_cords[1]]

        self.status = self.actions.possible_actions(list(map_cords))
        self.draw_menu()
        # tu pride daco co bude zo statusu pisat veci na sidebar
        # self.map_canvas.create_text(id[1][0], id[1][1], text=f"{map_cords[0]}, {map_cords[1]}")
        self.map_canvas.itemconfig(self.selected_pos[0], fill=self.clicked_hexagon_color)

        if self.build_window:
            try:
                self.build_window.destroy()
            except tk.TclError:
                pass

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

        self.disposable_trade_labels = []

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
            play_sound(False)
            print("eeee1")
            return
        if trade["count"].isnumeric():
            trade["count"] = int(trade["count"])
            if trade["count"] < 0:
                # e-ee
                play_sound(False)
                print("eeee2")
                return
        else:
            # e-ee
            play_sound(False)
            print("eeee3")
            return
        if trade["cost"].isnumeric():
            trade["cost"] = int(trade["cost"])
            if trade["cost"] < 0:
                # e-ee
                play_sound(False)
                print("eeee4")
                return
        else:
            # e-ee
            play_sound(False)
            print("eeee5")
            return
        
        if self.make_trade_objects["direction"]:
            if self.actions.inventory["money"] < trade["cost"]:
                # e-ee
                play_sound(False)
                print("eeee6")
                return
        else:
            if self.actions.inventory[trade["item"]] < trade["count"]:
                # e-ee
                play_sound(False)
                print("eeee7")
                return
        
        self.actions.place_trade(int(not self.make_trade_objects["direction"]), trade["item"], trade["count"], trade["cost"])

        # cink
        play_sound(True)
        print("cink")

    def buy(self, id):
        if self.actions.take_trade(id):
             # cink
            play_sound(True)
            print('cink')
        else:
             # e-eee
            play_sound(False)
            print('eeee')

    def create_army_window(self):
        if self.army_building_win:
            try:
                self.army_building_win.destroy()
            except tk.TclError:
                pass
        
        self.army_building_win = tk.Tk()
        self.update_create_army_window()
        self.army_building_win.title("Armáda")
         
    def update_create_army_window(self):
        if self.army_building_win:
            try:
                tk.Label(self.army_building_win, width=10, text='Názov', font=("smili", self.font_size)).grid(row=0, column=0)
                tk.Label(self.army_building_win, width=10, text='Koľko máš', font=("smili", self.font_size)).grid(row=0, column=1)
                tk.Label(self.army_building_win, width=10, text='Sila', font=("smili", self.font_size)).grid(row=0, column=2)
                tk.Label(self.army_building_win, width=10, text='Vyrobiť', font=("smili", self.font_size)).grid(row=0, column=3)
                tk.Label(self.army_building_win, text='Potrebné suroviny', font=("smili", self.font_size)).grid(row=0, column=4, columnspan=100)
                for i, soldier in enumerate(self.actions.army.keys()):
                    tk.Label(self.army_building_win, text=soldier, font=("smili", self.font_size)).grid(row=i+1, column=0)
                    tk.Label(self.army_building_win, text=f'{self.actions.army[soldier]["count"]}', font=("smili", self.font_size)).grid(row=i+1, column=1)
                    tk.Label(self.army_building_win, text=f'{self.actions.army[soldier]["strength"]}', font=("smili", self.font_size)).grid(row=i+1, column=2)
                    tk.Button(self.army_building_win, command=lambda x = soldier: self.make_soldier(x), width=10, text="+", font=("smili", self.font_size)).grid(row=i+1, column=3)
                    for j, item in enumerate(self.actions.army[soldier]["recipe"]):
                        tk.Label(self.army_building_win, text=f'{item}: {self.actions.army[soldier]["recipe"][item]}', font=("smili", self.font_size)).grid(row=i+1, column=4+j)
            except tk.TclError:
                pass

    def make_soldier(self, name):
        if self.actions.build_soldier(name):
            print('cink')
            self.create_army_window()
            play_sound(True)
            # cink
        else:
            print('eee')
            play_sound(False)
            # e-eee

    def change_build_page(self, value):
        self.build_page_number += value
        self.build_page_number %= ceil(len(self.actions.buildings) / 7)
        self.fill_build_window()

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
        
        tk.Button(self.build_window, text="<-", width=30, command=lambda: self.change_build_page(-1), font=("smili", self.font_size)).grid(row=15, column=0)
        tk.Button(self.build_window, text="->", width=30, command=lambda: self.change_build_page(1), font=("smili", self.font_size)).grid(row=15, column=2)
        self.fill_build_window()

    def fill_build_window(self):
        if self.build_window is None:
            return
        try:
            self.build_window.winfo_exists()
        except tk.TclError:
            return

        while self.build_page_number > len(self.actions.buildings) * 7:
            self.build_page_number -= 1

        for label in self.disposable_build_labels:
            try:
                label.destroy()
            except tk.TclError:
                pass

        self.disposable_build_labels = []

        resources = self.actions.find_resources(self.map_cords)

        for i, building in enumerate(list(self.actions.buildings.keys())[self.build_page_number * 7:]):
            if i >= 7:
                break

            is_buildable = True

            cost_text = ""
            for material in self.actions.buildings[building]["cost"][0].keys():
                cost_text += f'{self.actions.buildings[building]["cost"][0][material]} {material}, '
                if self.actions.inventory.get(material, 0) < self.actions.buildings[building]["cost"][0][material]:
                    is_buildable = False
            cost_text = cost_text[:-2]

            requirement_text = self.actions.buildings[building]["requrement"]
            if not requirement_text:
                requirement_text = "Môže byť kdekoľvek"
            else:
                requirement_text = "Musí byť pri: " + requirement_text
                if self.actions.buildings[building]["requrement"] not in resources:
                    is_buildable = False

            if self.actions.buildings[building]["generating"]:
                input_text = ""
                for material in self.actions.buildings[building]["input"][0].keys():
                    input_text += f'{self.actions.buildings[building]["input"][0][material]} {material}, '
                if input_text:
                    input_text = input_text[:-2]
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

            if "points" in self.actions.buildings[building].keys():
                points = self.actions.buildings[building]["points"][0]
                if points == 0:
                    points_text = "0 bodov"
                elif points == 1:
                    points_text = f'{points} bod'
                elif points <= 4:
                    points_text = f'{points} body'
                else:
                    points_text = f'{points} bodov'
            else:
                points_text = "0 bodov"

            self.disposable_build_labels.append(tk.Label(self.build_window, text=building, width=25, font=("smili", self.font_size)))
            self.disposable_build_labels[-1].grid(row=2 * i, column=0)
            self.disposable_build_labels.append(tk.Label(self.build_window, text=cost_text, width=45, font=("smili", int(self.font_size * 0.7))))
            self.disposable_build_labels[-1].grid(row=2 * i, column=1)
            self.disposable_build_labels.append(tk.Label(self.build_window, text=requirement_text, width=25, font=("smili", self.font_size)))
            self.disposable_build_labels[-1].grid(row=2 * i, column=2)
            self.disposable_build_labels.append(tk.Button(self.build_window, text="✔", command=lambda x=building: self.build_confirm_menu(x), bg="green2", width=15, font=("smili", self.font_size)))
            self.disposable_build_labels[-1].grid(row=2 * i, column=3)

            if not is_buildable:
                self.disposable_build_labels[-1].config(bg="grey", state="disabled")

            self.disposable_build_labels.append(tk.Label(self.build_window, text=input_text, width=25, font=("smili", self.font_size)))
            self.disposable_build_labels[-1].grid(row=2 * i + 1, column=0)
            self.disposable_build_labels.append(tk.Label(self.build_window, text="------->", font=("smili", self.font_size * 2)))
            self.disposable_build_labels[-1].grid(row=2 * i + 1, column=1)
            self.disposable_build_labels.append(tk.Label(self.build_window, text=output_text, width=25, font=("smili", self.font_size)))
            self.disposable_build_labels[-1].grid(row=2 * i + 1, column=2)
            self.disposable_build_labels.append(tk.Label(self.build_window, text=time_text, width=15, font=("smili", self.font_size)))
            self.disposable_build_labels[-1].grid(row=2 * i + 1, column=3)

            self.disposable_build_labels.append(tk.Label(self.build_window, text=f"{self.build_page_number + 1} / {ceil(len(self.actions.buildings) / 7)}", width=25, font=("smili", self.font_size)))
            self.disposable_build_labels[-1].grid(row=15, column=1)

            self.disposable_build_labels.append(tk.Label(self.build_window, text=points_text, width=10, font=("smili", int(self.font_size * 1.6))))
            self.disposable_build_labels[-1].grid(row=2 * i, column=4, rowspan=2)

    def build_confirm_menu(self, building):
        if self.build_confirm_window:
            try:
                self.build_confirm_window.destroy()
            except tk.TclError:
                pass
        self.build_confirm_window = tk.Tk()

        tk.Label(self.build_confirm_window, text=f"Zadaj kód pre: {building}", font=("smili", self.font_size), width=30).pack()
        entry = tk.Entry(self.build_confirm_window, font=("smili", self.font_size), width=30)
        entry.pack()
        tk.Button(self.build_confirm_window, text="✔", command=lambda: self.verify_build_confirmation(building, entry.get()), bg="green2", width=30, font=("smili", self.font_size)).pack()

    def verify_build_confirmation(self, building, code):
        if True: # TODO verifikacia kodu eventualne
            self.actions.build_new(building, self.map_cords)
            self.actions.frontend_update()
            self.build_confirm_window.destroy()
            self.build_window.destroy()
            self.draw_menu()
            self.polygons = []
            self.draw_map()
            # zvuky stavby
        else:
            play_sound(False)
             # e-ee

    def upgrade_selected_building(self):
        self.actions.upgrade(self.map_cords)
        if self.upgrade_window:
            try:
                self.upgrade_window.destroy()
            except tk.TclError:
                pass
        self.draw_menu()
        
    def create_upgrade_window(self, infos):
        if self.upgrade_window:
            try:
                self.upgrade_window.destroy()
            except tk.TclError:
                pass
        
        self.upgrade_window = tk.Tk()

        next_level = infos["level"]

        tk.Label(self.upgrade_window, text=f'{infos["name"]}: {next_level + 1}', font=("smili", self.font_size)).pack()

        if self.actions.buildings[infos["name"]]["generating"]:
            input_text = ""
            for material in self.actions.buildings[infos["name"]]["input"][next_level].keys():
                input_text += f'{self.actions.buildings[infos["name"]]["input"][next_level][material]} {material}, '
            if input_text:
                input_text = input_text[:-2]
            else:
                input_text = "Z ničoho"

            time_text = f'↓ {self.actions.buildings[infos["name"]]["ticks per item"][next_level]} ⌛ ↓'

            output_text = ""
            for material in self.actions.buildings[infos["name"]]["output"][next_level].keys():
                output_text += f'{self.actions.buildings[infos["name"]]["output"][next_level][material]} {material}, '
            if output_text:
                output_text = output_text[:-2]
            else:
                output_text = "Nič"
        
        else:
            time_text = "↓ 0 ⌛ ↓"
            input_text = "Z ničoho"
            output_text = "Nič"
        
        if "points" in self.actions.buildings[infos["name"]].keys():
            points = self.actions.buildings[infos["name"]]["points"][infos["level"]]
            if points == 0:
                points_text = "0 bodov"
            elif points == 1:
                points_text = f'{points} bod'
            elif points <= 4:
                points_text = f'{points} body'
            else:
                points_text = f'{points} bodov'
        else:
            points_text = "0 bodov"
        tk.Label(self.upgrade_window, text=points_text, font=("smili", self.font_size)).pack()

        tk.Label(self.upgrade_window, text=input_text, font=("smili", self.font_size)).pack()
        tk.Label(self.upgrade_window, text=time_text, font=("smili", self.font_size)).pack()
        tk.Label(self.upgrade_window, text=output_text, font=("smili", self.font_size)).pack()

        is_buildable = True
        cost_text = ""
        for material in self.actions.buildings[infos["name"]]["cost"][next_level].keys():
            cost_text += f'{self.actions.buildings[infos["name"]]["cost"][next_level][material]} {material}, '
            if self.actions.inventory.get(material, 0) < self.actions.buildings[infos["name"]]["cost"][next_level][material]:
                is_buildable = False
        cost_text = cost_text[:-2]
        tk.Label(self.upgrade_window, text=cost_text, font=("smili", self.font_size)).pack()

        button = tk.Button(self.upgrade_window, text="✔", width=30, command=self.upgrade_selected_building, bg="green2", font=("smili", self.font_size))
        button.pack()
        if not is_buildable:
            button.configure(bg="gray", state="disabled")


    def draw_menu(self, ceiling=0):
        self.menu_canvas.delete('all')

        for i in self.disposable_menu_buttons:
            try:
                i.destroy()
            except tk.TclError:
                pass

        self.status = self.actions.possible_actions(list(self.map_cords))
        
        '''
        self.buttons = []
        x = self.menu_canvas_size['x']
        y = self.menu_canvas_size['y']

        infos = self.status['info']
        self.menu_canvas.create_rectangle(0, ceiling, x, ceiling+len(infos)*20, fill='yellow')
        for i, info in enumerate(infos.keys()):
            self.menu_canvas.create_text(x/2, ceiling+i*20+10, text=f'{info} : {infos[info]}')
        ceiling += len(infos)*20

        for action in self.status['actions']:
            ceiling += self.draw_button(action, ceiling)
        '''

        infos = self.status['info']
        name = infos["name"]
        if name in self.actions.buildings.keys():
            name += f": {infos['level']}"
        '''
        inv = self.actions.inventory
        self.menu_canvas.create_rectangle(0, ceiling, x, ceiling+len(inv)*20, fill='yellow')
        for i, item in enumerate(inv.keys()):
            self.menu_canvas.create_text(x/2, ceiling+i*20+10, text=f'{item} : {inv[item]}')
        '''

        self.disposable_menu_buttons.append(tk.Label(text=name, bg="yellow", borderwidth=4, font=("smili", self.font_size * 2)))
        self.disposable_menu_buttons[-1].place(rely=0, x=self.map_canvas_size["x"], width=self.menu_canvas_size["x"], relheight=0.12)

        if self.map_cords in self.actions.available_lands:
            self.disposable_menu_buttons.append(tk.Button(text="Stavať", command=self.create_build_window, borderwidth=4, font=("smili", self.font_size)))
            self.disposable_menu_buttons[-1].place(rely=0.68, x=self.map_canvas_size["x"], width=self.menu_canvas_size["x"], relheight=0.08)

        elif infos["name"] in list(self.actions.buildings.keys()):
            if infos["level"] < len(self.actions.buildings[infos["name"]]["cost"]):
                self.disposable_menu_buttons.append(tk.Button(text="Vylepšiť", command=lambda: self.create_upgrade_window(infos), borderwidth=4, font=("smili", self.font_size)))
                self.disposable_menu_buttons[-1].place(rely=0.68, x=self.map_canvas_size["x"], width=self.menu_canvas_size["x"] / 2, relheight=0.08)
            else:
                self.disposable_menu_buttons.append(tk.Button(text="MAX level", state="disabled", borderwidth=4, font=("smili", self.font_size)))
                self.disposable_menu_buttons[-1].place(rely=0.68, x=self.map_canvas_size["x"], width=self.menu_canvas_size["x"] / 2, relheight=0.08)

            if infos['is_sleeping']:
                self.disposable_menu_buttons.append(tk.Button(text="Zobuď", command=lambda: self.actions.wake_up(self.map_cords), borderwidth=4, font=("smili", self.font_size)))
            else:
                self.disposable_menu_buttons.append(tk.Button(text="Uspať", command=lambda: self.actions.sleep(self.map_cords), borderwidth=4, font=("smili", self.font_size)))
            self.disposable_menu_buttons[-1].place(rely=0.68, x=self.map_canvas_size["x"] + self.menu_canvas_size["x"] / 2, width=self.menu_canvas_size["x"] / 2, relheight=0.08)

            if self.actions.buildings[infos["name"]]["generating"]:
                input_text = ""
                for material in self.actions.buildings[infos["name"]]["input"][infos["level"] - 1].keys():
                    input_text += f'{self.actions.buildings[infos["name"]]["input"][infos["level"] - 1][material]} {material}, '
                if input_text:
                    input_text = input_text[:-2]
                else:
                    input_text = "Z ničoho"

                output_text = ""
                for material in self.actions.buildings[infos["name"]]["output"][infos["level"] - 1].keys():
                    output_text += f'{self.actions.buildings[infos["name"]]["output"][infos["level"] - 1][material]} {material}, '
                if output_text:
                    output_text = output_text[:-2]
                else:
                    output_text = "-"
                
                time_text = f"↓ {self.actions.buildings[infos['name']]['ticks per item'][infos['level'] - 1]} ⌛ ↓"

                self.disposable_menu_buttons.append(tk.Label(text=input_text, borderwidth=4, font=("smili", self.font_size)))
                self.disposable_menu_buttons[-1].place(rely=0.12, x=self.map_canvas_size["x"], width=self.menu_canvas_size["x"], relheight=0.08)
                self.disposable_menu_buttons.append(tk.Label(text=time_text, borderwidth=4, font=("smili", self.font_size)))
                self.disposable_menu_buttons[-1].place(rely=0.20, x=self.map_canvas_size["x"], width=self.menu_canvas_size["x"], relheight=0.08)
                self.disposable_menu_buttons.append(tk.Label(text=output_text, borderwidth=4, font=("smili", self.font_size)))
                self.disposable_menu_buttons[-1].place(rely=0.28, x=self.map_canvas_size["x"], width=self.menu_canvas_size["x"], relheight=0.08)
        elif infos["name"] in self.actions.beast_types.keys():
            self.disposable_menu_buttons.append(tk.Button(text="Zaútočiť", command=lambda: self.actions.fight_monster(infos["name"], infos["level"], self.actions.to_pos_string(*self.map_cords)), borderwidth=4, font=("smili", self.font_size)))
            self.disposable_menu_buttons[-1].place(rely=0.68, x=self.map_canvas_size["x"], width=self.menu_canvas_size["x"], relheight=0.08)

            strength_text = f'Sila {self.actions.beast_types[infos["name"]]["strength"]}'
            self.disposable_menu_buttons.append(tk.Label(text=strength_text, borderwidth=4, font=("smili", self.font_size)))
            self.disposable_menu_buttons[-1].place(rely=0.12, x=self.map_canvas_size["x"], width=self.menu_canvas_size["x"], relheight=0.08)



        self.disposable_menu_buttons.append(tk.Button(text="Armáda", command=self.create_army_window, borderwidth=4, font=("smili", self.font_size)))
        self.disposable_menu_buttons[-1].place(rely=0.76, x=self.map_canvas_size["x"], width=self.menu_canvas_size["x"], relheight=0.08)
        self.disposable_menu_buttons.append(tk.Button(text="Obchodovanie", command=self.create_trade_window, borderwidth=4, font=("smili", self.font_size)))
        self.disposable_menu_buttons[-1].place(rely=0.84, x=self.map_canvas_size["x"], width=self.menu_canvas_size["x"], relheight=0.08)
        self.disposable_menu_buttons.append(tk.Button(text="Inventár", command=self.create_inventory_window, borderwidth=4, font=("smili", self.font_size)))
        self.disposable_menu_buttons[-1].place(rely=0.92, x=self.map_canvas_size["x"], width=self.menu_canvas_size["x"], relheight=0.08)

        # print(len(self.window.winfo_children())) # useful check ci sa nezahlcuje okno

    def draw_button(self, action, ceiling):# button = (id, (x, y), (action))
        self.buttons.append((self.menu_canvas.create_rectangle(0, ceiling, self.menu_canvas_size['x'], ceiling+30, fill='grey'), (self.menu_canvas_size['x']/2, ceiling+15), action))
        self.menu_canvas.create_text(self.menu_canvas_size['x']/2, ceiling+10, text=action[0])
        self.menu_canvas.create_text(self.menu_canvas_size['x']/2, ceiling+20, text=action[2])
        return 30

    def menu_click(self, event):
        button = min(self.buttons, key=lambda l: ((l[1][0]-event.x)**2 + (l[1][1]-event.y)**2)**0.5)
        # print(button[2][1])
        button[2][1][0](*button[2][1][1])
        map_cords = self.tkinter_to_map_cords[self.selected_pos[1]]
        self.status = self.actions.possible_actions(list(map_cords))
        # print(self.status)
        self.draw_menu()

    def menu_scroll(self, event):
        self.draw_menu()

    def get_hexagon_color(self, cords):
        color = self.hexagon_color

        max_strength = 5000

        typ = self.actions.all_lands[self.actions.to_pos_string(*cords)]
        if typ["name"] in self.actions.beast_types.keys():
            strength = typ["level"] * self.actions.beast_types[typ["name"]]["strength"]

            if strength > max_strength:
                percentage = 1
            else:
                percentage = strength / max_strength
            percentage = 1 - percentage
            
            rgb_color = [int(percentage * 180) for i in range(3)]
            rgb_color[1] += 75

            color = f"#{rgb_color[0]:02x}{rgb_color[1]:02x}{rgb_color[2]:02x}"

        
        return color

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

                if self.actions.to_pos_string(*self.tkinter_to_map_cords[(center_pos_x, center_pos_y)]) not in self.actions.all_lands:
                    center_pos_x += (((3) ** 0.5) / 2) * side_length * 2
                    continue
                building = self.actions.all_lands[self.actions.to_pos_string(*self.tkinter_to_map_cords[(center_pos_x, center_pos_y)])]

                cords = list(self.tkinter_to_map_cords[(center_pos_x, center_pos_y)])

                color = self.get_hexagon_color(cords)

                if list(self.tkinter_to_map_cords[(center_pos_x, center_pos_y)]) == self.map_cords:
                    color = self.clicked_hexagon_color
               

                if building["name"] in self.actions.buildings.keys():
                    design = self.actions.buildings[building["name"]]["design"]
                    self.draw_hexagon(center_pos_x, center_pos_y, 0.95 * side_length, color, design["shape"], design["color"])
                elif building["name"] == "base":
                    self.draw_hexagon(center_pos_x, center_pos_y, 0.95 * side_length, color, "star", "black")
                else:
                    self.draw_hexagon(center_pos_x, center_pos_y, 0.95 * side_length, color)

                center_pos_x += (((3) ** 0.5) / 2) * side_length * 2

    def draw_hexagon(self, x, y, side_length, color, building_shape=None, building_color=None):
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

        if color == self.clicked_hexagon_color:
            self.selected_pos = self.polygons[-1]

        width = side_length // 15 + 1
        
        if building_shape == "dot":
            self.map_canvas.create_oval(
                x - side_length / 4, y - side_length / 4,
                x + side_length / 4, y + side_length / 4,
                fill=building_color, width=0
            )
        if building_shape == "square":
            self.map_canvas.create_rectangle(
                x - side_length / 2.5, y - side_length / 2.5,
                x + side_length / 2.5, y + side_length / 2.5,
                fill=building_color, outline="black", width=width
            )
        elif building_shape == "triangle":
            radius = side_length / 1.5
            distance = ((3 ** (0.5)) / 2) * radius
            self.map_canvas.create_polygon(
                x, y - radius,
                x - distance, y + radius / 2,
                x + distance, y + radius / 2,
                fill=building_color,
                outline="black",
                width=width
            )
        elif building_shape == "pentagon":
            radius = side_length * 0.6
            self.map_canvas.create_polygon(
                x, y - radius,
                x + radius*0.951, y - radius*0.309,
                x + radius*0.587, y + radius*0.809,
                x - radius*0.587, y + radius*0.809,
                x - radius*0.951, y - radius*0.309,
                fill=building_color,
                outline="black",
                width=width
            )
        elif building_shape == "star":
            radius = side_length * 0.6
            p = 0.618-1
            self.map_canvas.create_polygon(
                x, y - radius,
                x - radius*0.587*p, y + radius*0.809*p,
                x + radius*0.951, y - radius*0.309,
                x - radius*0.951*p, y - radius*0.309*p,
                x + radius*0.587, y + radius*0.809,
                x, y - radius*p,
                x - radius*0.587, y + radius*0.809,
                x + radius*0.951*p, y - radius*0.309*p,
                x - radius*0.951, y - radius*0.309,
                x + radius*0.587*p, y + radius*0.809*p,
                fill=building_color,
                outline="black",
                width=width
            )
        elif building_shape == "hexagon":
            side_length = side_length * 0.6
            x_shift = (((3) ** 0.5) / 2) * side_length
            y_shift = side_length / 2
            self.map_canvas.create_polygon(
                x, y + side_length,
                x - x_shift, y + y_shift,
                x - x_shift, y - y_shift,
                x, y - side_length,
                x + x_shift, y - y_shift,
                x + x_shift, y + y_shift,
                fill=building_color,
                outline="black",
                width=width
        )

        

    
def play_sound(is_correct: bool) -> None:
    print(is_correct)
    
    if is_correct:
        winsound.PlaySound('sounds/cin.wav', winsound.SND_ASYNC)
    else:
        winsound.PlaySound('sounds/eeee.wav', winsound.SND_ASYNC)
        


if __name__ == "__main__":
    front = Front(None)
    front.window.mainloop()
