"""Exceptions for Pynecil."""


class CommunicationError(Exception):
    """Exception raised for communication failures."""

    def __init__(self, message="Communication error occurred."):
        """Initialize the CommunicationError exception.

        Parameters
        ----------
        message : str, optional
            Error message describing the communication failure, by default
            "Communication error occurred."

        """
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        """Return a string representation of the exception.

        Returns
        -------
        str
            Formatted string containing the class name and the error message.

        """
        return f"{self.__class__.__name__}: {self.message}"


class UpdateException(Exception):
    """Exception raised for errors fetching latest release from github."""
