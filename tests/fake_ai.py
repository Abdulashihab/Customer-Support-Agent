import copy
import json
from types import SimpleNamespace


class FakeClient:
    """Pretends to be the AI. It returns the answers we prepared, one by one."""

    def __init__(self, answers):
        self.answers = list(answers)
        self.requests = []   # what we sent to the "AI", for checking
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.requests.append(copy.deepcopy(kwargs["messages"]))
        return self.answers.pop(0)


def text_answer(text):
    message = SimpleNamespace(content=text, tool_calls=None)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def tool_answer(name, args):
    call = SimpleNamespace(
        id="call_1", function=SimpleNamespace(name=name, arguments=json.dumps(args))
    )
    message = SimpleNamespace(content=None, tool_calls=[call])
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])