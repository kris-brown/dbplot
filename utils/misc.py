from typing import TypeVar,List
A = TypeVar('A')

def flatten(lol : List[List[A]]) -> List[A]:
    """
    Convert list of lists to a single list via concatenation
    """
    return [item for sublist in lol for item in sublist]
