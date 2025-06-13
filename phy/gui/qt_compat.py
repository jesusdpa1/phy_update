"""Qt5/Qt6 compatibility layer for phy with proper Mac modifier key handling.

This module provides a unified interface for both Qt5 and Qt6, handling:
- Import differences between PyQt5 and PyQt6
- Enum value changes (Qt5 uses integers, Qt6 uses proper enums)
- Module reorganization (QAction moved from QtWidgets to QtGui)
- API changes (QWebEnginePage location, matplotlib backend names)
- Method signature changes (exec_() vs exec())
- PIL API compatibility for icon generation
- Layout direction and widget feature detection
- Mac modifier key mapping (Command, Option, Control keys)
"""

import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Determine Qt version and set up imports
QT_VERSION = None

# Check for Qt6 first (preferred)
try:
    import PyQt6

    QT_VERSION = 6
    logger.debug('Qt6 detected')
except ImportError:
    pass

# Fall back to Qt5 if Qt6 not available
if QT_VERSION is None:
    try:
        import PyQt5

        QT_VERSION = 5
        logger.debug('Qt5 detected')
    except ImportError:
        pass

if QT_VERSION is None:
    raise ImportError(
        'Neither PyQt5 nor PyQt6 is available. Please install one of them.'
    )


# -----------------------------------------------------------------------------
# Core Qt imports with compatibility handling
# -----------------------------------------------------------------------------

if QT_VERSION == 6:
    # PyQt6 imports
    from PyQt6.QtCore import (
        QAbstractItemModel,
        QByteArray,
        QCoreApplication,
        QDir,
        QEvent,
        QEventLoop,
        QFileInfo,
        QItemSelectionModel,
        QMetaObject,
        QMimeData,
        QObject,
        QPoint,
        QRect,
        QRunnable,
        QSize,
        QStandardPaths,
        Qt,
        QThreadPool,
        QTimer,
        QUrl,
        QVariant,
        pyqtSignal,
        pyqtSlot,
        qInstallMessageHandler,
    )
    from PyQt6.QtGui import (
        QAction,  # Moved to QtGui in Qt6
        QColor,
        QFont,
        QFontDatabase,
        QGuiApplication,
        QIcon,
        QKeySequence,
        QMouseEvent,
        QPainter,
        QPixmap,
        QShortcut,
        QStandardItem,
        QStandardItemModel,
        QWindow,
    )

    # Handle QOpenGLWindow separately as it may not be available
    try:
        from PyQt6.QtOpenGL import QOpenGLWindow
    except ImportError:
        QOpenGLWindow = None
        logger.warning('QOpenGLWindow not available in PyQt6')

    try:
        from PyQt6.QtOpenGLWidgets import QOpenGLWidget
    except ImportError:
        QOpenGLWidget = None
        logger.warning('QOpenGLWidget not available in PyQt6')

    from PyQt6.QtWebChannel import QWebChannel
    from PyQt6.QtWebEngineCore import QWebEnginePage  # Moved in Qt6
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWidgets import (
        QAbstractItemView,
        QApplication,
        QCheckBox,
        QComboBox,
        QDockWidget,
        QDoubleSpinBox,
        QFileDialog,
        QFrame,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QHeaderView,
        QInputDialog,
        QLabel,
        QLineEdit,
        QListView,
        QListWidget,
        QListWidgetItem,
        QMainWindow,
        QMenu,
        QMenuBar,
        QMessageBox,
        QPlainTextEdit,
        QProgressBar,
        QPushButton,
        QScrollArea,
        QSlider,
        QSpinBox,
        QSplitter,
        QStatusBar,
        QStyleOptionTab,
        QStylePainter,
        QTabBar,
        QTableView,
        QTableWidget,
        QTableWidgetItem,
        QTabWidget,
        QTextEdit,
        QToolBar,
        QTreeView,
        QTreeWidget,
        QTreeWidgetItem,
        QVBoxLayout,
        QWidget,
    )

else:  # QT_VERSION == 5
    # PyQt5 imports
    from PyQt5.QtCore import (
        QAbstractItemModel,
        QByteArray,
        QCoreApplication,
        QDir,
        QEvent,
        QEventLoop,
        QFileInfo,
        QItemSelectionModel,
        QMetaObject,
        QMimeData,
        QObject,
        QPoint,
        QRect,
        QRunnable,
        QSize,
        QStandardPaths,
        Qt,
        QThreadPool,
        QTimer,
        QUrl,
        QVariant,
        pyqtSignal,
        pyqtSlot,
        qInstallMessageHandler,
    )
    from PyQt5.QtGui import (
        QColor,
        QFont,
        QFontDatabase,
        QGuiApplication,
        QIcon,
        QKeySequence,
        QMouseEvent,
        QOpenGLWindow,
        QPainter,
        QPixmap,
        QStandardItem,
        QStandardItemModel,
        QWindow,
    )

    try:
        from PyQt5.QtOpenGL import QOpenGLWidget
    except ImportError:
        QOpenGLWidget = None
        logger.warning('QOpenGLWidget not available in PyQt5')

    from PyQt5.QtWebChannel import QWebChannel
    from PyQt5.QtWebEngineWidgets import (
        QWebEnginePage,  # In QtWebEngineWidgets in Qt5
        QWebEngineView,
    )
    from PyQt5.QtWidgets import (
        QAbstractItemView,
        QAction,  # In QtWidgets in Qt5
        QApplication,
        QCheckBox,
        QComboBox,
        QDockWidget,
        QDoubleSpinBox,
        QFileDialog,
        QFrame,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QHeaderView,
        QInputDialog,
        QLabel,
        QLineEdit,
        QListView,
        QListWidget,
        QListWidgetItem,
        QMainWindow,
        QMenu,
        QMenuBar,
        QMessageBox,
        QPlainTextEdit,
        QProgressBar,
        QPushButton,
        QScrollArea,
        QShortcut,
        QSlider,
        QSpinBox,
        QSplitter,
        QStatusBar,
        QStyleOptionTab,
        QStylePainter,
        QTabBar,
        QTableView,
        QTableWidget,
        QTableWidgetItem,
        QTabWidget,
        QTextEdit,
        QToolBar,
        QTreeView,
        QTreeWidget,
        QTreeWidgetItem,
        QVBoxLayout,
        QWidget,
    )


