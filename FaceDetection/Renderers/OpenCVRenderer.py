import os
import cv2

from .RenderersConfig import Position, Colors
from .CommonFunctions import _getTextBoxParams, _getLetterThickness, _getLineThickness, _getPointRadius


def __getTextParams(shape, box, text, font, scale, thickness, adaptiveToBox=True, adaptiveToImage=False):
	iteration = 0
	
	h, w = shape
	y1, x1, y2, x2 = box
	wb = abs(x2 - x1)
	hb = abs(y2 - y1)
	
	if adaptiveToImage:
		upperRatio = 0.002
		lowerRatio = 0.001
		upscaleCoef = 2
		downscaleCoef = 0.7
		area = h * w
	elif adaptiveToBox:
		upperRatio = 0.08
		lowerRatio = 0.03
		upscaleCoef = 2
		downscaleCoef = 0.7
		area = wb * hb
	
	while True:
		iteration += 1
		textBox, baseline = cv2.getTextSize(text, font, scale, thickness)
		if not adaptiveToBox and not adaptiveToImage:
			break
		
		ratio = textBox[0] * textBox[1] / area
		if ratio > upperRatio:
			scale *= downscaleCoef
		if ratio < lowerRatio:
			scale *= upscaleCoef
		elif lowerRatio <= ratio <= upperRatio:
			break
		
		if iteration == 20:
			break
	
	return scale, textBox, baseline


def _checkCoords(box, height, width):
	y1, x1, y2, x2 = box
	
	if y1 > y2:
		y1, y2 = y2, y1
	if x1 > x2:
		x1, x2 = x2, x1
	
	y1 = max(0, y1)
	x1 = max(0, x1)
	y2 = min(height, y2)
	x2 = min(width, x2)
	
	return y1, x1, y2, x2


def drawBoxes(image, boxes, keypoints=None, text=None, **kwargs):
	boxColor = kwargs.get("boxColor", Colors.RGB_LIMEGREEN)
	keypontsColor = kwargs.get("keypointsColor", Colors.RGB_DARKORANGE)
	textColor = kwargs.get("textColor", Colors.RGB_WHITE)
	textPosition = kwargs.get("position", Position.TOP_LEFT)
	textOccurrence = kwargs.get("occurrence", Position.INNER)
	adaptiveToBox = kwargs.get("adaptiveToBox", False)
	adaptiveToImage = kwargs.get("adaptiveToImage", False)
	fillTextBox = kwargs.get("fillTextBox", True)
	
	drawPoints = False
	if keypoints is not None:
		assert len(keypoints) == len(boxes)
		drawPoints = True
	
	printText = False
	if text is not None:
		if isinstance(text, list):
			assert len(text) == len(boxes)
		else:
			text = [text for _ in boxes]
		printText = True
	
	height, width = image.shape[:2]
	size = min(height, width)
	
	lineThickness = _getLineThickness(size)
	
	for idx, bb in enumerate(boxes):
		y1, x1, y2, x2 = _checkCoords(bb, height, width)
		
		pt1, pt2 = (int(x1), int(y1)), (int(x2), int(y2))
		
		cv2.rectangle(image, pt1, pt2, boxColor, lineThickness)
		
		if printText:
			txt = text[idx]
			letterThickness = _getLetterThickness(bb)
			putText(image, (y1, x1, y2, x2), text=txt, thickness=letterThickness, boxColor=boxColor,
			        textColor=textColor, position=textPosition, occurrence=textOccurrence,
			        adaptiveToBox=adaptiveToBox, adaptiveToImage=adaptiveToImage, background=fillTextBox)
		
		if drawPoints:
			points = keypoints[idx]
			radius = _getPointRadius(bb)
			drawKeypoints(image, points, radius, keypontsColor)
	
	return image


def drawKeypoints(image, points, radius=2, color=Colors.RGB_ORANGE):
	for pnt in points:
		pnt = tuple(int(p) for p in pnt)
		cv2.circle(image, pnt, radius, color, thickness=cv2.FILLED)


def putText(image, box, text, thickness=1, font=cv2.FONT_HERSHEY_DUPLEX, scale=0.5, boxColor=Colors.RGB_LAWNGREEN,
            textColor=Colors.RGB_BLACK, position=Position.TOP_LEFT, occurrence=Position.INNER, background=False,
            **kwargs):

	adaptiveToBox = kwargs.get("adaptiveToBox", False)
	adaptiveToImage = kwargs.get("adaptiveToImage", False)
	
	shape = image.shape[:2]
	
	if not isinstance(text, list):
		text = [text]
	
	textLengths = [len(t) for t in text]
	maxText = text[textLengths.index(max(textLengths))]
	scale, textBox, baseline = __getTextParams(shape, box, maxText, font, scale, thickness,
	                                           adaptiveToBox, adaptiveToImage)
	
	for textBlock in text:
		pnt1, pnt2, textPnt = _getTextBoxParams(box, textBox, baseline, position, occurrence)
		
		if background:
			cv2.rectangle(image, pnt1, pnt2, boxColor, cv2.FILLED)
		
		cv2.putText(image, textBlock, textPnt, font, scale, textColor, thickness, lineType=cv2.LINE_AA)
		
		box = [box[0] - textBox[1] - baseline - 1, box[1], box[2] + textBox[1] + baseline + 1, box[3]]


def save(image, wpath=None, name=None):
	wpath = "./Temp" if wpath is None else wpath
	name = "result.png" if name is None else name
	
	os.makedirs(wpath, exist_ok=True)
	cv2.imwrite(os.path.join(wpath, name), image)


def show(image, waitkey=0):
	cv2.imshow("image", image)
	cv2.waitKey(waitkey)

