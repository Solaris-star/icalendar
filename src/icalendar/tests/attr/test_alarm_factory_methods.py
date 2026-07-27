"""Tests for Alarm.new_display(), Alarm.new_audio(), and Alarm.new_email()."""

from datetime import datetime, timedelta, timezone
from inspect import Parameter, signature

import pytest

from icalendar.cal.alarm import Alarm
from icalendar.error import InvalidCalendar
from icalendar.prop import vCalAddress
from icalendar.prop.binary import vBinary


def test_new_display_sets_action():
    alarm = Alarm.new_display("Reminder", timedelta(minutes=-15))
    assert alarm["ACTION"] == "DISPLAY"


def test_new_display_sets_description():
    alarm = Alarm.new_display("Stand-up in 15 min", timedelta(minutes=-15))
    assert alarm.description == "Stand-up in 15 min"


def test_new_display_sets_relative_trigger():
    trigger = timedelta(minutes=-30)
    alarm = Alarm.new_display("desc", trigger)
    assert alarm.TRIGGER == trigger


def test_new_display_sets_absolute_trigger():
    trigger = datetime(2025, 1, 1, 9, 0, tzinfo=timezone.utc)
    alarm = Alarm.new_display("desc", trigger)
    assert alarm.TRIGGER == trigger


def test_new_display_with_repeat():
    alarm = Alarm.new_display(
        "desc", timedelta(minutes=-10), duration=timedelta(minutes=5), repeat=2
    )
    assert alarm.DURATION == timedelta(minutes=5)
    assert alarm.REPEAT == 2


def test_new_display_requires_description():
    with pytest.raises(InvalidCalendar, match="description"):
        Alarm.new_display("", timedelta(minutes=-5))


def test_new_display_requires_trigger():
    with pytest.raises(InvalidCalendar, match="trigger"):
        Alarm.new_display("desc", None)


@pytest.mark.parametrize(
    "alarm_fn",
    [
        lambda: Alarm.new_display(
            "desc", timedelta(minutes=-5), duration=timedelta(minutes=1)
        ),
        lambda: Alarm.new_audio(timedelta(minutes=-5), duration=timedelta(minutes=1)),
        lambda: Alarm.new_email(
            "S",
            "D",
            timedelta(minutes=-30),
            vCalAddress("mailto:a@example.com"),
            duration=timedelta(minutes=5),
        ),
    ],
    ids=["display", "audio", "email"],
)
def test_duration_without_repeat_raises(alarm_fn):
    with pytest.raises(InvalidCalendar, match="DURATION and REPEAT"):
        alarm_fn()


@pytest.mark.parametrize(
    "alarm_fn",
    [
        lambda: Alarm.new_display("desc", timedelta(minutes=-5), repeat=3),
        lambda: Alarm.new_audio(timedelta(minutes=-5), repeat=3),
        lambda: Alarm.new_email(
            "S",
            "D",
            timedelta(minutes=-30),
            vCalAddress("mailto:a@example.com"),
            repeat=2,
        ),
    ],
    ids=["display", "audio", "email"],
)
def test_repeat_without_duration_raises(alarm_fn):
    with pytest.raises(InvalidCalendar, match="DURATION and REPEAT"):
        alarm_fn()


def test_new_audio_sets_action():
    alarm = Alarm.new_audio(timedelta(minutes=-5))
    assert alarm["ACTION"] == "AUDIO"


def test_new_audio_sets_trigger():
    trigger = timedelta(minutes=-5)
    alarm = Alarm.new_audio(trigger)
    assert alarm.TRIGGER == trigger


def test_new_audio_without_attach():
    alarm = Alarm.new_audio(timedelta(minutes=-5))
    assert alarm.get("ATTACH") is None


def test_new_audio_with_attach():
    uri = "ftp://example.com/pub/sounds/bell-01.aud"
    alarm = Alarm.new_audio(timedelta(minutes=-5), attach=uri)
    assert str(alarm["ATTACH"]) == uri


def test_new_audio_with_empty_attach_ignored():
    alarm = Alarm.new_audio(timedelta(minutes=-5), attach="")
    assert alarm.get("ATTACH") is None


def test_new_audio_with_repeat():
    alarm = Alarm.new_audio(
        timedelta(minutes=-5), duration=timedelta(minutes=2), repeat=3
    )
    assert alarm.DURATION == timedelta(minutes=2)
    assert alarm.REPEAT == 3


def test_new_audio_requires_trigger():
    with pytest.raises(InvalidCalendar, match="trigger"):
        Alarm.new_audio(None)


def test_new_audio_with_bytes_attach():
    data = b"\x00\x01\x02\x03"
    alarm = Alarm.new_audio(timedelta(minutes=-5), attach=data)
    assert isinstance(alarm["ATTACH"], vBinary)
    assert alarm["ATTACH"] == vBinary(data)


def test_new_email_sets_action():
    alarm = Alarm.new_email(
        summary="Reminder",
        description="Your meeting starts soon.",
        trigger=timedelta(minutes=-30),
        attendees=[vCalAddress("mailto:user@example.com")],
    )
    assert alarm["ACTION"] == "EMAIL"


