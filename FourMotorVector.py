import pygame
import math
import serial
import RPi.GPIO as GPIO
from numpy import matrix, nan_to_num

# Define some colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

SERIAL_MARKER = 128
VECTOR_MOTORS_IDNT = 0
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

##### CONFIGURE T   HESE AXES #####
X_AXIS = 0
Y_AXIS = 1
YAW_AXIS = 4
INVERT_X = False
INVERT_Y = False
INVERT_Yaw = False
################################

# Define some motor control matrices
Y_AXIS_MATRIX = matrix('-1, -1; 1, 1')
X_AXIS_MATRIX = matrix('1, -1; 1, -1')
YAW_MATRIX = matrix('1, -1; -1, 1')

# This is a simple class that will help us print to the screen
# It has nothing to do with the joysticks, just outputting the
# information.
class TextPrint:
    def __init__(self):
        self.reset()
        self.font = pygame.font.Font(None, 20)

    def printScreen(self, screen, textString):
        textBitmap = self.font.render(textString, True, BLACK)
        screen.blit(textBitmap, [self.x, self.y])
        self.y += self.line_height

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

#Opens Serial port on Rasberry PI3
ser = serial.Serial('/dev/ttyS0', 19200, timeout=5)

# Set the width and height of the screen [width,height]
size = [200, 420]
screen = pygame.display.set_mode(size)

pygame.display.set_caption("Four Motor Demo")

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

    # DRAWING STEP
    # First, clear the screen to white. Don't put other drawing commands
    # above this, or they will be erased with this command.
    screen.fill(WHITE)
    textPrint.reset()

    try:
        # Get joystick to work with.
        joystick = pygame.joystick.Joystick(0)
    except pygame.error:
        print('Please connect a controller')
        exit(1)
    joystick.init()

    # Print axis values.
    for i in range (joystick.get_numaxes()):
        axis = joystick.get_axis(i)
        axis = pmap(math.fabs(axis), math.sqrt(2 * math.pow(0.17, 2)), 1, 0, 1)
        axis = max(0, axis)
        axis = math.copysign(axis, joystick.get_axis(i))
        textPrint.printScreen(screen, "Axis {0} value:    {1:07.3f}".format(i, axis))
    textPrint.printScreen(screen, "")

    # Get axes to work with.
    # Set tolerance
    axisX = joystick.get_axis(X_AXIS)
    axisX = pmap(math.fabs(axisX), math.sqrt(2 * math.pow(0.17, 2)), 1, 0, 1)
    axisX = max(0, axisX)
    axisX = math.copysign(axisX, joystick.get_axis(X_AXIS))

    axisY = joystick.get_axis(Y_AXIS)
    axisY = pmap(math.fabs(axisY), math.sqrt(2 * math.pow(0.17, 2)), 1, 0, 1)
    axisY = max(0, axisY)
    axisY = math.copysign(axisY, joystick.get_axis(Y_AXIS))

    axisYaw = joystick.get_axis(YAW_AXIS)
    axisYaw = pmap(math.fabs(axisYaw), math.sqrt(2 * math.pow(0.17, 2)), 1, 0, 1)
    axisYaw = max(0, axisYaw)
    axisYaw = math.copysign(axisYaw, joystick.get_axis(YAW_AXIS))

    xAxis = axisX * (-1 if INVERT_X else 1)
    yAxis = axisY * (-1 if INVERT_Y else 1)
    yawAxis = axisYaw * (-1 if INVERT_Yaw else 1)

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

    # Print matrices to screen.
    textPrint.printScreen(screen, "xMatrix: ")
    textPrint.print2DMatrix(screen, xMatrix)
    textPrint.printScreen(screen, "")
    textPrint.printScreen(screen, "yMatrix: ")
    textPrint.print2DMatrix(screen, yMatrix)
    textPrint.printScreen(screen, "")
    textPrint.printScreen(screen, "yawMatrix: ")
    textPrint.print2DMatrix(screen, yawMatrix)
    textPrint.printScreen(screen, "")
    textPrint.printScreen(screen, "motorMatrix: ")
    textPrint.print2DMatrix(screen, motorMatrix)
    textPrint.printScreen(screen, "")

    # Print motor values.
    textPrint.printScreen(screen, "Fore-Port Motor:           {:03d}".format(motorMatrix.item(0)))
    textPrint.printScreen(screen, "Fore-Starboard Motor:  {:03d}".format(motorMatrix.item(1)))
    textPrint.printScreen(screen, "Aft-Port Motor:              {:03d}".format(motorMatrix.item(2)))
    textPrint.printScreen(screen, "Aft-Starboard Motor:     {:03d}".format(motorMatrix.item(3)))
    textPrint.printScreen(screen, "")


    FPM = motorMatrix.item(0) % 256
    FSM = motorMatrix.item(1) % 256
    APM = motorMatrix.item(2) % 256
    ASM = motorMatrix.item(3) % 256

    axisBytes = bytes([SERIAL_MARKER, VECTOR_MOTORS_IDNT , FPM, FSM, APM, ASM])
    sendSerial(ser, axisBytes)


    # ALL CODE TO DRAW SHOULD GO ABOVE THIS COMMENT

    # Go ahead and update the screen with what we've drawn.
    pygame.display.flip()

    # Limit to 20 frames per second
    clock.tick(20)

# Close the window and quit.
# If you forget this line, the program will 'hang'
# on exit if running from IDLE.
pygame.quit()

















