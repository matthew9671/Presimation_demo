from Animation import *
from interface import *
import copy

# TODO: Put layout parameters here
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

WORKSPACE_SIDES = 1/6
WORKSPACE_BOTTOM = 1/3
WORKSPACE_MARGIN = 1/20

# Bottom left
WORKSPACE_ORIGIN_X = SCREEN_WIDTH * (WORKSPACE_SIDES + WORKSPACE_MARGIN)
WORKSPACE_ORIGIN_Y = SCREEN_HEIGHT * (1 - WORKSPACE_BOTTOM - WORKSPACE_MARGIN)

# Convert global coordinates to coordinates in the workspace
# Just for reference
def global_to_workspace(x, y = None):
    if y == None:
        y = x[1]
        x = x[0]
    return (x - WORKSPACE_ORIGIN_X, WORKSPACE_ORIGIN_Y - y)

# colors
lightGrey = rgbString(200,200,200)
offWhite = rgbString(250, 250, 235)

def double_click_debug(): print("Registered double click!")

# This class stores information about fields of an object
# including how it is presented in the menu
class psm_field(object):

    ICON_SIZE = 32
    MARGIN = 10
    ICON_BOX_SPACING = 5
    ITEM_SPACING = 15
    BOX_HEIGHT = 40

    # TODO: LARGE input boxes
    BOX_WIDTH = {"NONE": 0,
                 "SMALL": 50,
                 "MEDIUM": 150}


    def __init__(self, name, position = None, parent = None,
        value = 0, 
        value_type = int,
        value_max = None,
        # "NONE" "SMALL" "MEDIUM" "LARGE"
        input_size = "SMALL"):

        self.name = name
        self.value = value
        # We will set the icons of the fields all at once using set_icon()
        self.icon = None

        self.value_type = value_type
        self.value_max = value_max

        # Hidden fields must have a parent
        self.is_hidden = False
        self.children = None
        self.input_size = input_size
        # (row, col)
        self.position = position
        # "BASIC" "COLOR" "DIMENSIONS" and so on
        self.tab = "BASIC"

    def set_value(self, value):
        self.value = value

    def get_value(self):
        return self.value

    def set_icon(self, icon):
        self.icon = icon

def insert_field_in_2d_array(array, field, position):
    row, col = position
    if len(array) <= row:
        n = len(array)
        for i in range(n, row + 1):
            array.append([])
    if len(array[row]) <= col:
        n = len(array[row])
        for i in range(n, row + 1):
            array[row].append(None)
    array[row][col] = field        

class psm_menu(psm_GUI_object):

    BG_COLOR_NORMAL = "grey"

    def __init__(self, attributes_dict):
        self.is_visible = False
        self.current_tab = "BASIC"
        self.tabs = dict()
        for field in attributes_dict.values():
            tab = field.tab
            if tab not in self.tabs.keys():
                self.tabs[tab] = []
            if not field.is_hidden:
                pos = field.position
                insert_field_in_2d_array(self.tabs[tab], field, pos)
        # Create the corresponding GUI items for each field
        self.init_items()

    def init_items(self):
        self.panels = dict()
        for tab in self.tabs.keys():
            # An invisible panel to hold all the buttons
            panel = psm_GUI_object(0,0,0,0)
            for row in range(len(self.tabs[tab])):
                for col in range(len(self.tabs[tab][row])):
                    item = self.tabs[tab][row][col]
                    x1, y1 = get_item_topleft_position(row, col)
                    button = psm_menu_icon(x1,
                                           y1,
                                           x1 + psm_field.ICON_SIZE,
                                           y1 + psm_field.ICON_SIZE,
                                           image = item.icon)
                    panel.add_child(button)
            self.panels[tab] = panel

    def get_item_topleft_position(self, row, col):
        row_height = psm_field.MARGIN * 2 + psm_field.ICON_SIZE
        top = row_height * row + psm_field.MARGIN
        left = psm_field.MARGIN
        for i in range(col):
            item = self.tabs[self.current_tab][row][i]
            left += psm_field.ICON_SIZE
            left += psm_field.ICON_BOX_SPACING
            left += psm_field.BOX_WIDTH[item.input_size]
            left += psm_field.ITEM_SPACING
        return left, top

    def get_dimensions(self):
        rows = len(self.tabs[self.current_tab])
        max_width = 0
        for row in range(rows):
            last_col = len(self.tabs[self.current_tab][row])
            # self.tabs[self.current_tab][row][last_col] doesn't exist
            # but it's okay - we're just calculating how wide
            # the menu should be using our item position method
            curr_width, height = self.get_item_topleft_position(row, last_col)
            if max_width < curr_width: max_width = curr_width

        # Since it's the last item in the row
        # there is no item spacing
        max_width += psm_field.MARGIN - psm_field.ITEM_SPACING
        height += psm_field.MARGIN + psm_field.ICON_SIZE

        return max_width, height

    def draw(self, canvas, startx, starty):
        width, height = self.get_dimensions()
        # Create background rectangle
        # Since we might get fancy with the shape, 
        # we will draw it here instead of in gui_rect
        canvas.create_rectangle(startx, 
                                starty,
                                startx + width,
                                starty + height, 
                                fill = psm_menu.BG_COLOR_NORMAL)
        self.panels[self.current_tab].resize_object(startx, starty)
        self.panels[self.current_tab].draw(canvas)
        # TODO: Add input fields!


