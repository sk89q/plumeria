import pytest
from plumeria.service import ServiceLocator, EARLY, NORMAL, LATE


@pytest.mark.asyncio
async def test_priority():
    locator = ServiceLocator()
    executed = []

    @locator.provide("test", priority=NORMAL)
    async def normal():
        executed.append("normal")

    @locator.provide("test", priority=EARLY)
    async def early():
        executed.append("early")

    @locator.provide("test", priority=LATE)
    async def late():
        executed.append("late")

    await locator.first_value("test")
    assert ['early', 'normal', 'late'] == executed


@pytest.mark.asyncio
async def test_first_value():
    locator = ServiceLocator()

    @locator.provide("test", priority=NORMAL)
    async def normal():
        return "apple"

    @locator.provide("test", priority=EARLY)
    async def early():
        return None

    @locator.provide("test", priority=LATE)
    async def late():
        return "banana"

    assert "apple" == await locator.first_value("test")


if __name__ == "__main__":
    pytest.main()
