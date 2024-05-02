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
        self.draw_map()

        self.map_canvas.bind("<MouseWheel>", self.scroll_response)


    def update(self): # call this function rapidly to make everything work
        self.map_canvas.update()


    def scroll_response(self, event):
        if event.num == 5 or event.delta == -120:
            self.zoom += 1
        if event.num == 4 or event.delta == 120:
            if self.zoom > 1:
                self.zoom -= 1
        self.draw_map()
    

    def draw_map(self):
        self.map_canvas.delete("all")

        side_length = (2 * self.map_canvas_size["y"]) / (3 * self.zoom + 1)
        hexagon_width = ((3) ** 0.5) * side_length
        full_num_of_columns = int(self.map_canvas_size["x"] / hexagon_width)

        center_piece_row = self.zoom // 2

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
                center_pos_x += (((3) ** 0.5) / 2) * side_length * 2
    
    def draw_hexagon(self, x, y, side_length): # TODO turn this into an object so that it's clickable
        x_shift = (((3) ** 0.5) / 2) * side_length
        y_shift = side_length / 2
        self.map_canvas.create_polygon(x, y + side_length,
                                       x - x_shift, y + y_shift,
                                       x - x_shift, y - y_shift,
                                       x, y - side_length,
                                       x + x_shift, y - y_shift,
                                       x + x_shift, y + y_shift,
                                       fill="red")


if __name__ == "__main__":
    front = Front(None)
    while True:
        front.update()
