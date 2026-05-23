"""Main entry point for the news report application."""

from gui import ModernNewsApp


def main():
    """Run the news report application."""
    app = ModernNewsApp()
    app.mainloop()


if __name__ == "__main__":
    main()