def test_new_email_sets_summary_and_description():
    alarm = Alarm.new_email(
        summary="Subject",
        description="Body",
        trigger=timedelta(minutes=-30),
        attendees=[vCalAddress("mailto:user@example.com")],
    )
    assert alarm.summary == "Subject"
    assert alarm.description == "Body"


def test_new_email_sets_attendees():
    attendees = [
        vCalAddress("mailto:a@example.com"),
        vCalAddress("mailto:b@example.com"),
    ]
    alarm = Alarm.new_email(
        summary="S",
        description="D",
        trigger=timedelta(minutes=-30),
        attendees=attendees,
    )
    assert len(alarm.attendees) == 2
    assert str(alarm.attendees[0]) == "mailto:a@example.com"
    assert str(alarm.attendees[1]) == "mailto:b@example.com"


def test_new_email_with_attachment():
    alarm = Alarm.new_email(
        summary="S",
        description="D",
        trigger=timedelta(minutes=-30),
        attendees=[vCalAddress("mailto:user@example.com")],
        attachments=["https://example.com/file.pdf"],
    )
    assert "ATTACH" in alarm
    assert str(alarm["ATTACH"]) == "https://example.com/file.pdf"


def test_new_email_requires_summary():
    with pytest.raises(InvalidCalendar, match="summary"):
        Alarm.new_email(
            summary="",
            description="D",
            trigger=timedelta(minutes=-30),
            attendees=[vCalAddress("mailto:user@example.com")],
        )


def test_new_email_requires_description():
    with pytest.raises(InvalidCalendar, match="description"):
        Alarm.new_email(
            summary="S",
            description="",
            trigger=timedelta(minutes=-30),
            attendees=[vCalAddress("mailto:user@example.com")],
        )


def test_new_email_requires_trigger():
    with pytest.raises(InvalidCalendar, match="trigger"):
        Alarm.new_email(
            summary="S",
            description="D",
            trigger=None,
            attendees=[vCalAddress("mailto:user@example.com")],
        )


def test_new_email_requires_attendees():
    with pytest.raises(InvalidCalendar, match="attendee"):
        Alarm.new_email(
            summary="S",
            description="D",
            trigger=timedelta(minutes=-30),
            attendees=[],
        )


def test_new_email_single_attendee():
    alarm = Alarm.new_email(
        summary="S",
        description="D",
        trigger=timedelta(minutes=-30),
        attendees=vCalAddress("mailto:user@example.com"),
    )
    assert len(alarm.attendees) == 1
    assert str(alarm.attendees[0]) == "mailto:user@example.com"


def test_new_email_single_attachment():
    alarm = Alarm.new_email(
        summary="S",
        description="D",
        trigger=timedelta(minutes=-30),
        attendees=[vCalAddress("mailto:user@example.com")],
        attachments="https://example.com/file.pdf",
    )
    assert "ATTACH" in alarm
    assert str(alarm["ATTACH"]) == "https://example.com/file.pdf"


FACTORY_CALLS = [
    pytest.param(
        lambda **kw: Alarm.new_display("desc", timedelta(minutes=-15), **kw),
        id="display",
    ),
    pytest.param(
        lambda **kw: Alarm.new_audio(timedelta(minutes=-5), **kw),
        id="audio",
    ),
    pytest.param(
        lambda **kw: Alarm.new_email(
            summary="S",
            description="D",
            trigger=timedelta(minutes=-30),
            attendees=[vCalAddress("mailto:user@example.com")],
            **kw,
        ),
        id="email",
    ),
]


@pytest.mark.parametrize("factory", FACTORY_CALLS)
def test_factory_forwards_relationship_attributes(factory):
    """All Alarm factory methods forward the RFC 9253 attributes to Alarm.new()."""
    alarm = factory(
        links="https://example.com/link",
        related_to="parent-uid",
        refids="refid-1",
        concepts="https://example.com/concept",
    )
    assert alarm.links == ["https://example.com/link"]
    assert alarm.related_to == ["parent-uid"]
    assert alarm.refids == ["refid-1"]
    assert alarm.concepts == ["https://example.com/concept"]


@pytest.mark.parametrize("factory", FACTORY_CALLS)
def test_factory_uid_is_forwarded(factory):
    """All Alarm factory methods forward ``uid`` to Alarm.new()."""
    alarm = factory(uid="alarm-uid-1")
    assert alarm.uid == "alarm-uid-1"


@pytest.mark.parametrize("factory", FACTORY_CALLS)
def test_factory_optional_parameters_are_keyword_compatible(factory):
    """Optional parameters stay addressable by keyword."""
    alarm = factory(duration=timedelta(minutes=1), repeat=2)
    assert alarm["DURATION"].td == timedelta(minutes=1)
    assert alarm["REPEAT"] == 2


@pytest.mark.parametrize(
    "method",
    [Alarm.new, Alarm.new_display, Alarm.new_audio, Alarm.new_email],
    ids=["new", "display", "audio", "email"],
)
def test_optional_parameters_are_in_alphabetical_order(method):
    """Optional parameters of every Alarm factory are in alphabetical order.

    :meth:`Alarm.new` sets the convention, so the three action-specific
    factories have to follow it.
    """
    optional = [
        name
        for name, parameter in signature(method).parameters.items()
        if parameter.default is not Parameter.empty
    ]
    assert optional == sorted(optional)
