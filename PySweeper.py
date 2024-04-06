################################################################################
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <https://www.gnu.org/licenses/>.
#
################################################################################

APPLICATION_NAME = "PySweeper"
APPLICATION_VERSION = "1.0.0.0"

import random
import os
import copy
import math

from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *

################################################################################

SKILL_LEVEL_BEGINNER = 8
SKILL_LEVEL_INTERMEDIATE = 16
SKILL_LEVEL_EXPERT = 32

MODE_NONE = 0
MODE_SELECT = 1
MODE_CHORD = 2

################################################################################

class Tile:
    def __init__(self):
        # Bit 0: uncovered
        # Bit 1: mined
        # Bit 2: flagged
        # Bit 3: marked (?)
        # Bit 4: exploded
        # Bits 8-11: mine count (number of neighbouring mines)
        self._data = 0x00
    
    def uncover(self):
        self._data |= 0x01
    
    def uncovered(self):
        return bool(self._data & 0x01)

    def covered(self):
        return not self.uncovered()

    def mine(self):
        self._data |= 0x02

    def mined(self):
        return self._data & 0x02

    def flag(self):
        self._data |= 0x04
        self.unmark()

    def unflag(self):
        self._data &= ~0x04

    def flagged(self):
        return self._data & 0x04

    def mark(self):
        self._data |= 0x08
        self.unflag()

    def unmark(self):
        self._data &= ~0x08
        
    def marked(self):
        return self._data & 0x08

    def explode(self):
        self._data |= 0x10

    def exploded(self):
        return self._data & 0x10
    
    def set_mine_count(self, n):
        self._data = (n << 8) | (self._data & 0xff)
        
    def mine_count(self):
        return self._data >> 8

    def reset(self):
        self._data = 0x00
        
class Board:
    def __init__(self):
        self._tiles = []
        self._mine_count = 10
        self.set_size(8, 8)

    def set_size(self, width, height):
        self._tiles.clear()
        for y in range(height):
            row = []
            for x in range(width):
                row.append(Tile())
            self._tiles.append(row)

    def set_mine_count(self, mine_count):
        self._mine_count = mine_count
        
    def clear(self):
        for y in range(self.height()):
            for x in range(self.width()):
                self._tiles[y][x].reset()

    def add_mines(self, exclude_x, exclude_y):
        
        def is_mine(tiles, x, y):
            if x >= 0 and x < len(tiles[0]) and \
               y >= 0 and y < len(tiles):
                if tiles[y][x].mined():
                    return 1
            return 0

        # ------- Add mines -------
        n = self._mine_count
        while n > 0:
            x = random.randint(0, self.width() - 1)
            y = random.randint(0, self.height() - 1)
            # exclude_x and exclude_y are the coords of
            # the tile the user clicked on the first time.
            if not self._tiles[y][x].mined() and \
               x != exclude_x and y != exclude_y:
                self._tiles[y][x].mine()
                n -= 1
        # ------- Update cell mine count -------
        for y in range(self.height()):
            for x in range(self.width()):
                n = 0
                n += is_mine(self._tiles, x - 1, y - 1)
                n += is_mine(self._tiles, x    , y - 1)
                n += is_mine(self._tiles, x + 1, y - 1)
                n += is_mine(self._tiles, x - 1, y    )
                n += is_mine(self._tiles, x + 1, y    )
                n += is_mine(self._tiles, x - 1, y + 1)
                n += is_mine(self._tiles, x    , y + 1)
                n += is_mine(self._tiles, x + 1, y + 1)
                self._tiles[y][x].set_mine_count(n)

    def mine_count(self):
        return self._mine_count

    def width(self):
        return len(self._tiles[0])
        
    def height(self):
        return len(self._tiles)
        
    def at(self, x, y):
        return self._tiles[y][x]

    def is_valid_position(self, x, y):
        return x >= 0 and x < self.width() and y >= 0 and y < self.height()

    def game_over(self):
        for y in range(self.height()):
            for x in range(self.width()):
                tile = self._tiles[y][x]
                if tile.exploded():
                    return True
        for y in range(self.height()):
            for x in range(self.width()):
                tile = self._tiles[y][x]
                if tile.covered() and not (tile.flagged() and tile.mined()):
                    return False
        return True
    
    def uncover(self, x, y):
        if self.is_valid_position(x, y):
            tile = self._tiles[y][x]
            if tile.covered():
                if not tile.flagged():
                    tile.uncover()
                    if tile.mine_count() == 0 and \
                        not tile.mined():
                        self.uncover(x - 1, y - 1)
                        self.uncover(x - 0, y - 1)
                        self.uncover(x + 1, y - 1)
                        self.uncover(x - 1, y - 0)
                        self.uncover(x + 1, y - 0)
                        self.uncover(x - 1, y + 1)
                        self.uncover(x - 0, y + 1)
                        self.uncover(x + 1, y + 1)

    def neighbours(self, x, y):

        def add(self, tiles, x, y):
            if self.is_valid_position(x, y):
                tiles.append(self._tiles[y][x])

        tiles = []
        add(self, tiles, x - 1, y - 1)
        add(self, tiles, x - 0, y - 1)
        add(self, tiles, x + 1, y - 1)
        add(self, tiles, x - 1, y - 0)
        add(self, tiles, x + 1, y - 0)
        add(self, tiles, x - 1, y + 1)
        add(self, tiles, x - 0, y + 1)
        add(self, tiles, x + 1, y + 1)
        return tiles
    