# -----------------------------------------------------------------------------
# Compatibility wrappers and helpers
# -----------------------------------------------------------------------------


class QtCompat:
    """Compatibility helpers for Qt5/Qt6 differences."""

    VERSION = QT_VERSION

    # Enum compatibility
    if QT_VERSION == 6:
        # Qt6 uses proper enums
        CheckState = Qt.CheckState
        LayoutDirection = Qt.LayoutDirection
        DockWidgetArea = Qt.DockWidgetArea
        DockWidgetFeature = QDockWidget.DockWidgetFeature
        DockOption = QMainWindow.DockOption
        Orientation = Qt.Orientation
        ProcessEventsFlag = QEventLoop.ProcessEventsFlag
        CursorShape = Qt.CursorShape
        KeyboardModifier = Qt.KeyboardModifier
        ApplicationAttribute = Qt.ApplicationAttribute

        # Common values
        Checked = Qt.CheckState.Checked
        Unchecked = Qt.CheckState.Unchecked
        PartiallyChecked = Qt.CheckState.PartiallyChecked
        RightToLeft = Qt.LayoutDirection.RightToLeft
        LeftToRight = Qt.LayoutDirection.LeftToRight
        LeftDockWidgetArea = Qt.DockWidgetArea.LeftDockWidgetArea
        RightDockWidgetArea = Qt.DockWidgetArea.RightDockWidgetArea
        TopDockWidgetArea = Qt.DockWidgetArea.TopDockWidgetArea
        BottomDockWidgetArea = Qt.DockWidgetArea.BottomDockWidgetArea
        AllDockWidgetAreas = Qt.DockWidgetArea.AllDockWidgetAreas
        NoDockWidgetArea = Qt.DockWidgetArea.NoDockWidgetArea
        DockWidgetClosable = QDockWidget.DockWidgetFeature.DockWidgetClosable
        DockWidgetMovable = QDockWidget.DockWidgetFeature.DockWidgetMovable
        DockWidgetFloatable = QDockWidget.DockWidgetFeature.DockWidgetFloatable
        AllowTabbedDocks = QMainWindow.DockOption.AllowTabbedDocks
        AllowNestedDocks = QMainWindow.DockOption.AllowNestedDocks
        AnimatedDocks = QMainWindow.DockOption.AnimatedDocks
        Horizontal = Qt.Orientation.Horizontal
        Vertical = Qt.Orientation.Vertical
        AllEvents = QEventLoop.ProcessEventsFlag.AllEvents
        WaitCursor = Qt.CursorShape.WaitCursor
        ArrowCursor = Qt.CursorShape.ArrowCursor

        # Keyboard modifiers
        ShiftModifier = Qt.KeyboardModifier.ShiftModifier
        ControlModifier = Qt.KeyboardModifier.ControlModifier
        AltModifier = Qt.KeyboardModifier.AltModifier
        MetaModifier = Qt.KeyboardModifier.MetaModifier
        NoModifier = Qt.KeyboardModifier.NoModifier

        # Window flags and types
        WindowType = Qt.WindowType
        Window = Qt.WindowType.Window
        Dialog = Qt.WindowType.Dialog
        Tool = Qt.WindowType.Tool

        # Alignment
        AlignmentFlag = Qt.AlignmentFlag
        AlignLeft = Qt.AlignmentFlag.AlignLeft
        AlignRight = Qt.AlignmentFlag.AlignRight
        AlignCenter = Qt.AlignmentFlag.AlignHCenter
        AlignTop = Qt.AlignmentFlag.AlignTop
        AlignBottom = Qt.AlignmentFlag.AlignBottom
        AlignVCenter = Qt.AlignmentFlag.AlignVCenter

        # Text interaction flags
        TextSelectableByMouse = Qt.TextInteractionFlag.TextSelectableByMouse
        TextSelectableByKeyboard = Qt.TextInteractionFlag.TextSelectableByKeyboard

        # Text flags
        TextDontClip = Qt.TextFlag.TextDontClip
        AlignCenter = Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter

        # Scroll bar policies
        ScrollBarAlwaysOff = Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        ScrollBarAlwaysOn = Qt.ScrollBarPolicy.ScrollBarAlwaysOn
        ScrollBarAsNeeded = Qt.ScrollBarPolicy.ScrollBarAsNeeded

    else:  # Qt5
        # Qt5 uses integer constants
        CheckState = Qt
        LayoutDirection = Qt
        DockWidgetArea = Qt
        DockWidgetFeature = QDockWidget
        DockOption = QMainWindow
        Orientation = Qt
        ProcessEventsFlag = QEventLoop
        CursorShape = Qt
        KeyboardModifier = Qt
        ApplicationAttribute = Qt

        # Common values (integers in Qt5)
        Checked = Qt.Checked
        Unchecked = Qt.Unchecked
        PartiallyChecked = Qt.PartiallyChecked
        RightToLeft = Qt.RightToLeft
        LeftToRight = Qt.LeftToRight
        LeftDockWidgetArea = Qt.LeftDockWidgetArea
        RightDockWidgetArea = Qt.RightDockWidgetArea
        TopDockWidgetArea = Qt.TopDockWidgetArea
        BottomDockWidgetArea = Qt.BottomDockWidgetArea
        AllDockWidgetAreas = Qt.AllDockWidgetAreas
        NoDockWidgetArea = Qt.NoDockWidgetArea
        DockWidgetClosable = QDockWidget.DockWidgetClosable
        DockWidgetMovable = QDockWidget.DockWidgetMovable
        DockWidgetFloatable = QDockWidget.DockWidgetFloatable
        AllowTabbedDocks = QMainWindow.AllowTabbedDocks
        AllowNestedDocks = QMainWindow.AllowNestedDocks
        AnimatedDocks = QMainWindow.AnimatedDocks
        Horizontal = Qt.Horizontal
        Vertical = Qt.Vertical
        AllEvents = QEventLoop.AllEvents
        WaitCursor = Qt.WaitCursor
        ArrowCursor = Qt.ArrowCursor

        # Keyboard modifiers (Qt5 uses direct Qt constants)
        ShiftModifier = Qt.ShiftModifier
        ControlModifier = Qt.ControlModifier
        AltModifier = Qt.AltModifier
        MetaModifier = Qt.MetaModifier
        NoModifier = Qt.NoModifier

        # Application attributes (Qt5 uses direct Qt constants)
        AA_EnableHighDpiScaling = Qt.AA_EnableHighDpiScaling
        AA_UseHighDpiPixmaps = Qt.AA_UseHighDpiPixmaps
        AA_DisableWindowContextHelpButton = Qt.AA_DisableWindowContextHelpButton

        # Window flags and types
        WindowType = Qt
        Window = Qt.Window
        Dialog = Qt.Dialog
        Tool = Qt.Tool

        # Alignment
        AlignmentFlag = Qt
        AlignLeft = Qt.AlignLeft
        AlignRight = Qt.AlignRight
        AlignCenter = Qt.AlignHCenter
        AlignTop = Qt.AlignTop
        AlignBottom = Qt.AlignBottom
        AlignVCenter = Qt.AlignVCenter

        # Text interaction flags
        TextSelectableByMouse = Qt.TextSelectableByMouse
        TextSelectableByKeyboard = Qt.TextSelectableByKeyboard

        # Text flags
        TextDontClip = Qt.TextDontClip
        AlignCenter = Qt.AlignHCenter | Qt.AlignVCenter

        # Scroll bar policies
        ScrollBarAlwaysOff = Qt.ScrollBarAlwaysOff
        ScrollBarAlwaysOn = Qt.ScrollBarAlwaysOn
        ScrollBarAsNeeded = Qt.ScrollBarAsNeeded

    @staticmethod
    def is_checked(state):
        """Check if a Qt checkbox state represents 'checked'."""
        if QT_VERSION == 6:
            return state == Qt.CheckState.Checked
        else:
            return state == Qt.Checked

    @staticmethod
    def is_unchecked(state):
        """Check if a Qt checkbox state represents 'unchecked'."""
        if QT_VERSION == 6:
            return state == Qt.CheckState.Unchecked
        else:
            return state == Qt.Unchecked

    @staticmethod
    def is_partially_checked(state):
        """Check if a Qt checkbox state represents 'partially checked'."""
        if QT_VERSION == 6:
            return state == Qt.CheckState.PartiallyChecked
        else:
            return state == Qt.PartiallyChecked

    @staticmethod
    def exec_dialog(dialog):
        """Execute a dialog with proper method name for Qt version."""
        if QT_VERSION == 6:
            return dialog.exec()
        else:
            return dialog.exec_()

    @staticmethod
    def exec_menu(menu, pos=None):
        """Execute a menu with proper method name for Qt version."""
        if QT_VERSION == 6:
            if pos is not None:
                return menu.exec(pos)
            else:
                return menu.exec()
        else:
            if pos is not None:
                return menu.exec_(pos)
            else:
                return menu.exec_()

    @staticmethod
    def exec_app(app):
        """Execute a QApplication with proper method name for Qt version."""
        if QT_VERSION == 6:
            return app.exec()
        else:
            return app.exec_()

    @staticmethod
    def exec_event_loop(loop):
        """Execute an event loop with proper method name for Qt version."""
        if QT_VERSION == 6:
            return loop.exec()
        else:
            return loop.exec_()

    @staticmethod
    def exec_file_dialog(dialog):
        """Execute a QFileDialog with proper method name for Qt version."""
        if QT_VERSION == 6:
            return dialog.exec()
        else:
            return dialog.exec_()

    @staticmethod
    def check_dock_feature(features, target_feature):
        """Check if dock widget has a specific feature (handles Qt5/Qt6 enum differences)."""
        try:
            return bool(features & target_feature)
        except TypeError:
            # Handle case where features might be int and target_feature is enum or vice versa
            return bool(int(features) & int(target_feature))

    @staticmethod
    def get_layout_direction(right_to_left=True):
        """Get the layout direction value."""
        if right_to_left:
            if QT_VERSION == 6:
                return Qt.LayoutDirection.RightToLeft
            else:
                return Qt.RightToLeft
        else:
            if QT_VERSION == 6:
                return Qt.LayoutDirection.LeftToRight
            else:
                return Qt.LeftToRight

    @staticmethod
    def get_horizontal_layout_direction(right_to_left=True):
        """Get the direction for QHBoxLayout."""
        if QT_VERSION == 6:
            return (
                QHBoxLayout.Direction.RightToLeft
                if right_to_left
                else QHBoxLayout.Direction.LeftToRight
            )
        else:
            return 1 if right_to_left else 0  # Qt5 integer values

    @staticmethod
    def set_widget_attribute(widget, attribute, on=True):
        """Set a widget attribute with Qt5/Qt6 compatibility."""
        try:
            widget.setAttribute(attribute, on)
        except (AttributeError, TypeError) as e:
            logger.warning(f'Could not set widget attribute {attribute}: {e}')

    @staticmethod
    def get_modifier_keys(event):
        """Get modifier keys from a Qt event with proper Mac handling."""
        modifiers = event.modifiers()
        result = []

        # Handle macOS modifier key mapping differences
        if sys.platform == 'darwin':  # macOS
            # On Mac:
            # - Qt::ControlModifier = Command key (⌘)
            # - Qt::MetaModifier = Control key
            # - Qt::AltModifier = Option key (⌥)
            modifier_map = [
                ('Shift', QtCompat.ShiftModifier),
                (
                    'Control',
                    QtCompat.MetaModifier,
                ),  # Control key on Mac maps to Qt::MetaModifier
                (
                    'Alt',
                    QtCompat.AltModifier,
                ),  # Option key on Mac maps to Qt::AltModifier
                (
                    'Command',
                    QtCompat.ControlModifier,
                ),  # Command key on Mac maps to Qt::ControlModifier
            ]
        else:  # Windows/Linux
            modifier_map = [
                ('Shift', QtCompat.ShiftModifier),
                ('Control', QtCompat.ControlModifier),
                ('Alt', QtCompat.AltModifier),
                ('Meta', QtCompat.MetaModifier),
            ]

        for name, modifier in modifier_map:
            try:
                if modifiers & modifier:
                    result.append(name)
            except TypeError:
                # Handle enum/int compatibility issues
                if int(modifiers) & int(modifier):
                    result.append(name)

        return tuple(result)

    @staticmethod
    def get_platform_modifier_name(qt_modifier):
        """Get the platform-appropriate name for a Qt modifier."""
        if sys.platform == 'darwin':  # macOS
            modifier_names = {
                QtCompat.ControlModifier: 'Cmd',  # Command key
                QtCompat.MetaModifier: 'Ctrl',  # Control key
                QtCompat.AltModifier: 'Option',  # Option key
                QtCompat.ShiftModifier: 'Shift',
            }
        else:  # Windows/Linux
            modifier_names = {
                QtCompat.ControlModifier: 'Ctrl',
                QtCompat.AltModifier: 'Alt',
                QtCompat.MetaModifier: 'Meta',
                QtCompat.ShiftModifier: 'Shift',
            }

        return modifier_names.get(qt_modifier, 'Unknown')

    @staticmethod
    def create_key_sequence(key_string):
        """Create a QKeySequence with proper platform handling."""
        # Qt automatically handles Ctrl->Cmd mapping on Mac for QKeySequence
        # But you might want to explicitly handle other cases
        if sys.platform == 'darwin':
            # Replace common Windows/Linux shortcuts with Mac equivalents if needed
            key_string = key_string.replace('Meta+', 'Ctrl+')  # Real Control key on Mac

        return QKeySequence(key_string)

    @staticmethod
    def is_mac_platform():
        """Check if running on macOS."""
        return sys.platform == 'darwin'

    @staticmethod
    def is_windows_platform():
        """Check if running on Windows."""
        return sys.platform == 'win32'

    @staticmethod
    def is_linux_platform():
        """Check if running on Linux."""
        return sys.platform.startswith('linux')

    @staticmethod
    def get_primary_modifier():
        """Get the primary modifier key for the platform (Ctrl on Win/Linux, Cmd on Mac)."""
        if sys.platform == 'darwin':
            return QtCompat.ControlModifier  # Maps to Command key on Mac
        else:
            return QtCompat.ControlModifier  # Maps to Control key on Win/Linux

    @staticmethod
    def get_platform_shortcut_text(shortcut_text):
        """Convert shortcut text to platform-appropriate format."""
        if sys.platform == 'darwin':
            # Convert to Mac-style shortcuts
            return (
                shortcut_text.replace('Ctrl+', '⌘')
                .replace('Alt+', '⌥')
                .replace('Shift+', '⇧')
                .replace('Meta+', '⌃')
            )  # Control key
        else:
            return shortcut_text

    @staticmethod
    def get_save_filename(
        parent=None, caption='', directory='', filter='', selected_filter=''
    ):
        """Get save filename with Qt5/Qt6 compatibility."""
        filename, _ = QFileDialog.getSaveFileName(
            parent, caption, directory, filter, selected_filter
        )
        return filename

    @staticmethod
    def get_open_filename(
        parent=None, caption='', directory='', filter='', selected_filter=''
    ):
        """Get open filename with Qt5/Qt6 compatibility."""
        filename, _ = QFileDialog.getOpenFileName(
            parent, caption, directory, filter, selected_filter
        )
        return filename

    @staticmethod
    def get_existing_directory(parent=None, caption='', directory=''):
        """Get existing directory with Qt5/Qt6 compatibility."""
        return QFileDialog.getExistingDirectory(parent, caption, directory)

    @staticmethod
    def copy_to_clipboard(text):
        """Copy text to clipboard."""
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(text)

    @staticmethod
    def get_clipboard_text():
        """Get text from clipboard."""
        clipboard = QGuiApplication.clipboard()
        return clipboard.text()

    @staticmethod
    def get_documents_path():
        """Get the Documents directory path."""
        try:
            if QT_VERSION == 6:
                return QStandardPaths.writableLocation(
                    QStandardPaths.StandardLocation.DocumentsLocation
                )
            else:
                return QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
        except Exception:
            return str(Path.home() / 'Documents')

    @staticmethod
    def get_desktop_path():
        """Get the Desktop directory path."""
        try:
            if QT_VERSION == 6:
                return QStandardPaths.writableLocation(
                    QStandardPaths.StandardLocation.DesktopLocation
                )
            else:
                return QStandardPaths.writableLocation(QStandardPaths.DesktopLocation)
        except Exception:
            return str(Path.home() / 'Desktop')

    @staticmethod
    def setup_table_widget(table, headers, data=None):
        """Setup a QTableWidget with proper compatibility."""
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)

        if data:
            table.setRowCount(len(data))
            for row, row_data in enumerate(data):
                for col, cell_data in enumerate(row_data):
                    item = QTableWidgetItem(str(cell_data))
                    table.setItem(row, col, item)

        # Auto-resize columns
        header = table.horizontalHeader()
        if QT_VERSION == 6:
            header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        else:
            header.setResizeMode(QHeaderView.ResizeToContents)

    @staticmethod
    def create_shortcut(key_sequence, parent, callback):
        """Create a QShortcut with proper compatibility."""
        shortcut = QShortcut(QKeySequence(key_sequence), parent)
        shortcut.activated.connect(callback)
        return shortcut

    @staticmethod
    def set_tab_position(tab_widget, position):
        """Set tab position with Qt5/Qt6 compatibility."""
        if QT_VERSION == 6:
            position_map = {
                'north': QTabWidget.TabPosition.North,
                'south': QTabWidget.TabPosition.South,
                'west': QTabWidget.TabPosition.West,
                'east': QTabWidget.TabPosition.East,
            }
        else:
            position_map = {
                'north': QTabWidget.North,
                'south': QTabWidget.South,
                'west': QTabWidget.West,
                'east': QTabWidget.East,
            }

        tab_widget.setTabPosition(position_map.get(position, position_map['north']))

    @staticmethod
    def set_frame_style(frame, shape, shadow):
        """Set frame style with Qt5/Qt6 compatibility."""
        if QT_VERSION == 6:
            shape_map = {
                'box': QFrame.Shape.Box,
                'panel': QFrame.Shape.Panel,
                'hline': QFrame.Shape.HLine,
                'vline': QFrame.Shape.VLine,
            }
            shadow_map = {
                'plain': QFrame.Shadow.Plain,
                'raised': QFrame.Shadow.Raised,
                'sunken': QFrame.Shadow.Sunken,
            }
        else:
            shape_map = {
                'box': QFrame.Box,
                'panel': QFrame.Panel,
                'hline': QFrame.HLine,
                'vline': QFrame.VLine,
            }
            shadow_map = {
                'plain': QFrame.Plain,
                'raised': QFrame.Raised,
                'sunken': QFrame.Sunken,
            }

        frame.setFrameShape(shape_map.get(shape, shape_map['box']))
        frame.setFrameShadow(shadow_map.get(shadow, shadow_map['plain']))

    @staticmethod
    def set_table_selection_behavior(table, behavior):
        """Set table selection behavior with Qt5/Qt6 compatibility."""
        if QT_VERSION == 6:
            behavior_map = {
                'rows': QAbstractItemView.SelectionBehavior.SelectRows,
                'columns': QAbstractItemView.SelectionBehavior.SelectColumns,
                'items': QAbstractItemView.SelectionBehavior.SelectItems,
            }
        else:
            behavior_map = {
                'rows': QAbstractItemView.SelectRows,
                'columns': QAbstractItemView.SelectColumns,
                'items': QAbstractItemView.SelectItems,
            }

        table.setSelectionBehavior(behavior_map.get(behavior, behavior_map['rows']))

    @staticmethod
    def set_table_edit_triggers(table, triggers):
        """Set table edit triggers with Qt5/Qt6 compatibility."""
        if QT_VERSION == 6:
            if triggers == 'none':
                table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            elif triggers == 'all':
                table.setEditTriggers(QAbstractItemView.EditTrigger.AllEditTriggers)
        else:
            if triggers == 'none':
                table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            elif triggers == 'all':
                table.setEditTriggers(QAbstractItemView.AllEditTriggers)


