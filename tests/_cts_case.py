"""A dataclass for a test case suitable for the CTS JSON schema."""

from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Dict
from typing import List
from typing import Mapping
from typing import Optional
from typing import Sequence
from typing import Union


@dataclass
class Case:
    name: str
    selector: str
    document: Union[Mapping[str, Any], Sequence[Any], None] = None
    result: Any = None
    results: Optional[List[Any]] = None
    result_paths: Optional[List[str]] = None
    results_paths: Optional[List[List[str]]] = None
    invalid_selector: Optional[bool] = None
    tags: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        rv: Dict[str, Any] = {
            "name": self.name,
            "selector": self.selector,
        }

        if self.document is not None:
            rv["document"] = self.document

            if self.result is not None:
                rv["result"] = self.result
                rv["result_paths"] = self.result_paths
            else:
                rv["results"] = self.results
                rv["results_paths"] = self.results_paths
        else:
            assert self.invalid_selector
            rv["invalid_selector"] = True

        rv["tags"] = self.tags

        return rv
