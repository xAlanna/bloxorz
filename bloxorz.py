import random, sys, copy, os, pygame
from pygame.locals import *

FPS = 30 # frames per second to update the screen
WINWIDTH = 1200 # width of the program's window, in pixels
WINHEIGHT = 600 # height in pixels
HALF_WINWIDTH = int(WINWIDTH / 2)
HALF_WINHEIGHT = int(WINHEIGHT / 2)

# The total width and height of each tile in pixels.
TILEWIDTH = 50
TILEHEIGHT = 85
TILEFLOORHEIGHT = 40

CAM_MOVE_SPEED = 5 # how many pixels per frame the camera moves

BRIGHTBLUE = (  0, 170, 255)
WHITE      = (255, 255, 255)
BGCOLOR = BRIGHTBLUE
TEXTCOLOR = WHITE

UP = 'up'
DOWN = 'down'
LEFT = 'left'
RIGHT = 'right'


def main():
    global FPSCLOCK, DISPLAYSURF, IMAGESDICT, TILEMAPPING, BASICFONT

    # Pygame initialization and basic set up of the global variables.
    pygame.init()
    FPSCLOCK = pygame.time.Clock()

    # Because the Surface object stored in DISPLAYSURF was returned
    # from the pygame.display.set_mode() function, this is the
    # Surface object that is drawn to the actual computer screen
    # when pygame.display.update() is called.
    DISPLAYSURF = pygame.display.set_mode((WINWIDTH, WINHEIGHT))

    pygame.display.set_caption('Bloxorz Remastered')
    BASICFONT = pygame.font.Font('freesansbold.ttf', 18)

    # A global dict value that will contain all the Pygame
    # Surface objects returned by pygame.image.load().
    IMAGESDICT = {'goal': pygame.image.load('RedSelector.png'),
                  'inside floor': pygame.image.load('Plain_Block.png'),
                  'title': pygame.image.load('star_title.png'),
                  'solved': pygame.image.load('star_solved.png'),
                  'rectangle': pygame.image.load('Wood_Block_Tall.png'),
		  'red floor': pygame.image.load('Red_Block.png'),
		  'bridge floor': pygame.image.load('Bridge_Block.png'),
		  #'bridge floor_x': pygame.image.load('Bridge_Block.png'),
		  'split block': pygame.image.load('Split_Block.png'),
		  'O block': pygame.image.load('O_Block.png'),
		  'X block': pygame.image.load('X_Block.png')}


    # These dict values are global, and map the character that appears
    # in the level file to the Surface object it represents.
    TILEMAPPING = {'_': IMAGESDICT['inside floor'],
		   '*': IMAGESDICT['red floor']}
		   #'O': IMAGESDICT['O block'],
		   #'X': IMAGESDICT['X block'],
		   #'o': IMAGESDICT['bridge floor_o'],
		   #'x': IMAGESDICT['bridge floor_x']}


    startScreen() # show the title screen until the user presses a key

    # Read in the levels from the text file. See the readLevelsFile() for
    # details on the format of this file and how to make your own levels.
    levels = readLevelsFile('bloxorz_levels.txt')
    currentLevelIndex = 0

    # The main game loop. This loop runs a single level, when the user
    # finishes that level, the next/previous level is loaded.
    while True: # main game loop
        # Run the level to actually start playing the game:
        result = runLevel(levels, currentLevelIndex)

        if result in ('solved', 'next'):
            # Go to the next level.
            currentLevelIndex += 1
            if currentLevelIndex >= len(levels):
                # If there are no more levels, go back to the first one.
                currentLevelIndex = 0
        elif result == 'back':
            # Go to the previous level.
            currentLevelIndex -= 1
            if currentLevelIndex < 0:
                # If there are no previous levels, go to the last one.
                currentLevelIndex = len(levels)-1
        elif result == 'reset':
            pass # Do nothing. Loop re-calls runLevel() to reset the level


