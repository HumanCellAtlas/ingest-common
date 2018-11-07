from datetime import datetime, timedelta


class TokenManager:
    def __init__(self, token_client):
        self.token_client = token_client
        self.token = None
        self.TOKEN_DURATION = 3600 * 1000 # milliseconds

    def get_token(self):
        token = None
        if self.token and not self.token.is_expired():
            token = self.token
        else:
            token_value = self.token_client.retrieve_token()
            token = self._create_token(token_value)
            self.token = token
        return token.value

    def _create_token(self, value):
        return Token(value=value, token_duration=self.TOKEN_DURATION)


class Token:
    def __init__(self, value, token_duration):
        self.value = value
        self.created_at = datetime.now()
        self.token_duration = token_duration

    def is_expired(self):
        return datetime.now() > self.created_at + timedelta(milliseconds=self.token_duration)