import math, os, random, sys, time
import pygame, pygame.gfxdraw

try:
    import psyco
    psyco.full()
except:
    pass

SCALE = 4

PIXEL_WIDTH = 1000
PIXEL_HEIGHT = 700

#_size = 4096
#TOTAL_WIDTH = _size
#TOTAL_HEIGHT = _size
#VIRTUAL_WIDTH = _size + PIXEL_WIDTH
#VIRTUAL_HEIGHT = _size + PIXEL_HEIGHT

n = 3
TOTAL_WIDTH = PIXEL_WIDTH * n
TOTAL_HEIGHT = PIXEL_HEIGHT * n
VIRTUAL_WIDTH = PIXEL_WIDTH * (n + 1)
VIRTUAL_HEIGHT = PIXEL_HEIGHT * (n + 1)

WHITE = pygame.Color(255, 255, 255, 255)
BLACK = pygame.Color(0, 0, 0, 255)

GOAL1_X = PIXEL_WIDTH + 234
GOAL1_Y = PIXEL_HEIGHT * 2 + 452

GOAL2A_X = PIXEL_WIDTH * 2 + 400
GOAL2A_Y = 500

GOAL2B_X = PIXEL_WIDTH * 2 + 560
GOAL2B_Y = 660

GOAL2C_X = PIXEL_WIDTH * 2 + 400
GOAL2C_Y = 500

GOAL2D_X = PIXEL_WIDTH * 2 + 560
GOAL2D_Y = 660

# deg:     0->N   90->E    180->S  270->W
# ccw:     0->N  270->E    180->S   90->W
# rot:    90->N    0->E    270->S  180->W
# tra:  pi/2->N    0->E  3pi/2->S   pi->W
PI2 = math.pi * 2
def degrees_to_pi(deg):
    return PI2 * (-deg + 90) / 360.0

def get_dxdy(deg, dist):
    theta = degrees_to_pi(deg)
    return math.cos(theta) * dist, -math.sin(theta) * dist

def scale_load(path):
    s = pygame.image.load(path)
    w = s.get_width() * SCALE
    h = s.get_height() * SCALE
    return pygame.transform.scale(s, (w, h))

class Rock(object):
    @classmethod
    def frompath(self, x, y, path, pts):
        img = scale_load(path)
        return Rock(x, y, img, pts)

    def __init__(self, x, y, img, pts):
        self.img = img
        self.x = x
        self.y = y
        self.w = 32
        self.h = 32
        self.pts = pts
        self.seen = False
        self.panel = False
    def get_img(self):
        return self.img

class Rover(object):
    groups = [['aa', 'bb', 'cc', 'dd'], ['bd', 'ca', 'db', 'ac']]

    def get_frame(self, suffix):
        return scale_load('gfx/rover-%s.png' % suffix)

    def __init__(self):
        self.frames = []
        for group in self.groups:
            imgs = [self.get_frame(zz) for zz in group]
            self.frames.append(imgs)

        self.frames.append(self.frames[0][2:4] + self.frames[0][0:2])
        self.frames.append(self.frames[1][2:4] + self.frames[1][0:2])

        self.i = 0
        self.j = 0

        self.ticks = 0

    def get_img(self, v=0, a=0):
        if v or a:
            if self.ticks == 4:
                self.ticks = 0
                if v > 0:
                    self.j = (self.j + 1) % 4
                elif v < 0:
                    self.j = (self.j - 1) % 4
                elif a  > 0:
                    self.i = (self.i + 1) % 4
                elif a  < 0:
                    self.i = (self.i - 1) % 4
            else:
                self.ticks += 1

        return self.frames[self.i][self.j]

