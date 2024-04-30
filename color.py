#!/usr/bin/env python3

from sys import argv, stderr
# Refer to /usr/lib/python3.11/site-packages/qui/clipboard.py
from qui.clipboard import pyinotify, qubesadmin, NotificationApp, DATA, Gtk, Gdk

from html import escape

TAG_START = lambda color: "<span data-mx-color='%s' style='color: %s;'>" %(color, color)
TAG_END = lambda: "</span>"

if len(argv) not in [1, 2]:
	print("Usage: %s <color>" %(argv[0]), file=stderr)
	raise SystemExit

class ColoredChar(object):
	def __init__(self, color, char):
		self.char = char
		self.html = escape(char)
		self.color = color
	def __str__(self):
		return self.html

class ColoredString(object):
	def __init__(self):
		self.chars = []
	def __add__(self, char):
		if isinstance(char, ColoredChar):
			self.chars += [char]
		elif isinstance(char, (list, tuple)):
			for c in char:
				self.__add__(c)
		else:
			raise TypeError("char must be of type ColoredChar")

		return self
	def __str__(self):
		if not self.chars:
			return ""

		ret = ""
		if self.chars[0].color != None:
			ret += TAG_START(self.chars[0].color)

		ret += str(self.chars[0])
		last_color = self.chars[0].color

		for char in self.chars[1:]:
			color = char.color
			if color != last_color:
				if last_color != None:
					ret += TAG_END()
				if color != None:
					ret += TAG_START(color)
				last_color = color
			ret += str(char)
		if last_color != None:
			ret += TAG_END()

		return ret

def colorify_trans3(char, ix, length):
	colors = ["#5BCEFA", "#F5A9B8", "#FFFFFF"]
	return ColoredChar(colors[ix * len(colors) // length], char)
def colorify_trans5(char, ix, length):
	colors = ["#5BCEFA", "#F5A9B8", "#FFFFFF", "#F5A9B8", "#5BCEFA"]
	return ColoredChar(colors[ix * len(colors) // length], char)
def colorify_nonbinary(char, ix, length):
	colors = ["#FCF434", "#FFFFFF", "#9C59D1", "#2C2C2C"]
	return ColoredChar(colors[ix * len(colors) // length], char)
def colorify_rgb(char, ix, length, hex):
	return ColoredChar(hex, char)

colors = {
		"default": lambda char, ix, length: ColoredChar("#eeaaff", char),
		"none": lambda char, ix, length: ColoredChar(None, char),
		"trans": colorify_trans5,
		"trans3": colorify_trans3,
		"trans5": colorify_trans5,
		"nonbinary": colorify_nonbinary,
		"nb": colorify_nonbinary
}

colorify = colors["default"]

def main():
	global colorify

	color = ""
	if len(argv) >= 2:
		color = argv[1]

	if color not in ["default", ""] and color[0] not in ["#"]:
		colorify = colors[color]
	if len(color) > 0 and color[0] in ["#"]:
		colorify = lambda char, ix, length: colorify_rgb(char, ix, length, color)

	wm = pyinotify.WatchManager()
	qubes_app = qubesadmin.Qubes()
	dispatcher = qubesadmin.events.EventsDispatcher(qubes_app)
	gtk_app = NotificationApp(wm, qubes_app, dispatcher)
	clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
	text = str(clipboard.wait_for_text()) # Save dom0's old clipboard

	with open(DATA, 'r', encoding='utf-8') as contents:
		global_text = contents.read()

		colored = ColoredString()
		global_text_len = len(global_text)
		for ix, char in enumerate(global_text):
			colored += colorify(char, ix, global_text_len)

	clipboard.set_text(str(colored), -1)
	gtk_app.copy_dom0_clipboard()

	if text != None:
		clipboard.set_text(text, -1) # Revert dom0's clipboard

if __name__ == "__main__":
	main()
