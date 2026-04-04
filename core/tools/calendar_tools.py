"""Tools for calendar scheduling and meeting management"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List


def confirm_groups(groups_json: str) -> str:
    """
    Wait for user confirmation before scheduling meetings.

    Args:
        groups_json: JSON string with grouped candidates

    Returns:
        JSON with confirmation status
    """
    try:
        groups_data = json.loads(groups_json)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON input"})

    return json.dumps({
        "status": "pending_confirmation",
        "groups": groups_data,
        "action_url": "/api/confirm-and-schedule",
        "message": "Ready to schedule meetings. Awaiting user confirmation.",
    })


def create_meeting_plan(groups_json: str) -> str:
    """
    Generate a meeting plan including kick-off, syncs, and 1:1s.

    Args:
        groups_json: JSON string with grouped candidates

    Returns:
        JSON string with meeting schedule
    """
    try:
        groups_data = json.loads(groups_json)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON input"})

    groups = groups_data.get("groups", {})
    meetings = []
    base_date = datetime.now() + timedelta(days=1)

    meeting_id = 1

    for domain, teams in groups.items():
        for team_idx, team in enumerate(teams):
            team_id = team.get("team_id", f"team_{team_idx}")
            members = team.get("members", [])

            # Get member emails/names
            participant_names = []
            for member in members:
                if isinstance(member, dict):
                    participant_names.append(member.get("name", "Unknown"))
                else:
                    participant_names.append(str(member))

            # Kick-off meeting
            kickoff_date = base_date + timedelta(days=team_idx)
            meetings.append({
                "id": f"meeting_{meeting_id}",
                "type": "kick_off",
                "title": f"{domain.title()} Team Kick-off - {team_id}",
                "team_id": team_id,
                "domain": domain,
                "date": kickoff_date.isoformat(),
                "time": "10:00",
                "duration": 60,
                "participants": participant_names,
                "description": f"Kick-off meeting for {domain} team to align on goals and expectations",
            })
            meeting_id += 1

            # Weekly sync (1 week after kick-off)
            sync_date = kickoff_date + timedelta(days=7)
            meetings.append({
                "id": f"meeting_{meeting_id}",
                "type": "weekly_sync",
                "title": f"{domain.title()} Team Weekly Sync - {team_id}",
                "team_id": team_id,
                "domain": domain,
                "date": sync_date.isoformat(),
                "time": "10:00",
                "duration": 30,
                "participants": participant_names,
                "description": "Weekly team sync to discuss progress and blockers",
                "recurring": "weekly",
            })
            meeting_id += 1

            # 1:1 meetings for each team member (2 days after kick-off)
            oneonone_date = kickoff_date + timedelta(days=2)
            for member_idx, member_name in enumerate(participant_names):
                meetings.append({
                    "id": f"meeting_{meeting_id}",
                    "type": "one_on_one",
                    "title": f"1:1 - {member_name}",
                    "team_id": team_id,
                    "domain": domain,
                    "date": (oneonone_date + timedelta(hours=member_idx)).isoformat(),
                    "time": f"{9 + member_idx:02d}:00",
                    "duration": 30,
                    "participants": [member_name, "Manager"],
                    "description": f"One-on-one with {member_name} to understand goals and expectations",
                })
                meeting_id += 1

    return json.dumps({
        "meetings": meetings,
        "total_meetings": len(meetings),
        "status": "planned",
        "requires_confirmation": True,
    })


def send_to_google_calendar(meetings_json: str) -> str:
    """
    Send meetings to Google Calendar API.

    Args:
        meetings_json: JSON string with meeting plan

    Returns:
        JSON with scheduling results
    """
    try:
        data = json.loads(meetings_json)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON input"})

    meetings = data.get("meetings", [])

    # For demo purposes, simulate sending to Google Calendar
    # In production, this would call the actual Google Calendar API
    results = {
        "total": len(meetings),
        "scheduled": len(meetings),
        "failed": 0,
        "meetings_sent": [],
    }

    for meeting in meetings:
        results["meetings_sent"].append({
            "id": meeting.get("id"),
            "title": meeting.get("title"),
            "status": "scheduled",
            "calendar_link": f"https://calendar.google.com/calendar/u/0/r/eventedit/{meeting.get('id')}",
        })

    results["status"] = "all_scheduled" if results["failed"] == 0 else "partial_failure"
    results["message"] = (
        f"Successfully scheduled {results['scheduled']} meetings"
        if results["failed"] == 0
        else f"Scheduled {results['scheduled']} meetings, {results['failed']} failed"
    )

    return json.dumps(results)


def send_confirmation_email(participants_json: str) -> str:
    """
    Send confirmation emails to all participants.

    Args:
        participants_json: JSON string with participant data

    Returns:
        JSON with email sending results
    """
    try:
        data = json.loads(participants_json)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON input"})

    # For demo purposes, simulate sending emails
    # In production, this would use an email service like SendGrid or AWS SES

    meetings = data.get("meetings", [])
    participants_set = set()

    for meeting in meetings:
        for participant in meeting.get("participants", []):
            participants_set.add(participant)

    results = {
        "total_participants": len(participants_set),
        "emails_sent": len(participants_set),
        "failed": 0,
        "recipients": list(participants_set),
        "status": "all_sent",
        "message": f"Confirmation emails sent to {len(participants_set)} participants",
    }

    return json.dumps(results)
