import time


class SimpleProgressBar:
    """Simple progress bar."""

    def __init__(self, total, desc="Progress", bar_length=40):
        """__init__."""
        self.total = total
        self.desc = desc
        self.bar_length = bar_length
        self.current = 0
        self.start_time = time.time()

    def update(self, n=1):
        """Update progress bar."""
        self.current += n
        self._render()

    def _render(self):
        """Render progress bar."""
        if self.total <= 0:
            return

        # Calculate percentage
        percent = (self.current / self.total) * 100

        # Calculate filled characters count
        filled = int(self.bar_length * self.current / self.total)

        # Create progress bar string
        bar = "█" * filled + "░" * (self.bar_length - filled)

        # Elapsed time
        elapsed = time.perf_counter() - self.start_time
        if self.current > 0:
            eta = (elapsed / self.current) * (self.total - self.current)
            eta_str = (
                f"{int(eta)}s" if eta < 60 else f"{int(eta // 60)}m {int(eta % 60)}s"
            )
        else:
            eta_str = "?"

        # Output in one line
        print(
            f"\r{self.desc}: [{bar}] {percent:.1f}%  [{self.current}/{self.total}]  ETA: {eta_str}",
            end="",
        )

        # If completed - move to new line
        if self.current >= self.total:
            print()