################################################################################

class MinesweeperWidget(QWidget):

    def __init__(self):
        super().__init__()
        self._grid_x = 0
        self._grid_y = 0
        self._tile_size = 0
        self._border_width = 1
        # Enable mouse move events without buttons pressed.
        self.setMouseTracking(True)
        self._board = Board()  
        self.recalc_layout()
        self.timer_id = 0
        self.setStyleSheet("font-family: times new roman")
        self._selected_tile = (-1, -1)
        self._marks = False
        self._color = True
        self._initialized = False
        self._mode = MODE_NONE
        self._mine_count_colors = (
            QColorConstants.Svg.black,
            QColorConstants.Svg.lightblue,
            QColorConstants.Svg.green,
            QColorConstants.Svg.red,
            QColorConstants.Svg.darkblue,
            QColorConstants.Svg.brown,
            QColorConstants.Svg.aqua,
            QColorConstants.Svg.black,
            QColorConstants.Svg.lightgray
            )
        # ------- Events -------
        self.on_game_start = None
        self.on_game_end = None
        self.on_flags_change = None
        
    def set_skill_level(self, level):
        if level == SKILL_LEVEL_BEGINNER:
            self._board.set_size(level, level)
            self._board.set_mine_count(10)
        elif level == SKILL_LEVEL_INTERMEDIATE:
            self._board.set_size(level, level)
            self._board.set_mine_count(40)
        elif level == SKILL_LEVEL_EXPERT:
            self._board.set_size(level, 16)
            self._board.set_mine_count(99)
        self.recalc_layout()
        self.repaint()

    def skill_level(self):
        return self._board.width()
    
    def set_mine_count(self, mine_count):
        self._board.set_mine_count(mine_count)

    def mine_count(self):
        return self._board.mine_count()
    
    def mine_count_color(self, i):
        return self._mine_count_colors[(i + 1) if self._color else 0] 

    def set_marks(self, flag):
        self._marks = flag

    def marks(self):
        return self._marks

    def set_color(self, flag):
        self._color = flag

    def color(self):
        return self._color

    def game_over(self):
        return self._board.game_over()

    def clear(self):
        self._initialized = False
        self._board.clear()
        self.repaint() 
        
    def recalc_layout(self):
        w = self.width() - (self._board.width() + 1) * self._border_width - \
                2 * round(self.fontMetrics().height())
        self._tile_size = w // self._board.width()
        h = self.height() - (self._board.height() + 1) * self._border_width - \
                2 * round(self.fontMetrics().height())
        if self._tile_size * self._board.height() > h:
            self._tile_size = h // self._board.height()
        self._grid_x = (self.width() - self._board.width() * (self._tile_size + \
                          self._border_width) - self._border_width) // 2
        self._grid_y = (self.height() - self._board.height() * (self._tile_size + \
                          self._border_width) - self._border_width) // 2
    
    def get_tile_rect(self, x, y):
        x = self._grid_x + (1 + x) * self._border_width + x * self._tile_size
        y = self._grid_y + (1 + y) * self._border_width + y * self._tile_size
        w = self._tile_size
        h = self._tile_size
        return QRect(x, y, w, h)
        
    def resizeEvent(self, event):
        self.recalc_layout()
        QWidget.resizeEvent(self, event)

    def draw_grid(self, qpainter):
        qpainter.save()
        pen = QPen()
        pen.setStyle(Qt.PenStyle.NoPen)
        qpainter.setPen(pen)
        qpainter.setBrush(QColorConstants.Black)
        # Vertical lines.
        w = self._board.width()
        h = self._board.height()
        for i in range(w + 1):
            r = QRect(self._grid_x + i * (self._tile_size + self._border_width),
                      self._grid_y,
                      self._border_width,
                      h * self._tile_size + (h + 1) * self._border_width)
            qpainter.drawRect(r)
        # Horizontal lines.
        for i in range(h + 1):
            r = QRect(self._grid_x + self._border_width,
                      self._grid_y + i * (self._tile_size + self._border_width),
                      w * (self._tile_size + self._border_width),
                      self._border_width)
            qpainter.drawRect(r)
        qpainter.restore()

    def draw_mine(self, qpainter, rect, draw_background, draw_cross_mark):
        # ------- Background -------
        if draw_background:
            if self._color:
                qpainter.setPen(Qt.PenStyle.NoPen)
                qpainter.setBrush(QColorConstants.Red)
                qpainter.drawRect(rect)
            else:            
                qpainter.setPen(Qt.PenStyle.NoPen)
                qpainter.setBrush(QBrush(QColorConstants.Black, style=Qt.BrushStyle.BDiagPattern))
                qpainter.drawRect(rect)
        # ------- Mine -------
        pen = QPen()        
        qpainter.setBrush(QColorConstants.Black)
        center = QPointF(round(rect.x() + rect.width() / 2), round(rect.y() + rect.height() / 2))
        # ---- Big Protuberances ----
        pen.setWidth(int(rect.width() * 0.1))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        qpainter.setPen(pen)
        t = round(rect.width() * 0.35)
        p1 = QPointF(center.x(), center.y() - t)
        p2 = QPointF(center.x(), center.y() + t)
        qpainter.drawLine(p1, p2)
        p1 = QPointF(center.x() - t, center.y())
        p2 = QPointF(center.x() + t, center.y())       
        qpainter.drawLine(p1, p2)
        # ---- Small Protuberances ----
        pen.setWidth(int(rect.width() * 0.075))
        qpainter.setPen(pen)
        t = round(rect.width() * 0.25)
        p1 = QPointF(center.x() - t, center.y() - t)
        p2 = QPointF(center.x() + t, center.y() + t)
        qpainter.drawLine(p1, p2)
        p1 = QPointF(center.x() + t, center.y() - t)
        p2 = QPointF(center.x() - t, center.y() + t)       
        qpainter.drawLine(p1, p2)
        # ---- Shell ----
        pen.setStyle(Qt.PenStyle.NoPen)
        qpainter.setPen(pen)
        rx = round(rect.width() * 0.3)
        ry = round(rect.height() * 0.3)
        qpainter.drawEllipse(center, rx, ry)
        # ---- Reflection ----
        pen.setStyle(Qt.PenStyle.NoPen)
        qpainter.setPen(pen)
        qpainter.setBrush(QColorConstants.White)
        center.setX(round(center.x() - rect.width() * 0.125))
        center.setY(round(center.y() - rect.height() * 0.13))
        rx = round(rect.width() * 0.05)
        ry = round(rect.height() * 0.05)
        qpainter.drawEllipse(center, rx, ry)
        # ------- Cross Mark -------
        if draw_cross_mark:
            pen.setStyle(Qt.PenStyle.SolidLine)
            pen.setColor(QColorConstants.Red if self._color else QColorConstants.Black)
            pen.setWidth(round(rect.width() * 0.05))
            qpainter.setPen(pen)
            qpainter.setClipRect(rect)
            qpainter.drawLine(rect.topLeft(), rect.bottomRight())
            qpainter.drawLine(rect.topRight(), rect.bottomLeft())
            qpainter.setClipping(False)
        
    def draw_flag(self, qpainter, rect):
        pen = QPen()
        pen.setStyle(Qt.PenStyle.NoPen)
        qpainter.setPen(pen)
        # ------- Flag -------
        qpainter.setBrush(QColorConstants.Red if self._color else QColorConstants.Black)
        p1 = QPointF(rect.x() + 0.39 * rect.width(), rect.y() + 0.18 * rect.height())
        p2 = QPointF(p1.x() + 0.37 * rect.width(), p1.y() + 0.20 * rect.height())
        p3 = QPointF(p1.x(), p1.y() + 0.40 * rect.height())
        qpainter.drawConvexPolygon(QPolygonF((p1, p2, p3)))
        # ------- Pole -------
        pen.setWidth(int(rect.width() * 0.04))
        pen.setStyle(Qt.PenStyle.SolidLine)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p3.setY(p1.y() + 0.63 * rect.height())
        qpainter.setPen(pen)
        qpainter.setBrush(QColorConstants.Black)
        qpainter.drawLine(p1, p3)
        # Create a new pen because calling setCapStyle() again doesn't seem to work.
        pen = QPen(pen.width())
        pen.setCapStyle(Qt.PenCapStyle.SquareCap)
        qpainter.setPen(pen)
        r = QRectF(p3.x() - 0.13 * rect.width(), p3.y(), 0.13 * rect.width() * 2, 0.04 * rect.height())
        qpainter.drawRect(r)

    def draw_tile_background(self, qpainter, tile, x, y, rect):

        def in_chord_range(x, y, sx, sy):
            return (x == sx and y == sy) or (int(math.sqrt((sx - x) ** 2 + (sy - y) ** 2)) == 1)

        qpainter.setPen(Qt.PenStyle.NoPen)
        if tile.covered():
            if self._selected_tile == (-1, -1):
                qpainter.setBrush(QPalette().dark())
            else:
                if (self._mode == MODE_SELECT and self._selected_tile == (x, y)) or \
                   (self._mode == MODE_CHORD and in_chord_range(x, y, self._selected_tile[0], \
                                                                      self._selected_tile[1])):
                    qpainter.setBrush(QPalette().light())
                else:
                    qpainter.setBrush(QPalette().dark())
        else:
            qpainter.setBrush(QPalette().light())
        qpainter.drawRect(rect)
            
    def draw_tiles(self, qpainter):
        qpainter.save()
        qpainter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform|QPainter.RenderHint.Antialiasing)
        # ------- Determine font height in pixels -------
        tile_rect = self.get_tile_rect(0, 0)
        font = qpainter.font()
        font.setPixelSize(int(tile_rect.height() * 0.75))
        qpainter.setFont(font)
        # ------- Draw tiles -------
        for y in range(self._board.height()):
            for x in range(self._board.width()):
                tile = self._board.at(x, y)
                rect = self.get_tile_rect(x, y)
                self.draw_tile_background(qpainter, tile, x, y, rect)
                if tile.covered():
                    if self.game_over():
                        if tile.exploded():
                            self.draw_mine(qpainter, rect, True, False)
                        elif tile.flagged():
                            if tile.mined():
                                self.draw_flag(qpainter, rect)
                            else:
                                self.draw_mine(qpainter, rect, False, True)
                        elif tile.mined():
                            self.draw_mine(qpainter, rect, False, False)
                    else:
                        if tile.flagged():
                            self.draw_flag(qpainter, rect)
                        elif tile.marked():
                            qpainter.setPen(Qt.PenStyle.SolidLine)
                            qpainter.setBrush(QColorConstants.Black)
                            qpainter.drawText(rect, Qt.AlignmentFlag.AlignCenter, '?')
                else:
                    if tile.mine_count() > 0 and tile.mine_count() <= 8:
                        pen = QPen()
                        pen.setStyle(Qt.PenStyle.SolidLine)
                        pen.setColor(self.mine_count_color(tile.mine_count()))
                        qpainter.setPen(pen)
                        qpainter.setBrush(self.mine_count_color(tile.mine_count()))
                        qpainter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(tile.mine_count()))
        qpainter.restore()
        
    def paintEvent(self, event):
        qpainter = QPainter(self)
        # Screen scaling makes drawing fine lines ugly.
        #self.draw_grid(qpainter)
        self.draw_tiles(qpainter)
        
    def get_tile_at(self, posx, posy):
        for y in range(self._board.height()):
            for x in range(self._board.width()):
                if self.get_tile_rect(x, y).contains(posx, posy, False):
                    return x, y
        return -1, -1
    
    def mousePressEvent(self, event):
        if self.game_over():
            return
        x = int(event.position().x())
        y = int(event.position().y())
        tx, ty = self.get_tile_at(x, y)
        if (tx, ty) == (-1, -1):
            return
        tile = self._board.at(tx, ty)
        buttons = event.buttons()
        if buttons & Qt.MouseButton.LeftButton and \
           buttons & Qt.MouseButton.RightButton:
            self._mode = MODE_CHORD
        elif event.button() == Qt.MouseButton.LeftButton:
            self._mode = MODE_SELECT
            self._selected_tile = (tx, ty)
        elif event.button() == Qt.MouseButton.RightButton:
            if not tile.flagged():
                if not tile.marked():
                    tile.flag()
                    if self.on_flags_change:
                        self.on_flags_change(+1)
                    if self.game_over():
                        self.end_game(tx, ty)
                else:
                    tile.unmark()
            else:
                tile.unflag()
                if self.on_flags_change:
                    self.on_flags_change(-1)
                if self.marks():
                    tile.mark()
        self.repaint()
        
    def mouseMoveEvent(self, event):
        if not self.game_over():
            if self._mode != MODE_NONE:
                x = int(event.position().x())
                y = int(event.position().y())
                tile = self.get_tile_at(x, y)
                if tile != (-1, -1):
                    self._selected_tile = tile
                self.repaint()
  
    def mouseReleaseEvent(self, event):
        x = int(event.position().x())
        y = int(event.position().y())
        if not self.game_over():
            if self._selected_tile != (-1, -1):
                tx, ty = self._selected_tile
                tile = self._board.at(tx, ty)
                if self._mode == MODE_SELECT:
                    # Add mines to board on first click so that
                    # user never hits a mine on first click.
                    if not self._initialized:
                        self._board.add_mines(tx, ty)
                        if self.on_game_start:
                            self.on_game_start()
                        self._initialized = True
                    if tile.mined():
                        tile.explode()
                        self.repaint()
                        self.end_game(True)
                    else:
                        self._board.uncover(tx, ty)
                        self.repaint()
                        if self.game_over():
                            self.end_game(False)
                elif self._mode == MODE_CHORD:
                    if tile.mine_count() > 0:
                        neighbours = self._board.neighbours(tx, ty)
                        flag_count = sum(1 for item in neighbours if item.flagged())
                        if flag_count == tile.mine_count():
                            # Test only if flag count matches mine count.
                            mismatch_found = False
                            for neighbour in neighbours:
                                if neighbour.mined() and not neighbour.flagged():
                                    # Make sure _board.game_over() works.
                                    neighbour.explode()
                                    mismatch_found = True
                                elif not neighbour.mined() and not neighbour.flagged():
                                    neighbour.uncover()
                            if mismatch_found:
                                self.end_game(True)
        self._selected_tile = (-1, -1)
        self._mode = MODE_NONE
        self.repaint()
                               
    def end_game(self, hit_mine):
        if self.on_game_end:
            self.on_game_end(hit_mine)
            
