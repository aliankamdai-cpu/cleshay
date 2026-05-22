"""Main entry point for the news report application."""

from gui import NewsReportApp


def main():
    """Run the news report application."""
    app = NewsReportApp()
    app.mainloop()


if __name__ == "__main__":
    main()