"""
Enhanced shortcuts popup window with tabs, search, file dialog export, and table view.
File: phy/gui/shortcuts_dialog.py
"""

import logging
from pathlib import Path

from .qt import (
    QComboBox,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QKeySequence,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPoint,
    QPushButton,
    QRect,
    QScrollArea,
    QShortcut,
    QSize,
    QSplitter,
    QStyleOptionTab,
    QStylePainter,
    Qt,
    QTabBar,
    QTableWidget,
    QTableWidgetItem,
    # New imports for enhanced functionality
    QTabWidget,
    QtCompat,
    QVBoxLayout,
    QWidget,
)

# Import QStyle for the control elements
if QtCompat.VERSION == 6:
    from PyQt6.QtWidgets import QStyle
else:
    from PyQt5.QtWidgets import QStyle

logger = logging.getLogger(__name__)


class HorizontalTabBar(QTabBar):
    """Custom QTabBar that displays horizontal text even when positioned vertically."""

    def tabSizeHint(self, index):
        """Return size hint with swapped dimensions for vertical positioning."""
        size = QTabBar.tabSizeHint(self, index)
        # Swap width and height for vertical tabs
        if size.width() < size.height():
            size.transpose()
        return size

    def paintEvent(self, event):
        """Custom paint event to draw horizontal text in vertical tabs."""
        painter = QStylePainter(self)
        option = QStyleOptionTab()

        for index in range(self.count()):
            self.initStyleOption(option, index)
            # Draw the tab shape
            painter.drawControl(QStyle.CE_TabBarTabShape, option)
            # Draw the text horizontally
            painter.drawText(
                self.tabRect(index),
                Qt.AlignCenter | Qt.TextDontClip,
                self.tabText(index),
            )

        # Important: End the painter to avoid recursive painting
        painter.end()