################################################################################

class BestTimesDialog(QDialog):
    
    def __init__(self):
        super().__init__()
        # ------- Dialog Stuff -------
        self.setWindowTitle("Fastest Mine Sweepers")
        # ------- Labels -------
        self._beginner_time_label = QLabel()
        self._beginner_name_label = QLabel()
        self._intermediate_time_label = QLabel()
        self._intermediate_name_label = QLabel()
        self._expert_time_label = QLabel()
        self._expert_name_label = QLabel()
        grid = QGridLayout()
        grid.addWidget(QLabel("Beginner:"), 0, 0)
        grid.addWidget(QLabel("Intermediate:"), 1, 0)
        grid.addWidget(QLabel("Expert:"), 2, 0)
        grid.addWidget(self._beginner_time_label, 0, 1)
        grid.addWidget(self._intermediate_time_label, 1, 1)
        grid.addWidget(self._expert_time_label, 2, 1)
        grid.addWidget(self._beginner_name_label, 0, 2)
        grid.addWidget(self._intermediate_name_label, 1, 2)
        grid.addWidget(self._expert_name_label, 2, 2)
        # ------- Buttons -------
        hbox = QHBoxLayout()
        reset_scores_button = QPushButton("&Reset Scores")
        reset_scores_button.clicked.connect(self.on_reset_scores)
        hbox.addWidget(reset_scores_button)
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        ok_button.setDefault(True)
        hbox.addWidget(ok_button)
        grid.addLayout(hbox, 3, 0, 1, 3, Qt.AlignmentFlag.AlignRight)
        grid.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.setLayout(grid)
        self.load()
        
    def load(self):

        def fmt(s):
            return f"       {s}"
        
        settings = QSettings(APPLICATION_NAME, APPLICATION_NAME)
        self._beginner_time_label.setText(fmt(settings.value("beginner_time", "9999999")))
        self._beginner_name_label.setText(fmt(settings.value("beginner_name", "Anonymous")))
        self._intermediate_time_label.setText(fmt(settings.value("intermediate_time", "9999999")))
        self._intermediate_name_label.setText(fmt(settings.value("intermediate_name", "Anonymous")))
        self._expert_time_label.setText(fmt(settings.value("expert_time", "9999999")))
        self._expert_name_label.setText(fmt(settings.value("expert_name", "Anonymous")))

    def on_reset_scores(self):
        settings = QSettings(APPLICATION_NAME, APPLICATION_NAME)
        settings.setValue("beginner_time", "9999999")
        settings.setValue("beginner_name", "Anonymous")
        settings.setValue("intermediate_time", "9999999")
        settings.setValue("intermediate_name", "Anonymous")
        settings.setValue("expert_time", "9999999")
        settings.setValue("expert_name", "Anonymous")
        self.load()

