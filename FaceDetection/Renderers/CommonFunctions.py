from Renderers.RenderersConfig import Position


def _getLineThickness(size):
	return int(round(size * 0.003))


def _getLetterThickness(box):
	y1, x1, y2, x2 = box
	return max(1, int(round(min(y2 - y1, x2 - x1) * 0.005)))


def _getPointRadius(box):
	y1, x1, y2, x2 = box
	return max(2, int(round(min(y2 - y1, x2 - x1) * 0.01)))


def _getTextBoxParams(box, textBox, baseline, position=Position.TOP_LEFT, occurrence=Position.INNER):
	y1, x1, y2, x2 = box
	tw, th = textBox
	
	pnt1 = [0, 0]
	pnt2 = [0, 0]
	textPnt = [th, 0]
	
	shift = 0 if occurrence == Position.INNER else th + baseline
	
	if position in Position.TOP:
		pnt1[1] = y1 + th + baseline - shift
		pnt2[1] = y1 - shift
		textPnt[1] = y1 + th + baseline // 2 - shift
	elif position in Position.BOTTOM:
		pnt1[1] = y2 + shift
		pnt2[1] = y2 - th - baseline + shift
		textPnt[1] = y2 - baseline // 2 + shift
	
	if position in Position.LEFT:
		pnt1[0] = x1
		pnt2[0] = x1 + tw
	elif position in Position.CENTER:
		pnt1[0] = (x2 + x1) // 2 - tw // 2
		pnt2[0] = (x2 + x1) // 2 + tw // 2
	elif position in Position.RIGHT:
		pnt1[0] = x2 - tw
		pnt2[0] = x2
	
	textPnt[0] = pnt1[0]

	pnt1 = tuple(int(p) for p in pnt1)
	pnt2 = tuple(int(p) for p in pnt2)
	textPnt = tuple(int(p) for p in textPnt)
	
	return pnt1, pnt2, textPnt