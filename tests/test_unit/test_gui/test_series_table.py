from unittest.mock import MagicMock
from unittest.mock import patch

from cbz_tagger.gui.elements.series_table import series_table


@patch("cbz_tagger.gui.elements.series_table.ui.table")
def test_series_table(mock_ui_table):
    mock_table = MagicMock()
    mock_ui_table.return_value.classes.return_value.props.return_value = mock_table

    table = series_table()

    # pylint: disable=duplicate-code
    expected_columns = [
        {
            "name": "entity_name",
            "label": "Entity Name",
            "field": "entity_name",
            "required": True,
            "align": "left",
        },
        {
            "name": "entity_id",
            "label": "Entity ID",
            "field": "entity_id",
            "required": True,
            "align": "left",
            "sortable": True,
            "classes": "hidden",
            "headerClasses": "hidden",
        },
        {"name": "status", "label": "Status", "field": "status", "sortable": True},
        {
            "name": "tracked",
            "label": "Tracked",
            "field": "tracked",
            "sortable": True,
        },
        {"name": "latest_chapter", "label": "Chapter", "field": "latest_chapter", "sortable": True},
        {
            "name": "latest_chapter_date",
            "label": "Chapter Updated",
            "field": "latest_chapter_date",
            "sortable": True,
        },
        {
            "name": "updated",
            "label": "Metadata Updated",
            "field": "updated",
            "sortable": True,
            "classes": "hidden",
            "headerClasses": "hidden",
        },
        {
            "name": "plugin",
            "label": "Plugin",
            "field": "plugin",
            "sortable": True,
            "classes": "hidden",
            "headerClasses": "hidden",
        },
    ]

    mock_ui_table.assert_called_once_with(columns=expected_columns, rows=[], row_key="entity_name")
    assert table == mock_table
    assert mock_table.add_slot.call_count == 4
