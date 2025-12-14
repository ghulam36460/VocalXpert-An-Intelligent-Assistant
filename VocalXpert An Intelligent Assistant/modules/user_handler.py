"""
User Handler Module - User Profile Management

Manages user data including name, gender, and avatar selection.
"""

import pickle
import os

# Get the module directory for file paths
_module_dir = os.path.dirname(os.path.abspath(__file__))
_project_dir = os.path.dirname(_module_dir)
_user_data_dir = os.path.join(_project_dir, 'userData')
_user_data_file = os.path.join(_user_data_dir, 'userData.pck')

# Ensure userData directory exists
if not os.path.exists(_user_data_dir):
    os.makedirs(_user_data_dir)

class UserData:
    def __init__(self):
        self.name = 'User'
        self.gender = 'None'
        self.userphoto = 0

    def extractData(self):
        """Load user data from pickle file."""
        try:
            with open(_user_data_file, 'rb') as file:
                details = pickle.load(file)
                self.name = details.get('name', 'User')
                self.gender = details.get('gender', 'None')
                self.userphoto = details.get('userphoto', 0)
        except FileNotFoundError:
            # Create default user data
            self.updateData('User', 'None', 0)
        except Exception as e:
            print(f"Error loading user data: {e}")

    def updateData(self, name, gender, userphoto):
        """Save user data to pickle file."""
        try:
            with open(_user_data_file, 'wb') as file:
                details = {'name': name, 'gender': gender, 'userphoto': userphoto}
                pickle.dump(details, file)
            self.name = name
            self.gender = gender
            self.userphoto = userphoto
        except Exception as e:
            print(f"Error saving user data: {e}")

    def getName(self):
        return self.name

    def getGender(self):
        return self.gender

    def getUserPhoto(self):
        return self.userphoto


def UpdateUserPhoto(avatar):
    """Update just the user's avatar."""
    u = UserData()
    u.extractData()
    u.updateData(u.getName(), u.getGender(), avatar)


def UpdateUserName(name):
    """Update the user's name."""
    u = UserData()
    u.extractData()
    u.updateData(name, u.getGender(), u.getUserPhoto())


def GetUserInfo():
    """Get all user information as a dict."""
    u = UserData()
    u.extractData()
    return {
        'name': u.getName(),
        'gender': u.getGender(),
        'avatar': u.getUserPhoto()
    }
