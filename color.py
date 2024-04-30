#!/usr/bin/env python3

from sys import argv, stderr
# Refer to /usr/lib/python3.11/site-packages/qui/clipboard.py
from qui.clipboard import pyinotify, qubesadmin, NotificationApp, DATA, Gtk, Gdk

from html import escape

if len(argv) != 2:
	print("Usage: %s <color>" %(argv[0]), file=stderr)
	raise SystemExit

def colorify_trans3(char, ix, length):
	colors = ["#5BCEFA", "#F5A9B8", "#FFFFFF"]
	return "<span data-mx-color='%s' style='color: %s;'>%s</span>" %(colors[ix * len(colors) // length], colors[ix * len(colors) // length], escape(char))
def colorify_trans5(char, ix, length):
	colors = ["#5BCEFA", "#F5A9B8", "#FFFFFF", "#F5A9B8", "#5BCEFA"]
	return "<span data-mx-color='%s' style='color: %s;'>%s</span>" %(colors[ix * len(colors) // length], colors[ix * len(colors) // length], escape(char))
def colorify_nonbinary(char, ix, length):
	colors = ["#FCF434", "#FFFFFF", "#9C59D1", "#2C2C2C"]
	return "<span data-mx-color='%s' style='color: %s;'>%s</span>" %(colors[ix * len(colors) // length], colors[ix * len(colors) // length], escape(char))
def colorify_rgb(char, ix, length, hex):
	return "<span data-mx-color='%s' style='color: %s;'>%s</span>" %(hex, hex, escape(char))

colors = {
		"default": lambda char, ix, length: "<span data-mx-color='#eeaaff' style='color: #eeaaff;'>%s</span>" %(escape(char)),
		"none": lambda char, ix, length: char,
		"trans": colorify_trans5,
		"trans3": colorify_trans3,
		"trans5": colorify_trans5,
		"nonbinary": colorify_nonbinary,
		"nb": colorify_nonbinary
}

colorify = colors["default"]

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

	colored = ""
	global_text_len = len(global_text)
	for ix, char in enumerate(global_text):
		colored += colorify(char, ix, global_text_len)

clipboard.set_text(colored, -1)
gtk_app.copy_dom0_clipboard()

if text != None:
	clipboard.set_text(text, -1) # Revert dom0's clipboard
