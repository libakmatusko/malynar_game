import tkinter as tk

MAP_RADIUS = 30


class Front:
    def __init__(self, actions):
        self.actions = actions
        self.window = tk.Tk()

        window_height = self.window.winfo_screenheight() # - 200 # - 200 only for easier testing
        window_width = self.window.winfo_screenwidth() # - 200 # - 200 only for easier testing

        self.map_canvas_size = {"x": window_width - (window_height / 2), "y": window_height}
        self.menu_canvas_size = {"x": window_height / 2, "y": window_height}

        # line below makes window completely fullscreen (annoying to test with)
        self.window.overrideredirect(True)
        self.window.geometry(f"{window_width}x{window_height}+0+0")

        self.map_canvas = tk.Canvas(self.window, bg="green2")
        self.map_canvas.place(y=0, width=self.map_canvas_size["x"], relheight=1)

        self.menu_canvas = tk.Canvas(self.window, bg="grey")
        self.menu_canvas.place(y=0, x=self.map_canvas_size["x"], width=self.menu_canvas_size["x"], relheight=1)

        self.zoom = 7 # describes how many rows of tiles will be displayed
        self.selected_pos = []

        self.map_canvas.bind("<MouseWheel>", self.scroll_response)
        # matus sprta to kodu
        self.map_canvas.bind('<Button-1>', self.select_hex)
        self.polygons = []
        self.tkinter_to_map_cords = {}

        self.center_hexagon_cords = {"x": 0, "y": 0} # defining on which hexagon the map is centered

        self.draw_map()


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
            self.map_canvas.create_text(id[1][0], id[1][1], text=f"{map_cords[0]}, {map_cords[1]}")
            self.map_canvas.itemconfig(self.selected_pos[0], fill='blue')
        self.update()


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
    while True:
        front.update()