# -----------------------------------------------------------------------------
# Enhanced error handling and logging
# -----------------------------------------------------------------------------


def _safe_import(module_name, class_name=None):
    """Safely import a module or class with error handling."""
    try:
        module = __import__(module_name, fromlist=[class_name] if class_name else [])
        if class_name:
            return getattr(module, class_name)
        return module
    except (ImportError, AttributeError) as e:
        logger.warning(f'Could not import {module_name}.{class_name or ""}: {e}')
        return None


# -----------------------------------------------------------------------------
# Matplotlib backend compatibility
# -----------------------------------------------------------------------------


def get_matplotlib_backend():
    """Get the appropriate matplotlib Qt backend name for the current Qt version."""
    if QT_VERSION == 6:
        return 'matplotlib.backends.backend_qtagg'
    else:
        return 'matplotlib.backends.backend_qt5agg'


def get_matplotlib_canvas():
    """Get the appropriate FigureCanvasQTAgg class for the current Qt version."""
    try:
        if QT_VERSION == 6:
            from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
        else:
            from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
        return FigureCanvasQTAgg
    except ImportError as e:
        logger.warning(f'Could not import matplotlib Qt backend: {e}')
        return None


# -----------------------------------------------------------------------------
# Font loading compatibility
# -----------------------------------------------------------------------------


