#!/usr/bin/env python3

from sys import argv, stderr

from subprocess import run # For spawning disposables
from string import printable # For sanitizing strings

# Create our own Exception for security-related errors
class SecurityException(Exception):
	pass

class SecurityContext:
	is_dvm_agent = False

# The name of the VM to use for processing. This should be a disposable VM, but technically it can be any VM you want, except dom0
# It is not recommended to do processing in a trusted VM, since the global clipboard is an untrusted input
AGENT_QUBE = "sys-colorify"

def clean_str(string):
	ret = ""
	for char in string:
		if char in printable:
			ret += char
	return ret

def format_exc(e):
	return "%s: %s" %(type(e).__name__, e)
def print_exc(e):
	print(format_exc(e), file=stderr)

def dvm_agent():
	# Implement all parsing logic here to avoid accidentally calling potentially-vulnerable parsing code
	
	# If we're not running as a DVM agent, abort immediately
	if not SecurityContext.is_dvm_agent:
		raise SecurityException("Not running as DVM agent, aborting.")
	
	# Modules which increase attack surface are only imported if running in a DVM agent
	import re
	from html import escape
	
	TAG_START = lambda color: "<span data-mx-color='%s' style='color: %s;'>" %(color, color)
	TAG_END = lambda: "</span>"

	whitespace = r'\s+'
	def count_words(string):
		return len(re.findall(whitespace, " " + string))

	def index_words(string):
		words = count_words(string)
		if words > 0:
			return words - 1
		else:
			return 0

	class ColoredChar(object):
		def __init__(self, color, char):
			self.char = char
			self.html = escape(char).encode("ascii", "xmlcharrefreplace").decode("ascii")
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

	def colorify_trans3(char, ix, length, text):
		colors = ["#5BCEFA", "#F5A9B8", "#FFFFFF"]
		return ColoredChar(colors[ix * len(colors) // length], char)
	def colorify_trans5(char, ix, length, text):
		colors = ["#5BCEFA", "#F5A9B8", "#FFFFFF", "#F5A9B8", "#5BCEFA"]
		return ColoredChar(colors[ix * len(colors) // length], char)
	def colorify_trans3_loop(char, ix, length, text):
		colors = ["#5BCEFA", "#F5A9B8", "#FFFFFF"]
		return ColoredChar(colors[ix % len(colors)], char)
	def colorify_trans5_loop(char, ix, length, text):
		colors = ["#5BCEFA", "#F5A9B8", "#FFFFFF", "#F5A9B8"]
		return ColoredChar(colors[ix % len(colors)], char)
	def colorify_nonbinary(char, ix, length, text):
		colors = ["#FCF434", "#FFFFFF", "#9C59D1", "#2C2C2C"]
		return ColoredChar(colors[ix * len(colors) // length], char)
	def colorify_nb_loop(char, ix, length, text):
		colors = ["#FCF434", "#FFFFFF", "#9C59D1", "#2C2C2C"]
		return ColoredChar(colors[ix % len(colors)], char)
	def colorify_rgb(char, ix, length, text, hex):
		return ColoredChar(hex, char)

	def colorify_trans5_words(char, ix, length, text):
		colors = ["#5BCEFA", "#F5A9B8", "#FFFFFF", "#F5A9B8", "#5BCEFA"]
		return ColoredChar(colors[index_words(text[:ix]) * len(colors) // count_words(text)], char)
	def colorify_nb_words(char, ix, length, text):
		colors = ["#FCF434", "#FFFFFF", "#9C59D1", "#2C2C2C"]
		return ColoredChar(colors[index_words(text[:ix]) * len(colors) // count_words(text)], char)

	colors = {
			"default": lambda char, ix, length, text: ColoredChar("#eeaaff", char),
			"none": lambda char, ix, length, text: ColoredChar(None, char),
			"trans": colorify_trans5,
			"trans3": colorify_trans3,
			"trans5": colorify_trans5,
			"nonbinary": colorify_nonbinary,
			"nb": colorify_nonbinary,
			"trans3-loop": colorify_trans3_loop,
			"trans5-loop": colorify_trans5_loop,
			"nb-loop": colorify_nb_loop,
			"trans5-words": colorify_trans5_words,
			"nb-words": colorify_nb_words
	}

	colorify = colors["default"]

	color = ""
	if len(argv) >= 2:
		color = argv[1]

	if color not in ["default", ""]:
		if color[0] in ["#"]:
			colorify = lambda char, ix, length, text: colorify_rgb(char, ix, length, text, color)
		else:
			colorify = colors[color]

	with open(DATA, 'r', encoding='utf-8') as contents:
		global_text = contents.read()
		global_text_length = len(global_text)

		colored = ColoredString()
		for ix, char in enumerate(global_text):
			colored += colorify(char, ix, global_text_length, global_text)

		return colored

def main():
	global argv

	if len(argv) > 2 and argv[1] == "--dvm-agent": # Tells the script that it's running in a disposable
		global DATA
		SecurityContext.is_dvm_agent = True
		DATA = argv[2]
		argv = argv[2:]
		print(dvm_agent(), end="")
		return
	elif len(argv) not in [1, 2]:
		print("Usage: %s <color>" %(argv[0]), file=stderr)
		raise SystemExit

	if AGENT_QUBE == "dom0":
		raise SecurityException("dom0 cannot be used as a colorification agent")

	# Refer to /usr/lib/python3.11/site-packages/qui/clipboard.py
	from qui.clipboard import pyinotify, qubesadmin, NotificationApp, DATA, Gtk, Gdk

	wm = pyinotify.WatchManager()
	qubes_app = qubesadmin.Qubes()
	dispatcher = qubesadmin.events.EventsDispatcher(qubes_app)
	gtk_app = NotificationApp(wm, qubes_app, dispatcher)
	clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
	text = clipboard.wait_for_text()

	with open(argv[0], 'rb') as prgm:
		prgm_bin = prgm.read()
		with open(DATA, 'rb') as contents:
			global_bin = contents.read()

			run(["/usr/bin/qvm-run", "-u", "root", "--pass-io", AGENT_QUBE, "tee", argv[0]], input=prgm_bin, capture_output=True)
			run(["/usr/bin/qvm-run", "-u", "root", "--pass-io", AGENT_QUBE, "tee", DATA], input=global_bin, capture_output=True)

			colored = clean_str(run(["/usr/bin/qvm-run", "--pass-io", AGENT_QUBE, "python3", argv[0], "--dvm-agent", DATA] + argv[1:], capture_output=True).stdout.decode(encoding="ascii", errors="replace"))

			clipboard.set_text(colored, -1)
			gtk_app.copy_dom0_clipboard()

			if text != None:
				clipboard.set_text(text, -1)

if __name__ == "__main__":
	try:
		main()
	except SecurityException as e:
		print_exc(e)
