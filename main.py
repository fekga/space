from pyglet.gl import *
from pyglet.window import *
pyglet.options['audio'] = ('openal', 'directsound', 'pulse', 'silent')
from pyglet.media import *
from pyglet.app import EventLoop
from ctypes import *

#from shader import Shader
from OpenGL.GL.shaders import *

vec2 = GLfloat * 2
vec3 = GLfloat * 3
vec4 = GLfloat * 4
mat3 = GLfloat * 9
mat4 = GLfloat * 16

class Label(pyglet.text.Label):
    def __init__(self, window,**kwargs):
        self.window = window
        self.window.push_handlers(self)
        self.init_settings = dict()
        for k,v in kwargs.items():
            if callable(v):
                kwargs[k] = v(self.window)
                self.init_settings[k] = v
        super().__init__(**kwargs)
        
    def on_resize(self, width, height):
        for k,v in self.init_settings.items():
            setattr(self,k,v(self.window))

class EventLoop(pyglet.app.EventLoop):
    def idle(self):
        pyglet.clock.tick(poll=True)
        return pyglet.clock.get_sleep_time(sleep_idle=True)

    def run(self):
        super(EventLoop, self).run()

class Camera(object):
    
    def __init__(self, window=None):
        self.window = window
        self.type = None
    
    def perspective(self, eye=(0, 0, 1), target=(0, 0, -1), up=(0, 1, 0), fov = 45.0, near=0.1, far=100.0):
        self.fov = fov
        self.near = near
        self.far = far
        self.eye = eye
        self.target = target
        self.up = up
        self.type = 'perspective'
        self.setup()
        
    def orthographic(self, left=-1, right=1, bottom=-1, top=1, near=-1, far=1):
        self.left=left
        self.right=right
        self.top=top
        self.bottom=bottom
        self.near = near
        self.far = far
        self.type = 'orthographic'
        self.setup()

    def _update_mvp(self):
        pass

    def setup(self):
        if self.type == None:
            return
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        if self.type == 'orthographic':
            glOrtho(self.left,self.right,self.bottom,self.top,self.near,self.far)
        if self.type == 'perspective':
            w,h = self.window.width,self.window.height
            gluPerspective(self.fov,w/h,self.near,self.far)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        if self.type == 'perspective':
            ex,ey,ez = self.eye
            tx,ty,tz = self.target
            ux,uy,uz = self.up
            gluLookAt(ex,ey,ez,tx,ty,tz,ux,uy,uz)

    def mvp(self):
        self._update_mvp()
        return self.mvp

class Scene(object):
    def __init__(self, window):
        self.window = window
        self.camera = Camera(window)

    def update(self, dt=0.0):
        pass
    def render(self):
        pass

class PauseScene(Scene):
    def __init__(self, window, prev):
        super().__init__(window)
        self.prev = prev
        w,h = self.window.width,self.window.height

        self.label = Label(window=self.window,
                        text='PAUSED',
                        multiline=False,
                        font_name='Times New Roman',
                        bold=True,
                        font_size=lambda win:24*win.height/win.initial_height,
                        width=lambda win:win.width/4,
                        x=lambda win:win.width/2,
                        y=lambda win:win.height/2,
                        color=(255, 255, 255, 255),
                        anchor_x='center', anchor_y='center')
        self.batch = pyglet.graphics.Batch()
        self.batch.add(4,GL_QUADS,None,
                       ('v2f',(0,0, 1,0, 1,1, 0,1)),
                       ('c4B',(0,0,0,196,0,0,0,196,0,0,0,196,0,0,0,196)))

    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.ESCAPE:
            self.window.exit()
        if symbol == pyglet.window.key.SPACE:
            self.window.toggle_pause()
            self.window.pop_scene()
        return True

    def render(self):
        self.prev.render()
        w,h =self.window.size
        self.camera.orthographic(0,w,0,h,-1,1)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glPushMatrix()
        glScalef(w,h,1)
        self.batch.draw()
        glPopMatrix()
        self.label.draw()
        
def resize_label(obj):
    if hasattr(obj,'init_settings'):
        settings = obj.init_settings
        window = settings['window']
        iw,ih=window.initial_size
        w,h=window.size
        ratio = ih/h
        for k,v in settings.items():
            if k is 'window':
                continue
            if callable(v):
                v=v(settings)
            setattr(obj,k,v*ratio)
            print(k,v,v*ratio)
        
