import asyncio
import pytest

from improver.integration import IntegrationRunner
from improver.models import PlanAndCode, FileEdit
from safe_io import SafeIO

# A lightweight fake IntegratorTask to simulate LLM behavior
class FakeIntegratorTask:
    def __init__(self, responses):
        # responses is a list of PlanAndCode objects to return in sequence
        self.responses = responses
        self.calls = 0
        self.error_contexts = []

    async def execute(self, proposals=None, error_context=None):
        self.error_contexts.append(error_context)
        resp = self.responses[self.calls]
        self.calls += 1
        return resp


def make_bad_plan():
    return PlanAndCode(reasoning="dummy", edits=[FileEdit(file_path='a.py', code='def f(:)')])


def make_good_plan():
    return PlanAndCode(reasoning="dummy", edits=[FileEdit(file_path='a.py', code='def f():\n    return 1')])


@pytest.mark.asyncio
async def test_integration_self_correction_success_on_final_attempt():
    safe_io = SafeIO()
    runner = IntegrationRunner("Goal", safe_io)
    # First two attempts produce a syntax error, third succeeds
    fake = FakeIntegratorTask(responses=[make_bad_plan(), make_bad_plan(), make_good_plan()])
    runner.integrator_task = fake

    proposals = [
        {'id': 'prop1', 'plan': 'Plan', 'edits': [ {'file_path': 'a.py', 'code': 'def f(:)'} ]}
    ]

    result = await runner.run(proposals)
    assert isinstance(result, PlanAndCode)
    assert result.edits[0].code == 'def f():\n    return 1'


@pytest.mark.asyncio
async def test_integration_self_correction_failure_after_max_retries():
    safe_io = SafeIO()
    runner = IntegrationRunner("Goal", safe_io)
    # All three attempts fail syntax check
    fake = FakeIntegratorTask(responses=[make_bad_plan(), make_bad_plan(), make_bad_plan()])
    runner.integrator_task = fake

    proposals = [
        {'id': 'prop1', 'plan': 'Plan', 'edits': [ {'file_path': 'a.py', 'code': 'def f(:)'} ]}
    ]

    result = await runner.run(proposals)
    assert result is None


@pytest.mark.asyncio
async def test_integration_error_context_passed_on_retry():
    safe_io = SafeIO()
    runner = IntegrationRunner("Goal", safe_io)
    # First two attempts fail; third succeeds
    bad = make_bad_plan()
    good = make_good_plan()
    fake = FakeIntegratorTask(responses=[bad, bad, good])
    runner.integrator_task = fake

    proposals = [
        {'id': 'prop1', 'plan': 'Plan', 'edits': [ {'file_path': 'a.py', 'code': 'def f(:)'} ]}
    ]

    result = await runner.run(proposals)
    assert isinstance(result, PlanAndCode)
    # Ensure error_context was passed on at least one retry (non-None for retry attempts)
    assert any(ctx is not None for ctx in fake.error_contexts[1:3])
