import pygame
import math
import serial
import RPi.GPIO as GPIO
from numpy import matrix, nan_to_num

# Define some colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
SERIAL_MARKER = 128
JOYSTICK_A_IDNT = 0
#LEFT_MOTOR_IDNT = 0
#RIGHT_MOTOR_IDNT = 1
UP_DOWN_MOTOR_IDNT = 2
LIGHT_TOGGLE_IDNT = 5
CLAW_OPEN_CLOSE_IDNT = 4
CLAW_SPIN_IDNT = 3
CLAW_OPEN_CLOSE_GPIO_PIN = 2
TRIPPLE_ROTATE_RIGHT_IDNT = 6
TRIPPLE_ROTATE_LEFT_IDNT = 7
def pmap( value, istart, istop, ostart, ostop):
    return ostart + (ostop - ostart) * ((value - istart) / (istop - istart))
def sendSerial(serialPort , data):
    serialPort.write(data)

#NEW
X_AXIS = 0
Y_AXIS = 1
YAW_AXIS = 3
INVERT_X = False
INVERT_Y = False
INVERT_Yaw = False

#NEW
Y_AXIS_MATRIX = matrix('-1, -1; 1, 1')
X_AXIS_MATRIX = matrix('1, -1; 1, -1')
YAW_MATRIX = matrix('1, -1; -1, 1')

#things needed to send over serial:
#claw spin (A/D) - max 7 bits
#claw open/close (J)
#light on/off (L)
#2 motors forward/back - 8 bits each
#motors up/down - 8 bits
#drill thingy(K)
#10 bits

# This is a simple class that will help us print to the screen
# It has nothing to do with the joysticks, just outputing the
# information.
class TextPrint:
    def __init__(self):
        self.reset()
        self.font = pygame.font.Font(None, 20)

    def printScreen(self, screen, textString):
        textBitmap = self.font.render(textString, True, BLACK)
        screen.blit(textBitmap, [self.x, self.y])
        self.y += self.line_height
    #NEW
    def print2DMatrix(self, screen, matrix):
        array = matrix.getA()
        for row in array:
            self.printScreen(screen, "[{0:07.3f}, {1:07.3f}]".format(row[0].item(), row[1].item()))

    def reset(self):
        self.x = 10
        self.y = 10
        self.line_height = 15

    def indent(self):
        self.x += 10

    def unindent(self):
        self.x -= 10


pygame.init()
#Opens Serial port on Ra    sberry PI3
ser = serial.Serial('/dev/ttyS0', 19200, timeout=5)

#Setup GPIO for claw open/close relay
GPIO.setmode(GPIO.BCM)
GPIO.setup(CLAW_OPEN_CLOSE_GPIO_PIN, GPIO.OUT)
clawClosed = True