class psm_object(object):
    def __init__(self, name, index):
        # A list of all the field names
        # Which are keys to the attributes dictionary
        self.fields = ["NAME", "INDEX"]

        # A dictionary that stores all of the object's attributes
        self.attributes = dict()

        # Whether this object will be rendered in the final presentation
        self.is_visible = True

        self.mouse_on = False
        self.is_selected = False
        self.menu_on = False
        # We'll generate the corresponding menu in the specific classes
        self.menu = None

        # TODO: These can be further specified
        name_field = psm_field(name)
        index_field = psm_field(index)
        self.attributes["NAME"] = name_field
        self.attributes["INDEX"] = index_field

    def set_value(self, field, value):
        if field not in self.fields:
            raise Exception("""Field \"" + field + "\" 
does not belong to object!""")
        else:
            self.attributes[field].set_value(value)

    def get_value(self, field):
        if field not in self.fields:
            raise Exception("""Field \"" + field + "\" 
does not belong to object!""")
        else:
            return self.attributes[field].get_value()

    # Returns true if point (x,y) counts as "on" the object
    def in_borders(self, x, y):
        pass

    def mouse_down(self, x, y):
        if self.in_borders(x, y):
            self.is_selected = True
            self.menu_on = True
        else:
            self.is_selected = False

    # Useful when we are drag-selecting objects
    def set_selected(self, value):
        self.is_selected = value

    # Pass in the ratio for drawing miniture slides
    def draw(self, canvas, startx, starty, ratio = 1):
        # We don't want to display the menu in the thumbnail
        if self.menu_on and self.menu != None and ratio == 1:
            self.menu.draw(canvas, startx, starty)

    def get_hashables(self):
        return (self.name, self.index)

    def __eq__(self, other):
        if other == None: return False
        if not isinstance(other, psm_object):
            raise Exception("""Comparing an instance of psm_object
with another object""")
        # We might change this if we allow object aliases
        # i.e. two objects that have the same name and index
        return self.name == other.name and self.index == other.index

    def __hash__(self, other):
        return hash(self.get_hashables())

class psm_circle(psm_object):
    def __init__(self, name, index):
        super().__init__(name, index)
        self.fields.extend (["CENTER_X", "CENTER_Y", "RADIUS", 
                             "FILL_COLOR", "BORDER_COLOR",
                             "BORDER_WIDTH"])
        self.init_attributes()

    def init_attributes(self):
        # Only temporary
        # Finally we will have to customize each of the fields
        for i in range(len(self.fields)):
            field_name = self.fields[i]
            self.attributes[field_name] = psm_field(field_name)

    # The x and y should be in the canvas coodrinate system
    def in_borders(self, x, y):
        center_x = self.get_value("CENTER_X")
        center_y = self.get_value("CENTER_Y")
        radius = self.get_value("RADIUS")
        border = self.get_value("BORDER_WIDTH")
        return ((x - center_x) ** 2 + (y - center_y) ** 2 
               <= (radius + border / 2) ** 2)

    def draw(self, canvas, startx, starty, ratio = 1):
        super().draw(canvas, startx, starty, ratio)
        center_x = self.get_value("CENTER_X")
        center_y = self.get_value("CENTER_Y")
        radius = self.get_value("RADIUS")
        x1 = startx + (center_x - radius) * ratio
        x2 = startx + (center_x + radius) * ratio
        # Note the the +y direction on the canvas is up
        # Because it is convinient for a coordinate system 
        y1 = starty - (center_y + radius) * ratio
        y2 = starty - (center_y - radius) * ratio
        canvas.create_oval(x1, y1, x2, y2)

