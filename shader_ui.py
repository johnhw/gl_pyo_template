import imgui

# class for shader variables
# that are set via ui
class ShaderCheckbox:
    def __init__(self, shader, uniform, init_state=False):
        self.state = init_state
        self.shader = shader
        self.uniform = uniform

    def checkbox(self, name):
        _, self.state = imgui.checkbox(name, self.state)
        self.shader[self.uniform] = 1.0 if self.state else 0.0

# Slider directly setting a uniform in a shader
class ShaderSlider:
    def __init__(self, shader, uniform, min=0.0, max=1.0, init=0.5, format="%.2f"):
        self.min = min
        self.max = max
        self.state = init
        self.shader = shader
        self.uniform = uniform
        self.format = format

    def slider(self, name):
        _, self.state = imgui.slider_float(
            name, self.state, self.min, self.max, self.format, 1.0
        )
        self.shader[self.uniform] = self.state

# simple list selector for pyimgui
class ComboList:
    def __init__(self, options, default_option=None):
        # options should be a {name: value} dict
        self.dict = options
        self.options = [(k, v) for k, v in options.items()]
        self.keys = list(options.keys())
        self.default_option = default_option or self.keys[0]
        self.index = self.keys.index(self.default_option)

    def combobox(self, title):
        """Show the combobox with the given title.
        Return None if no change.
        Return the value if one is selected."""
        changed, self.index = imgui.combo(title, self.index, self.keys)
        if changed:
            return self.options[self.index][1]
        else:
            return None

    def option(self):
        return self.options[self.index][1]