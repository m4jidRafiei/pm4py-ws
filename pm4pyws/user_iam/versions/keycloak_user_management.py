from keycloak import KeycloakOpenID

from pm4pyws.user_iam.interface.user_management import UserManagement

import traceback


class KeycloakUserManagement(UserManagement):
    def __init__(self, ex, parameters=None):
        if parameters is None:
            parameters = {}
        self.ex = ex
        self.server_url = parameters["server_url"]
        self.client_id = parameters["client_id"]
        self.realm_name = parameters["realm_name"]
        self.client_secret_key = parameters["client_secret_key"]

        self.keycloak_manager = KeycloakOpenID(server_url=self.server_url, client_id=self.client_id,
                                               realm_name=self.realm_name, client_secret_key=self.client_secret_key)

        UserManagement.__init__(self, ex)

    def do_login(self, user, password):
        """
        Logs in a user and returns a session id

        Parameters
        ------------
        user
            Username
        password
            Password

        Returns
        ------------
        session_id
            Session ID
        """
        try:
            token = self.keycloak_manager.token(user, password)
            return token['access_token']
        except:
            # traceback.print_exc()
            pass
        return None

    def check_session_validity(self, session_id):
        """
        Checks the validity of a session

        Parameters
        ------------
        session_id
            Session ID

        Returns
        ------------
        boolean
            Boolean value
        """
        validity = False
        try:
            if not (str(session_id) == "null"):
                userinfo = self.keycloak_manager.userinfo(session_id)
                if type(userinfo["preferred_username"]) is str:
                    if userinfo["preferred_username"]:
                        validity = True
        except:
            # traceback.print_exc()
            pass
        return validity

    def get_user_from_session(self, session_id):
        """
        Gets the user from the session

        Parameters
        ------------
        session_id
            Session ID

        Returns
        ------------
        user
            User ID
        """
        user = None
        try:
            if not (str(session_id) == "null"):
                userinfo = self.keycloak_manager.userinfo(session_id)
                if type(userinfo["preferred_username"]) is str:
                    if userinfo["preferred_username"]:
                        user = userinfo["preferred_username"]
        except:
            # traceback.print_exc()
            pass
        return user

    def clean_expired_sessions(self):
        """
        Cleans the expired sessions in IAM
        """
        pass

    def get_all_sessions(self):
        """
        Gets all sessions from the users database

        Returns
        -----------
        sessions
            List of sessions
        """

        return None