def load_font_compatible(name, size=8):
    """Load a TTF font with Qt5/Qt6 compatibility."""
    static_path = Path(__file__).parent / 'static' / name

    if not static_path.exists():
        logger.warning(f'Font file not found: {static_path}')
        return None

    font_id = QFontDatabase.addApplicationFont(str(static_path))

    if font_id == -1:
        logger.warning(f'Failed to load font: {name}')
        return None

    font_families = QFontDatabase.applicationFontFamilies(font_id)
    if not font_families:
        logger.warning(f'No font families found for: {name}')
        return None

    font_family = font_families[0]

    try:
        if QT_VERSION == 6:
            # Qt6: Use QFont constructor directly
            font = QFont(font_family, size)
        else:
            # Qt5: Use QFontDatabase.font() method
            font_db = QFontDatabase()
            font = font_db.font(font_family, None, size)

        return font
    except Exception as e:
        logger.warning(f'Error creating font {font_family}: {e}')
        return None


# -----------------------------------------------------------------------------
# High DPI support (disabled by default due to known issues)
# -----------------------------------------------------------------------------


def setup_high_dpi():
    """Setup high DPI support for the current Qt version.

    Note: This is disabled by default due to scaling issues on some systems,
    particularly Ubuntu. Qt6 has better automatic high DPI support, but even
    there it can cause problems, so it's commented out in the original code.
    """
    # Disabled due to known issues - see original Qt6 implementation
    # where this is also commented out:
    # # Enable high DPI support.
    # # QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)

    logger.debug('High DPI scaling setup skipped (disabled due to known issues)')
    pass


