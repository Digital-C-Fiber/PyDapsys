from abc import ABC, abstractmethod

import neo


class INeoConverter(ABC):
    """Interface for neo converters"""

    @abstractmethod
    def to_neo(self) -> neo.Block:
        """
        Create a neo structure based on the given recording
        :return: A neo block containing the data from the recording
        """
        ...