def runLevel(levels, levelNum):
    levelObj = levels[levelNum]
    mapObj = decorateMap(levelObj['mapObj'], levelObj['startState']['player'])
    gameStateObj = copy.deepcopy(levelObj['startState'])
    mapNeedsRedraw = True # set to True to call drawMap()
    levelSurf = BASICFONT.render('Level %s of %s' % (levelNum + 1, len(levels)), 1, TEXTCOLOR)
    levelRect = levelSurf.get_rect()
    levelRect.bottomleft = (20, WINHEIGHT - 35)
    mapWidth = len(mapObj) * TILEWIDTH
    mapHeight = (len(mapObj[0]) - 1) * TILEFLOORHEIGHT + TILEHEIGHT
    MAX_CAM_X_PAN = abs(HALF_WINHEIGHT - int(mapHeight / 2)) + TILEWIDTH
    MAX_CAM_Y_PAN = abs(HALF_WINWIDTH - int(mapWidth / 2)) + TILEHEIGHT

    levelIsComplete = False
    # Track how much the camera has moved:
    cameraOffsetX = 0
    cameraOffsetY = 0
    # Track if the keys to move the camera are being held down:
    cameraUp = False
    cameraDown = False
    cameraLeft = False
    cameraRight = False

    while True: # main game loop
        # Reset these variables:
        playerMoveTo = None
        keyPressed = False

        for event in pygame.event.get(): # event handling loop
            if event.type == QUIT:
                # Player clicked the "X" at the corner of the window.
                terminate()

            elif event.type == KEYDOWN:
                # Handle key presses
                keyPressed = True
                if event.key == K_LEFT:
                    playerMoveTo = LEFT
                elif event.key == K_RIGHT:
                    playerMoveTo = RIGHT
                elif event.key == K_UP:
                    playerMoveTo = UP
                elif event.key == K_DOWN:
                    playerMoveTo = DOWN

                # Set the camera move mode.
                elif event.key == K_a:
                    cameraLeft = True
                elif event.key == K_d:
                    cameraRight = True
                elif event.key == K_w:
                    cameraUp = True
                elif event.key == K_s:
                    cameraDown = True

                elif event.key == K_n:
                    return 'next'
                elif event.key == K_b:
                    return 'back'

                elif event.key == K_ESCAPE:
                    terminate() # Esc key quits.
                elif event.key == K_BACKSPACE:
                    return 'reset' # Reset the level.

            elif event.type == KEYUP:
                # Unset the camera move mode.
                if event.key == K_a:
                    cameraLeft = False
                elif event.key == K_d:
                    cameraRight = False
                elif event.key == K_w:
                    cameraUp = False
                elif event.key == K_s:
                    cameraDown = False



        if playerMoveTo != None and not levelIsComplete:
            # If the player pushed a key to move, make the move
            # (if possible) and push any stars that are pushable.

		
            moved = makeMove(mapObj, gameStateObj, playerMoveTo)

            for current in gameStateObj['switchList']:
	        switchx = current[3]
	        switchy = current[4]
                if current[1] == 'O':
                    if ((switchx, switchy)) == gameStateObj['player'] and ((switchx, switchy)) == gameStateObj['block2']:
                        count = 0
                        for currentbridge in gameStateObj['bridgeList']:
                            count = count +1
                            if currentbridge[0] == current[5]:
                                if current[2] == '$':
                                    currentbridge[2] = not currentbridge[2]
                                elif current[2] == '+':
                                    currentbridge[2] = True
                                elif current[2] == '-':
                                    currentbridge[2] = False
                                gameStateObj['bridgeList'][count] = current
                                mapNeedsRedraw = True
                else:
                    if ((switchx, switchy)) == gameStateObj['player'] or ((switchx, switchy)) == gameStateObj['block2']:
		        count=0
                        for currentbridge in gameStateObj['bridgeList']:
                            count = count + 1
                            if currentbridge[0] == current[5]:
                                if current[2] == '$':
                                    currentbridge[2] = not currentbridge[2]
                                elif current[2] == '+':
                                    currentbridge[2] = True
                                elif current[2] == '-':
                                    currentbridge[2] = False
		                gameStateObj['bridgeList'][count] = current
                                mapNeedsRedraw = True

	
            if moved:
                # increment the step counter.
                gameStateObj['stepCounter'] += 1
                mapNeedsRedraw = True
            else:
		return 'reset'

            if isLevelFinished(levelObj, gameStateObj):
                # level is solved, we should show the "Solved!" image.
                levelIsComplete = True
                keyPressed = False

        DISPLAYSURF.fill(BGCOLOR)


        if mapNeedsRedraw:
            mapSurf = drawMap(mapObj, gameStateObj, levelObj['goal'])
            mapNeedsRedraw = False

        if cameraUp and cameraOffsetY < MAX_CAM_X_PAN:
            cameraOffsetY += CAM_MOVE_SPEED
        elif cameraDown and cameraOffsetY > -MAX_CAM_X_PAN:
            cameraOffsetY -= CAM_MOVE_SPEED
        if cameraLeft and cameraOffsetX < MAX_CAM_Y_PAN:
            cameraOffsetX += CAM_MOVE_SPEED
        elif cameraRight and cameraOffsetX > -MAX_CAM_Y_PAN:
            cameraOffsetX -= CAM_MOVE_SPEED

        # Adjust mapSurf's Rect object based on the camera offset.
        mapSurfRect = mapSurf.get_rect()
        mapSurfRect.center = (HALF_WINWIDTH + cameraOffsetX, HALF_WINHEIGHT + cameraOffsetY)

        # Draw mapSurf to the DISPLAYSURF Surface object.
        DISPLAYSURF.blit(mapSurf, mapSurfRect)

        DISPLAYSURF.blit(levelSurf, levelRect)
        stepSurf = BASICFONT.render('Steps: %s' % (gameStateObj['stepCounter']), 1, TEXTCOLOR)
        stepRect = stepSurf.get_rect()
        stepRect.bottomleft = (20, WINHEIGHT - 10)
        DISPLAYSURF.blit(stepSurf, stepRect)

	for current in levelObj['red floor']:
	    if current == gameStateObj['player'] and current == gameStateObj['block2']:
		showYouFellOffScreen()
		return 'reset'

        for currentBridge in gameStateObj['bridgeList']:
            if currentBridge[2] == False:
                for bridgePos in currentBridge[1]:
                    if bridgePos == gameStateObj['player'] or bridgePos == gameStateObj['block2']:      
				showYouFellOffScreen()
				return 'reset'
			    



        if levelIsComplete:
            # is solved, show the "Solved!" image until the player
            # has pressed a key.
            solvedRect = IMAGESDICT['solved'].get_rect()
            solvedRect.center = (HALF_WINWIDTH, HALF_WINHEIGHT)
            DISPLAYSURF.blit(IMAGESDICT['solved'], solvedRect)

            if keyPressed:
                return 'solved'

        pygame.display.update() # draw DISPLAYSURF to the screen.
        FPSCLOCK.tick(FPS)


