#!/usr/bin/env python

# Sozi - A presentation tool using the SVG standard
# 
# Copyright (C) 2010 Guillaume Savaton
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os

# These lines are only needed if you don't put the script directly into
# the installation directory
import sys
# Unix
sys.path.append('/usr/share/inkscape/extensions')
# OS X
sys.path.append('/Applications/Inkscape.app/Contents/Resources/extensions')
# Windows
sys.path.append('C:\Program Files\Inkscape\share\extensions')

# We will use the inkex module with the predefined Effect base class.
import inkex

import pygtk
pygtk.require("2.0")
import gtk

import re

class SoziEditFrame(inkex.Effect):
   VERSION = "{{SOZI_VERSION}}"

   PROFILES = ["linear",
               "accelerate", "strong-accelerate",
               "decelerate", "strong-decelerate",
               "accelerate-decelerate", "strong-accelerate-decelerate",
               "decelerate-accelerate", "strong-decelerate-accelerate"]

   def __init__(self):
      inkex.Effect.__init__(self)
      inkex.NSS[u"sozi"] = u"http://sozi.baierouge.fr"

      self.element = None
      self.all_frame_elements = []
      self.frame_element = None
      self.fields = {}


   def effect(self):
      # Check script version
      version = None
      for elt in self.document.xpath("//svg:script[@id='sozi-script']", namespaces=inkex.NSS):
         version = elt.get("{" + inkex.NSS["sozi"] + "}version")
      
      if version == None:
         sys.stderr.write("The presentation script is not installed in this document.\n")
         exit()

      if version < SoziEditFrame.VERSION:
         sys.stderr.write("Please upgrade the presentation script installed in this document.\n")
         exit()

      # Get selected element
      for id, elt in self.selected.items():
         if self.element == None:
            self.element = elt
         else:
            sys.stderr.write("More than one element selected. Please select only one element.\n")
            exit()

      if self.element == None:
         sys.stderr.write("No element selected.\n")
         exit()

      # Get a sorted list of all frame elements 
      self.all_frame_elements = self.document.xpath("//sozi:frame", namespaces=inkex.NSS)
      self.all_frame_elements = sorted(self.all_frame_elements, key=lambda elt:
         int(elt.attrib["{" + inkex.NSS["sozi"] + "}sequence"]) if elt.attrib.has_key("{" + inkex.NSS["sozi"] + "}sequence") else len(self.all_frame_elements))

      # Find frame element for the selected element
      for elt in self.all_frame_elements:
         if elt.attrib["{" + inkex.NSS["sozi"] + "}refid"] == self.element.attrib["id"]: # TODO check namespace?
            self.frame_element = elt
            break

      # If no frame element exists, create a new one
      if self.frame_element == None:
         self.frame_element = inkex.etree.Element(inkex.addNS("frame", "sozi"))
         self.frame_element.set("{" + inkex.NSS["sozi"] + "}refid", self.element.attrib["id"]) # TODO check namespace?
         self.document.getroot().append(self.frame_element)

      self.show_form()


   def create_text_field(self, attr, label, value):
      if self.frame_element.attrib.has_key("{" + inkex.NSS["sozi"] + "}" + attr):
         value = self.frame_element.attrib["{" + inkex.NSS["sozi"] + "}" + attr]

      lbl = gtk.Label(label)

      entry = gtk.Entry()
      entry.set_text(value)

      hbox = gtk.HBox()
      hbox.add(lbl)
      hbox.add(entry)

      self.fields[attr] = entry
      return hbox

      
   def create_combo_field(self, attr, label, items, index):
      if self.frame_element.attrib.has_key("{" + inkex.NSS["sozi"] + "}" + attr):
         text = self.frame_element.attrib["{" + inkex.NSS["sozi"] + "}" + attr]
         if items.count(text) > 0:
            index = items.index(text)

      lbl = gtk.Label(label)

      combo = gtk.combo_box_new_text()
      for text in items:
         combo.append_text(text)
      combo.set_active(index)

      hbox = gtk.HBox()
      hbox.add(lbl)
      hbox.add(combo)

      self.fields[attr] = combo 
      return hbox

      
   def create_checked_spinbutton_field(self, enable_attr, value_attr, label, enable, value):
      if self.frame_element.attrib.has_key("{" + inkex.NSS["sozi"] + "}" + enable_attr):
         enable = self.frame_element.attrib["{" + inkex.NSS["sozi"] + "}" + enable_attr]
      if self.frame_element.attrib.has_key("{" + inkex.NSS["sozi"] + "}" + value_attr):
         value = int(self.frame_element.attrib["{" + inkex.NSS["sozi"] + "}" + value_attr])

      button = gtk.CheckButton(label)
      button.set_active(enable == "true")

      spin = gtk.SpinButton(digits=0)
      spin.set_range(0, 1000000)
      spin.set_increments(1, 1)
      spin.set_numeric(True)
      spin.set_value(value)

      hbox = gtk.HBox()
      hbox.pack_start(button)
      hbox.pack_start(spin)

      self.fields[enable_attr] = button
      self.fields[value_attr] = spin
      return hbox


   def create_checkbox_field(self, attr, label, value):
      if self.frame_element.attrib.has_key("{" + inkex.NSS["sozi"] + "}" + attr):
         value = self.frame_element.attrib["{" + inkex.NSS["sozi"] + "}" + attr]

      button = gtk.CheckButton(label)
      button.set_active(value == "true")

      self.fields[attr] = button
      return button


   def create_spinbutton_field(self, attr, label, value, minValue = 0, maxValue = 1000000):
      if self.frame_element.attrib.has_key("{" + inkex.NSS["sozi"] + "}" + attr):
         value = int(self.frame_element.attrib["{" + inkex.NSS["sozi"] + "}" + attr])
      
      lbl = gtk.Label(label)

      spin = gtk.SpinButton(digits=0)
      spin.set_range(minValue, maxValue)
      spin.set_increments(1, 1)
      spin.set_numeric(True)
      spin.set_value(value)

      hbox = gtk.HBox()
      hbox.pack_start(lbl)
      hbox.pack_start(spin)

      self.fields[attr] = spin
      return hbox


   def show_form(self):
      window = gtk.Window(gtk.WINDOW_TOPLEVEL)
      window.connect("destroy", self.destroy)

      # Rectangles are configured to be hidden by default.
      # Other elements are configured to be visible.
      if self.element.tag == "rect" or self.element.tag == "{" + inkex.NSS["svg"] + "}rect":
         default_hide = "true"
      else:
         default_hide = "false"

      # Create form for the selected element
      # TODO click in frame list to change sequence
      # TODO change frame list when title field is changed
      title_field = self.create_text_field("title", "Title:", "New frame")
      sequence_field = self.create_spinbutton_field("sequence", "Sequence:", 1)
      hide_field = self.create_checkbox_field("hide", "Hide", default_hide)
      clip_field = self.create_checkbox_field("clip", "Clip", "true")
      timeout_field = self.create_checked_spinbutton_field("timeout-enable", "timeout-ms", "Timeout (ms):", "false", 5000)
      transition_duration_field = self.create_spinbutton_field("transition-duration-ms", "Duration (ms):", 1000)
      transition_zoom_field = self.create_spinbutton_field("transition-zoom-percent", "Zoom (%):", 0, -100, 100)
      transition_profile_field = self.create_combo_field("transition-profile", "Profile:", SoziEditFrame.PROFILES, 0)

      # Create "Done" and "Cancel" buttons
      done_button = gtk.Button("Done")
      done_button.connect("clicked", self.done)
      done_button.connect_object("clicked", gtk.Widget.destroy, window)

      cancel_button = gtk.Button("Cancel")
      cancel_button.connect_object("clicked", gtk.Widget.destroy, window)

      buttons_box = gtk.HBox()
      buttons_box.pack_start(done_button)
      buttons_box.pack_start(cancel_button)

      # Create frame list

      frame_index = len(self.all_frame_elements)
      list_store = gtk.ListStore(str)
      for index, elt in enumerate(self.all_frame_elements):
         if elt == self.frame_element:
            frame_index = index

         if elt.attrib.has_key("{" + inkex.NSS["sozi"] + "}title"):
            title = elt.attrib["{" + inkex.NSS["sozi"] + "}title"]
         else:
            title = "Untitled"

         list_store.append([str(index+1) + ". " + title])

      if frame_index < len(self.all_frame_elements):
         self.fields["sequence"].set_range(1, len(self.all_frame_elements))
      else:
         self.fields["sequence"].set_range(1, len(self.all_frame_elements) + 1)
      self.fields["sequence"].set_value(frame_index + 1)

      list_renderer = gtk.CellRendererText()
      list_column = gtk.TreeViewColumn("Sequence", list_renderer, text = 0)

      list_view = gtk.TreeView(list_store)
      list_view.append_column(list_column)

      if frame_index < len(self.all_frame_elements):
         list_view.get_selection().select_path(frame_index)

      list_scroll = gtk.ScrolledWindow()
      list_scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)	
      list_scroll.add(list_view)

      # Transition properties
      transition_box = gtk.VBox()
      transition_box.pack_start(transition_duration_field, expand=False)
      transition_box.pack_start(transition_zoom_field, expand=False)
      transition_box.pack_start(transition_profile_field, expand=False)

      transition_group = gtk.Frame("Transition")
      transition_group.add(transition_box)

      # Frame properties
      frame_box = gtk.VBox()
      frame_box.pack_start(title_field, expand=False)
      frame_box.pack_start(sequence_field, expand=False)
      frame_box.pack_start(hide_field, expand=False)
      frame_box.pack_start(clip_field, expand=False)
      frame_box.pack_start(timeout_field, expand=False)

      frame_group = gtk.Frame("Frame")
      frame_group.add(frame_box)

      # Fill left pane
      left_pane = gtk.VBox()
      left_pane.pack_start(transition_group, expand=False)
      left_pane.pack_start(frame_group, expand=False)
      left_pane.pack_start(buttons_box, expand=False)

      hbox = gtk.HBox()
      hbox.pack_start(left_pane)
      hbox.pack_start(list_scroll)

      window.add(hbox)
      window.show_all()

      gtk.main()


   def done(self, widget):
      # Update frame attributes using form data
      self.frame_element.set("{" + inkex.NSS["sozi"] + "}title", unicode(self.fields["title"].get_text()))
      self.frame_element.set("{" + inkex.NSS["sozi"] + "}sequence", unicode(self.fields["sequence"].get_value_as_int()))
      self.frame_element.set("{" + inkex.NSS["sozi"] + "}hide", unicode("true" if self.fields["hide"].get_active() else "false"))
      self.frame_element.set("{" + inkex.NSS["sozi"] + "}clip", unicode("true" if self.fields["clip"].get_active() else "false"))
      self.frame_element.set("{" + inkex.NSS["sozi"] + "}timeout-enable", unicode("true" if self.fields["timeout-enable"].get_active() else "false"))
      self.frame_element.set("{" + inkex.NSS["sozi"] + "}timeout-ms", unicode(self.fields["timeout-ms"].get_value_as_int()))
      self.frame_element.set("{" + inkex.NSS["sozi"] + "}transition-duration-ms", unicode(self.fields["transition-duration-ms"].get_value_as_int()))
      self.frame_element.set("{" + inkex.NSS["sozi"] + "}transition-zoom-percent", unicode(self.fields["transition-zoom-percent"].get_value_as_int()))
      self.frame_element.set("{" + inkex.NSS["sozi"] + "}transition-profile", unicode(SoziEditFrame.PROFILES[self.fields["transition-profile"].get_active()]))

      # TODO remove frames with non-existent ref element

      # Renumber frames
      sequence = int(self.frame_element.attrib["{" + inkex.NSS["sozi"] + "}sequence"])
      index = 1
      for elt in self.all_frame_elements:
         if index == sequence:
            index += 1
         if elt != self.frame_element:
            elt.set("{" + inkex.NSS["sozi"] + "}sequence", str(index))
            index += 1


   def destroy(self, widget, data=None):
      gtk.main_quit()


# Create effect instance
effect = SoziEditFrame()
effect.affect()