clawSpin = 0

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
        if event.tSype == pygame.JOYBUTTONUP:
            print("Joystick button released.")

        if (event.type == pygame.KEYDOWN):
            print ("key pressed " + pygame.key.name(event.key))
            keys = 0
            idnt = 255
            

            if (event.key == pygame.K_c and pygame.key.get_mods() & pygame.KMOD_SHIFT):
                idnt = TRIPPLE_ROTATE_RIGHT_IDNT
                keys = 1
            if (event.key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_SHIFT):
                idnt = TRIPPLE_ROTATE_LEFT_IDNT
                keys = 1

            if (event.key == pygame.K_l):
                idnt = LIGHT_TOGGLE_IDNT
                keys = 1
            if (event.key == pygame.K_j):
                idnt = CLAW_OPEN_CLOSE_IDNT
                keys = 1
                GPIO.output(CLAW_OPEN_CLOSE_GPIO_PIN, GPIO.HIGH if clawClosed else GPIO.LOW)
                clawClosed = not clawClosed
                print("Setting claw: " + ("GPIO.HIGH" if clawClosed else "GPIO.LOW"))

            if (event.key == pygame.K_d):
                clawSpin += 1
            if (event.key == pygame.K_a):
                clawSpin -= 1

            keyBytes = bytes([SERIAL_MARKER, idnt, keys])
            sendSerial(ser, keyBytes)

        if (event.type == pygame.KEYUP):
            if (event.key == pygame.K_d):
                clawSpin -= 1
                print ("key released " + pygame.key.name(event.key))
            if (event.key == pygame.K_a):
                clawSpin += 1
                print ("key released " + pygame.key.name(event.key))

    # DRAWING STEP
    # First, clear the screen to white. Don't put other drawing commands
    # above this, or they will be erased with this command.
    screen.fill(WHITE)
    textPrint.reset()

    #NEW
    try:
        # Get joystick to work with.
        joystick = pygame.joystick.Joystick(0)
    except pygame.error:
        print('Please connect a controller')
        exit(1)
    joystick.init()

    # Print axis values.
    for i in range (joystick.get_numaxes()):
        textPrint.printScreen(screen, "Axis {0} value:    {1:07.3f}".format(i, joystick.get_axis(i)))
    textPrint.printScreen(screen, "")

    # Get axes to work with.
    xAxis = joystick.get_axis(X_AXIS) * (-1 if INVERT_X else 1)
    yAxis = joystick.get_axis(Y_AXIS) * (-1 if INVERT_Y else 1)
    yawAxis = joystick.get_axis(YAW_AXIS) * (-1 if INVERT_Yaw else 1)

    # Construct individual thrust matrices.
    xMatrix = (X_AXIS_MATRIX * xAxis)
    yMatrix = (Y_AXIS_MATRIX * yAxis)
    yawMatrix = (YAW_MATRIX * yawAxis)
    # Combine individual thrust matrices into complete motor thrust matrix.
    motorMatrix = (xMatrix + yMatrix + yawMatrix)

    # Calculate thrust matrix scaling factor.
    maxInputMag = max(abs(xAxis), abs(yAxis), abs(yawAxis))
    maxThrust = max(abs(motorMatrix.min()), motorMatrix.max())
    motorScalar = nan_to_num(maxInputMag / maxThrust)

    # Scale thrust matrix down to within motor thrust range.
    motorMatrix = (motorMatrix * motorScalar) * 128
    # Clip off thrust matrix values less than -127.
    motorMatrix = motorMatrix.clip(min=-127)
    # Cast matrix values to integers.
    motorMatrix = motorMatrix.astype(int)

    #END NEW

    if (clawSpin != 0):
        spinBytes = bytes([SERIAL_MARKER, CLAW_SPIN_IDNT, clawSpin % 256])
        sendSerial(ser, spinBytes)
        ser.read(1)


        for i in range(axes):
            if i == 4 or i == 5:
                continue
            #find number of axes, build tolerance around neutral position, get sign of axis back,
            #map axis between -127 and 127
            axis = joystick.get_axis(i)
            axis = pmap(math.fabs(axis), math.sqrt(2 * math.pow(0.17,2)), 1, 0, 1)
            axis = max(0, axis)
            axis = math.copysign(axis , joystick.get_axis(i))
            axis = pmap(axis, -1, 1, -127, 127)
            axis = int(axis)

            #Since on Linux there are 6 axes, axes 2 and 5 are combined
            #if i== 2 and axes >= 6:
                #get same information about axis 5
               # axis5 = joystick.get_axis(5)
               # axis5 = pmap(math.fabs(axis5), math.sqrt(2 * math.pow(0.17, 2)), 1, 0, 1)
                #axis5 = max(0, axis5)
                #axis5 = math.copysign(axis5, joystick.get_axis(5))
                #axis5 = pmap(axis5, -1, 1, 0, -127)
                #axis5 = int(axis5)


                #map axis 2 from -127 threw 127 to 0 threw 127
                #axis = pmap(axis, -127, 127, 0, 127)
                #axis = int(axis)

                #combine axes 2 and 5
                #axis = (axis + axis5)

            textPrint.print(screen, "Axis {} value: {:>6.3f}".format(i, axis))

            #define the identification number axis-motorcontrol
            idnt = 255
            if i == 1:
                idnt = LEFT_MOTOR_IDNT
            if i == 4:
                idnt = RIGHT_MOTOR_IDNT
            if i == 2:
                idnt = UP_DOWN_MOTOR_IDNT

            #Convert axis information and identification number to byte array, send bytes over serial
            axisBytes = bytes ([SERIAL_MARKER, idnt , axis % 256])
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
GPIO.cleanup()
pygame.quit()


