import abc

from schedule.generators import Session


class ConnectorInterface(abc.ABC):
    """
    An abstract base class defining the interface for connectors.

    Connectors are responsible for transferring sessions to external systems. For example, TelegramConnector
    communicates with TelegramService, including registration of answers and transmitting data back and forth.

    All connectors must implement the `transfer` method.

    Attributes:
        None
    """

    @abc.abstractmethod
    def transfer(self, sessions: list[Session]):
        """
        Transfer sessions to an external system.

        This method must be implemented by concrete subclasses.

        Args:
            sessions (list[Session]): A list of Session instances to be transferred.

        Returns:
            None
        """
        pass
