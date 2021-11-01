import sys
import string
import os
import cv2 as cv
import numpy as np
from matplotlib import pyplot as plt
from cmu_112_graphics import *
from tkinter import *
from PIL import Image
import random

print('loaded cv version: ', cv.__version__)

#################################################
# Citations
#
# 15-112 Modal App Framework: http://www.cs.cmu.edu/~112/notes/notes-animations-part1.html
#
# OpenCV: https://opencv.org/
##################################################

def nothing(x):
    pass

def getKthDigit(n, k):
    return (n//10**k)%10

def readFile(path):
    with open(path, "rt") as f:
        return f.read()

def writeFile(path, contents):
    with open(path, "wt") as f:
        f.write(contents)


class CalibrationMode(Mode):
    def appStarted(mode):
        mode.showMask = False
        mode.showFrame = False
        mode.imageX = mode.width/2
        mode.imageY = mode.height/2
        mode.imageScale = 1.0
        mode.image = mode.app.frame
        mode.hsvImage = cv.cvtColor(mode.image, cv.COLOR_BGR2HSV)
        mode.hueList = [ ]
        mode.satList = [ ]
        mode.valList = [ ]
        mode.clicks =  [ ]

        mode.homeImage = mode.loadImage('Home.png')
        mode.homeBounds = (mode.width*(6.5/16), mode.height*(13.2/16),
                            mode.width*(9.5/16), mode.height*(14.8/16))

        mode.x, mode.y = 0, 0

    def timerFired(mode):
        mode.app.processImage()
        mode.image = mode.app.frame
        mode.hsvImage = cv.cvtColor(mode.image, cv.COLOR_BGR2HSV)
        if mode.showMask:
            cv.imshow('result', mode.app.result)

    def keyPressed(mode, event):
        if event.key == 'g':
            cv.destroyAllWindows()
            mode.app.setActiveMode(mode.app.gameMode)
        elif event.key == 'f':
            if mode.showMask:
                mode.showMask = False
            else:
                mode.showMask = True
        elif event.key == 'Space':
            mode.hueList = [ ]
            mode.satList = [ ]
            mode.valList = [ ]
            mode.clicks = [ ]  
        elif event.key == 'h':
            print(mode.app.hsvBounds)

    def mouseMoved(mode, event):
        mode.x, mode.y = event.x, event.y

    def mousePressed(mode, event):
        x, y = event.x, event.y
        hx0, hy0, hx1, hy1 = mode.homeBounds
        if ( (hx0 <= x <= hx1) and (hy0 <= y <= hy1) ):
            mode.app.setActiveMode(mode.app.splashScreenMode)
        if mode.mapClickToFrame(x, y) == None:
            return
        imgX, imgY = mode.mapClickToFrame(x, y)
        meanHue, meanSat, meanVal = mode.getRegionHSV(imgX, imgY)
        mode.hueList.append(meanHue)
        mode.satList.append(meanSat)
        mode.valList.append(meanVal)
        mode.updateMask()

    def getRegionHSV(mode, imgX, imgY):
        image = mode.hsvImage
        hues = [ ]
        sats = [ ]
        vals = [ ]
        for x in range(imgX-10, imgX+11):
            if x < 0 or x > image.shape[1]:
                continue
            for y in range(imgY-10, imgY+11):
                if y < 0 or y > image.shape[0]:
                    continue
                hues.append(image[y,x,0])
                sats.append(image[y,x,1])
                vals.append(image[y,x,2])
        meanHue = sum(hues)/len(hues)
        meanSat = sum(sats)/len(sats)
        meanVal = sum(vals)/len(vals)
        return meanHue, meanSat, meanVal

    def mapClickToFrame(mode, x, y):
        image = mode.image
        width, height = image.shape[1], image.shape[0]
        imgX = int(x + (width/2) * mode.imageScale - mode.imageX)
        imgY = int(y + (height/2) * mode.imageScale - mode.imageY)
        if (imgX < 0) or (imgX > width) or (imgY < 0) or (imgY > height):
            return None
        mode.clicks.append( (imgX-5, imgY-5, imgX+5, imgY+5) )
        return (imgX, imgY)

    def updateMask(mode):
        if mode.hueList == [ ]:
            mode.app.hsvBounds = (0, 0, 0, 255, 255, 255)
        hList = mode.hueList
        sList = mode.satList
        vList = mode.valList
        
        hue_l, hue_h = int(min(mode.hueList) - 10), int(max(mode.hueList) + 10)
        sat_l, sat_h = int(min(mode.satList) - 20), int(max(mode.satList) + 40)
        val_l, val_h = int(min(mode.valList) - 20), int(max(mode.valList) + 20)
        mode.app.hsvBounds = (hue_l, hue_h, sat_l, sat_h, val_l, val_h)

    def getColor(mode, button='default'):
        neonBlue = '#00ffff'
        highlighted = '#ff0080'
        x, y = mode.x, mode.y
        textTab = 300
        if button == 'default':
            return None
        elif button == 'home':
            x0, y0, x1, y1 = mode.homeBounds
        
        if ( (x0 <= x <= x1) and (y0 <= y <= y1) ):
            return highlighted
        else:
            return neonBlue

    def redrawAll(mode, canvas):
        canvas.create_rectangle(0, 0, mode.width, mode.height, fill='black')
        x, y = mode.app.paddleX, mode.app.paddleY
        
        canvas.create_image(mode.imageX, mode.imageY, 
            image=mode.getTkImageRGB(mode.image))

        font = 'system 20 roman'
        color = '#00e500'
        canvas.create_text(mode.width/2, mode.height * (2/16), 
            text=f'Hold your paddle in various positions/lightings and click to calibrate.',
            fill=color, font=font)
        canvas.create_text(mode.width/2, mode.height * (2.5/16), 
            text=f'Press \'Space\' to reset on a misclick.',
            fill=color, font=font)         

        canvas.create_image(mode.width/2, mode.height * (14/16),
            image=ImageTk.PhotoImage(mode.homeImage))
        hx0, hy0, hx1, hy1 = mode.homeBounds
        canvas.create_rectangle(hx0, hy0, hx1, hy1, outline=mode.getColor(button='home'))

        for (x0, y0, x1, y1) in mode.clicks:
            imgW, imgH = mode.image.shape[1], mode.image.shape[0]
            x0 = x0 + mode.width/2 - imgW/2 * mode.imageScale
            y0 = y0 + mode.height/2 - imgH/2 * mode.imageScale
            x1 = x1 + mode.width/2 - imgW/2 * mode.imageScale
            y1 = y1 + mode.height/2 - imgH/2 * mode.imageScale
            canvas.create_rectangle(x0, y0, x1, y1, outline='blue')

    def getTkImageRGB(mode, bgrArray):
        rgbFrame = cv.cvtColor(bgrArray, cv.COLOR_BGR2RGB)
        frame = Image.fromarray(rgbFrame)
        frame = mode.scaleImage(frame, mode.imageScale)
        frame = ImageTk.PhotoImage(frame)
        return frame

class GameOverMode(Mode):
    def appStarted(mode):
        mode.gameOverImage = mode.scaleImage(mode.loadImage('GameOverRed.png'), 0.7)
        mode.playAgainImage = mode.scaleImage(mode.loadImage('PlayAgain.png'), 1.0)
        mode.quitImage = mode.scaleImage(mode.loadImage('Quit.png'), 1.0)
        mode.homeImage = mode.scaleImage(mode.loadImage('Home.png'), 1.0)
        mode.x, mode.y = 0, 0
        mode.playAgainBounds = (mode.width*(.8/16), mode.height*(13.7/16),
                                mode.width*(7.2/16), mode.height*(15.3/16) )
        mode.quitBounds = (mode.width*(8.15/16), mode.height*(13.7/16),
                            mode.width*(10.85/16), mode.height*(15.3/16))
        mode.homeBounds = (mode.width*(11.65/16), mode.height*(13.7/16),
                    mode.width*(14.75/16), mode.height*(15.3/16))
        mode.gamerTag = [ ]
        mode.timer = 0
        mode.enterPressed = False
        mode.leaderboardTxt = readFile('Leaderboard.txt')

    def keyPressed(mode, event):
        key = str(event.key).upper()
        if mode.enterPressed:
            return
        if key == 'BACKSPACE':
            if len(mode.gamerTag) > 0:
                mode.gamerTag.pop()
        elif key == 'ENTER':
            if len(mode.gamerTag) > 0:
                mode.enterPressed = True
                mode.saveScore()
                mode.leaderboardTxt = leaderboardTxt = readFile('Leaderboard.txt')
        elif key in string.ascii_uppercase:
            char = key.upper()
            mode.gamerTag.append(char)
            if len(mode.gamerTag) > 5:
                mode.gamerTag.pop()

    def saveScore(mode):
        gamerScore = mode.app.score
        gamerTag = ''.join(mode.gamerTag)
        data = f'{gamerTag}, #{gamerScore}' #'CHRIS, #3'
        added = False
        leaderboard = readFile('Leaderboard.txt')
        leaderboard = leaderboard.strip()
        if leaderboard == '':
            newLeaderboard = data
        else:
            leaderboardList = leaderboard.splitlines()
            for i in range(len(leaderboardList)):
                leaderboardData = leaderboardList[i]
                j = 1 + leaderboardData.index('#')
                leaderboardScore = int(leaderboardData[j:])
                if leaderboardScore < gamerScore:
                    leaderboardList.insert(i, f'{data}')
                    newLeaderboard = '\n'.join(leaderboardList)
                    added = True
                    break
            if added == False:
                newLeaderboard = leaderboard + f'\n{data}'
        writeFile('Leaderboard.txt', newLeaderboard)



    def mouseMoved(mode, event):
        mode.x, mode.y = event.x, event.y

    def mousePressed(mode, event):
        x, y = event.x, event.y
        px0, py0, px1, py1 = mode.playAgainBounds
        qx0, qy0, qx1, qy1 = mode.quitBounds
        hx0, hy0, hx1, hy1 = mode.homeBounds
        if ( (px0 <= x <= px1) and (py0 <= y <= py1)):
            mode.app.level = 1
            mode.gamerTag = [ ]
            mode.enterPressed = False
            mode.app.score = 0
            mode.app.setActiveMode(mode.app.roundWonMode)
        elif ( (qx0 <= x <= qx1) and (qy0 <= y <= qy1) ):
            mode.app.cap.release()
            mode.app.quit()
        elif ( (hx0 <= x <= hx1) and (hy0 <= y <= hy1) ):
            mode.gamerTag = [ ]
            mode.app.setActiveMode(mode.app.splashScreenMode)
        else:
            None

    def timerFired(mode):
        mode.timer += 1
    
    def getColor(mode, button='default'):
        neonBlue = '#00ffff'
        highlighted = '#ff0080'
        x, y = mode.x, mode.y
        textTab = 300
        if button == 'default':
            return None
        elif button == 'playAgain':
            x0, y0, x1, y1 = mode.playAgainBounds
        elif button == 'quit':
            x0, y0, x1, y1 = mode.quitBounds
        elif button == 'home':
            x0, y0, x1, y1 = mode.homeBounds
        
        if ( (x0 <= x <= x1) and (y0 <= y <= y1) ):
            return highlighted
        else:
            return neonBlue

    def redrawAll(mode, canvas):
        gameOverRed = '#FF163E'
        canvas.create_rectangle(0, 0, mode.width, mode.height, fill='black')
        canvas.create_image(mode.width/2, mode.height * (2/16), 
            image=ImageTk.PhotoImage(mode.gameOverImage))
        canvas.create_image(mode.width * (4/16), mode.height * (14.5/16), 
            image=ImageTk.PhotoImage(mode.playAgainImage))
        px0, py0, px1, py1 = mode.playAgainBounds
        canvas.create_rectangle(px0, py0, px1, py1, outline=mode.getColor(button='playAgain'))
        canvas.create_image(mode.width * (9.5/16), mode.height * (14.5/16), 
            image=ImageTk.PhotoImage(mode.quitImage))
        qx0, qy0, qx1, qy1 = mode.quitBounds
        canvas.create_rectangle(qx0, qy0, qx1, qy1, outline=mode.getColor(button='quit'))
        canvas.create_image(mode.width * (13.2/16), mode.height * (14.5/16), 
            image=ImageTk.PhotoImage(mode.homeImage))
        hx0, hy0, hx1, hy1 = mode.homeBounds
        canvas.create_rectangle(hx0, hy0, hx1, hy1, outline=mode.getColor(button='home'))
        font = 'system 40 roman'
        color = '#00e500'
        canvas.create_text(mode.width * (8/16), mode.height* (11.3/16), font=font, fill=color,
            text='- Player     Score -')
        font= 'system 32 roman'
        color = '#edff00'
        canvas.create_text(mode.width * (5.1/16), mode.height* (12.6/16), font=font, fill=color,
            text=mode.getText(), anchor='w')
        mode.drawLeaderboard(canvas)
    
    def drawLeaderboard(mode, canvas):
        s = ''
        leaderboardList = mode.leaderboardTxt.strip().splitlines()
        for i in range(min(len(leaderboardList), 5)):
            data = leaderboardList[i]
            formattedScore = ''
            hitNumber = False
            for c in data:
                if c.isalpha():
                    formattedScore += c
                elif c.isnumeric():
                    while len(formattedScore) < 10:
                        formattedScore += ' '
                    if not hitNumber:
                        formattedScore += '\t\t'
                        hitNumber = True

                    formattedScore += c 
            s += f'{i+1}.  {formattedScore}\n'
        font= 'system 30 roman'
        color = '#edff00'
        canvas.create_text(mode.width * (8/16), mode.height* (5.3/16), font=font, fill=color,
            text=s, anchor='n')

    def getText(mode):
        gamerTag = ''.join(mode.gamerTag)
        score = str(mode.app.score)
        if mode.enterPressed:
            return gamerTag + '\t        ' + score 
        elif len(gamerTag) == 5:
            if (mode.timer//20) % 2 == 0:

                gamerTag = gamerTag

            else:
                gamerTag = ''
        elif len(gamerTag) < 5:
            if (mode.timer//20) % 2 == 0:

                gamerTag += '_'

            else:
                gamerTag += ''       
        if len(mode.gamerTag) > 0:
            return gamerTag + '\t        ' + score + '              ENTER'
        return gamerTag + '\t        ' + score 

class RoundWonMode(Mode):
    def appStarted(mode):
        mode.roundImage = mode.scaleImage(mode.loadImage('Round.png'), 0.5)
        img = mode.loadImage('NumbersRed.png')
        mode.numberImage = mode.scaleImage(img, 0.5)
        mode.timer = 0

    def keyPressed(mode, event):
        if event.key == 'g':
            mode.backToGameMode()

    def timerFired(mode):
        mode.timer += 10
        if mode.timer == 2000:
            mode.timer = 0
            mode.app.setActiveMode(mode.app.gameMode)

    def backToGameMode(mode):
        mode.app.level += 1
        mode.app.setActiveMode(mode.app.gameMode)

    def getNumberImage(mode, n):
        k = 0
        digitImage = mode.numberImage.crop( (0, k + 121.5*n, 100, k + 121.5*(n+1)) )
        digitImage = mode.scaleImage(digitImage, 2)
        return digitImage

    def redrawAll(mode, canvas):
        canvas.create_rectangle(0, 0, mode.width, mode.height, fill='black')
        canvas.create_image(mode.width * (6.5/16), mode.height/2,
            image=ImageTk.PhotoImage(mode.roundImage))
        mode.displayLevel(canvas)

    def displayLevel(mode, canvas):
        level = mode.app.level
        if level < 10:
            numberImg = mode.scaleImage(mode.getNumberImage(level), .5)
            canvas.create_image(mode.width * (11/16), mode.height/2,
                image=ImageTk.PhotoImage(numberImg))
        elif 10 <= level < 100:
            digit0 = getKthDigit(level, 0)
            digit0Img = mode.scaleImage(mode.getNumberImage(digit0), .5)
            digit1 = getKthDigit(level, 1)
            digit1Img = mode.scaleImage(mode.getNumberImage(digit1), .5)
            canvas.create_image(mode.width * (11/16), mode.height/2,
                image=ImageTk.PhotoImage(digit1Img))
            canvas.create_image(mode.width * (12.2/16), mode.height/2,
                image=ImageTk.PhotoImage(digit0Img))
        else:
            print('get a life')

class LeaderboardMode(Mode):
    def appStarted(mode):
        mode.leaderboardTxt = readFile('Leaderboard.txt')
        mode.homeImage = mode.loadImage('Home.png')
        mode.homeBounds = (mode.width*(6.5/16), mode.height*(13.2/16),
                            mode.width*(9.5/16), mode.height*(14.8/16))
        mode.x, mode.y = 0, 0
        mode.time = 0

    def keyPressed(mode, event):
        pass
    
    def mouseMoved(mode, event):
        mode.x, mode.y = event.x, event.y

    def mousePressed(mode, event):
        x, y = event.x, event.y
        hx0, hy0, hx1, hy1 = mode.homeBounds
        if ( (hx0 <= x <= hx1) and (hy0 <= y <= hy1) ):
            mode.app.setActiveMode(mode.app.splashScreenMode)

    def redrawAll(mode, canvas):
        canvas.create_rectangle(0, 0, mode.width, mode.height, fill='black')
        mode.drawLeaderboard(canvas)

        canvas.create_image(mode.width/2, mode.height * (14/16),
            image=ImageTk.PhotoImage(mode.homeImage))
        hx0, hy0, hx1, hy1 = mode.homeBounds
        canvas.create_rectangle(hx0, hy0, hx1, hy1, outline=mode.getColor(button='home'))
    
    def getColor(mode, button='default'):
        neonBlue = '#00ffff'
        highlighted = '#ff0080'
        x, y = mode.x, mode.y
        textTab = 300
        if button == 'default':
            return None
        elif button == 'home':
            x0, y0, x1, y1 = mode.homeBounds
        
        if ( (x0 <= x <= x1) and (y0 <= y <= y1) ):
            return highlighted
        else:
            return neonBlue

    def drawLeaderboard(mode, canvas):
        s = ''
        leaderboardList = mode.leaderboardTxt.strip().splitlines()
        for i in range(min(len(leaderboardList), 9)):
            data = leaderboardList[i]
            formattedScore = ''
            hitNumber = False
            for c in data:
                if c.isalpha():
                    formattedScore += c
                elif c.isnumeric():
                    while len(formattedScore) < 10:
                        formattedScore += ' '
                    if not hitNumber:
                        formattedScore += '\t\t'
                        hitNumber = True

                    formattedScore += c 
            s += f'{i+1}.  {formattedScore}\n'
        font= 'system 30 roman'
        color = '#edff00'
        canvas.create_text(mode.width * (8/16), mode.height* (2.5/16), font=font, fill=color,
            text=s, anchor='n')
        color = '#00e500'
        font= 'system 30 roman'
        canvas.create_text(mode.width * (8.7/16), mode.height* (2.4/16), font=font, fill=color,
            text='-Player-                         -Score-', anchor='s')

class SplashScreenMode(Mode):
    def appStarted(mode):
        mode.titleImage = mode.loadImage('Title.png')
        mode.playImage = mode.loadImage('Play.png')
        mode.playImage = mode.scaleImage(mode.playImage, .5)
        mode.calibrateImage = mode.loadImage('Calibrate.png')
        mode.calibrateImage = mode.scaleImage(mode.calibrateImage, .5)
        mode.leaderboardImage = mode.loadImage('Leaderboard.png')
        mode.leaderboardImage = mode.scaleImage(mode.leaderboardImage, .5)
        mode.screensaverImage = mode.loadImage('Screensaver.png')
        mode.quitImage = mode.scaleImage(mode.loadImage('Quit.png'), 1.2)
        
        mode.x = 0
        mode.y = 0

        textTab = 300
        mode.playBounds = (mode.width/2 - textTab, mode.height * (7.2/16), 
            mode.width/2 - 80, mode.height * (8.8/16))
        mode.calibrationBounds = (mode.width/2 - textTab, mode.height * (9.2/16), 
            mode.width/2 + 120, mode.height * (10.8/16))
        mode.leaderboardBounds = (mode.width/2 - textTab, mode.height * (11.2/16),
            mode.width/2 + 250, mode.height * (12.8/16))
        mode.quitBounds = (mode.width/2 - textTab, mode.height*(13.2/16),
                            mode.width/2 - 90, mode.height*(14.8/16))

    def keyPressed(mode, event):
        if event.key == 'g':
            mode.app.setActiveMode(mode.app.gameMode)
    
    def mouseMoved(mode, event):
        mode.x, mode.y = event.x, event.y

    def mousePressed(mode, event):
        x, y = event.x, event.y
        px0, py0, px1, py1 = mode.playBounds
        cx0, cy0, cx1, cy1 = mode.calibrationBounds
        lx0, ly0, lx1, ly1 = mode.leaderboardBounds
        qx0, qy0, qx1, qy1 = mode.quitBounds
        if ( (px0 <= x <= px1) and (py0 <= y <= py1)):
            mode.app.setActiveMode(mode.app.roundWonMode)
        elif ( (lx0 <= x <= lx1) and (ly0 <= y <= ly1) ):
            mode.app.leaderboardMode.leaderboardTxt = readFile('Leaderboard.txt')
            mode.app.setActiveMode(mode.app.leaderboardMode)
        elif ( (cx0 <= x <= cx1) and (cy0 <= y <= cy1) ):
            mode.app.setActiveMode(mode.app.calibrationMode)
        elif ( (qx0 <= x <= qx1) and (qy0 <= y <= qy1) ):
            mode.app.cap.release()
            mode.app.quit()
        else:
            None

    
    def getColor(mode, button='default'):
        neonBlue = '#00ffff'
        highlighted = '#ff0080'
        x, y = mode.x, mode.y
        textTab = 300
        if button == 'default':
            return None
        elif button == 'play':
            x0, y0, x1, y1 = mode.playBounds
        elif button == 'calibrate':
            x0, y0, x1, y1 = mode.calibrationBounds
        elif button == 'leaderboard':
            x0, y0, x1, y1 = mode.leaderboardBounds
        elif button == 'quit':
            x0, y0, x1, y1 = mode.quitBounds
        
        if ( (x0 <= x <= x1) and (y0 <= y <= y1) ):
            return highlighted
        else:
            return neonBlue

    def redrawAll(mode, canvas):
        canvas.create_rectangle(0, 0, mode.width, mode.height, fill='black')
        canvas.create_image(mode.width/2, mode.height * (4/16), 
            image=ImageTk.PhotoImage(mode.titleImage))
        textTab = 300
        canvas.create_image(mode.width/2 - textTab, mode.height * (8/16), 
            image=ImageTk.PhotoImage(mode.playImage), anchor = 'w')
        x0, y0, x1, y1 = mode.playBounds
        canvas.create_rectangle(x0, y0, x1, y1, outline=mode.getColor(button='play'))
        canvas.create_image(mode.width/2 - textTab, mode.height * (10/16), 
            image=ImageTk.PhotoImage(mode.calibrateImage), anchor = 'w')
        x0, y0, x1, y1 = mode.calibrationBounds
        canvas.create_rectangle(x0, y0, x1, y1, outline=mode.getColor(button='calibrate'))
        canvas.create_image(mode.width/2 - textTab, mode.height * (12/16), 
            image=ImageTk.PhotoImage(mode.leaderboardImage), anchor = 'w')
        x0, y0, x1, y1 = mode.leaderboardBounds
        canvas.create_rectangle(x0, y0, x1, y1, outline=mode.getColor(button='leaderboard'))
        canvas.create_image(mode.width/2 - textTab - 20, mode.height * (14/16), 
            image=ImageTk.PhotoImage(mode.quitImage), anchor = 'w')
        qx0, qy0, qx1, qy1 = mode.quitBounds
        canvas.create_rectangle(qx0, qy0, qx1, qy1, outline=mode.getColor(button='quit'))
        


class GameMode(Mode):
    def appStarted(mode):
        mode.depth = 3000
        mode.width = 1000
        mode.height = 800
        mode.dmarg = 50
        mode.distance = 1000

        mode.player = Player(mode)
        mode.ball = Ball(mode)
        mode.opponent = Opponent(mode)

        mode.paddleX = mode.width/2
        mode.paddleY = mode.height/2
        mode.faceX = mode.width/2
        mode.faceY = mode.width/2
        mode.headSize = 50

        mode.background = [ ]
        mode.ballLines = [ ]
        mode.ballTrail = [ ]
        mode.playerScore = 0
        mode.opponentScore = 0
        mode.initBackground()
        mode.initBall()

        mode.startCountdown = False
        mode.paused = False
        mode.timerCounter = -1
        mode.numberImage = mode.loadImage('NumbersRed.png')
        mode.resumingImage = mode.scaleImage(mode.loadImage('ResumingRed.png'), .8)
        mode.pausedImage = mode.loadImage('Paused.png')
        mode.numberDisplay = None
        mode.firstStart = True
        mode.startingInImage = mode.scaleImage(mode.loadImage('StartingIn.png'), .6)

        mode.mouseMode = False
        mode.app.score = 0
    
    
    def initBall(mode):
        x = random.randint(-20, 20)
        y = random.randint(-20, 20)
        z = -80
        mode.ball = Ball(mode, vx=x, vy=y, vz=z)
        ## ball lines ##
        mode.ballLines = [ ]
        mode.ballLines.append(Background(mode, (0, 0, 0), (1000, 0, 0)))
        mode.ballLines.append(Background(mode, (0, 0, 0), (0, 800, 0)))
        mode.ballLines.append(Background(mode, (1000, 0, 0), (1000, 800, 0)))
        mode.ballLines.append(Background(mode, (0, 800, 0), (1000, 800, 0)))


    def initBackground(mode):
        ## depth lines ##
        depth = mode.depth
        dmarg = mode.dmarg
        mode.background.append(Background(mode, (0, 0, 0+dmarg), (0, 0, depth+dmarg)))
        mode.background.append(Background(mode, (1000, 0, 0+dmarg), (1000, 0, depth+dmarg)))
        mode.background.append(Background(mode, (0, 800, 0+dmarg), (0, 800, depth+dmarg)))
        mode.background.append(Background(mode, (1000, 800, 0+dmarg), (1000, 800, depth+dmarg)))

        ## x-y slices
        for n in range(0, 6):
            mode.background.append(Background(mode, (0, 0, n*depth/5+dmarg), (1000, 0, n*depth/5+dmarg)))
            mode.background.append(Background(mode, (0, 0, n*depth/5+dmarg), (0, 800, n*depth/5+dmarg)))
            mode.background.append(Background(mode, (1000, 0, n*depth/5+dmarg), (1000, 800, n*depth/5+dmarg)))
            mode.background.append(Background(mode, (0, 800, n*depth/5+dmarg), (1000, 800, n*depth/5+dmarg)))

    def timerFired(mode):
        mode.app.time += 1
        mode.app.processImage()
        mode.faceX = int((mode.app.faceX - 150) * (1000/850))
        ## should range from 0 to 1000
        mode.faceY = int((mode.app.faceY - 176) * (800/569))
        mode.projectAll()
        if mode.startCountdown == True:
            mode.updateCountdown()
            return
        if mode.paused:
            return
        mode.updatePlayer(mode.player)
        mode.updateBackground()
        mode.updateBall(mode.ball)
        mode.updateOpponent(mode.opponent)
        if mode.timerCounter == -1:
            mode.timerCounter += 1
            mode.startCountdown = True
        cv.imshow('frame', mode.app.frame)

    def projectAll(mode):
        ball = mode.ball
        opponent =  mode.opponent
        player = mode.player
        ball.project(mode)
        for line in mode.ballLines:
            line.project(mode)
        for line in mode.ballTrail:
            line.project(mode)
        opponent.project(mode)
        player.project(mode)
        for line in mode.background:
            line.project(mode)


    def updateCountdown(mode):
        k = 100
        mode.timerCounter += k
        if mode.timerCounter == k:
            mode.numberDisplay = mode.getNumberImage(3)
        elif mode.timerCounter == 1000//k * k:
            mode.numberDisplay = mode.getNumberImage(2)
        elif mode.timerCounter == 2000//k * k:
            mode.numberDisplay = mode.getNumberImage(1)
        elif mode.timerCounter == 3000//k * k:
            mode.numberDisplay = None
            mode.startCountdown = False
            mode.timerCounter = 0
    
    def getNumberImage(mode, n):
        k = 0
        digitImage = mode.numberImage.crop( (0, k + 240*n, 200, k + 240*(n+1)) )
        digitImage = mode.scaleImage(digitImage, .8)
        return digitImage

    def updatePlayer(mode, player):
        if not mode.mouseMode:
            player.x = mode.app.paddleX * (3/4)
            if player.x > mode.width - player.width/2:
                player.x = mode.width - player.width/2
            elif player.x < player.width/2:
                player.x = player.width/2
            player.y = (mode.app.paddleY - 150) * (5/4)
            if player.y > mode.height - player.height/2:
                player.y = mode.height - player.height/2
            elif player.y < player.height/2:
                player.y = player.height/2
        ## should range from 0 to 800
         #mode.app.headSize * 10
        mode.headSize = mode.app.headSize
        player.updateVelocity()

    def mouseMoved(mode, event):
        player = mode.player
        if mode.mouseMode:
            player.x, player.y = event.x, event.y

    def updateOpponent(mode, opponent):
        (vx, vy) = opponent.getVelocity(mode)
        opponent.x += vx
        if opponent.x > mode.width - opponent.width/2:
            opponent.x = mode.width - opponent.width/2
        elif opponent.x < opponent.width/2:
            opponent.x = opponent.width/2
        opponent.y += vy
        if opponent.y > mode.height - opponent.height/2:
            opponent.y = mode.height - opponent.height/2
        elif opponent.y < opponent.height/2:
            opponent.y = opponent.height/2
    
    def updateBackground(mode):
        pass

    def updateBall(mode, ball):
        ball.doMove(mode)
        ball.checkContact(mode)
        mode.makeBallTrail(ball)


    def applySpin(mode, player = False, opponent = False):
        ## net velocity is viewed from the ball's frame
        ## Positive net velocity is if the ball has no spin, no vx, and player vx is positive
        ## spinX is thetawise viewed from the top of the box
        ## spinY is thetawise from the right of the box
        ball = mode.ball
        player = mode.player
        opponent = mode.opponent
        if player:
            netVx = player.vx - ball.spinX - ball.vx
            netVy = player.vy - ball.spinY - ball.vy
        elif opponent:
            netVx = ball.vx - ball.spinX - opponent.vx
            netVy = opponent.vy - ball.spinY - ball.vy
        else:
            pass
        k = .05
        ball.spinX = k * netVx
        ball.spinY = k * netVy

    def doScore(mode, player = False, opponent = False):
        if player:
            mode.playerScore += 1
            mode.app.score += 10
        elif opponent:
            mode.opponentScore += 1
        if mode.playerScore == 3:
            mode.playerScore = 0
            mode.opponentScore = 0
            mode.opponent.level += 1
            mode.timerCounter = -1
            mode.firstStart = True
            mode.ball.prevPositions = [ ]
            mode.ballTrail = [ ]
            mode.app.level += 1
            mode.app.setActiveMode(mode.app.roundWonMode)
        if mode.opponentScore == 3:
            mode.playerScore = 0
            mode.opponentScore = 0
            mode.opponent.level = 0
            mode.firstStart = True
            mode.timerCounter = -1
            mode.ball.prevPositions = [ ]
            mode.ballTrail = [ ]
            mode.app.setActiveMode(mode.app.gameOverMode)
        mode.initBall()

    def makeBallTrail(mode, ball):
        ballPos = (ball.x, ball.y, ball.z)
        ball.prevPositions.append(ballPos)
        if len(ball.prevPositions) >= 6:
            ball.prevPositions.pop(0)
        if len(ball.prevPositions) >= 2:
            start = ball.prevPositions[-2]
            end = ball.prevPositions[-1]
            ballLine = Background(mode, start, end)
            mode.ballTrail.append(ballLine)
            if len(mode.ballTrail) >= 6:
                mode.ballTrail.pop(0)

    def keyPressed(mode, event):
        if event.key == 'c':
            mode.app.setActiveMode(mode.app.calibrationMode)
        elif event.key == 'w':
            mode.playerScore = 0
            mode.opponentScore = 0
            mode.opponent.level += 1
            mode.timerCounter = -1
            mode.firstStart = True
            mode.ball.prevPositions = [ ]
            mode.ballTrail = [ ]
            mode.app.level += 1
            mode.app.setActiveMode(mode.app.roundWonMode)
        elif event.key == 's':
            mode.app.score += 10
        elif event.key == 'l':
            mode.playerScore = 0
            mode.opponentScore = 0
            mode.opponent.level = 0
            mode.firstStart = True
            mode.timerCounter = -1
            mode.ball.prevPositions = [ ]
            mode.ballTrail = [ ]
            mode.app.setActiveMode(mode.app.gameOverMode)
        elif event.key == 'r':
            mode.initBall()
        elif event.key == 'Space':
            mode.firstStart = False
            if mode.paused == True:
                mode.paused = False
                mode.startCountdown = True
            elif mode.startCountdown == False:
                mode.paused = True
        elif event.key == 'm':
            if mode.mouseMode:
                mode.mouseMode = False
            else:
                mode.mouseMode = True

    def redrawAll(mode, canvas):
        mode.drawBackground(canvas)
        mode.drawOpponent(canvas)
        mode.drawBall(canvas)
        mode.drawPlayer(canvas)
        if mode.paused:
            canvas.create_image(mode.width/2, mode.height*(6/16), image=ImageTk.PhotoImage(mode.pausedImage))
        if mode.startCountdown:
            mode.drawStartCounter(canvas)

    def drawStartCounter(mode, canvas):
        if mode.firstStart:
            image = ImageTk.PhotoImage(mode.startingInImage)
        else:
            image=ImageTk.PhotoImage(mode.resumingImage)
        canvas.create_image(mode.width/2, mode.height * (6/16), image=image)
        if mode.numberDisplay != None:
            canvas.create_image(mode.width/2, mode.height * (9/16), image=ImageTk.PhotoImage(mode.numberDisplay))


    def drawBackground(mode, canvas):
        canvas.create_rectangle(0, 0, mode.width, mode.height, fill='black')
        for line in mode.background:
            x0, y0 = line.projectedStart
            x1, y1 = line.projectedEnd
            color = '#00ffff'
            canvas.create_line(x0, y0, x1, y1, width=2, fill=color)
        for line in mode.ballLines:
            x0, y0 = line.projectedStart
            x1, y1 = line.projectedEnd
            canvas.create_line(x0, y0, x1, y1, width=2, fill='green')
        for line in mode.ballTrail:
            x0, y0 = line.projectedStart
            x1, y1 = line.projectedEnd
            canvas.create_line(x0, y0, x1, y1, width=1, fill='red')
    
    def drawPlayer(mode, canvas):
        x0, y0 = mode.player.projectedStart
        x1, y1 = mode.player.projectedEnd
        cx = (x0 + x1)/2
        cy = (y0 + y1)/2
        font = 'system 36 roman'
        color = '#0080ff'
        canvas.create_rectangle(x0, y0, x1, y1, width=7, outline=color)
        canvas.create_text(cx, cy, text=f'{mode.playerScore}', fill=color, font=font)

    def drawOpponent(mode, canvas):
        x0, y0 = mode.opponent.projectedStart
        x1, y1 = mode.opponent.projectedEnd
        cx = (x0 + x1)/2
        cy = (y0 + y1)/2
        font = 'system 20 roman'
        color = '#e50000'
        canvas.create_rectangle(x0, y0, x1, y1, width=3, outline=color)
        canvas.create_text(cx, cy, text=f'{mode.opponentScore}', fill=color, font=font)

    def drawBall(mode, canvas):
        for (x0, y0, x1, y1) in mode.ball.projections:
            color = '#00cd00'
            canvas.create_oval(x0, y0, x1, y1, width=5, outline=color)

    def getProjections(mode, t1, t2):
        # feed t1 and t2 3D coords
        x0, y0, z0 = t1
        x1, y1, z1 = t2

        d = mode.distance
        fx = mode.faceX
        fy = mode.faceY

        projX0 = fx + (d/(d+z0)) * (x0 - fx)
        projX1 = fx + (d/(d+z1)) * (x1 - fx)
        
        projY0 = fy + (d/(d+z0)) * (y0 - fy)
        projY1 = fy + (d/(d+z1)) * (y1 - fy)

        return (projX0, projY0, projX1, projY1)

class Player(object):
    def __init__(self, mode):
        self.x = mode.width/2
        self.y = mode.height/2
        self.z = mode.dmarg
        self.width = 300
        self.height = 200
        self.lastPos = (mode.width/2, mode.height/2)
        self.vx = 0
        self.vy = 0
        self.projectedStart = (0, 0)
        self.projectedEnd = (0, 0)

    def updateVelocity(self):
        currX, currY = self.x, self.y
        lastX, lastY = self.lastPos
        self.vx = currX - lastX
        self.vy = currY - lastY
        self.lastPos = (currX, currY)

    def project(self, mode):
        x0, y0, z0 = self.x - self.width/2, self.y - self.height/2, self.z
        x1, y1, z1 = self.x + self.width/2, self.y + self.height/2, self.z

        projX0, projY0, projX1, projY1 = mode.getProjections((x0, y0, z0), (x1, y1, z1))

        self.projectedStart = (projX0, projY0)
        self.projectedEnd = (projX1, projY1)

    

class Opponent(object):
    def __init__(self, mode):
        self.x = mode.width/2
        self.y = mode.height/2
        self.z = mode.depth
        self.width = 300
        self.height = 200
        self.level = 0
        self.projectedStart = (0, 0)
        self.projectedEnd = (0, 0)

    def getVelocity(self, mode):
        ball = mode.ball
        vectorX = ball.x - self.x
        vectorY = ball.y - self.y
        norm = (vectorX**2 + vectorY**2)**0.5
        if norm == 0:
            dx, dy = 0, 0
        else:
            dx, dy = vectorX/norm, vectorY/norm
        k = 5
        maxSpeed = 20 + k * self.level
        speed = min(maxSpeed, norm)
        velocity = (speed * dx, speed * dy)
        return velocity


    def project(self, mode):
        x0, y0, z0 = self.x - self.width/2, self.y - self.height/2, self.z
        x1, y1, z1 = self.x + self.width/2, self.y + self.height/2, self.z

        projX0, projY0, projX1, projY1 = mode.getProjections((x0, y0, z0), (x1, y1, z1))

        self.projectedStart = (projX0, projY0)
        self.projectedEnd = (projX1, projY1)


class Ball(object):
    def __init__(self, mode, vx=10, vy=20, vz=-70):
        self.r = 40
        self.x = mode.width/2
        self.y = mode.height/2
        self.z = mode.depth * (7/8)
        self.vx = vx
        self.vy = vy
        self.vz = vz
        self.spinX = 0
        self.spinY = 0
        self.projections = [ (0,0,0,0), (0,0,0,0), (0,0,0,0) ]
        self.prevPositions = [ ]

    def project(self, mode):
        #XY
        x0, y0, z0 = self.x - self.r, self.y - self.r, self.z
        x1, y1, z1 = self.x + self.r, self.y + self.r, self.z
        self.projections[0] = mode.getProjections( (x0,y0,z0), (x1,y1,z1))

    def checkContact(self, mode):
        dmarg = mode.dmarg
        ## Player ##
        player = mode.player
        px0, px1 = player.x - player.width/2, player.x + player.width/2
        py0, py1 = player.y - player.height/2, player.y + player.height/2
        ## Opponent ##
        opponent = mode.opponent
        ox0, ox1 = opponent.x - opponent.width/2, opponent.x + opponent.width/2
        oy0, oy1 = opponent.y - opponent.height/2, opponent.y + opponent.height/2
        xMin, xMax = self.x - self.r, self.x + self.r
        yMin, yMax = self.y - self.r, self.y + self.r
        zMin, zMax = self.z - self.r, self.z + self.r
        if xMin <= 0:
            self.vx *= -1
            self.x = self.r
        elif xMax >= mode.width:
            self.vx *= -1
            self.x = mode.width - self.r
        if yMin <= 0:
            self.vy *= -1
            self.y = self.r 
        elif yMax >= mode.height:
            self.vy *= -1
            self.y = mode.height - self.r
        if (zMax >= mode.depth):
            if ( (ox0 <= self.x <= ox1)
                and (oy0 <= self.y <= oy1) ):
                self.vz *= -1.05
                self.z = mode.depth - self.r
                mode.applySpin(opponent = True)
            else:
                mode.doScore(player = True)
        elif (zMin <= dmarg):
            if ( (px0 - 0.5*self.r <= self.x <= px1 + 0.5*self.r)
                and (py0 - 0.5*self.r <= self.y <= py1 + 0.5*self.r) ):
                self.vz *= -1
                self.z = self.r + dmarg
                mode.applySpin(player = True)
            else:
                mode.doScore(opponent = True)

    
    def doMove(self, mode):
        self.x += self.vx
        self.y += self.vy
        self.z += self.vz
        self.vx -= self.spinX
        self.vy -= self.spinY
        for line in mode.ballLines:
            x0, y0, z0 = line.start
            x1, y1, z1 = line.end

            line.start = (x0, y0, self.z)
            line.end = (x1, y1, self.z)
        

    def __repr__(self):
        return f'Ball: {self.projectedStart}, {self.projectedEnd}'

class Background(object):
    def __init__(self, mode, start, end):
        self.start = start
        self.end = end
        ## tuples of (x, y, z) ##
        self.projectedStart = (0, 0)
        self.projectedEnd = (0, 0)
        ## tuples of (x, y) ##

    def project(self, mode):
        x0, y0, z0 = self.start
        x1, y1, z1 = self.end

        projX0, projY0, projX1, projY1 = mode.getProjections((x0, y0, z0), (x1, y1, z1))

        self.projectedStart = (projX0, projY0)
        self.projectedEnd = (projX1, projY1)

    def __repr__(self):
        return f'Line: {self.projectedStart}, {self.projectedEnd}'


class TermProjectDemo(ModalApp):
    def appStarted(app):
        app.gameMode = GameMode()
        app.calibrationMode = CalibrationMode()
        app.splashScreenMode = SplashScreenMode()
        app.gameOverMode = GameOverMode()
        app.roundWonMode = RoundWonMode()
        app.leaderboardMode = LeaderboardMode()
        app.calibrationMode = CalibrationMode()
        app.setActiveMode(app.splashScreenMode)

        app.level = 1

        app.timerDelay = 1

        app.cap = cv.VideoCapture(0)
        app.face_cascade = cv.CascadeClassifier('haarcascade_frontalface_default.xml')
        app.success, app.frame = app.cap.read()
        app.gray = None
        app.mask = None
        app.tracker = None
        app.result = None

        '''
        cv.namedWindow('sliders')
        cv.createTrackbar('L_Hue', 'sliders', 0, 255, nothing)
        cv.createTrackbar('L_Saturation', 'sliders', 0, 255, nothing)
        cv.createTrackbar('L_Value', 'sliders', 0, 255, nothing)
        cv.createTrackbar('U_Hue', 'sliders', 0, 255, nothing)
        cv.createTrackbar('U_Saturation', 'sliders', 0 , 255, nothing)
        cv.createTrackbar('U_Value', 'sliders', 0, 255, nothing)
        '''

        app.hsvBounds = (0, 255, 0, 255, 0, 255)

        app.paddleX = app.width/2
        app.paddleY = app.height/2

        app.faceX = app.width/2
        app.faceY = app.height/2
        app.headSize = 50
        app.distance = 200
        # constant for now, measured in cm. Should eventually relate to head size

        app.time = 0


    def processImage(app):
        #if app.time % 10 != 0:
        #   return
        success, frame = app.cap.read()
        frame = cv.flip(frame, 1)

        hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)

        '''
        #SLIDER METHOD
        l_h = cv.getTrackbarPos('L_Hue', 'sliders')
        l_s = cv.getTrackbarPos('L_Saturation', 'sliders')
        l_v = cv.getTrackbarPos('L_Value', 'sliders')

        u_h = cv.getTrackbarPos('U_Hue', 'sliders')
        u_s = cv.getTrackbarPos('U_Saturation', 'sliders')
        u_v = cv.getTrackbarPos('U_Value', 'sliders')

        l_c = np.array([l_h, l_s, l_v]) 
        u_c = np.array([u_h, u_s, u_v]) 
        '''

        l_h, u_h, l_s, u_s, l_v, u_v = app.hsvBounds
        l_c = np.array([l_h, l_s, l_v]) 
        u_c = np.array([u_h, u_s, u_v]) 

        '''
        HARD CODED
        l_c = np.array([58, 80, 25]) #hsv low of green
        u_c = np.array([74, 232, 255]) #hsv high of green
        '''

        kernal = np.ones( (10, 10), np.uint8)

        mask = cv.inRange(hsv, l_c, u_c)
        app.mask = mask

        tracker = cv.morphologyEx(mask, cv.MORPH_CLOSE, kernal, iterations=3)
        app.tracker = tracker

        result = cv.bitwise_and(frame, frame, mask=tracker)
        app.result = result

        gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        app.gray = gray
        

        contours, _ = cv.findContours(tracker, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

        if len(contours) != 0:
            k = 2
            xList = [ ]
            yList = [ ]
            for contour in contours:
                if cv.contourArea(contour) < 40:
                    continue
                x, y, w, h = cv.boundingRect(contour)
                xList.extend( [ x, x+w ] ) 
                yList.extend( [ y, y+h ] )
            if xList != [] and yList != []:
                x0, y0, x1, y1 = min(xList), min(yList), max(xList), max(yList)
                rectangle = (x0, y0, x1, y1)
                cv.rectangle(frame, (x0,y0), (x1, y1), (0,255,0), 2)
                app.paddleX, app.paddleY = k*(x0+x1)/2, k*(y0+y1)/2

            app.frame = frame
        else:
            None

        faces = app.face_cascade.detectMultiScale( gray, 1.1, 4)

        primaryFace = app.getLargestFace(faces)
        if isinstance(primaryFace, np.ndarray):
            (x, y, w, h) = primaryFace

            cv.rectangle(frame, (x,y), (x+w, y+h), (0,0,255), 2)
            k = 2
            app.faceX, app.faceY = k*(x+w/2), k*(y+h/2)

            app.frame = frame
            app.headSize = h

    def getLargestFace(app, faces):
        largestArea = 0
        largestFace = False
        for face in faces:
            (x, y, w, h) = face
            area = w * h
            if area > largestArea:
                largestArea = area
                largestFace = face
        return largestFace

TermProjectDemo(width=1000, height=800)

def clear():
    cap = cv.VideoCapture(0)
    cap.release()

cv.destroyAllWindows()