# -----------------------------------------------------------------------------
# Complete Qt setup function
# -----------------------------------------------------------------------------


def setup_qt_environment():
    """Setup the complete Qt environment with all compatibility fixes."""
    # Always setup macOS compatibility first (before QApplication creation)

    # High DPI setup is available but disabled by default
    # setup_high_dpi()  # Uncomment if needed, but beware of scaling issues


# -----------------------------------------------------------------------------
# PIL compatibility for icon generation
# -----------------------------------------------------------------------------


def get_text_size_compatible(draw, text, font):
    """Get text size with PIL API compatibility."""
    try:
        # Newer PIL versions (>=8.0.0)
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
    except AttributeError:
        try:
            # Older PIL versions
            return draw.textsize(text, font=font)
        except Exception as e:
            logger.warning(f'Could not get text size: {e}')
            return (10, 10)  # Fallback size


def get_image_resampling():
    """Get the appropriate image resampling constant for PIL version."""
    try:
        # Newer PIL versions
        from PIL import Image

        return Image.Resampling.LANCZOS
    except AttributeError:
        try:
            # Older PIL versions
            from PIL import Image

            return Image.ANTIALIAS
        except Exception:
            # Final fallback
            return 1  # Nearest neighbor


# -----------------------------------------------------------------------------
# Screenshot compatibility
# -----------------------------------------------------------------------------


