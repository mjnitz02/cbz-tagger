"""Navigation bar component for the Reflex GUI."""

import reflex as rx

from cbz_tagger.common.env import AppEnv


def navbar() -> rx.Component:
    """Create the navigation bar with tabs.

    Returns:
        A Reflex component containing the navigation bar
    """
    env = AppEnv()

    return rx.box(
        rx.hstack(
            rx.heading(f"CBZ Tagger {env.VERSION}", size="7", weight="bold"),
            rx.spacer(),
            rx.hstack(
                rx.link("Series", href="/", color="white", _hover={"opacity": 0.8}),
                rx.link("Manage", href="/manage", color="white", _hover={"opacity": 0.8}),
                rx.link("Config", href="/config", color="white", _hover={"opacity": 0.8}),
                rx.link("Logs", href="/logs", color="white", _hover={"opacity": 0.8}),
                spacing="6",
            ),
            justify="between",
            align="center",
            padding="1rem",
        ),
        background_color="#2F4F4F",
        color="white",
        width="100%",
        position="sticky",
        top="0",
        z_index="999",
    )
