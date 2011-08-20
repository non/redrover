import math, os, random, sys
import pygame, pygame.gfxdraw

SCALE = 4

NUM_SCREENS_WIDE = 5
NUM_SCREENS_TALL = 5

PIXEL_WIDTH = 1000
PIXEL_HEIGHT = 700

TOTAL_WIDTH = PIXEL_WIDTH * (NUM_SCREENS_WIDE - 1)
TOTAL_HEIGHT = PIXEL_HEIGHT * (NUM_SCREENS_TALL - 1)

VIRTUAL_WIDTH = PIXEL_WIDTH * NUM_SCREENS_WIDE
VIRTUAL_HEIGHT = PIXEL_HEIGHT * NUM_SCREENS_TALL

BLACK = pygame.Color(0, 0, 0, 255)

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
        self.img = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))

        self.img.fill(self.light)
        for h in range(0, NUM_SCREENS_TALL):
            for w in range(0, NUM_SCREENS_WIDE):
                ## debugging colors
                #r = (h + 1) * 51
                #g = (w + 1) * 51
                #b = ((h + w) % 2) * 100
                #color = pygame.Color(r, g, b, 255)
                color = self.light

                rect = pygame.Rect(w * PIXEL_WIDTH, h * PIXEL_HEIGHT, PIXEL_WIDTH, PIXEL_HEIGHT)

                self.img.fill(color, rect)
                #self.snowscreen(rect)

        self.wheelmarks = self.init_wheelmarks()
        self.rotate_wheelmarks(0)

    def snowscreen(self, rect):
        print 'snow', rect
        for y in range(rect.top, rect.top + rect.h, 4):
            for x in range(rect.left, rect.left + rect.w, 4):
                color = random.choice(self.weighted)
                pygame.gfxdraw.box(self.img, pygame.Rect(x, y, 4, 4), color)

    def generate_altitude(self):
        pass

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
    def __init__(self):
        self.done = False
        self.screen = None
        self.clock = None

        # map stuff
        self.map = Map()
        self.ox = 0
        self.oy = 0

        # rover stuff
        self.rover = Rover()
        self.rx = 500
        self.ry = 350
        self.rv = 0
        self.ra = 0
        self.curr_rover_img = pygame.transform.rotate(self.rover.get_img(), -self.ra)

        # player stuff
        self.vdelta = 0
        self.adelta = 0

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
            #print 'big shift left (ny=%r oy=%r ry=%r)' % (ny, self.oy, self.ry)
            self.ox = nx + TOTAL_WIDTH
            self.rx += TOTAL_WIDTH
        else:
            #print 'little shift left (ny=%r oy=%r ry=%r)' % (ny, self.oy, self.ry)
            self.ox = nx
        assert self.ox < TOTAL_WIDTH

    def shift_map_right(self):
        nx = self.rx - 800
        if nx > TOTAL_WIDTH:
            #print 'big shift right (ny=%r oy=%r ry=%r)' % (ny, self.oy, self.ry)
            self.ox = nx - TOTAL_WIDTH
            self.rx -= TOTAL_WIDTH
        else:
            #print 'little shift right (ny=%r oy=%r ry=%r)' % (ny, self.oy, self.ry)
            self.ox = nx
        assert self.ox >= 0

    def shift_map_up(self):
        ny = self.ry - 200
        if ny < 0:
            #print 'big shift up (ny=%r oy=%r ry=%r)' % (ny, self.oy, self.ry)
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
            #print 'big shift down (ny=%r oy=%r ry=%r)' % (ny, self.oy, self.ry)
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

    def draw(self):
        self.draw_map()
        self.draw_rover()

    def run(self):
        pygame.init()
        flags = 0
        self.screen = pygame.display.set_mode((PIXEL_WIDTH, PIXEL_HEIGHT), flags)
        self.clock = pygame.time.Clock()

        self.draw()
        while not self.done:
            self.clock.tick(60)

            for event in pygame.event.get():
                self.handle(event)
            self.handle_rover()

            self.draw()
            pygame.display.flip()

    def handle(self, ev):
        MOVE = 2
        ANGLE = 1

        if ev.type == pygame.QUIT:
            self.done = True

        elif ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                #print 'quitting now...'
                self.done = True
            elif ev.key == pygame.K_UP:
                self.start_move(MOVE)
            elif ev.key == pygame.K_DOWN:
                self.start_move(-MOVE)
            elif ev.key == pygame.K_LEFT:
                self.start_turn(-ANGLE)
            elif ev.key == pygame.K_RIGHT:
                self.start_turn(ANGLE)

        elif ev.type == pygame.KEYUP:
            if ev.key == pygame.K_UP:
                self.end_move(MOVE)
            elif ev.key == pygame.K_DOWN:
                self.end_move(-MOVE)
            elif ev.key == pygame.K_LEFT:
                self.end_turn(-ANGLE)
            elif ev.key == pygame.K_RIGHT:
                self.end_turn(ANGLE)


if __name__ == "__main__":
    g = Game()
    g.run()