################################################################################

class NewBestTimeDialog(QDialog):
    
    def __init__(self, skill_level_string):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.CustomizeWindowHint |
            Qt.WindowType.WindowTitleHint
            )
        self.setWindowTitle(APPLICATION_NAME)
        text = f"You have the fastest time for {skill_level_string} level.\n" \
                "Please type your name."
        # ------- VBox -------
        vbox = QVBoxLayout()
        vbox.setAlignment(Qt.AlignmentFlag.AlignTop)
        # ---- Label ----
        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(label)
        # ---- Input Box ----
        self._line_edit = QLineEdit()
        self._line_edit.setText("Anonymous")
        self._line_edit.selectAll()
        vbox.addWidget(self._line_edit)
        # ---- OK Button ----
        hbox = QHBoxLayout()
        hbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        ok_button.setDefault(True)
        hbox.addWidget(ok_button)
        vbox.addLayout(hbox)
        vbox.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.setLayout(vbox)

    def text(self):
        return self._line_edit.text()

    def reject(self):
        # Prevent dialog from closing using the escape key.
        pass
        
################################################################################

class MainWindow(QMainWindow):
    
    def __init__(self):
        super().__init__()
        self._minesweeper_widget = MinesweeperWidget()
        self._timer_id = None
        self._time_elapsed = 0
        self._mines_left = self._minesweeper_widget.mine_count()
        self.setStyleSheet("font-size: 10pt;")
        self.init_ui()
        self.load_settings()    # Must be called after init_ui().
        self.setWindowTitle(APPLICATION_NAME)
        self.setWindowIcon(QIcon("PySweeper.ico"))
        self.show()

    def init_ui(self):
        self._minesweeper_widget.on_game_start = self.on_game_start
        self._minesweeper_widget.on_game_end = self.on_game_end
        self._minesweeper_widget.on_flags_change = self.on_flags_change
        self.setCentralWidget(self._minesweeper_widget)
        menu_bar = self.menuBar()
        # ------- Game Menu -------
        game_menu = menu_bar.addMenu("&Game")
        #game_menu.aboutToShow.connect(self.game_menu_about_to_show)
        menu_item = QAction("&New", self)
        menu_item.setShortcut(QKeySequence(Qt.Key.Key_F2))
        menu_item.triggered.connect(self.on_game_new)
        game_menu.addAction(menu_item)
        game_menu.addSeparator()
        # ---- Skill Level ----
        self._skill_level_action_group = QActionGroup(self)
        self._skill_level_action_group.triggered.connect(self.on_game_skill_level)
        # Beginner
        menu_item = self._skill_level_action_group.addAction("&Beginner")
        menu_item.setCheckable(True)
        menu_item.setChecked(True)
        menu_item.setData(SKILL_LEVEL_BEGINNER)
        game_menu.addAction(menu_item)
        # Intermediate
        menu_item = self._skill_level_action_group.addAction("&Intermediate")
        menu_item.setCheckable(True)
        menu_item.setData(SKILL_LEVEL_INTERMEDIATE)
        game_menu.addAction(menu_item)
        # Expert
        menu_item = self._skill_level_action_group.addAction("&Expert")
        menu_item.setCheckable(True)
        menu_item.setData(SKILL_LEVEL_EXPERT)
        game_menu.addAction(menu_item)
        game_menu.addSeparator()
        # ---- Marks and Color ----
        self._marks_action = QAction("&Marks (?)", self)
        self._marks_action.setCheckable(True)
        self._marks_action.triggered.connect(self.on_game_marks)
        game_menu.addAction(self._marks_action)
        self._color_action = QAction("Co&lor", self)
        self._color_action.setCheckable(True)
        self._color_action.setChecked(True)
        self._color_action.triggered.connect(self.on_game_color)
        game_menu.addAction(self._color_action)
        # ---- Best Times ----
        game_menu.addSeparator()
        menu_item = QAction("Best &Times...", self)
        menu_item.triggered.connect(self.on_game_best_times)
        game_menu.addAction(menu_item)
        game_menu.addSeparator()
        # ---- Exit ----
        menu_item = QAction("E&xit", self)
        menu_item.triggered.connect(self.close)
        game_menu.addAction(menu_item)
        # ------- Help Menu -------
        help_menu = menu_bar.addMenu("&Help")
        menu_item = QAction("&About...", self)
        menu_item.triggered.connect(self.on_help_about)
        help_menu.addAction(menu_item)
        # ------- Status Bar -------
        self._mines_label = QLabel()
        self._time_label = QLabel()
        self.statusBar().addPermanentWidget(QLabel())
        self.statusBar().addPermanentWidget(self._mines_label)
        self.statusBar().addPermanentWidget(self._time_label)
        self.update_status_bar()

    def update_status_bar(self):
        self._mines_label.setText(f" Mines: {self._mines_left} ")
        self._time_label.setText(f" Time: {self._time_elapsed} ")