def isWall(mapObj, x, y):
    """Returns True if the (x, y) position on
    the map is a wall, otherwise return False."""
    if x < 0 or x >= len(mapObj) or y < 0 or y >= len(mapObj[x]):
        return False # x and y aren't actually on the map.
    elif mapObj[x][y] in ('#', 'x'):
        return True # wall is blocking
    return False

def drawPressKeyMsg():
    pressKeySurf = BASICFONT.render('Press a key to play.', True, BRIGHTBLUE)
    pressKeyRect = pressKeySurf.get_rect()
    pressKeyRect.topleft = (WINWIDTH - 200, WINHEIGHT - 30)
    DISPLAYSURF.blit(pressKeySurf, pressKeyRect)


def checkForKeyPress():
    if len(pygame.event.get(QUIT)) > 0:
        terminate()

    keyUpEvents = pygame.event.get(KEYUP)
    if len(keyUpEvents) == 0:
        return None
    if keyUpEvents[0].key == K_ESCAPE:
        terminate()
    return keyUpEvents[0].key


def showYouFellOffScreen():
    gameOverFont = pygame.font.Font('freesansbold.ttf', 75)
    gameSurf = gameOverFont.render('You fell of the map', True, WHITE)
    gameRect = gameSurf.get_rect()
    gameRect.midtop = (WINWIDTH / 2, 10)

    DISPLAYSURF.blit(gameSurf, gameRect)
    
    pygame.display.update()
    pygame.time.wait(500)


