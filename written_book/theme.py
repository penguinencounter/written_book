from asset_resource import AssetResource


class Theme:
    """
    Represents a theme for the documentation. Usually these are called "light" and "dark".
    """
    def __init__(self, name: str):
        self.name = name