##    def game_menu_about_to_show(self):
##        self.beginner_action.setChecked(True)
##        self.pass_action.setEnabled(len(self.minesweeper_widget.valid_moves) == 0) 

    def start_timer(self):
        if self._timer_id != None:
            self.killTimer(self._timer_id)
        self._timer_id = self.startTimer(1000)
        
    def stop_timer(self):
        if self._timer_id != None:
            self.killTimer(self._timer_id)
            self._timer_id = None
        
    def new_game(self):
        # Mines will be added on first click.
        self._minesweeper_widget.clear()
        self._mines_left = self._minesweeper_widget.mine_count()
        self._time_elapsed = 0
        self.stop_timer()
        self.update_status_bar()
        
    def on_game_new(self, s):
        self.new_game()
        
    def on_game_skill_level(self, action):
        self._minesweeper_widget.set_skill_level(action.data())
        self.new_game()
        
    def on_game_marks(self, s):
        self._minesweeper_widget.set_marks(self._marks_action.isChecked())
        
    def on_game_color(self, s):
        self._minesweeper_widget.set_color(self._color_action.isChecked())
        self._minesweeper_widget.repaint()
        
    def on_game_best_times(self, s):
        dialog = BestTimesDialog()
        dialog.exec()
        
    def on_help_about(self, s):
        QMessageBox.aboutQt(self, APPLICATION_NAME)

    def load_settings(self):
        settings = QSettings(APPLICATION_NAME, APPLICATION_NAME)
        self.resize(settings.value("size", QSize(800, 600)))
        self.move(settings.value("pos", QPoint(0, 0)))
        self._marks_action.setChecked(settings.value("marks", "false").lower() == "true")
        self._minesweeper_widget.set_marks(self._marks_action.isChecked())
                                      
    def save_settings(self):
        settings = QSettings(APPLICATION_NAME, APPLICATION_NAME)
        settings.setValue("size", self.size())
        settings.setValue("pos", self.pos())
        settings.setValue("marks", self._marks_action.isChecked())
        
    def closeEvent(self, event):
        self.save_settings()

    def on_game_start(self):
        self.start_timer()
        self._time_elapsed = 0
        self.update_status_bar()

    def on_game_end(self, hit_mine):
        self.stop_timer()
        if hit_mine:
            return
        settings = QSettings(APPLICATION_NAME, APPLICATION_NAME)
        skill_level = self._minesweeper_widget.skill_level()
        s = { 8 : "beginner", 16 : "intermediate", 32 : "expert" }[skill_level]
        time = 9999999
        try:
            time = int(settings.value(s + "_time", "9999999"))
        except ValueError:
            pass
        if self._time_elapsed < time:
            input_dialog = NewBestTimeDialog(s)
            input_dialog.exec()
            settings.setValue(s + "_name", input_dialog.text())
            settings.setValue(s + "_time", self._time_elapsed)
        else:
            mb = QMessageBox()
            mb.setIcon(QMessageBox.Icon.Information)
            mb.setWindowTitle(self.windowTitle())
            mb.setText("You win!")
            mb.setInformativeText("You uncovered all the squares without mines.")
            mb.exec()
            
    def on_flags_change(self, n):
        self._mines_left -= n
        self.update_status_bar()
        
    def timerEvent(self, event):
        self._time_elapsed += 1
        self.update_status_bar()
        
################################################################################

def main():
    app = QApplication([])
    app.setApplicationName(APPLICATION_NAME)
    app.setApplicationVersion(APPLICATION_VERSION)
    app.setWindowIcon(QIcon("PySweeper.ico"))
    main_window = MainWindow()
    main_window.show()
    app.exec()

if __name__ == "__main__":
    main()

    
