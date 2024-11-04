from nicegui import ui


def series_table():
    columns = [
        {
            "name": "entity_name",
            "label": "Entity Name",
            "field": "entity_name",
            "required": True,
            "align": "left",
            "sortable": True,
        },
        {"name": "latest_chapter", "label": "Latest Chapter", "field": "latest_chapter", "sortable": True},
        {"name": "updated", "label": "Metadata Updated", "field": "updated", "sortable": True},
        {
            "name": "latest_chapter_date",
            "label": "Chapter Updated",
            "field": "latest_chapter_date",
            "sortable": True,
        },
        {
            "name": "tracked",
            "label": "Tracked",
            "field": "tracked",
            "sortable": True,
        },
        {
            "name": "plugin",
            "label": "Plugin",
            "field": "plugin",
            "sortable": True,
        },
        {"name": "entity_id", "label": "Entity ID", "field": "entity_id", "sortable": True},
    ]
    table = ui.table(columns=columns, rows=[], row_key="entity_name")
    table.add_slot(
        "body-cell-updated",
        """
        <q-td key="updated" :props="props">
            <q-badge
                :color="
                Date.parse(props.value) > Date.now() - (30 * 86400000) ? 'green' :
                    Date.parse(props.value) > Date.now() - (90 * 86400000) ? 'orange' : 'red'
            ">
                {{ new Date(props.value).toISOString().substring(0, 16) }}
            </q-badge>
        </q-td>
    """,
    )
    table.add_slot(
        "body-cell-latest_chapter_date",
        """
        <q-td key="latest_chapter_date" :props="props">
            <q-badge
                :color="
                Date.parse(props.value) > Date.now() - (30 * 86400000) ? 'green' :
                    Date.parse(props.value) > Date.now() - (90 * 86400000) ? 'orange' : 'red'
            ">
                {{ new Date(props.value).toISOString().substring(0, 16) }}
            </q-badge>
        </q-td>
    """,
    )
    return table
