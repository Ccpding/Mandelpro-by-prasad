import kivy
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics.texture import Texture
from kivy.properties import ObjectProperty, NumericProperty, ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.core.window import Window
import array

# Configuration for the fractal resolution (Performance tradeoff)
TEXTURE_SIZE = 256  # Lower = Faster, Higher = More Detail
MAX_ITER = 30       # Lower = Faster, Higher = More accurate edges

class FractalRenderer(Widget):
    """
    A custom widget that renders the Mandelbrot set onto a GPU Texture.
    """
    
    # Define the region of the complex plane we are viewing
    # Center (x, y) and Zoom level
    center_x_pos = NumericProperty(-0.75)
    center_y_pos = NumericProperty(0.0)
    zoom = NumericProperty(1.0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.texture = None
        # Trigger an update when the widget is fully loaded
        Clock.schedule_once(self.setup_texture, 0)
        self.bind(size=self.update_fractal, pos=self.update_fractal)

    def setup_texture(self, dt):
        """Initialize the GPU texture."""
        self.texture = Texture.create(size=(TEXTURE_SIZE, TEXTURE_SIZE), colorfmt='rgb')
        self.update_fractal()

    def update_fractal(self, *args):
        """
        The core logic: Calculates the Mandelbrot set and updates the texture.
        """
        if not self.texture:
            return

        # 1. Setup the complex plane coordinates
        w, h = TEXTURE_SIZE, TEXTURE_SIZE
        # Scale determines how much of the complex plane fits in the texture
        scale = 1.5 / self.zoom
        
        cx = self.center_x_pos
        cy = self.center_y_pos

        # 2. Create a buffer for RGB data (3 bytes per pixel)
        # We use a flat array for performance
        buf = bytearray(w * h * 3)

        # 3. The Heavy Math Loop (Optimized for Pure Python)
        # Iterating over every pixel
        idx = 0
        for y in range(h):
            # Map pixel y to complex plane imaginary part
            zy_0 = (y - h / 2) * (scale * 2 / h) + cy
            
            for x in range(w):
                # Map pixel x to complex plane real part
                zx_0 = (x - w / 2) * (scale * 2 / w) + cx
                
                # Mandelbrot iteration: z = z^2 + c
                zx, zy = 0.0, 0.0
                iteration = 0
                
                while (zx*zx + zy*zy < 4.0) and (iteration < MAX_ITER):
                    xtemp = zx*zx - zy*zy + zx_0
                    zy = 2*zx*zy + zy_0
                    zx = xtemp
                    iteration += 1

                # 4. Color Mapping (Simple Grayscale/Blue tint)
                if iteration == MAX_ITER:
                    # Inside the set: Black
                    r, g, b = 0, 0, 0
                else:
                    # Outside the set: Gradient based on iteration count
                    col = int((iteration / MAX_ITER) * 255)
                    r, g, b = col, col // 2, 255 - col

                buf[idx] = r
                buf[idx+1] = g
                buf[idx+2] = b
                idx += 3

        # 5. Blit (transfer) the buffer to the GPU texture
        self.texture.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')
        
        # 6. Draw the texture on the Widget's canvas
        self.canvas.clear()
        with self.canvas:
            # We draw a rectangle that fills the widget, mapped to our texture
            from kivy.graphics import Rectangle
            Rectangle(texture=self.texture, pos=self.pos, size=self.size)

    # --- Touch Interaction for Navigation ---
    def on_touch_move(self, touch):
        """Handle dragging to pan the view."""
        if touch.grab_current is self:
            # Calculate movement in complex plane units
            scale = 1.5 / self.zoom
            dx = -touch.dx * (scale * 2 / self.width)
            dy = -touch.dy * (scale * 2 / self.height)
            
            self.center_x_pos += dx
            self.center_y_pos += dy
            
            # Request a redraw
            self.update_fractal()
            return True
        return super().on_touch_move(touch)

    def on_touch_down(self, touch):
        """Handle zooming on tap."""
        if self.collide_point(*touch.pos):
            touch.grab(self)
            # Simple zoom in on tap (in a real app, use pinch gestures)
            if touch.is_double_tap:
                self.zoom *= 1.5
                self.update_fractal()
            return True
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            return True
        return super().on_touch_up(touch)


class MandelbrotApp(App):
    def build(self):
        # Main Layout
        root = BoxLayout(orientation='vertical')
        
        # Info Header
        header = Label(
            text="Mandelbrot Explorer\nDouble-tap to Zoom | Drag to Pan", 
            size_hint=(1, 0.1),
            halign="center"
        )
        
        # The Fractal Widget
        self.fractal = FractalRenderer()
        
        root.add_widget(header)
        root.add_widget(self.fractal)
        return root

if __name__ == '__main__':
    MandelbrotApp().run()