def screenshot_widget_compatible(widget, path):
    """Take a screenshot of a widget with Qt5/Qt6 compatibility."""
    try:
        if QT_VERSION == 6:
            # Qt6 screenshot approach
            success = _screenshot_qt6(widget, path)
        else:
            # Qt5 screenshot approach
            success = _screenshot_qt5(widget, path)

        return success
    except Exception as e:
        logger.warning(f'Screenshot failed: {e}')
        return False


def _screenshot_qt6(widget, path):
    """Qt6-specific screenshot implementation."""
    try:
        # Method 1: Try screen grabWindow
        if hasattr(widget, 'screen') and widget.screen():
            screen = widget.screen()
        else:
            screen = QGuiApplication.primaryScreen()

        window_id = widget.winId()
        pixmap = screen.grabWindow(window_id)
        pixmap.save(str(path))
        return True
    except Exception:
        try:
            # Method 2: Try render method
            pixmap = QPixmap(widget.size())
            widget.render(pixmap)
            pixmap.save(str(path))
            return True
        except Exception:
            try:
                # Method 3: Screenshot screen area
                screen = QGuiApplication.primaryScreen()
                global_pos = widget.mapToGlobal(widget.rect().topLeft())
                size = widget.size()
                screen_pixmap = screen.grabWindow(
                    0, global_pos.x(), global_pos.y(), size.width(), size.height()
                )
                screen_pixmap.save(str(path))
                return True
            except Exception:
                return False


def _screenshot_qt5(widget, path):
    """Qt5-specific screenshot implementation."""
    try:
        if QOpenGLWindow and isinstance(widget, QOpenGLWindow):
            # Special handling for OpenGL widgets
            widget.grabFramebuffer().save(str(path))
        else:
            # Generic Qt5 screenshot
            widget.grab().save(str(path))
        return True
    except Exception:
        return False


# -----------------------------------------------------------------------------
# WebEngine compatibility
# -----------------------------------------------------------------------------


class CompatWebPage(QWebEnginePage):
    """WebEngine page with Qt5/Qt6 compatibility."""

    _raise_on_javascript_error = False

    def javaScriptConsoleMessage(self, level, msg, line, source):
        try:
            super().javaScriptConsoleMessage(level, msg, line, source)
        except Exception as e:
            logger.warning(f'Error in javaScriptConsoleMessage: {e}')

        msg = f'[JS:L{line:02d}] {msg}'

        # Handle enum vs integer level values
        try:
            if QT_VERSION == 6:
                level_int = level.value if hasattr(level, 'value') else int(level)
            else:
                level_int = int(level)
        except (ValueError, TypeError):
            level_int = 1  # Default to warning level

        # Choose logging function based on level
        log_funcs = [
            lambda m: logger.log(5, m),  # Debug
            logger.warning,  # Warning
            logger.error,  # Error
        ]

        if 0 <= level_int < len(log_funcs):
            log_funcs[level_int](msg)
        else:
            logger.error(msg)

        if self._raise_on_javascript_error and level_int >= 2:
            raise RuntimeError(msg)


# -----------------------------------------------------------------------------
# Qt Test compatibility
# -----------------------------------------------------------------------------