class psm_tool(object):

    # The minimum size (width and height) that an object can have
    MIN_ELEM_SIZE = 10

    def __init__(self, tool_name, object_name):
        # True when the mouse is pressed
        self.mouse_pressed = False
        self.current_object = None
        # A tuple (x, y) of position coordinates
        self.drag_start = None
        self.tool_name = tool_name
        self.object_name = object_name

    def mouse_down(self, x, y, object_name):
        if not self.mouse_pressed:
            self.drag_start = (x, y)
            self.mouse_pressed = True
            self.generate_object(object_name)

    def mouse_up(self, x, y):
        self.mouse_pressed = False
        # Pass the "ownership" of the object being generated
        # from itself to the main loop
        current_object = self.current_object
        self.current_object = None
        return current_object

    def mouse_move(self, x, y):
        if self.mouse_pressed:
            width = x - self.drag_start[0]
            height = y - self.drag_start[1]
            if width >= 0:
                width = max(width, psm_tool.MIN_ELEM_SIZE)
            else:
                width = min(width, -psm_tool.MIN_ELEM_SIZE)
            if height >= 0: 
                height = max(height, psm_tool.MIN_ELEM_SIZE)
            else:
                height = min(height, -psm_tool.MIN_ELEM_SIZE)
            self.resize_object(width, height)

    def generate_object(self, object_name):
        pass

    def resize_object(self, width, height):
        pass

    def draw_object(self, canvas):
        if self.current_object != None:
            self.current_object.draw(canvas, WORKSPACE_ORIGIN_X, 
                                             WORKSPACE_ORIGIN_Y)

    def get_object_name(self):
        return self.object_name

class psm_circle_tool(psm_tool):

    MIN_RADIUS = 5

    def __init__(self):
        super().__init__(tool_name = "Circle tool", object_name = "Circle")

    def generate_object(self, object_name):
        x, y = global_to_workspace(self.drag_start)
        self.current_object = psm_circle(object_name, 0)
        self.current_object.set_value("CENTER_X", x)
        self.current_object.set_value("CENTER_Y", y)
        self.current_object.set_value("RADIUS", psm_circle_tool.MIN_RADIUS)

    def resize_object(self, dx, dy):
        r = (dx ** 2 + dy ** 2) ** 0.5
        self.current_object.set_value("RADIUS", r)

class slide(object):
    def __init__(self):
        self.objects = []

    def add_object(self, user_object):
        self.objects.append(user_object)

    # Returns an object name that is unique in the slide
    # TODO: Write this
    def generate_object_name(self, name):
        return name

    # Render is specific to slides
    # Has a more professional feel
    def render(self, canvas, startx, starty, edit = True, display_ratio = 1):

        for user_object in self.objects:
            if edit or user_object.is_visible:
                user_object.draw(canvas, startx, starty, display_ratio)