def decorateMap(mapObj, startxy):
    """Makes a copy of the given map object and modifies it.
    Here is what is done to it:
        * The outside/inside floor tile distinction is made.
        

    Returns the decorated map object."""

    startx, starty = startxy # Syntactic sugar

    # Copy the map object so we don't modify the original passed
    mapObjCopy = copy.deepcopy(mapObj)

    # Remove the non-wall characters from the map data
    for x in range(len(mapObjCopy)):
        for y in range(len(mapObjCopy[0])):
            if mapObjCopy[x][y] in ('@'):
                mapObjCopy[x][y] = ' '

    # Flood fill to determine inside/outside floor tiles.
    floodFill(mapObjCopy, startx, starty, ' ', '_')

    # Convert the adjoined walls into corner tiles.

    return mapObjCopy


def makeMove(mapObj, gameStateObj, playerMoveTo):
    """Given a map and game state object, see if it is possible for the
    player to make the given move. If it is, then change the player's
    position (and the position of any pushed star). If not, do nothing.

    Returns True if the player moved, otherwise False."""

    # Make sure the player can move in the direction they want.
    playerx, playery = gameStateObj['player']
    block2x, block2y = gameStateObj['block2']

    # This variable is "syntactic sugar". Typing "stars" is more
    # readable than typing "gameStateObj['stars']" in our code.
    blockState = gameStateObj['blockState']

    # The code for handling each of the directions is so similar aside
    # from adding or subtracting 1 to the x/y coordinates. We can
    # simplify it by using the xOffset and yOffset variables.

    if gameStateObj['blockState'] == 'stand':
	if playerMoveTo == UP:
	    if not isWall(mapObj, playerx, playery-1)and not isWall(mapObj, block2x, block2y-2):
		gameStateObj['blockState'] = 'foward'
		gameStateObj['player'] = (playerx, playery-1)
		gameStateObj['block2'] = (block2x, block2y-2)
		return True
	    else:
	        return showYouFellOffScreen()
	elif playerMoveTo == DOWN:
	    if not isWall(mapObj, playerx, playery+1)and not isWall(mapObj, block2x, block2y+2):
		gameStateObj['blockState'] = 'back'
		gameStateObj['player'] = (playerx, playery+1)
		gameStateObj['block2'] = (block2x, block2y+2)
		return True
	    else:
	        return showYouFellOffScreen()
	elif playerMoveTo == RIGHT:
	    if not isWall(mapObj, playerx+1, playery)and not isWall(mapObj, block2x+2, block2y):
		gameStateObj['blockState'] = 'right'
		gameStateObj['player'] = (playerx+1, playery)
		gameStateObj['block2'] = (block2x+2, block2y)
		return True
	    else:
	        return showYouFellOffScreen()
	elif playerMoveTo == LEFT:
	    if not isWall(mapObj, playerx-1, playery)and not isWall(mapObj, block2x-2, block2y):
		gameStateObj['blockState'] = 'left'
		gameStateObj['player'] = (playerx-1, playery)
		gameStateObj['block2'] = (block2x-2, block2y)
		return True
	    else:
	        return showYouFellOffScreen()
    elif gameStateObj['blockState'] == 'foward':
	if playerMoveTo == UP:
	    if not isWall(mapObj, block2x, block2y-1):
		gameStateObj['blockState'] = 'stand'
		gameStateObj['player'] = (block2x, block2y-1)
		gameStateObj['block2'] = (block2x, block2y-1)
		return True
	    else:
	        return showYouFellOffScreen() 
	elif playerMoveTo == DOWN:
	    if not isWall(mapObj, playerx, playery+1):
		gameStateObj['blockState'] = 'stand'
		gameStateObj['player'] = (playerx, playery+1)
		gameStateObj['block2'] = (playerx, playery+1)
		return True
	    else:
	        return showYouFellOffScreen()
	elif playerMoveTo == RIGHT:
	    if not isWall(mapObj, playerx+1, playery)and not isWall(mapObj, block2x+1, block2y):
		gameStateObj['player'] = (playerx+1, playery)
		gameStateObj['block2'] = (block2x+1, block2y)
		return True
	    else:
	        return showYouFellOffScreen()
	elif playerMoveTo == LEFT:
	    if not isWall(mapObj, playerx-1, playery)and not isWall(mapObj, block2x-1, block2y):
		gameStateObj['player'] = (playerx-1, playery)
		gameStateObj['block2'] = (block2x-1, block2y)
		return True
	    else:
	        return showYouFellOffScreen()
    elif gameStateObj['blockState'] == 'back':
	if playerMoveTo == UP:
	    if not isWall(mapObj, playerx, playery-1):
		gameStateObj['blockState'] = 'stand'
		gameStateObj['player'] = (playerx, playery-1)
		gameStateObj['block2'] = (playerx, playery-1)
		return True
	    else:
	        return showYouFellOffScreen() 
	elif playerMoveTo == DOWN:
	    if not isWall(mapObj, block2x, block2y+1):
		gameStateObj['blockState'] = 'stand'
		gameStateObj['player'] = (block2x, block2y+1)
		gameStateObj['block2'] = (block2x, block2y+1)
		return True
	    else:
	        return showYouFellOffScreen()
	elif playerMoveTo == RIGHT:
	    if not isWall(mapObj, playerx+1, playery) and not isWall(mapObj, block2x+1, block2y):
		gameStateObj['player'] = (playerx+1, playery)
		gameStateObj['block2'] = (block2x+1, block2y)
		return True
	    else:
	        return showYouFellOffScreen()
	elif playerMoveTo == LEFT:
	    if not isWall(mapObj, playerx-1, playery) and not isWall(mapObj, block2x-1, block2y):
		gameStateObj['player'] = (playerx-1, playery)
		gameStateObj['block2'] = (block2x-1, block2y)
		return True
	    else:
	        return showYouFellOffScreen()
    elif gameStateObj['blockState'] == 'right':
	if playerMoveTo == UP:
	    if not isWall(mapObj, playerx, playery-1)and not isWall(mapObj, block2x, block2y-1):
		gameStateObj['player'] = (playerx, playery-1)
		gameStateObj['block2'] = (block2x, block2y-1)
		return True
	    else:
	        return showYouFellOffScreen() 
	elif playerMoveTo == DOWN:
	    if not isWall(mapObj, playerx, playery+1)and not isWall(mapObj, block2x, block2y+1):
		gameStateObj['player'] = (playerx, playery+1)
		gameStateObj['block2'] = (block2x, block2y+1)
		return True
	    else:
	        return showYouFellOffScreen()
	elif playerMoveTo == RIGHT:
	    if not isWall(mapObj, block2x+1, block2y):
		gameStateObj['blockState'] = 'stand'
		gameStateObj['player'] = (block2x+1, block2y)
		gameStateObj['block2'] = (block2x+1, block2y)
		return True
	    else:
	        return showYouFellOffScreen()
	elif playerMoveTo == LEFT:
	    if not isWall(mapObj, playerx-1, playery):
		gameStateObj['blockState'] = 'stand'
		gameStateObj['player'] = (playerx-1, playery)
		gameStateObj['block2'] = (playerx-1, playery)
		return True
	    else:
	        return showYouFellOffScreen()
    elif gameStateObj['blockState'] == 'left':
	if playerMoveTo == UP:
	    if not isWall(mapObj, playerx, playery-1)and not isWall(mapObj, block2x, block2y-1):
		gameStateObj['player'] = (playerx, playery-1)
		gameStateObj['block2'] = (block2x, block2y-1)
		return True
	    else:
	        return showYouFellOffScreen() 
	elif playerMoveTo == DOWN:
	    if not isWall(mapObj, playerx, playery+1)and not isWall(mapObj, block2x, block2y+1):
		gameStateObj['player'] = (playerx, playery+1)
		gameStateObj['block2'] = (block2x, block2y+1)
		return True
	    else:
	        return showYouFellOffScreen()
	elif playerMoveTo == RIGHT:
	    if not isWall(mapObj, playerx+1, playery):
		gameStateObj['blockState'] = 'stand'
		gameStateObj['player'] = (playerx+1, playery)
		gameStateObj['block2'] = (playerx+1, playery)
		return True
	    else:
	        return showYouFellOffScreen()
	elif playerMoveTo == LEFT:
	    if not isWall(mapObj, block2x-1, block2y):
		gameStateObj['blockState'] = 'stand'
		gameStateObj['player'] = (block2x-1, block2y)
		gameStateObj['block2'] = (block2x-1, block2y)
		return True
	    else:
	        return showYouFellOffScreen()
	return False

    

