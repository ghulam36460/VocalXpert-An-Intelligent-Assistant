"""
Todo Handler Module - Task List Management

Provides simple to-do list functionality for the voice assistant.
"""

from datetime import datetime
import os

# Get the module directory for file paths
_module_dir = os.path.dirname(os.path.abspath(__file__))
_project_dir = os.path.dirname(_module_dir)
_todo_dir = os.path.join(_project_dir, "userData")
_todo_file = os.path.join(_todo_dir, "toDoList.txt")

# Ensure userData directory exists
if not os.path.exists(_todo_dir):
    os.makedirs(_todo_dir)


def createList():
    """Create a new to-do list file with this date."""
    with open(_todo_file, "w") as f:
        present = datetime.now()
        dt_format = present.strftime("Date: %d/%m/%Y Time: %H:%M:%S\n")
        f.write(dt_format)


def toDoList(text):
    """
    Add an item to the to-do list.

    Args:
        text: The task to add

    Returns:
        str: Confirmation message
    """
    # Create file if it doesn't exist
    if not os.path.isfile(_todo_file):
        createList()

    # Check if list is from a previous day and reset
    try:
        with open(_todo_file, "r") as f:
            first_line = f.readline()
            if first_line.startswith("Date:"):
                date_str = first_line.split()[1]  # Get DD/MM/YYYY
                day = int(date_str.split("/")[0])
                time = datetime.now().day
                if time != day:
                    createList()
    except Exception:
        createList()

    # Add the new task
    with open(_todo_file, "a") as f:
        dt_format = datetime.now().strftime("%H:%M")
        # Clean up the text
        task = text.replace("add", "").replace("to do", "").replace("todo", "")
        task = task.replace("to my list", "").replace("to list", "").strip()
        if task:
            f.write(f"[{dt_format}] : {task}\n")
            return f"Added '{task}' to your list."

    return "Could not add to list. Please specify a task."


def showtoDoList():
    """
    Show all items in the to-do list.

    Returns:
        list: List of strings with tasks
    """
    if not os.path.isfile(_todo_file):
        return ["Your to-do list is empty. Say 'add to my list' to start!"]

    try:
        with open(_todo_file, "r") as f:
            lines = f.readlines()

        if len(lines) <= 1:
            return ["Your to-do list is empty. Say 'add to my list' to start!"]

        items = []
        for line in lines[1:]:  # Skip the date header
            line = line.strip()
            if line:
                items.append(line)

        if not items:
            return ["Your to-do list is empty."]

        result = [
            f"You have {len(items)} item{'s' if len(items) > 1 else ''} in your list:"
        ]
        result.extend(items)
        return result

    except Exception as e:
        return [f"Error reading to-do list: {str(e)}"]


def clearToDoList():
    """Clear the to-do list."""
    createList()
    return "To-do list cleared!"


def removeFromList(item_text):
    """Remove an item from the to-do list by text match."""
    if not os.path.isfile(_todo_file):
        return "Your to-do list is empty."

    try:
        with open(_todo_file, "r") as f:
            lines = f.readlines()

        # Find and remove matching item
        new_lines = [lines[0]]  # Keep header
        removed = False
        for line in lines[1:]:
            if item_text.lower() not in line.lower():
                new_lines.append(line)
            else:
                removed = True

        if removed:
            with open(_todo_file, "w") as f:
                f.writelines(new_lines)
            return f"Removed '{item_text}' from your list."
        else:
            return f"Couldn't find '{item_text}' in your list."

    except Exception as e:
        return f"Error: {str(e)}"