class Map(object):
    darker = pygame.Color(180, 70, 0, 255)
    dark   = pygame.Color(200, 80, 10, 255)
    medium = pygame.Color(220, 90, 30, 255)
    light  = pygame.Color(255, 140, 70, 255)

    #kinds = [darker, dark, medium, light]
    kinds = [darker, dark, dark, medium]
    #kinds = [darker]

    weighted = [light, light, light, light, medium, medium, dark]

    def __init__(self):
        if False and os.path.exists('save/terrain.png'):
            self.img = pygame.image.load('save/terrain.png')
        else:
            self.img = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
            self.img.fill(self.light)
            self.snowscreen()

            pygame.image.save(self.img, 'save/terrain.png')

        panel = scale_load('gfx/panel.png')

        self.panelrect = pygame.Rect(PIXEL_WIDTH + 234, PIXEL_HEIGHT + 452, 32, 32)
        self.img.blit(panel, self.panelrect)

        self.wheelmarks = self.init_wheelmarks()
        self.rotate_wheelmarks(0)

    def snowscreen(self):
        for y in range(0, TOTAL_HEIGHT, 4):
            for x in range(0, TOTAL_WIDTH, 4):
                color = random.choice(self.weighted)
                pygame.gfxdraw.box(self.img, pygame.Rect(x, y, 4, 4), color)
        self.sync_doubled_area()

    def sync_doubled_area(self):
        area = pygame.Rect(0, 0, PIXEL_WIDTH, VIRTUAL_HEIGHT)
        dest = pygame.Rect(TOTAL_WIDTH, 0, PIXEL_WIDTH, VIRTUAL_HEIGHT)
        self.img.blit(self.img, dest, area)

        area = pygame.Rect(0, 0, VIRTUAL_WIDTH, PIXEL_HEIGHT)
        dest = pygame.Rect(0, TOTAL_HEIGHT, VIRTUAL_WIDTH, PIXEL_HEIGHT)
        self.img.blit(self.img, dest, area)

    def rotate_wheelmark(self, wm, angle):
        return pygame.transform.rotate(wm, angle)

    def rotate_wheelmarks(self, angle):
        self.curr_wms = [self.rotate_wheelmark(wm, angle) for wm in self.wheelmarks]

    def init_wheelmarks(self):
        wm = []
        img = scale_load('gfx/rover-wheels.png')
        for i in range(0, 4):
            wm.append(self.create_wheelmark(img))
        return wm

    def create_wheelmark(self, img):
        img2 = img.copy()
        for y in range(0, img.get_height()):
            for x in range(0, img.get_width()):
                if img.get_at((x, y)) != BLACK: continue
                color = random.choice(self.kinds)
                img2.set_at((x, y), color)
        return img2

    def get_wheelmark(self):
        return random.choice(self.curr_wms)

    def track_wheelmarks(self, rect):
        wm = self.get_wheelmark()

        if rect.right > TOTAL_WIDTH:
            dx = -TOTAL_WIDTH
        elif rect.left < PIXEL_WIDTH:
            dx = TOTAL_WIDTH
        else:
            dx = 0

        if rect.bottom > TOTAL_HEIGHT:
            dy = -TOTAL_HEIGHT
        elif rect.top < PIXEL_HEIGHT:
            dy = TOTAL_HEIGHT
        else:
            dy = 0

        self.img.blit(wm, rect)
        self.img.blit(wm, rect.move(dx, dy))
        self.img.blit(wm, rect.move(dx, 0))
        self.img.blit(wm, rect.move(0, dy))