def startScreen():
    """Display the start screen (which has the title and instructions)
    until the player presses a key. Returns None."""

    # Position the title image.
    titleRect = IMAGESDICT['title'].get_rect()
    topCoord = 50 # topCoord tracks where to position the top of the text
    titleRect.top = topCoord
    titleRect.centerx = HALF_WINWIDTH
    topCoord += titleRect.height

    # Unfortunately, Pygame's font & text system only shows one line at
    # a time, so we can't use strings with \n newline characters in them.
    # So we will use a list with each line in it.
    instructionText = ['Move the 2x1 to the goal.',
                       'Arrow keys to move, WASD for camera control.',
                       'Backspace to reset level, Esc to quit.',
                       'N for next level, B to go back a level.']

    # Start with drawing a blank color to the entire window:
    DISPLAYSURF.fill(BGCOLOR)

    # Draw the title image to the window:
    DISPLAYSURF.blit(IMAGESDICT['title'], titleRect)

    # Position and draw the text.
    for i in range(len(instructionText)):
        instSurf = BASICFONT.render(instructionText[i], 1, TEXTCOLOR)
        instRect = instSurf.get_rect()
        topCoord += 10 # 10 pixels will go in between each line of text.
        instRect.top = topCoord
        instRect.centerx = HALF_WINWIDTH
        topCoord += instRect.height # Adjust for the height of the line.
        DISPLAYSURF.blit(instSurf, instRect)

    while True: # Main loop for the start screen.
        for event in pygame.event.get():
            if event.type == QUIT:
                terminate()
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    terminate()
                return # user has pressed a key, so return.

        # Display the DISPLAYSURF contents to the actual screen.
        pygame.display.update()
        FPSCLOCK.tick()