class EnhancedShortcutsDialog(QWidget):
    """Enhanced widget window that displays all shortcuts with tabs, table view, and export."""

    def __init__(self, gui, parent=None):
        super().__init__(parent)
        self.gui = gui
        self.setWindowTitle('Keyboard Shortcuts & Commands')
        self.setWindowFlags(Qt.Window)

        # Make window much larger for better readability
        if parent:
            parent_size = parent.size()
            self.resize(
                int(parent_size.width() * 0.95), int(parent_size.height() * 0.95)
            )
        else:
            self.resize(1400, 900)  # Increased from 1200x800

        # Store all shortcuts data
        self.all_shortcuts_data = {}
        self.filtered_data = {}

        # Setup keyboard shortcuts
        self.setup_shortcuts()

        # Set up the UI
        self.setup_ui()
        self.collect_all_shortcuts()
        self.populate_tabs()

    def setup_shortcuts(self):
        """Setup keyboard shortcuts for the dialog."""
        # Close dialog with Esc
        close_shortcut = QtCompat.create_shortcut('Esc', self, self.close)

        # Export with Ctrl+E
        export_shortcut = QtCompat.create_shortcut(
            'Ctrl+E', self, self.export_shortcuts
        )

        # Copy to clipboard with Ctrl+C
        copy_shortcut = QtCompat.create_shortcut('Ctrl+C', self, self.copy_current_tab)

        # Search focus with Ctrl+F
        search_shortcut = QtCompat.create_shortcut('Ctrl+F', self, self.focus_search)

    def setup_ui(self):
        """Set up the enhanced user interface."""
        layout = QVBoxLayout(self)

        # Header section
        header_group = QGroupBox('Search & Filter')
        header_layout = QHBoxLayout(header_group)

        # Title
        header_label = QLabel('Keyboard Shortcuts & Commands')
        header_label.setStyleSheet('font-weight: bold; font-size: 14px;')

        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText('Search shortcuts and commands... (Ctrl+F)')
        self.search_box.textChanged.connect(self.filter_shortcuts)

        # Filter combo
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(['All Types', 'Shortcuts Only', 'Commands Only'])
        self.filter_combo.currentTextChanged.connect(self.apply_filter)

        header_layout.addWidget(header_label)
        header_layout.addStretch()
        header_layout.addWidget(QLabel('Filter:'))
        header_layout.addWidget(self.filter_combo)
        header_layout.addWidget(QLabel('Search:'))
        header_layout.addWidget(self.search_box)

        layout.addWidget(header_group)

        # Main content with splitter
        splitter = QSplitter(Qt.Horizontal)

        # Tab widget with custom horizontal text tab bar
        self.tab_widget = QTabWidget()

        # Use custom tab bar for horizontal text in vertical tabs
        custom_tab_bar = HorizontalTabBar()
        self.tab_widget.setTabBar(custom_tab_bar)
        QtCompat.set_tab_position(self.tab_widget, 'west')  # Vertical tabs on left
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        # Set fixed width for tab widget to prevent table overflow
        self.tab_widget.setFixedWidth(200)

        # Enhanced styling with proper selection colors - ONLY tab highlighting fix
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid palette(mid);
            }
            QTabBar::tab {
                padding: 8px 12px;
                margin: 1px;
                min-width: 160px;
                min-height: 25px;
                background: palette(button);
                border: 1px solid palette(mid);
            }
            QTabBar::tab:selected {
                background: palette(highlight);
                color: palette(highlighted-text);
                font-weight: bold;
                border: 1px solid palette(highlight);
            }
            QTabBar::tab:hover:!selected {
                background: palette(light);
                color: palette(text);
            }
        """)

        # Add tab widget to splitter
        splitter.addWidget(self.tab_widget)

        # Create content area for the table that will be shown
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)

        # Add content widget to splitter
        splitter.addWidget(self.content_widget)

        # Set splitter proportions (tabs: content = 1:5)
        splitter.setSizes([200, 1200])
        splitter.setCollapsible(0, False)  # Don't allow tab area to be collapsed
        splitter.setCollapsible(1, False)  # Don't allow content area to be collapsed

        layout.addWidget(splitter)

        # Footer with enhanced buttons
        footer_group = QGroupBox('Actions')
        footer_layout = QHBoxLayout(footer_group)

        # Copy to clipboard button
        copy_btn = QPushButton('Copy to Clipboard (Ctrl+C)')
        copy_btn.clicked.connect(self.copy_current_tab)

        # Export button with file dialog
        export_btn = QPushButton('Export to File (Ctrl+E)')
        export_btn.clicked.connect(self.export_shortcuts)

        # Statistics label
        self.stats_label = QLabel('Total shortcuts: 0')

        # Close button
        close_btn = QPushButton('Close (Esc)')
        close_btn.clicked.connect(self.close)

        footer_layout.addWidget(copy_btn)
        footer_layout.addWidget(export_btn)
        footer_layout.addStretch()
        footer_layout.addWidget(self.stats_label)
        footer_layout.addWidget(close_btn)

        layout.addWidget(footer_group)

    def create_table_widget(self, data):
        """Create a table widget for displaying shortcuts data."""
        table = QTableWidget()

        if not data:
            return table

        # Setup headers with better column names
        headers = ['Action', 'Shortcut', 'Description', 'Type', 'Command']
        QtCompat.setup_table_widget(table, headers)

        # Populate data
        table.setRowCount(len(data))
        for row, item in enumerate(data):
            # Format action name nicely
            action_name = item['name']
            table.setItem(row, 0, QTableWidgetItem(action_name))

            # Format shortcut with better display
            shortcut_text = self._format_shortcut_display(item['shortcut'])
            table.setItem(row, 1, QTableWidgetItem(shortcut_text))

            # Description
            table.setItem(row, 2, QTableWidgetItem(item['description']))

            # Type with better formatting
            type_text = item['type'].title()
            table.setItem(row, 3, QTableWidgetItem(type_text))

            # Alias with proper formatting
            alias_text = item.get('alias', '')
            if alias_text:
                alias_text = f':{alias_text}'
            table.setItem(row, 4, QTableWidgetItem(alias_text))

        # Make table read-only and sortable
        QtCompat.set_table_edit_triggers(table, 'none')
        table.setSortingEnabled(True)

        # Enable selection
        QtCompat.set_table_selection_behavior(table, 'rows')

        # Set column widths for better readability - adjusted for available space
        table.setColumnWidth(0, 200)  # Action name
        table.setColumnWidth(1, 130)  # Keyboard shortcut
        table.setColumnWidth(2, 400)  # Description
        table.setColumnWidth(3, 80)  # Type
        table.setColumnWidth(4, 120)  # Command alias

        # Set standard row height
        table.verticalHeader().setDefaultSectionSize(22)

        # Clean, minimal styling with dark headers
        table.setAlternatingRowColors(False)  # Keep default background
        table.setStyleSheet("""
            QTableWidget {
                gridline-color: #e0e0e0;
                selection-background-color: palette(highlight);
                selection-color: palette(highlighted-text);
            }
            QTableWidget::item {
                padding: 4px;
                border: none;
            }
            QHeaderView::section {
                background-color: #2b2b2b;
                color: white;
                padding: 6px;
                border: 1px solid #1a1a1a;
                border-left: none;
                font-weight: bold;
            }
            QHeaderView::section:first {
                border-left: 1px solid #1a1a1a;
            }
        """)

        # Hide row numbers
        table.verticalHeader().setVisible(False)

        return table

    def _format_shortcut_display(self, shortcut):
        """Format shortcut for better display in table."""
        if not shortcut:
            return ''

        if isinstance(shortcut, (tuple, list)):
            formatted_shortcuts = []
            for s in shortcut:
                formatted_shortcuts.append(self._format_single_shortcut(s))
            return ' or '.join(formatted_shortcuts)
        else:
            return self._format_single_shortcut(shortcut)

    def _format_single_shortcut(self, shortcut):
        """Format a single shortcut with platform-appropriate symbols."""
        if hasattr(shortcut, 'toString'):
            shortcut_str = str(shortcut.toString())
        else:
            shortcut_str = str(shortcut)

        if not shortcut_str:
            return ''

        # Convert to platform-appropriate format
        if QtCompat.is_mac_platform():
            # Use Mac symbols
            shortcut_str = (
                shortcut_str.replace('Ctrl+', '⌘')
                .replace('Alt+', '⌥')
                .replace('Shift+', '⇧')
                .replace('Meta+', '⌃')
            )
        else:
            # Ensure proper capitalization for Windows/Linux
            shortcut_str = (
                shortcut_str.replace('ctrl+', 'Ctrl+')
                .replace('alt+', 'Alt+')
                .replace('shift+', 'Shift+')
                .replace('meta+', 'Meta+')
            )

        return shortcut_str

    def collect_all_shortcuts(self):
        """Collect all shortcuts and organize by source."""
        self.all_shortcuts_data = {}

        # Main GUI Actions
        for actions in self.gui.actions:
            if not hasattr(actions, 'shortcuts') or not actions.shortcuts:
                continue

            tab_name = f'{actions.name} Actions'
            shortcuts_list = []

            for name in sorted(actions.shortcuts.keys()):
                if name.startswith('_'):
                    continue

                action_obj = actions._actions_dict.get(name)
                if not action_obj or not getattr(action_obj, 'show_shortcut', True):
                    continue

                shortcut_str = self._format_shortcut(actions.shortcuts[name])
                if not shortcut_str or shortcut_str.startswith('-'):
                    continue

                description = getattr(action_obj, 'docstring', None) or 'No description'
                alias = getattr(action_obj, 'alias', None)

                shortcuts_list.append(
                    {
                        'name': name.replace('_', ' ').title(),
                        'shortcut': shortcut_str,
                        'description': description,
                        'alias': alias or '',
                        'type': 'shortcut',
                        'source': actions.name,
                    }
                )

            if shortcuts_list:
                self.all_shortcuts_data[tab_name] = shortcuts_list

        # Command Snippets
        snippets_list = []
        for actions in self.gui.actions:
            if not hasattr(actions, '_actions_dict') or not actions._actions_dict:
                continue

            for name in sorted(actions._actions_dict.keys()):
                if name.startswith('_'):
                    continue

                action_obj = actions._actions_dict[name]
                alias = getattr(action_obj, 'alias', None)
                if not alias:
                    continue

                description = getattr(action_obj, 'docstring', None) or 'No description'
                snippets_list.append(
                    {
                        'name': name.replace('_', ' ').title(),
                        'shortcut': f':{alias}',
                        'description': description,
                        'alias': alias,
                        'type': 'command',
                        'source': actions.name,
                    }
                )

        if snippets_list:
            self.all_shortcuts_data['Command Snippets'] = snippets_list

        # REMOVED: View-specific shortcuts collection
        # No longer collecting view shortcuts to eliminate unwanted tabs

        # All shortcuts combined
        all_combined = []
        for tab_data in self.all_shortcuts_data.values():
            all_combined.extend(tab_data)
        if all_combined:
            self.all_shortcuts_data['All Shortcuts'] = all_combined

    def populate_tabs(self):
        """Create tabs and populate with table widgets."""
        self.tab_widget.clear()

        # Organize tabs in a better order
        tab_order = []

        # First add "All Shortcuts" if it exists
        if 'All Shortcuts' in self.all_shortcuts_data:
            tab_order.append('All Shortcuts')

        # Then add action tabs (sorted)
        action_tabs = [
            name
            for name in self.all_shortcuts_data.keys()
            if name.endswith(' Actions') and name != 'All Shortcuts'
        ]
        tab_order.extend(sorted(action_tabs))

        # Then add Command Snippets
        if 'Command Snippets' in self.all_shortcuts_data:
            tab_order.append('Command Snippets')

        # REMOVED: View tabs logic - no longer needed

        # Add any remaining tabs
        remaining_tabs = [
            name for name in self.all_shortcuts_data.keys() if name not in tab_order
        ]
        tab_order.extend(sorted(remaining_tabs))

        # Create tabs in the organized order
        for tab_name in tab_order:
            if tab_name in self.all_shortcuts_data:
                tab_data = self.all_shortcuts_data[tab_name]

                # Shorten tab names for better fit
                display_name = self._shorten_tab_name(tab_name)
                self.tab_widget.addTab(
                    QWidget(), display_name
                )  # Placeholder widget for tab

        # Show the first tab's content
        if self.tab_widget.count() > 0:
            self.tab_widget.setCurrentIndex(0)
            self.on_tab_changed(0)

        self.update_statistics()

    def _shorten_tab_name(self, tab_name):
        """Shorten tab names for better display in vertical tabs."""
        # Remove redundant words and shorten common terms
        shortened = tab_name
        shortened = shortened.replace(' Actions', '')
        shortened = shortened.replace('Command Snippets', 'Commands')
        shortened = shortened.replace('All Shortcuts', 'All')

        # Limit length but keep readability
        if len(shortened) > 18:
            shortened = shortened[:15] + '...'

        return shortened

    def on_tab_changed(self, index):
        """Handle tab change events."""
        self._update_current_tab_content()
        self.update_statistics()

    def filter_shortcuts(self, search_text):
        """Filter shortcuts based on search text and filter combo."""
        search_text = search_text.lower()
        filter_type = self.filter_combo.currentText()

        if not search_text and filter_type == 'All Types':
            # No filter, clear filtered data and update current tab
            self.filtered_data = {}
            self._update_current_tab_content()
            return

        # Apply filters to all data
        self.filtered_data = {}
        best_match_tab = None
        best_match_count = 0

        for tab_name, tab_data in self.all_shortcuts_data.items():
            filtered_items = []

            for item in tab_data:
                # Apply type filter
                if filter_type == 'Shortcuts Only' and item['type'] != 'shortcut':
                    continue
                elif filter_type == 'Commands Only' and item['type'] != 'command':
                    continue

                # Apply search filter
                if search_text:
                    searchable_text = (
                        f'{item["name"]} {item["shortcut"]} {item["description"]}'
                    )
                    if item.get('alias'):
                        searchable_text += f' {item["alias"]}'

                    if search_text not in searchable_text.lower():
                        continue

                filtered_items.append(item)

            # Store filtered data for this tab (even if empty)
            self.filtered_data[tab_name] = filtered_items

            # Find the tab with most matches (excluding "All Shortcuts" for priority)
            if tab_name != 'All Shortcuts' and len(filtered_items) > best_match_count:
                best_match_count = len(filtered_items)
                best_match_tab = tab_name

        # If we have search results, automatically select the best matching tab
        if search_text and best_match_tab and best_match_count > 0:
            self._select_tab_by_name(best_match_tab)
        else:
            # Just update the current tab content
            self._update_current_tab_content()

        self.update_statistics()

    def _update_current_tab_content(self):
        """Update the current tab's content based on current filters."""
        current_index = self.tab_widget.currentIndex()
        if current_index < 0:
            return

        # Clear the content area
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # Get the current tab name
        tab_display_name = self.tab_widget.tabText(current_index)

        # Map display name back to data key
        tab_name = None
        for key in self.all_shortcuts_data.keys():
            if self._shorten_tab_name(key) == tab_display_name:
                tab_name = key
                break

        if not tab_name:
            return

        # Use filtered data if filtering is active, otherwise use all data
        if self.filtered_data:
            tab_data = self.filtered_data.get(tab_name, [])
        else:
            tab_data = self.all_shortcuts_data.get(tab_name, [])

        # Create and show the table for this tab
        table_widget = self.create_table_widget(tab_data)
        self.content_layout.addWidget(table_widget)

    def _select_tab_by_name(self, tab_name):
        """Select a tab by its data name and trigger the content update."""
        target_display_name = self._shorten_tab_name(tab_name)

        for i in range(self.tab_widget.count()):
            tab_text = self.tab_widget.tabText(i)
            if tab_text == target_display_name:
                # Actually select the tab and trigger the change event
                self.tab_widget.setCurrentIndex(i)
                # Force the tab change event to fire
                self.on_tab_changed(i)
                break

    def apply_filter(self):
        """Apply the filter when combo box changes."""
        self.filter_shortcuts(self.search_box.text())

    def focus_search(self):
        """Focus the search box."""
        self.search_box.setFocus()
        self.search_box.selectAll()
        """Focus the search box."""
        self.search_box.setFocus()
        self.search_box.selectAll()

    def copy_current_tab(self):
        """Copy current tab content to clipboard."""
        # Get the current table from the content area
        current_table = None
        for i in range(self.content_layout.count()):
            widget = self.content_layout.itemAt(i).widget()
            if isinstance(widget, QTableWidget):
                current_table = widget
                break

        if not current_table:
            return

        # Get table data
        text_lines = []
        tab_name = self.tab_widget.tabText(self.tab_widget.currentIndex())
        text_lines.append(f'{tab_name.upper()}')
        text_lines.append('=' * 80)
        text_lines.append('')

        # Add headers
        headers = []
        for col in range(current_table.columnCount()):
            header_item = current_table.horizontalHeaderItem(col)
            headers.append(header_item.text() if header_item else f'Column {col}')

        text_lines.append('\t'.join(headers))
        text_lines.append('-' * 80)

        # Add data rows
        for row in range(current_table.rowCount()):
            row_data = []
            for col in range(current_table.columnCount()):
                item = current_table.item(row, col)
                row_data.append(item.text() if item else '')
            text_lines.append('\t'.join(row_data))

        # Copy to clipboard
        text_content = '\n'.join(text_lines)
        QtCompat.copy_to_clipboard(text_content)

        QMessageBox.information(
            self, 'Copied', 'Current tab content copied to clipboard!'
        )

    def export_shortcuts(self):
        """Export shortcuts using file dialog."""
        default_filename = f'shortcuts_{self.gui.name.replace(" ", "_")}.txt'
        default_path = Path(QtCompat.get_documents_path()) / default_filename

        filename = QtCompat.get_save_filename(
            self,
            'Export Shortcuts',
            str(default_path),
            'Text Files (*.txt);;CSV Files (*.csv);;All Files (*.*)',
        )

        if not filename:
            return

        try:
            file_path = Path(filename)

            if file_path.suffix.lower() == '.csv':
                self._export_csv(file_path)
            else:
                self._export_text(file_path)

            QMessageBox.information(
                self, 'Export Complete', f'Shortcuts exported to:\n{filename}'
            )

        except Exception as e:
            QMessageBox.critical(
                self, 'Export Failed', f'Failed to export shortcuts:\n{str(e)}'
            )
            logger.error(f'Failed to export shortcuts: {e}')

    def _export_text(self, file_path):
        """Export shortcuts as text file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f'Keyboard Shortcuts and Commands - {self.gui.name}\n')
            f.write('=' * 80 + '\n\n')

            for tab_name, tab_data in self.all_shortcuts_data.items():
                if tab_name == 'All Shortcuts':
                    continue

                f.write(f'{tab_name.upper()}\n')
                f.write('-' * 80 + '\n\n')

                for item in tab_data:
                    f.write(
                        f'{item["name"]:<35} {item["shortcut"]:<20} {item["description"]}\n'
                    )
                    if item.get('alias') and item.get('type') == 'shortcut':
                        f.write(f'{"":<35} (:{item["alias"]:<19}) Snippet command\n')
                f.write('\n')

    def _export_csv(self, file_path):
        """Export shortcuts as CSV file."""
        import csv

        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Write header
            writer.writerow(
                ['Tab', 'Name', 'Shortcut', 'Description', 'Type', 'Alias', 'Source']
            )

            # Write data
            for tab_name, tab_data in self.all_shortcuts_data.items():
                if tab_name == 'All Shortcuts':
                    continue

                for item in tab_data:
                    writer.writerow(
                        [
                            tab_name,
                            item['name'],
                            item['shortcut'],
                            item['description'],
                            item['type'],
                            item.get('alias', ''),
                            item.get('source', ''),
                        ]
                    )

    def update_statistics(self):
        """Update the statistics label."""
        # Get the current table from the content area
        current_table = None
        for i in range(self.content_layout.count()):
            widget = self.content_layout.itemAt(i).widget()
            if isinstance(widget, QTableWidget):
                current_table = widget
                break

        if current_table:
            count = current_table.rowCount()
            tab_name = self.tab_widget.tabText(self.tab_widget.currentIndex())
            self.stats_label.setText(f'{tab_name}: {count} items')
        else:
            total_count = sum(
                len(data) for data in self.all_shortcuts_data.values() if data
            )
            self.stats_label.setText(f'Total shortcuts: {total_count}')

    def _format_shortcut(self, shortcut):
        """Format shortcut for display."""
        if not shortcut:
            return ''
        if isinstance(shortcut, (tuple, list)):
            return ', '.join([self._format_shortcut(s) for s in shortcut])
        if hasattr(shortcut, 'toString'):
            return str(shortcut.toString()) or ''
        return str(shortcut).lower()


def show_enhanced_shortcuts_dialog(gui):
    """Show the enhanced shortcuts dialog window."""
    try:
        # Create and show the dialog
        dialog = EnhancedShortcutsDialog(gui, parent=gui)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
        return dialog
    except Exception as e:
        logger.error(f'Failed to create enhanced shortcuts dialog: {e}')
        # Fall back to console output
        for actions in gui.actions:
            actions.show_shortcuts()
        return None


# Backward compatibility - keep the original dialog available
def show_shortcuts_dialog(gui):
    """Show the enhanced shortcuts dialog window (updated default)."""
    return show_enhanced_shortcuts_dialog(gui)
