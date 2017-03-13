import pygame
import math
import serial
# Define some colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
def pmap( value, istart, istop, ostart, ostop):
    return ostart + (ostop - ostart) * ((value - istart) / (istop - istart))
def sendSerial(serialPort , data):
    serialPort.write(data)

#things needed to send over serial:
#claw spin - max 7 bits
#claw open/close
#light on/off
#2 motors forward/back - 8 bits each
#motors up/down - 8 bits
#drill thingy
#10 bits

# This is a simple class that will help us print to the screen
# It has nothing to do with the joysticks, just outputing the
# information.
class TextPrint:
    def __init__(self):
        self.reset()
        self.font = pygame.font.Font(None, 20)

    def print(self, screen, textString):
        textBitmap = self.font.render(textString, True, BLACK)
        screen.blit(textBitmap, [self.x, self.y])
        self.y += self.line_height

    def reset(self):
        self.x = 10
        self.y = 10
        self.line_height = 15

    def indent(self):
        self.x += 10

    def unindent(self):
        self.x -= 10


pygame.init()
ser = serial.Serial('/dev/ttyS0', 19200)
#ser = serial.Serial('/dev/ttyUSB13', 9600)
sendSerial(ser, bytes([0 ,64]))
# Set the width and height of the screen [width,height]
size = [500, 700]
screen = pygame.display.set_mode(size)

pygame.display.set_caption("My Game")

# Loop until the user clicks the close button.
done = False

# Used to manage how fast the screen updates
clock = pygame.time.Clock()

# Initialize the joysticks
pygame.joystick.init()

# Get ready to print
textPrint = TextPrint()

# -------- Main Program Loop -----------
while done == False:
    # EVENT PROCESSING STEP
    for event in pygame.event.get():  # User did something
        if event.type == pygame.QUIT:  # If user clicked close
            done = True  # Flag that we are done so we exit this loop

        # Possible joystick actions: JOYAXISMOTION JOYBALLMOTION JOYBUTTONDOWN JOYBUTTONUP JOYHATMOTION
        if event.type == pygame.JOYBUTTONDOWN:
            print("Joystick button pressed.")
        if event.type == pygame.JOYBUTTONUP:
            print("Joystick button released.")
        if (event.type == pygame.KEYDOWN):
            print ("key pressed " + pygame.key.name(event.key))
        if (event.type == pygame.KEYUP):
            print ("key released " + pygame.key.name(event.key))
    # DRAWING STEP
    # First, clear the screen to white. Don't put other drawing commands
    # above this, or they will be erased with this command.
    screen.fill(WHITE)
    textPrint.reset()

    # Get count of joysticks
    joystick_count = pygame.joystick.get_count()

    textPrint.print(screen, "Number of joysticks: {}".format(joystick_count))
    textPrint.indent()

    # For each joystick:
    for i in range(joystick_count):
        joystick = pygame.joystick.Joystick(i)
        joystick.init()

        textPrint.print(screen, "Joystick {}".format(i))
        textPrint.indent()

        # Get the name from the OS for the controller/joystick
        name = joystick.get_name()
        textPrint.print(screen, "Joystick name: {}".format(name))

        # Usually axis run in pairs, up/down for one, and left/right for
        # the other.
        axes = joystick.get_numaxes()
        textPrint.print(screen, "Number of axes: {}".format(axes))
        textPrint.indent()

        for i in range(axes):
            if i == 0 or i == 3 or i == 5:
                continue
            axis = joystick.get_axis(i)

            axis = pmap(math.fabs(axis), math.sqrt(2 * math.pow(0.17,2)), 1, 0, 1)
            axis = max(0, axis)
            axis = math.copysign(axis , joystick.get_axis(i))
            axis = pmap(axis, -1, 1, -127, 127)
            #axis = min(127, axis)
            axis = int(axis)
            if i== 2 and axes >= 6:
                axis5 = joystick.get_axis(5)
                axis5 = pmap(math.fabs(axis5), math.sqrt(2 * math.pow(0.17, 2)), 1, 0, 1)
                axis5 = max(0, axis5)
                axis5 = math.copysign(axis5, joystick.get_axis(5))
                axis5 = pmap(axis5, -1, 1, 0, -127)
                axis5 = int(axis5)

                axis = pmap(axis, -127, 127, 0, 127)
                axis = int(axis)

                axis = (axis + axis5)
                #sign = math.copysign(1 , axis)
                #axis = ((math.fabs(axis)) % 128) * sign
                #axis = (axis -axis5) % 128
            textPrint.print(screen, "Axis {} value: {:>6.3f}".format(i, axis))
            idnt = 255
            if i == 1:
                idnt = 0
            if i == 4:
                idnt = 1
            if i == 2:
                idnt = 2
            axisBytes = bytes ([128, idnt , axis % 256])
            sendSerial(ser , axisBytes)
        textPrint.unindent()

        buttons = joystick.get_numbuttons()
        textPrint.print(screen, "Number of buttons: {}".format(buttons))
        textPrint.indent()

        for i in range(buttons):
            button = joystick.get_button(i)
            textPrint.print(screen, "Button {:>2} value: {}".format(i, button))
        textPrint.unindent()

        # Hat switch. All or nothing for direction, not like joysticks.
        # Value comes back in an array.
        hats = joystick.get_numhats()
        textPrint.print(screen, "Number of hats: {}".format(hats))
        textPrint.indent()

        for i in range(hats):
            hat = joystick.get_hat(i)
            textPrint.print(screen, "Hat {} value: {}".format(i, str(hat)))
        textPrint.unindent()

        textPrint.unindent()

    # ALL CODE TO DRAW SHOULD GO ABOVE THIS COMMENT

    # Go ahead and update the screen with what we've drawn.
    pygame.display.flip()

    # Limit to 20 frames per second
    clock.tick(20)

# Close the window and quit.
# If you forget this line, the program will 'hang'
# on exit if running from IDLE.
pygame.quit()


