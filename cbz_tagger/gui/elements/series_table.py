from nicegui import ui


def series_table():
    columns = [
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
    table = ui.table(columns=columns, rows=[], row_key="entity_name").classes("table-auto").props("flat dense")
    table.add_slot(
        "body-cell-entity_name",
        """
        <q-td :props="props">
            <a :href="props.value.link">{{ props.value.name }}</a>
        </q-td>
        """,
    )
    table.add_slot(
        "body-cell-updated",
        """
        <q-td :props="props">
            <q-badge
                :color="
                Date.parse(props.value) > Date.now() - (45 * 86400000) ? 'green' :
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
        <q-td :props="props">
            <q-badge
                :color="
                Date.parse(props.value) > Date.now() - (45 * 86400000) ? 'green' :
                    Date.parse(props.value) > Date.now() - (90 * 86400000) ? 'orange' : 'red'
            ">
                {{ new Date(props.value).toISOString().substring(0, 16) }}
            </q-badge>
        </q-td>
    """,
    )
    table.add_slot(
        "body-cell-plugin",
        """
        <q-td :props="props">
            <a :href="props.value.link">{{ props.value.name }}</a>
        </q-td>
        """,
    )
    return table