class Game(object):

    def mktext(self, s, color=None):
        if color is None: color = WHITE
        return self.font.render(s, False, color)

    def mkbigtext(self, s, color=None):
        if color is None: color = WHITE
        return self.bigfont.render(s, False, color)

    def init_rocks(self):
        nrocks = 40

        imgs = [scale_load('gfx/rock%d.png' % i) for i in range(1, 7)]
        pts = [10, 10, 10, 10, 25, 25, 25, 50, 50, 100, 200]
        self.rocks = [
            Rock.frompath(PIXEL_WIDTH + 234 + 16, PIXEL_HEIGHT + 452 + 16, 'gfx/cover.png', 1000)
        ]

        for i in range(0, nrocks):
            while True:
                x = random.randint(0, TOTAL_WIDTH)
                y = random.randint(0, TOTAL_HEIGHT)
                rect = pygame.Rect(x - 20, y - 20, 40, 40) 
                other = self.find_rock(rect)
                if other is None:
                    break

            img = random.choice(imgs)
            pt = random.choice(pts)
            self.rocks.append(Rock(x, y, img, pt))

        self.maxscore = min(9999, sum([rock.pts for rock in self.rocks]))

    def __init__(self):
        self.done = False
        self.screen = None
        self.clock = None

        # text stuff
        self.banner = True

        self.font = pygame.font.Font('font/emulator.ttf', 32, bold=True)
        self.bigfont = pygame.font.Font('font/emulator.ttf', 96, bold=True)

        self.score = 0
        self.scoretxt = self.mktext("SCORE %8d" % 0)
        self.clawtxt = self.mktext("CLAW EMPTY")

        self.statustxt = None
        self.statust = pygame.time.get_ticks()

        self.msgtxt = None
        self.msgt = pygame.time.get_ticks()

        self.bannertxt = self.mkbigtext("RED ROVER")
        self.helptxt1 = self.mktext("PRESS ENTER TO PLAY")
        self.helptxt2 = self.mktext("ARROWS TO MOVE")
        self.helptxt3 = self.mktext("SPACE TO USE CLAW")
        self.helptxt4 = self.mktext("CTRL TO CRUSH ROCKS ")

        # map stuff
        self.map = Map()
        self.ox = 0
        self.oy = 0

        # rocks
        self.init_rocks()

        # rover stuff
        self.rover = Rover()
        self.rx = 500
        self.ry = 350
        self.rv = 0
        self.ra = 0
        self.curr_rover_img = pygame.transform.rotate(self.rover.get_img(), -self.ra)
        self.curr_rock = None

        # player stuff
        self.vdelta = 0
        self.adelta = 0

    def addpoints(self, pts):
        self.score = min(9999, self.score + pts)
        self.scoretxt = self.mktext("SCORE %4d" % self.score)

    def start_move(self, delta):
        self.vdelta = delta
    def end_move(self, delta):
        if self.vdelta == delta:
            self.vdelta = 0

    def start_turn(self, delta):
        self.adelta = delta
    def end_turn(self, delta):
        if self.adelta == delta:
            self.adelta = 0

    def shift_map_left(self):
        nx = self.rx - 200
        if nx < 0:
            print 'big shift left (nx=%r ox=%r rx=%r)' % (nx, self.ox, self.rx)
            self.ox = nx + TOTAL_WIDTH
            self.rx += TOTAL_WIDTH
        else:
            #print 'little shift left (ny=%r oy=%r ry=%r)' % (ny, self.oy, self.ry)
            self.ox = nx
        assert self.ox < TOTAL_WIDTH

    def shift_map_right(self):
        nx = self.rx - 800
        if nx > TOTAL_WIDTH:
            print 'big shift right (nx=%r ox=%r rx=%r)' % (nx, self.ox, self.rx)
            self.ox = nx - TOTAL_WIDTH
            self.rx -= TOTAL_WIDTH
        else:
            #print 'little shift right (ny=%r oy=%r ry=%r)' % (ny, self.oy, self.ry)
            self.ox = nx
        assert self.ox >= 0

    def shift_map_up(self):
        ny = self.ry - 200
        if ny < 0:
            print 'big shift up (ny=%r oy=%r ry=%r)' % (ny, self.oy, self.ry)
            self.oy = ny + TOTAL_HEIGHT
            self.ry += TOTAL_HEIGHT
        else:
            #print 'little shift up (ny=%r oy=%r ry=%r)' % (ny, self.oy, self.ry)
            self.oy = ny
        assert self.ry >= self.oy + 200
        assert self.oy < TOTAL_HEIGHT, (self.oy, self.ry, TOTAL_HEIGHT)

    def shift_map_down(self):
        ny = self.ry - 500
        if ny > TOTAL_HEIGHT:
            print 'big shift down (ny=%r oy=%r ry=%r)' % (ny, self.oy, self.ry)
            self.oy = ny - TOTAL_HEIGHT
            self.ry -= TOTAL_HEIGHT
        else:
            #print 'little shift down (ny=%r oy=%r ry=%r)' % (ny, self.oy, self.ry)
            self.oy = ny
        assert self.oy >= 0, (self.oy, 0)

    def handle_rover(self):
        self.rotate_rover()
        self.move_rover()

        img = self.rover.get_img(self.vdelta, self.adelta)
        self.curr_rover_img = pygame.transform.rotate(img, -self.ra)

        if self.adelta:
            self.map.rotate_wheelmarks(-self.ra)

        if self.vdelta or self.adelta:
            self.map.track_wheelmarks(self.get_rover_rect())

        if self.rx < self.ox + 200:
            self.shift_map_left()
        elif self.rx > self.ox + 800:
            self.shift_map_right()
        
        if self.ry < self.oy + 200:
            self.shift_map_up()
        elif self.ry > self.oy + 500:
            self.shift_map_down()

    def move_rover(self):
        if self.vdelta == 0: return
        dx, dy = get_dxdy(self.ra, self.vdelta)
        self.rx += dx
        self.ry += dy

    def rotate_rover(self):
        if self.adelta == 0: return
        self.ra = (self.ra + self.adelta) % 360

    def get_map_rect(self):
        return pygame.Rect(self.ox, self.oy, PIXEL_WIDTH, PIXEL_HEIGHT)

    def get_map_screen_rect(self):
        return pygame.Rect(0, 0, PIXEL_WIDTH, PIXEL_HEIGHT)

    def draw_map(self):
        area = self.get_map_rect()
        dest = self.get_map_screen_rect()
        self.screen.blit(self.map.img, dest, area)
        return area

    def get_rock_rect(self, rock):
        w2, h2 = rock.w / 2, rock.h / 2
        left, top = rock.x, rock.y
        if left < PIXEL_WIDTH and self.ox > PIXEL_WIDTH:
            left += TOTAL_WIDTH
        if top < PIXEL_HEIGHT and self.oy > PIXEL_HEIGHT:
            top += TOTAL_HEIGHT
        rect = pygame.Rect(left - w2, top - h2, rock.w, rock.h)
        return rect

    def get_rock_screen_rect(self, rock):
        return self.get_rock_rect(rock).move(-self.ox, -self.oy)

    def draw_rocks(self, area):
        for rock in self.rocks:
            rect = self.get_rock_rect(rock)
            #print area, dest
            if area.colliderect(rect):
                img = rock.get_img()
                self.screen.blit(img, rect.move(-self.ox, -self.oy))

    def get_rover_screen_rect(self):
        w = self.curr_rover_img.get_width()
        h = self.curr_rover_img.get_height()
        w2, h2 = w / 2, h / 2
        return pygame.Rect(self.rx - self.ox - w2, self.ry - self.oy - h2, w, h)

    def get_rover_rect(self):
        w = self.curr_rover_img.get_width()
        h = self.curr_rover_img.get_height()
        w2, h2 = w / 2, h / 2
        return pygame.Rect(self.rx - w2, self.ry - h2, w, h)

    def draw_rover(self):
        dest = self.get_rover_screen_rect()
        self.screen.blit(self.curr_rover_img, dest)

    def draw_text(self):
        if self.banner:
            self.screen.blit(self.bannertxt, (80, 80))
            self.screen.blit(self.helptxt1, (200, 200))
            self.screen.blit(self.helptxt2, (200, 500))
            self.screen.blit(self.helptxt3, (200, 550))
        else:
            self.screen.blit(self.scoretxt, (0, 0))
            self.screen.blit(self.clawtxt, (620, 0))

            if self.statustxt:
                self.screen.blit(self.statustxt, (0, 44))
                if (pygame.time.get_ticks() - self.statust) > 3000:
                    self.statustxt = None

            if self.msgtxt:
                self.screen.blit(self.msgtxt, (0, 650))
                if (pygame.time.get_ticks() - self.msgt) > 3000:
                    self.msgtxt = None

    def pick_up_rock(self, rock):
        if not rock.seen:
            rock.seen = True
            self.setstatus("ANALYZING ROCK! %+d POINTS!" % rock.pts, pygame.Color(0, 255, 0))
            self.addpoints(rock.pts)

        self.curr_rock = rock
        rect = self.get_rock_rect(rock)
        if self.map.panelrect.colliderect(rect):
            self.setmsg("HOW DID THAT GET HERE?")
        else:
            for y in range(0, rect.height):
                for x in range(0, rect.width):
                    if rock.img.get_at((x, y)).a == 0: continue
                    xy = int(rock.x - rock.w / 2 + x), int(rock.y - rock.h / 2 + y)
                    color = random.choice(self.map.kinds)
                    self.map.img.set_at(xy, color)

        self.map.sync_doubled_area()
        self.rocks.remove(rock)
        self.clawtxt = self.mktext("HOLDING ROCK")

    def drop_rock(self):
        self.clawtxt = self.mktext("CLAW EMPTY")
        self.curr_rock.x = int(self.rx) % TOTAL_WIDTH
        self.curr_rock.y = int(self.ry) % TOTAL_HEIGHT
        self.rocks.append(self.curr_rock)

        rect = self.get_rock_rect(self.curr_rock)
        if not self.curr_rock.panel and self.map.panelrect.colliderect(rect):
            self.setstatus("PUSHED THE BUTTON", pygame.Color(0, 255, 0))
            self.setmsg("WHAT WAS THAT SOUND!?")
        else:
            self.setstatus("DROPPED THE ROCK", pygame.Color(255, 255, 255))

        self.curr_rock = None

    def crush_rock(self):
        self.clawtxt = self.mktext("CLAW EMPTY")
        self.setstatus("CRUSHED THE ROCK", pygame.Color(255, 255, 255))
        self.curr_rock = None

    def get_claw_rect(self):
        return pygame.Rect(self.rx - 32, self.ry - 32, 64, 64)

    def get_drop_rect(self):
        return pygame.Rect(self.rx - 16, self.ry - 16, 32, 32)

    def find_rock(self, rect):
        for rock in self.rocks:
            rect2 = self.get_rock_rect(rock)
            if rect.colliderect(rect2):
                return rock
        return None

    def engage_claw(self):
        if self.curr_rock:
            rect = self.get_drop_rect()
            rock = self.find_rock(rect)
            if rock:
                self.setstatus("ALREADY A ROCK THERE", pygame.Color(255, 255, 0))
            else:
                self.drop_rock()
        else:
            rect = self.get_claw_rect()
            rock = self.find_rock(rect)
            if rock:
                self.pick_up_rock(rock)
            else:
                self.setstatus("I DON'T SEE A ROCK", pygame.Color(255, 255, 0))

    def draw(self):
        area = self.draw_map()
        self.draw_rocks(area)
        self.draw_rover()
        self.draw_text()

    def draw_banner(self):
        self.screen.blit(self.bannertxt, (80, 80))
        self.screen.blit(self.helptxt1, (200, 200))
        self.screen.blit(self.helptxt2, (200, 500))
        self.screen.blit(self.helptxt3, (200, 550))
        self.screen.blit(self.helptxt4, (200, 600))

    def setmsg(self, s):
        self.msgtxt = self.mktext('"' + s + '"', pygame.Color(0, 0, 255))
        self.msgt = pygame.time.get_ticks()

    def setstatus(self, s, color=None):
        if color is None: color = pygame.Color(0, 255, 0)
        self.statustxt = self.mktext(s, color)
        self.statust = pygame.time.get_ticks()

    def run(self):

        pygame.mixer.music.load('snd/redrover.mp3')
        pygame.mixer.music.play(-1) # FIXME

        flags = 0
        self.screen = pygame.display.set_mode((PIXEL_WIDTH, PIXEL_HEIGHT), flags)
        self.clock = pygame.time.Clock()

        self.draw()
        self.draw_banner()
        pygame.display.flip()

        while self.banner:
            self.clock.tick(60)
            for ev in pygame.event.get():
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_RETURN:
                    self.banner = False
                    break

        msgs = [
            (5000, "TIME TO GO TO WORK"),
            (15000, "THIS RESEARCH WON'T DO ITSELF"),
            (35000, "SURE IS LONELY OUT HERE"),
            (50000, "MISSION CONTROL? YOU THERE?"),
            (80000, "I HAVE A STRANGE FEELING"),
        ]

        self.setstatus("DEPLOY CLAW WHEN OVER ROCKS")

        while not self.done:
            self.clock.tick(60)

            if self.msgtxt is None and msgs and msgs[0][0] < pygame.time.get_ticks():
                self.setmsg(msgs[0][1])
                del msgs[0]

            for event in pygame.event.get():
                self.handle(event)
            self.handle_rover()

            self.draw()
            pygame.display.flip()

        pygame.mixer.fadeout(300)

    def handle(self, ev):
        MOVE = 2
        ANGLE = 1

        if ev.type == pygame.QUIT:
            self.done = True

        elif ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                self.done = True
            elif ev.key == pygame.K_UP:
                self.start_move(MOVE * 1.5)
            elif ev.key == pygame.K_DOWN:
                self.start_move(-MOVE)
            elif ev.key == pygame.K_LEFT:
                self.start_turn(-ANGLE)
            elif ev.key == pygame.K_RIGHT:
                self.start_turn(ANGLE)

            elif ev.key == pygame.K_LCTRL:
                if self.curr_rock:
                    self.crush_rock()
                else:
                    self.setstatus("NOT HOLDING A ROCK", pygame.Color(255, 255, 0))

            elif ev.key == pygame.K_SPACE:
                self.engage_claw()

            elif ev.key == pygame.K_MINUS:
                v = pygame.mixer.music.get_volume()
                v = max(0.0, v - 0.1)
                pygame.mixer.music.set_volume(v)
            elif ev.key == pygame.K_EQUALS or ev.key == pygame.K_PLUS:
                v = pygame.mixer.music.get_volume()
                v = max(0.0, v + 0.1)
                pygame.mixer.music.set_volume(v)

        elif ev.type == pygame.KEYUP:
            if ev.key == pygame.K_UP:
                self.end_move(MOVE * 1.5)
            elif ev.key == pygame.K_DOWN:
                self.end_move(-MOVE)
            elif ev.key == pygame.K_LEFT:
                self.end_turn(-ANGLE)
            elif ev.key == pygame.K_RIGHT:
                self.end_turn(ANGLE)


if __name__ == "__main__":
    pygame.init()
    pygame.font.init()
    pygame.mixer.init(frequency=44100)

    g = Game()
    g.run()
