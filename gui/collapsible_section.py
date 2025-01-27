import customtkinter

class CollapsibleSection(customtkinter.CTkFrame):
    def __init__(self, master, title="Section", items=None, on_select=None, **kwargs):
        super().__init__(master, **kwargs)
        self.title = title
        self.items = items if items else []
        self.on_select = on_select

        self.is_expanded = True
        self.configure(fg_color="#1b1b1b")

        self.header_frame = customtkinter.CTkFrame(self, fg_color="#1b1b1b")
        self.header_frame.pack(fill="x", expand=False)
        self.title_label = customtkinter.CTkLabel(
            self.header_frame, text=self.title, font=("Arial", 14), text_color="white"
        )
        self.title_label.pack(side="left", padx=5)

        self.toggle_button = customtkinter.CTkButton(
            self.header_frame, text="▲", width=20,
            command=self.toggle_items,
            fg_color="#333333", text_color="white",
            hover_color="#555555"
        )
        self.toggle_button.pack(side="right", padx=2)

        self.items_frame = customtkinter.CTkFrame(self, fg_color="#1b1b1b")
        self.item_buttons = []
        for item_name in self.items:
            btn = customtkinter.CTkButton(
                self.items_frame,
                text=item_name,
                fg_color="#333333",
                text_color="white",
                command=lambda n=item_name: self.on_item_clicked(n),
                width=150
            )
            self.item_buttons.append(btn)

        self.show_items()

    def toggle_items(self):
        if self.is_expanded:
            self.hide_items()
        else:
            self.show_items()

    def show_items(self):
        self.items_frame.pack(fill="x", expand=False, padx=5, pady=5)
        self.toggle_button.configure(text="▲")
        self.is_expanded = True
        for b in self.item_buttons:
            b.pack(fill="x", pady=2)

    def hide_items(self):
        self.items_frame.pack_forget()
        self.toggle_button.configure(text="▼")
        self.is_expanded = False

    def on_item_clicked(self, item_name):
        if self.on_select:
            self.on_select(item_name)

    def add_item(self, new_item):
        btn = customtkinter.CTkButton(
            self.items_frame, text=new_item,
            fg_color="#333333", text_color="white",
            command=lambda: self.on_item_clicked(new_item)
        )
        self.item_buttons.append(btn)
        if self.is_expanded:
            btn.pack(fill="x", pady=2)