class Presimation(Animation):

    # Defining the toolsets and tools here improves clarity
    # Every item should be a tuple of name(key) and instance of a class

    # TODO: This is only temporary
    TOOLS = [["Objects",
                [("CIRCLE", psm_circle_tool())]
             ],
             ["Drawing",
                []
             ],
             ["Animation", 
                []
             ]
            ]

    def __init__(self, width, height):
        self.width = width
        self.height = height

        # The list of top level GUI objects 
        # including the toolbar, workspace and the timeline
        # TODO: This should be changed since the name is too general
        self.GUI_objects = []

        # (int) The index of the current slide
        # TODO: This needs to be changed since an edited slide is a new slide
        self.current_slide = 0

        # We might not need this -- we can just let objects draw their own menus
        # The list of menus currently opened
        self.menus = []
        
        # The list of slides created
        self.slides = [slide()]

        self.tools = self.get_tool_dict()
        # (psm_tool)
        self.current_tool = None

        # "EDIT" "PLAYBACK"
        self.mode = "EDIT"

        self.init_GUI()

        self.run(width, height)

    def get_tool_dict(self):
        tool_dict = dict()
        for toolset in Presimation.TOOLS:
            tool_dict.update(toolset[1])
        return tool_dict

    def init_GUI(self):
        # TODO: Move these to the top level for convenience
        # independent ratio and size
        self.wkspace_w_ratio = 0.6  # width of the workspace
        self.tmline_h_ratio = 0.25  # height of the timeline
        self.tmline_margin_w = 5
        self.tmline_margin_h = 5

        # users can always see 1/4 of the rest snapshots
        self.tmline_uncover_ratio = 0.25

        self.init_size()
        self.create_outline()
        self.init_tools()
        self.create_timeline()

        self.canvas_start_x = None
        self.canvas_start_y = None

    def init_size(self):
        # dependent ratio
        self.toolbar_w_ratio = (1 - self.wkspace_w_ratio) / 2
        self.toolbar_h_ratio = self.wkspace_h_ratio = 1 - self.tmline_h_ratio
        self.tmline_w_ratio = 1

        # size
        self.toolbar_w = self.width * self.toolbar_w_ratio
        self.toolbar_h = self.height * self.toolbar_h_ratio

        self.tmline_w = self.width * self.tmline_w_ratio
        self.tmline_h = self.height * self.tmline_h_ratio

        self.wkspace_w = self.width * self.wkspace_w_ratio
        self.wkspace_h = self.height * self.wkspace_h_ratio

        # fixed width to height ratio
        self.wkspace_w_to_h = self.wkspace_w / self.wkspace_h

    def create_outline(self):
        # create workspace
        workspace = psm_GUI_object(self.toolbar_w, 0,
          self.toolbar_w + self.wkspace_w, self.wkspace_h, offWhite)
        self.GUI_objects.append(workspace)

        # create toolbars
        left_toolbar = psm_GUI_object(0, 0, 
            self.toolbar_w, self.toolbar_h,lightGrey)
        right_toolbar = psm_GUI_object(self.toolbar_w + self.wkspace_w, 0,
            self.width, self.toolbar_h, lightGrey)
        self.GUI_objects.extend([left_toolbar, right_toolbar])

        # create timeline
        timeline = psm_GUI_object(0, self.toolbar_h,
            self.width, self.height, lightGrey)
        self.GUI_objects.append(timeline)

    def init_tools(self):
        toolbar = self.GUI_objects[1] # Clarity
        toolset_count = len(Presimation.TOOLS)

        # determine the top_left corner of the tools
        top = (self.toolbar_h / toolset_count 
            - psm_toolbar_btn_large.BUTTON_SIZE) / 2
        left = (self.toolbar_w - psm_toolbar_btn_large.BUTTON_SIZE
            - psm_toolbar_btn_small.BUTTON_SIZE) / 2

        for i in range(toolset_count):
            # top_left corner of the first small button
            small_btn_start_x = left + psm_toolbar_btn_large.BUTTON_SIZE
            small_btn_start_y = top + self.toolbar_h * i / toolset_count
            toolset_name = Presimation.TOOLS[i][0]
            toolset = psm_toolbar_btn_large(
                left,
                small_btn_start_y,
                toolset_name,
                alt_text = toolset_name,
                orientation = "left",
                color = "blue", 
                parent = toolbar)  # Clarity      

            for sub_tool in Presimation.TOOLS[i][1]:
                tool_name = sub_tool[0]
                tool = sub_tool[1]

                tool_btn = psm_toolbar_btn_small(
                    0,
                    0, 
                    tool_name, 
                    color = "red",
                    parent = toolset,
                    alt_text = tool.tool_name, # A little different
                                          # Maybe I should clarify this later...
                    active_fill = "orange",
                    click_func = lambda : self.select_tool(tool_name),
                    double_click_func = double_click_debug)

                small_btn_start_y += psm_toolbar_btn_small.BUTTON_SIZE

            self.GUI_objects[1].add_child(toolset)

    def create_timeline(self):
        # camera button
        self.GUI_objects.append(psm_button(self.toolbar_w + self.wkspace_w,
            self.toolbar_h, self.width, self.height, "blue"))

        # TODO: max limit??
        self.snapshots = []

        snapshot_h = self.tmline_h - self.tmline_margin_h * 2
        snapshot_w = snapshot_h * self.wkspace_w_to_h
        self.snapshot_uncover_w = snapshot_w * self.tmline_uncover_ratio

        # set initial position of the snapshots
        self.start_x = self.toolbar_w + self.tmline_margin_w
        self.end_x = self.toolbar_w + self.wkspace_w\
            - self.tmline_margin_w - snapshot_w
        self.start_y = self.toolbar_h + self.tmline_margin_h

        # TODO: Create another class for this
        # create initial snapshots (5 as an example)
        for i in range(5):
            self.snapshots.append(psm_button(
                self.start_x + i * self.snapshot_uncover_w, self.start_y,
                self.start_x + i * self.snapshot_uncover_w + snapshot_w,
                self.start_y + snapshot_h, offWhite))
        self.update_snapshots()  

    # adjust the positions of the snapshots according to current_slide
    def update_snapshots(self):
        # left stack
        y1 = self.start_y
        for i in range(self.current_slide + 1):
            x1 = self.start_x + self.snapshot_uncover_w * i
            self.snapshots[i].resize(x1, y1)

        # right stack
        x1 = self.end_x
        for i in range(len(self.snapshots)-1, self.current_slide, -1):
            self.snapshots[i].resize(x1, y1)
            x1 = x1 - self.snapshot_uncover_w

    def select_tool(self, tool_name):
        # substitute it with real functions
        print("Click ", tool_name)
        self.current_tool = self.tools[tool_name]

    def mouse_down(self, event):
        for GUI_object in self.GUI_objects:
            GUI_object.on_mouse_down(event.x, event.y)
        if self.mode == "EDIT":
            # Process the mouse down event for user objects
            # for user_object in self.slides[self.current_slide]:
            #     pressed = user_object.mouse_down(event.x, event.y)
            #     if pressed:
            #         # Only one object can be pressed
            #         break
            if self.current_tool != None:
                object_name = self.current_tool.get_object_name()
                object_name = self.slides[
                    self.current_slide
                    ].generate_object_name(object_name)
                self.current_tool.mouse_down(event.x, event.y, object_name)

    def mouse_up(self, event):
        for GUI_object in self.GUI_objects:
            GUI_object.on_mouse_up(event.x, event.y)
        if self.current_tool != None:
            new_object = self.current_tool.mouse_up(event.x, event.y)
            if new_object != None:
                self.slides[self.current_slide].add_object(new_object)

    def keyPressed(self, event): pass
    def keyReleased(self,event): pass

    def mouse_move(self,event):
        if self.current_tool != None:
                self.current_tool.mouse_move(event.x, event.y)

        # check if the mouse hovers on the snapshots
        # left stack
        for i in range(self.current_slide, -1, -1):
            if self.snapshots[i].in_borders(event.x, event.y):
                # Actually you have to click to change slides
                # TODO: Change this
                #self.current_slide = i
                return

        # right stack
        for i in range(len(self.snapshots)-1, self.current_slide, -1):
            if self.snapshots[i].in_borders(event.x, event.y):
                #self.current_slide = i
                return

    def timer_fired(self):
        self.update_snapshots()
        # Update all the buttons
        self.GUI_objects[1].update()

    def redraw_all(self):
        # Draw GUI
        for GUI_object in self.GUI_objects:
            GUI_object.draw(self.canvas)

        # Draw snapshots
        # right stack
        for i in range(self.current_slide+1, len(self.snapshots)):
            self.snapshots[i].draw(self.canvas)

        # left stack
        for i in range(self.current_slide+1):
            self.snapshots[i].draw(self.canvas)

        # Draw workspace
        self.slides[self.current_slide].render(
             self.canvas,
             WORKSPACE_ORIGIN_X,
             WORKSPACE_ORIGIN_Y)
        if self.current_tool != None:
            self.current_tool.draw_object(self.canvas)

psm = Presimation(900, 600)