def get_qt_test():
    """Get the QTest class for the current Qt version."""
    if QT_VERSION == 6:
        from PyQt6.QtTest import QTest

        return QTest
    else:
        from PyQt5.QtTest import QTest

        return QTest


# -----------------------------------------------------------------------------
# Debug compatibility
# -----------------------------------------------------------------------------


def remove_input_hook():
    """Remove the PyQt input hook for debugging."""
    try:
        if QT_VERSION == 6:
            from PyQt6.QtCore import pyqtRemoveInputHook
        else:
            from PyQt5.QtCore import pyqtRemoveInputHook
        pyqtRemoveInputHook()
    except Exception as e:
        logger.warning(f'Could not remove input hook: {e}')


# -----------------------------------------------------------------------------
# Shortcut helper functions
# -----------------------------------------------------------------------------


def get_copy_shortcut():
    """Get the platform-appropriate copy shortcut."""
    if QtCompat.is_mac_platform():
        return QKeySequence.StandardKey.Copy  # Automatically maps to Cmd+C
    else:
        return QKeySequence('Ctrl+C')


def get_paste_shortcut():
    """Get the platform-appropriate paste shortcut."""
    if QtCompat.is_mac_platform():
        return QKeySequence.StandardKey.Paste  # Automatically maps to Cmd+V
    else:
        return QKeySequence('Ctrl+V')


def get_save_shortcut():
    """Get the platform-appropriate save shortcut."""
    if QtCompat.is_mac_platform():
        return QKeySequence.StandardKey.Save  # Automatically maps to Cmd+S
    else:
        return QKeySequence('Ctrl+S')


def get_undo_shortcut():
    """Get the platform-appropriate undo shortcut."""
    if QtCompat.is_mac_platform():
        return QKeySequence.StandardKey.Undo  # Automatically maps to Cmd+Z
    else:
        return QKeySequence('Ctrl+Z')


def get_redo_shortcut():
    """Get the platform-appropriate redo shortcut."""
    if QtCompat.is_mac_platform():
        return QKeySequence.StandardKey.Redo  # Automatically maps to Cmd+Shift+Z
    else:
        return QKeySequence('Ctrl+Y')


def get_quit_shortcut():
    """Get the platform-appropriate quit shortcut."""
    if QtCompat.is_mac_platform():
        return QKeySequence.StandardKey.Quit  # Automatically maps to Cmd+Q
    else:
        return QKeySequence('Ctrl+Q')


# -----------------------------------------------------------------------------
# Example usage functions
# -----------------------------------------------------------------------------


def handle_key_event(event):
    """Example of how to handle key events with proper Mac support."""
    modifiers = QtCompat.get_modifier_keys(event)

    if QtCompat.is_mac_platform():
        # On Mac, check for Command key (which Qt reports as ControlModifier)
        if 'Command' in modifiers and event.key() == Qt.Key_C:
            print('Copy command detected on Mac')
        elif 'Control' in modifiers and event.key() == Qt.Key_C:
            print('Actual Control key pressed on Mac (rare)')
        elif 'Alt' in modifiers and event.key() == Qt.Key_C:
            print('Option key + C pressed on Mac')
    else:
        # On Windows/Linux, standard behavior
        if 'Control' in modifiers and event.key() == Qt.Key_C:
            print('Copy command detected on Windows/Linux')
        elif 'Alt' in modifiers and event.key() == Qt.Key_C:
            print('Alt + C pressed on Windows/Linux')


def create_platform_aware_shortcut(base_shortcut):
    """Create a shortcut that's aware of platform differences."""
    if QtCompat.is_mac_platform():
        # Convert Windows/Linux shortcuts to Mac equivalents
        mac_shortcut = (
            base_shortcut.replace('Ctrl+', 'Cmd+')
            .replace('Alt+', 'Option+')
            .replace('Meta+', 'Ctrl+')
        )  # Real Control key on Mac
        return QKeySequence(mac_shortcut)
    else:
        return QKeySequence(base_shortcut)


def get_modifier_display_text(modifiers):
    """Get display text for modifiers appropriate for the platform."""
    if not modifiers:
        return ''

    if QtCompat.is_mac_platform():
        # Use Mac symbols
        symbols = {
            'Shift': '⇧',
            'Control': '⌃',  # Real Control key
            'Alt': '⌥',  # Option key
            'Command': '⌘',  # Command key
        }
        return ''.join(symbols.get(mod, mod) for mod in modifiers)
    else:
        # Use standard text
        return '+'.join(modifiers) + '+'


# -----------------------------------------------------------------------------
# Export commonly used Qt objects with compatibility
# -----------------------------------------------------------------------------

# Re-export Qt classes and constants through compatibility layer
Qt = QtCompat