class MainScene(Scene):
    def __init__(self, window):
        super().__init__(window)
        
        self.pause_scene = PauseScene(window,self)
        self.label = Label(window=self.window,
                           text='',
                           multiline=True,
                           font_name='Times New Roman',
                           bold=True,
                           font_size=lambda win:12*win.height/win.initial_height,
                           width=lambda win:200*win.height/win.initial_height,
                           x=0,
                           y=lambda win:win.height,
                           color=(255, 255, 255, 255),
                           anchor_x='left', anchor_y='top')
        
        with open('res/default.vert','r') as f:
            self.vert = f.read()
        with open('res/default.geom','r') as f:
            self.geom = f.read()
        with open('res/default.frag','r') as f:
            self.frag = f.read()
        self.shader = compileProgram(
                    compileShader(self.vert,GL_VERTEX_SHADER),
                    compileShader(self.geom,GL_GEOMETRY_SHADER),
                    compileShader(self.frag,GL_FRAGMENT_SHADER)
        )
        self.uniform_locations = {
            'time': glGetUniformLocation(self.shader,'time')
        }

    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.ESCAPE:
            self.window.exit()
        if symbol == pyglet.window.key.SPACE:
            self.window.toggle_pause()
            self.window.push_scene(self.pause_scene)
        return True

    def update(self, dt):
        self.label.text = 'Time: {:.3f}'.format(self.window.elapsed_time)

    def render(self):
        w,h=self.window.size
        self.camera.orthographic(0,w,0,h,-1,1)
        self.label.draw()
        
        self.camera.perspective()
        glColor3f(1,1,1)
        with self.shader:
            # glUniform1f(self.uniform_locations['time'],self.window.elapsed_time)
            glBegin(GL_TRIANGLES)
            glVertex3f(0,0,0)
            glVertex3f(1,0,0)
            glVertex3f(1,1,0)
            # glVertex3f(1,1,0)
            # glVertex3f(0,1,0)
            # glVertex3f(0,0,0)
            glEnd()

class GameWindow(pyglet.window.Window):
    
    @property
    def size(self):
        return self.width, self.height

    def __init__(self, fps=60,*args, **kwargs):
        platform = pyglet.window.get_platform()
        display = platform.get_default_display()
        screen = display.get_default_screen()

        template = pyglet.gl.Config(alpha_size=8, sample_buffers=1, samples=8)
        config = screen.get_best_config(template)
        context = config.create_context(None)
        kwargs['context'] = context
        super(GameWindow,self).__init__(*args,**kwargs)
        
        self.initial_height,self.initial_width = self.initial_size = self.size

        self.fps = fps
        self.elapsed_time = 0.0
        self.camera = Camera()
        self.scenes = list()
        self.push_scene(MainScene(window=self))

        pyglet.app.event_loop = EventLoop()
        pyglet.clock.schedule_interval(self.update, 1.0 / float(self.fps))
        pyglet.clock.schedule_interval(self.update_physics, 1.0 / 60.0)

        #self.set_location( (screen.width-self.width)//2, (screen.height-self.height)//2)

        self.paused = False

    def push_scene(self, scene):
        self.scenes.append(scene)
        self.push_handlers(scene)
        self.set_caption(str(scene.__class__))

    def pop_scene(self):
        self.scenes.pop()
        self.pop_handlers()
        self.set_caption(str(self.scenes[-1].__class__))

    def on_close(self):
        self.exit()

    def exit(self):
        self.has_exit = True

    def toggle_pause(self):
        self.paused = not self.paused
        
    def on_resize(self, width, height):
        glViewport(0,0,width,height)

    def on_draw(self):
        self.clear()
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glClearColor(0,0,0, 1)
        self.scenes[-1].render()

    def update(self, dt=0.0):
        if not self.has_exit:
            self.scenes[-1].update(dt)
            self.dispatch_event('on_draw')
            self.flip()
        else:
            pyglet.app.exit()

    def update_physics(self, dt):
        if not self.has_exit:
            if not self.paused:
                if dt > 0.0:
                    self.elapsed_time += dt

if __name__ == '__main__':
    window = GameWindow(width=640,
                        height=480,
                        resizable=True,
                        caption='game',
                        vsync=False,
                        fps=240)
    pyglet.app.run()