def readLevelsFile(filename):
    assert os.path.exists(filename), 'Cannot find the level file: %s' % (filename)
    mapFile = open(filename, 'r')
    # Each level must end with a blank line
    content = mapFile.readlines() + ['\r\n']
    mapFile.close()

    levels = [] # Will contain a list of level objects.
    levelNum = 0
    mapTextLines = [] # contains the lines for a single level's map.
    mapObj = [] # the map object made from the data in mapTextLines
    for lineNum in range(len(content)):
        # Process each line that was in the level file.
        line = content[lineNum].rstrip('\r\n')

        if ';' in line:
            # Ignore the ; lines, they're comments in the level file.
            line = line[:line.find(';')]

        if line != '':
            # This line is part of the map.
            mapTextLines.append(line)
        elif line == '' and len(mapTextLines) > 0:
            # A blank line indicates the end of a level's map in the file.
            # Convert the text in mapTextLines into a level object.

            # Find the longest row in the map.
            maxWidth = -1
            for i in range(len(mapTextLines)):
                if len(mapTextLines[i]) > maxWidth:
                    maxWidth = len(mapTextLines[i])
            # Add spaces to the ends of the shorter rows. This
            # ensures the map will be rectangular.
            for i in range(len(mapTextLines)):
                mapTextLines[i] += ' ' * (maxWidth - len(mapTextLines[i]))

            # Convert mapTextLines to a map object.
            for x in range(len(mapTextLines[0])):
                mapObj.append([])
            for y in range(len(mapTextLines)):
                for x in range(maxWidth):
                    mapObj[x].append(mapTextLines[y][x])

            # Loop through the spaces in the map and find the @, ., and $
            # characters for the starting game state.
            startx = None # The x and y for the player's starting position
            starty = None
            goal = None
	    red_Floor = [] 
	    switchList = []
            bridgeList = []
            for x in range(maxWidth):	   
                for y in range(len(mapObj[x])):
		    if mapObj[0][y] == '=':
		        switch = mapObj[1][y]
		        switchType = mapObj[2][y]
		        switchFunction = mapObj[3][y]
		        bridge = []
                        bridgeName = mapObj[4][y] 
 		        for tempx in range(maxWidth):
			    for tempy in range(len(mapObj[tempx])): 
		                if mapObj[0][tempy] != '=' and mapObj[0][tempy] != '%':
				    if mapObj[tempx][tempy] == switch:
				        switchx = tempx
				        switchy = tempy
				    #if mapObj[tempx][tempy] == bridgeName:
				    #    bridgex = tempx
				    #    bridgey = tempy
				    #    bridge.append((bridgex, bridgey))
		        switchList.append([switch, switchType, switchFunction, switchx, switchy, bridgeName])
                        addBridge = False
			for currentBridge in bridgeList:
			    if currentBridge[0] == bridgeName:
                                addBridge = True 
                        if addBridge:                       
			    bridgeList.append([bridgeName, bridge, False])

                    if mapObj[0][y] == '%':
                        count = -1
                        for currentBridge in bridgeList:
                            count = count + 1
			    if mapObj[1][y] == currentBridge[0]:
                               currentBridge[1] = True	
                               bridgeList[count] = currentBridge
                       
                    if mapObj[x][y] in ('@'):
                         # '@' is player
                         startx = x
                         starty = y
                    if mapObj[x][y] in ('.'):
                         # ' ' is goal
                         goal = (x, y)
		    if mapObj[x][y] in ('*'):
	          	 red_Floor.append((x, y))
		    #for currentswitch in switchList:
		    
			

            # Basic level design sanity checks:
            assert startx != None and starty != None, 'Level %s (around line %s) in %s is missing a "@" or "+" to mark the start point.' % (levelNum+1, lineNum, filename)
            assert goal != None, 'Level %s (around line %s) in %s must have one goal.' % (levelNum+1, lineNum, filename)

            # Create level object and starting game state object.
            gameStateObj = {'player': (startx, starty),
                            'stepCounter': 0,
                            'blockState': 'stand',
			    'block2': (startx, starty),
			    'switchList': switchList,
                            'bridgeList': bridgeList}
            levelObj = {'width': maxWidth,
                        'height': len(mapObj),
                        'mapObj': mapObj,
                        'goal': goal,
			'red floor': red_Floor,
                        'startState': gameStateObj}

            levels.append(levelObj)

            # Reset the variables for reading the next map.
            mapTextLines = []
            mapObj = []
            gameStateObj = {}
            levelNum += 1
    return levels


