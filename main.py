import sys
import pyMeow as pm
import math


try:
    proc = pm.open_process("quake2.exe")
except Exception as e:
    sys.exit(e)

class Colors:
    cyan = pm.get_color("cyan")

class Modules:
    base = pm.get_module(proc, "quake2.exe")["base"]
    gamex86 = pm.get_module(proc,"gamex86.dll")["base"]
    gameoverlay = pm.get_module(proc,"gameoverlayrenderer.dll")["base"]
    ref_gl = pm.get_module(proc,"ref_gl.dll")["base"]

class Addresses:
    entity_list = pm.r_int(proc,Modules.base + 0x7D2FC)
    enemies_killed = Modules.gamex86 + 0x67120
    total_enemies = Modules.gamex86+0x6711C
    player_direction = Modules.base+0xC9290
    screen_resolution = Modules.gameoverlay+0x10F7A8
    x_fov = Modules.base+0x6F05D8
    view_matrix = Modules.ref_gl+0x567F0
    camera_pos = Modules.base+0x6F1558



class Offsets:
    ent = 0x37C
    health = 0x1E0
    position = 0x4
    is_valid = 0x44

class Entity:
    def __init__(self,base):
        self.base = base
        self.h = self.base+Offsets.health
        self.pos = self.base+Offsets.position
    def position(self):
        return pm.r_floats(proc,self.pos,3) 
    def health(self):
        return pm.r_int(proc,self.h)  
    def teleport(self,vec):
        pm.w_floats(proc,self.pos,vec)
    
def total_enemies():
    return pm.r_int(proc,Addresses.total_enemies)

def player_direction():
    return pm.r_floats(proc,Addresses.player_direction,3)

def camera_pos():
    return pm.r_floats(proc,Addresses.camera_pos,3)

def entities():
    ents = []
    n_tofind = total_enemies()
    ent_index = 1
    while len(ents) != n_tofind:
        base = Addresses.entity_list + Offsets.ent * ent_index
        if pm.r_int(proc,base+Offsets.is_valid)==64:
            ents.append(Entity(base))
        ent_index+=1
    return Entity(Addresses.entity_list),ents

def screen_resolution():
    return pm.r_ints(proc,Addresses.screen_resolution,2)

def fovs():
    width,height = screen_resolution()
    x_fov = math.radians(pm.r_float(proc,Addresses.x_fov)) 
    y_fov = x_fov/width * height
    return [x_fov,y_fov]


def viewmatrix():
    return pm.r_floats(proc,Addresses.view_matrix,16)

def print_matrix(matrix):
    for i in range(0, 16, 4):
        print("{:8.3f} {:8.3f} {:8.3f} {:8.3f}".format(*matrix[i:i+4]))

def norm(vec):
    m = math.sqrt(sum([vec[i]**2 for i in range(3)]))
    return [i/m for i in vec]

def wts(ply,worldpos):
    width,height = screen_resolution()
    x_fov = math.radians(pm.r_float(proc,Addresses.x_fov)) 
    y_fov = x_fov/width * height
    cam_pos = ply.position()
    cam_look = player_direction()
    camToObj = [worldpos[i]-cam_pos[i] for i in range(3)]
    camToObj = norm(camToObj)
    camYaw = math.atan2(cam_look[1],cam_look[0])
    objYaw = math.atan2(camToObj[1],camToObj[0])
    relYaw = camYaw-objYaw
    objPitch = math.asin(camToObj[2])
    camPitch = math.asin(cam_look[2])
    relPitch = camPitch-objPitch
    x = relYaw/(0.5*x_fov)
    y = relPitch/(0.5*y_fov)
    x = (x+1)/2
    y = (y+1)/2
    return [x*width,y*height]

def draw_pos(ply,pos):
    try:
        xcor,ycor = wts(ply,pos)
        pm.draw_line(0,0,xcor,ycor,Colors.cyan)
    except:
        pass


def main():
    pm.overlay_init(target="Quake 2", fps=144, trackTarget=True)
    ply,ents = entities()
    while pm.overlay_loop():
        alive_enemies = [i for i in ents if i.health()>0]       
        vm = viewmatrix()
        pm.begin_drawing()
        for i in alive_enemies:
            pos = i.position()
            draw_pos(ply,pos)
        pm.end_drawing()
    
if __name__ == "__main__":
    main()