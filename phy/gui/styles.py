# -----------------------------------------------------------------------------
# Dock widget
# -----------------------------------------------------------------------------

DOCK_TITLE_STYLESHEET = """
    * {
        padding: 0;
        margin: 0;
        border: 0;
        background: #232426;
        color: white;
    }

    QPushButton {
        padding: 4px;
        margin: 0 1px;
    }

    QCheckBox {
        padding: 2px 4px;
        margin: 0 1px;
    }

    QLabel {
        padding: 3px;
    }

    QPushButton:hover, QCheckBox:hover {
        background: #323438;
    }

    QPushButton:pressed {
        background: #53575e;
    }

    QPushButton:checked {
        background: #6c717a;
    }
"""


DOCK_STATUS_STYLESHEET = """
    * {
        padding: 0;
        margin: 0;
        border: 0;
        background: black;
        color: white;
    }

    QLabel {
        padding: 3px;
    }
"""