def floodFill(mapObj, x, y, oldCharacter, newCharacter):
    """Changes any values matching oldCharacter on the map object to
    newCharacter at the (x, y) position, and does the same for the
    positions to the left, right, down, and up of (x, y), recursively."""

    # In this game, the flood fill algorithm creates the inside/outside
    # floor distinction. This is a "recursive" function.
    # For more info on the Flood Fill algorithm, see:
    #   http://en.wikipedia.org/wiki/Flood_fill
    if mapObj[x][y] == oldCharacter:
        mapObj[x][y] = newCharacter

    if x < len(mapObj) - 1 and mapObj[x+1][y] == oldCharacter:
        floodFill(mapObj, x+1, y, oldCharacter, newCharacter) # call right
    if x > 0 and mapObj[x-1][y] == oldCharacter:
        floodFill(mapObj, x-1, y, oldCharacter, newCharacter) # call left
    if y < len(mapObj[x]) - 1 and mapObj[x][y+1] == oldCharacter:
        floodFill(mapObj, x, y+1, oldCharacter, newCharacter) # call down
    if y > 0 and mapObj[x][y-1] == oldCharacter:
        floodFill(mapObj, x, y-1, oldCharacter, newCharacter) # call up


def drawMap(mapObj, gameStateObj, goal):
    """Draws the map to a Surface object, including the player and
    stars. This function does not call pygame.display.update(), nor
    does it draw the "Level" and "Steps" text in the corner."""

    # mapSurf will be the single Surface object that the tiles are drawn
    # on, so that it is easy to position the entire map on the DISPLAYSURF
    # Surface object. First, the width and height must be calculated.
    mapSurfWidth = len(mapObj) * TILEWIDTH
    mapSurfHeight = (len(mapObj[0]) - 1) * TILEFLOORHEIGHT + TILEHEIGHT
    mapSurf = pygame.Surface((mapSurfWidth, mapSurfHeight))
    mapSurf.fill(BGCOLOR) # start with a blank color on the surface.

    OList = []
    XList = []
    currentBridgeList = []
    count = -1
    for currentswitch in gameStateObj['switchList']:
        count = count + 1
	if currentswitch[1] == 'O':
	    OList.append((currentswitch[3], currentswitch[4]))
	elif currentswitch[1] == 'X':
	    XList.append((currentswitch[3], currentswitch[4]))

    for currentbridge in gameStateObj['bridgeList']:
        if currentbridge[2] == True:
            for bridgePositions in currentbridge[1]:
			currentBridgeList.append(bridgePositions)

    for x in range(len(mapObj)):
        for y in range(len(mapObj[x])):
            spaceRect = pygame.Rect((x * TILEWIDTH, y * TILEFLOORHEIGHT, TILEWIDTH, TILEHEIGHT))
            if mapObj[x][y] in TILEMAPPING:
                baseTile = TILEMAPPING[mapObj[x][y]]

                # First draw the base ground/wall tile.
                mapSurf.blit(baseTile, spaceRect)
            if (x, y) in XList:
		mapSurf.blit(IMAGESDICT['X block'], spaceRect)
	    if (x, y) in OList:
		mapSurf.blit(IMAGESDICT['O block'], spaceRect)
	    if (x, y) in currentBridgeList:
		mapSurf.blit(IMAGESDICT['bridge floor'], spaceRect)
            #if (x, y) == goal:
                # Draw a goal without a star on it.
                #mapSurf.blit(IMAGESDICT['goal'], spaceRect)
	    if (x, y) == gameStateObj['player']: 
		 baseblock = pygame.Rect((x * TILEWIDTH, y * TILEFLOORHEIGHT-20, TILEWIDTH, TILEHEIGHT))
		 mapSurf.blit(IMAGESDICT['rectangle'], baseblock)	
           	 if (x, y) == gameStateObj['block2']:
		 	stand = pygame.Rect((x * TILEWIDTH, y * TILEFLOORHEIGHT-60, TILEWIDTH, TILEHEIGHT))
		 	mapSurf.blit(IMAGESDICT['rectangle'], stand)
	    elif (x, y) != gameStateObj['player']and (x, y) == gameStateObj['block2']:
		 baseblock = pygame.Rect((x * TILEWIDTH, y * TILEFLOORHEIGHT-20, TILEWIDTH, TILEHEIGHT))
		 mapSurf.blit(IMAGESDICT['rectangle'], baseblock)

    return mapSurf

def isLevelFinished(levelObj, gameStateObj):
    """Returns True if all the goals have stars in them."""
    goal = levelObj['goal']
    player = gameStateObj['player']
    block2 =  gameStateObj['block2']
    if player == goal and block2 == goal:
	return True
    return False


def terminate():
    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()
