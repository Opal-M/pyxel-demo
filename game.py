import pyxel

SPEED = 0.4
BLOCK = 8
LENGTH = 16
#block to make things more detailed later
#length to make frame bigger later

def lerp(a, b, t):
    """lerp = linear interpolation.
    Returns a value between a and b, based on the value of t
    When t=0, a is returned. When t=1, b is returned.
    When t is between 0 and 1, a value mixed between a and b is returned.
    For example, lerp(10,20,0.5) will return 15.
    Note the result is not clamped, so if t is less than 0 or greater than 1
    then the value is extrapolated beyond a or b.
    """
    return a + (b - a) * t

def walkable(x, y):
    """Is the map tile at x,y walkable?"""
    t = pyxel.tilemap(0).get(x,y)
    return t == 0

class Thing:
    def __init__(self, name, x, y):
        self.name = name
        # grid coordinates
        self.x = x
        self.y = y
        # pixel coordinates
        self.px = x*8
        self.py = y*8

    def update(self, speed=SPEED):
        # smoothly step pixel coordinates px,py towards grid x,y
        # by default use SPEED, but you can override that to go
        # quicker or slower.
        self.px = lerp(self.px, self.x*8, speed)
        self.py = lerp(self.py, self.y*8, speed)

class Sprite(Thing):
    def __init__(self, name, x, y, tile):
        super().__init__(name, x, y)
        #^ what's this?
        self.tile = tile
        self.xflip = 1
        self.yflip = 1

    def draw(self, camera):
        # pyxel.rect(self.px - camera.px, self.py - camera.py, 8, 8, 9)
        pyxel.blt(
            # pixel coords to draw
            self.px - camera.px,
            self.py - camera.py,
            # read from image bank 0, where the sprites are
            0,
            # read from the right spot based on the tile number
            (self.tile % 32) * 8,
            (self.tile // 32) * 8,
            # width and height
            8 * self.xflip,
            8 * self.yflip,
            # which color is transparent?
            #better question is which is black like the bg
            0
        )

class Pot(Sprite):
    def smash(self):
        self.tile += 1
        #i take it this just animates it one frame over?
        #you can make a gem inside a pot here by putting a three frame an

class Player(Sprite):
    def __init__(self, name, x, y, t):
        super().__init__(name, x, y, t)
        self.gems = 0

    def keys_pressed(self, *keys):
        for k in keys:
            if pyxel.btnp(k, 8, 8):
                return True
    #& move this somewhere where everyone can access it

    def update(self):
        # which way is the controller pressed?
        # arrow keys, WASD, etc.
        cx = 0
        cy = 0
        if self.keys_pressed(pyxel.KEY_UP, pyxel.KEY_W):
            cy -= 1
        if self.keys_pressed(pyxel.KEY_DOWN, pyxel.KEY_S):
            cy += 1
        if self.keys_pressed(pyxel.KEY_LEFT, pyxel.KEY_A):
            cx -= 1
            self.xflip = -1
        if self.keys_pressed(pyxel.KEY_RIGHT, pyxel.KEY_D):
            cx += 1
            self.xflip = 1

        if walkable(self.x + cx, self.y + cy):
            self.x += cx
            self.y += cy

        super().update()
        #figure out who listens to cx and cy so i can see if/how multiplayer might work
        #& right before/after cy and cx change note which way player is facing and cardinally going for other stuff to ref 

class App:
    def __init__(self):
        pyxel.init(BLOCK*LENGTH, BLOCK*LENGTH)
        pyxel.load("assets/my_resource.pyxres")
        self.camera = Thing("camera", 0, 0)
        self.sprites = []
        self.colliders = []
        self.tilemap = pyxel.tilemap(0)
        self.scan_map()
        self.camera.x = self.player.x - 8
        self.camera.y = self.player.y - 8
        self.camera.update(1)
        pyxel.run(self.update, self.draw)

    def colliders_at(self, x, y):
        # result = []
        # for sprite in self.colliders:
        #     if sprite.x == x and sprite.y == y:
        #         result.append(sprite)
        # return result

        return [s for s in self.colliders if s.x==x and s.y==y]
        #oh very fancy and weird... showoff

    def scan_map(self):
        """Scan the map for special tiles, spawning sprites, etc."""
        for y in range(self.tilemap.height):
            for x in range(self.tilemap.width):
                t = self.tilemap.get(x,y)
                if t == 0:
                    # empty
                    pass
                elif t == 1:
                    # solid
                    pass
                elif t == 2:
                    # pot
                    sprite = Pot("pot", x, y, t)
                    self.sprites.append(sprite)
                    self.colliders.append(sprite)
                    self.tilemap.set(x,y,0)
                elif t == 32:
                    # player
                    self.player = Player("player", x, y, t)
                    self.tilemap.set(x,y,0)
                elif t == 33:
                    # gem
                    sprite = Sprite("gem", x, y, t)
                    self.sprites.append(sprite)
                    self.colliders.append(sprite)
                    self.tilemap.set(x,y,0)
                else:
                    raise Exception("unexpected map tile? "+str(t))
                #makes sense, show me what this looks like in the resource editor

    def smash_pot(self, pot):
        pot.smash()
        # leave it in sprites, but remove it from colliders
        self.colliders.remove(pot)
        #i feel like it would be more clear to have a general disappear function
        #and a separate function for animating that didn't say smash in it
        #and then the gem would just add a point

    def pickup_gem(self, gem):
        self.player.gems += 1
        # remove it from both sprites, and colliders
        self.sprites.remove(gem)
        self.colliders.remove(gem)
        #wait why do gems get deleted from both?

    def update(self):
        self.player.update()

        for sprite in self.sprites:
            sprite.update()

        for thing in self.colliders_at(self.player.x, self.player.y):
            if thing.name == "pot":
                self.smash_pot(thing)
            if thing.name == "gem":
                self.pickup_gem(thing)

        # camera follows the player
        
        #camera.update(1) snaps the camera to the new place
        #any lower number (1<x<0) will be jittery and slow moving
        global TOP
        TOP = self.camera.y
        global BOTTOM
        BOTTOM = self.camera.y + 15
        global LEFT
        LEFT = self.camera.x - 1
        global RIGHT
        RIGHT = self.camera.x + 16

        if self.player.y < TOP:
            #too high, shift down
            self.camera.y = self.player.y - 15
        elif self.player.y > BOTTOM:
            #too low, shift up
            self.camera.y = self.player.y - 1
        elif self.player.x < LEFT:
            #too right, shift left
            self.camera.x = self.player.x - 15
        elif self.player.x > RIGHT:
            #too left, shift right
            self.camera.x = self.player.x - 1
        self.camera.update(1)

    def draw(self):
        pyxel.cls(0)
        #^ what's this
        pyxel.bltm(-self.camera.px, -self.camera.py, 0, 0, 0, self.tilemap.width, self.tilemap.height)

        for sprite in self.sprites:
            sprite.draw(self.camera)

        self.player.draw(self.camera)

        #pyxel.text(1, 1, "GEMS: {}".format(self.player.gems), 7)
        pyxel.text(1, 8, "PLAYER COORDS: {},{}".format(self.player.x,self.player.y), 7)
        pyxel.text(1, 15, "CAM COORDS: {},{}".format(self.camera.x,self.camera.y), 7)
        pyxel.text(1, 1, "LEFT: {}".format(LEFT), 7)
        pyxel.text(1, 23, "RIGHT: {}".format(RIGHT), 7)

App()
