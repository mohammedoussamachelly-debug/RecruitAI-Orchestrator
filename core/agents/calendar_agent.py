"""Calendar Agent - Schedules meetings and syncs with Google Calendar"""

from core.tools.calendar_tools import (
    confirm_groups,
    create_meeting_plan,
    send_to_google_calendar,
    send_confirmation_email,
)


def create_calendar_tools():
    """Create tool functions for calendar management"""

    def plan_and_schedule_meetings(groups_json):
        """Create meeting plan"""
        meeting_plan = create_meeting_plan(groups_json)
        return meeting_plan

    def schedule_meetings(meetings_json):
        """Send meetings to Google Calendar"""
        schedule_result = send_to_google_calendar(meetings_json)
        email_result = send_confirmation_email(meetings_json)
        return schedule_result

    return [plan_and_schedule_meetings, schedule_meetings]


def create_calendar_agent():
    """Create Calendar Agent"""
    return {
        "role": "Calendar & Meeting Specialist",
        "goal": "Create and manage team meetings",
    }


def create_calendar_task(agent):
    """Create task for Calendar Agent"""
    return {
        "description": "Create and schedule meetings for all teams",
        "agent": agent,
    }