# Export the compatibility helpers
__all__ = [
    # Qt version info
    'QT_VERSION',
    'QtCompat',
    # Core Qt classes
    'QApplication',
    'QWidget',
    'QMainWindow',
    'QDockWidget',
    'QHBoxLayout',
    'QVBoxLayout',
    'QGridLayout',
    'QPushButton',
    'QLabel',
    'QCheckBox',
    'QMenu',
    'QMenuBar',
    'QToolBar',
    'QStatusBar',
    'QMessageBox',
    'QInputDialog',
    'QAction',
    'QTimer',
    'QObject',
    'QPoint',
    'QRect',
    'QSize',
    'QIcon',
    'QColor',
    'QFont',
    'QFontDatabase',
    'QPixmap',
    'QPainter',
    'QWebEngineView',
    'QWebEnginePage',
    'QWebChannel',
    'QThreadPool',
    'QRunnable',
    'pyqtSignal',
    'pyqtSlot',
    'QEventLoop',
    'QUrl',
    'QEvent',
    'QCoreApplication',
    'qInstallMessageHandler',
    'QByteArray',
    'QMetaObject',
    'QVariant',
    'QKeySequence',
    'QMouseEvent',
    'QGuiApplication',
    'QWindow',
    'QScrollArea',
    'QPlainTextEdit',
    'QLineEdit',
    'QSlider',
    'QSpinBox',
    'QDoubleSpinBox',
    # New widgets for enhanced functionality
    'QTabWidget',
    'QTabBar',
    'QFileDialog',
    'QTableWidget',
    'QTableView',
    'QHeaderView',
    'QAbstractItemView',
    'QTextEdit',
    'QFrame',
    'QSplitter',
    'QGroupBox',
    'QProgressBar',
    'QComboBox',
    'QTreeWidget',
    'QTreeView',
    'QListWidget',
    'QListView',
    'QShortcut',
    'QStandardItemModel',
    'QStandardItem',
    'QTreeWidgetItem',
    'QTableWidgetItem',
    'QListWidgetItem',
    'QAbstractItemModel',
    'QItemSelectionModel',
    'QStandardPaths',
    'QDir',
    'QFileInfo',
    'QMimeData',
    'QStylePainter',
    'QStyleOptionTab',
    # Compatibility helpers
    'get_matplotlib_backend',
    'get_matplotlib_canvas',
    'load_font_compatible',
    'setup_high_dpi',
    'CompatWebPage',
    'get_text_size_compatible',
    'get_image_resampling',
    'screenshot_widget_compatible',
    'get_qt_test',
    'remove_input_hook',
    'setup_qt_environment',
    # Shortcut helpers
    'get_copy_shortcut',
    'get_paste_shortcut',
    'get_save_shortcut',
    'get_undo_shortcut',
    'get_redo_shortcut',
    'get_quit_shortcut',
    'create_platform_aware_shortcut',
    'get_modifier_display_text',
    'handle_key_event',
    # Original Qt module for advanced usage
    'Qt' + ('6' if QT_VERSION == 6 else '5'),  # Qt6 or Qt5 for accessing original
]

# Add OpenGL if available
if QOpenGLWindow is not None:
    __all__.append('QOpenGLWindow')
if QOpenGLWidget is not None:
    __all__.append('QOpenGLWidget')


# -----------------------------------------------------------------------------
# Module-level convenience functions
# -----------------------------------------------------------------------------


def get_qt_version():
    """Return the Qt version being used (5 or 6)."""
    return QT_VERSION


def is_qt6():
    """Return True if using Qt6."""
    return QT_VERSION == 6


def is_qt5():
    """Return True if using Qt5."""
    return QT_VERSION == 5


def get_qt_version_string():
    """Return a descriptive string of the Qt version."""
    return f'PyQt{QT_VERSION}'


def print_qt_info():
    """Print information about the Qt version and available features."""
    print(f'Using {get_qt_version_string()}')
    print(f'Platform: {sys.platform}')
    print(f'QOpenGLWindow available: {QOpenGLWindow is not None}')
    print(f'QOpenGLWidget available: {QOpenGLWidget is not None}')

    try:
        canvas_class = get_matplotlib_canvas()
        print(f'Matplotlib Qt backend: {get_matplotlib_backend()}')
        print(f'Matplotlib canvas available: {canvas_class is not None}')
    except Exception as e:
        print(f'Matplotlib backend error: {e}')

    # Print platform-specific modifier info
    if QtCompat.is_mac_platform():
        print('Mac modifier mapping:')
        print('  Qt::ControlModifier -> Command key (⌘)')
        print('  Qt::MetaModifier -> Control key (⌃)')
        print('  Qt::AltModifier -> Option key (⌥)')
    else:
        print('Windows/Linux modifier mapping:')
        print('  Qt::ControlModifier -> Control key')
        print('  Qt::AltModifier -> Alt key')
        print('  Qt::MetaModifier -> Meta/Windows key')


def check_qt_dependencies():
    """Check if all required Qt dependencies are available."""
    missing = []

    # Check core Qt
    if QT_VERSION is None:
        missing.append('PyQt5 or PyQt6')

    # Check matplotlib integration
    if get_matplotlib_canvas() is None:
        missing.append('matplotlib Qt backend')

    # Check WebEngine
    try:
        QWebEngineView()
    except Exception:
        missing.append('QtWebEngine')

    if missing:
        logger.warning(f'Missing Qt dependencies: {", ".join(missing)}')
        return False

    return True


def test_modifier_keys():
    """Test function to verify modifier key mapping works correctly."""
    print('Testing modifier key mapping...')
    print(f'Platform: {sys.platform}')

    # Create a mock event-like object for testing
    class MockEvent:
        def __init__(self, modifiers):
            self._modifiers = modifiers

        def modifiers(self):
            return self._modifiers

    # Test different modifier combinations
    test_cases = [
        (QtCompat.ControlModifier, 'Control/Command'),
        (QtCompat.AltModifier, 'Alt/Option'),
        (QtCompat.MetaModifier, 'Meta/Control'),
        (QtCompat.ShiftModifier, 'Shift'),
        (QtCompat.ControlModifier | QtCompat.AltModifier, 'Control+Alt'),
    ]

    for modifier, description in test_cases:
        event = MockEvent(modifier)
        detected = QtCompat.get_modifier_keys(event)
        print(f'  {description}: {detected}')

    print('Test complete.')


# Log successful initialization
logger.info(f'Qt compatibility layer initialized with {get_qt_version_string()}')
if QtCompat.is_mac_platform():
    logger.info('Mac modifier key mapping enabled')

# Note: setup_high_dpi() is available but not called automatically due to known issues
# on various systems. Call manually if needed, but be aware of potential scaling problems.
