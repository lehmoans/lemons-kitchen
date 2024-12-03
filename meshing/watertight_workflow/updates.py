import requests # dependency
from inputs import DISCORD_WEBHOOK

class Updates:
    def __init__(self,verbose = False):
        self.verbose = verbose
        self.webhook = DISCORD_WEBHOOK

    def send_update(self,title, message):
        if not self.verbose:
            return "verbose set to False"

        # for all params, see https://discordapp.com/developers/docs/resources/webhook#execute-webhook
        data = {}

        # leave this out if you dont want an embed
        # for all params, see https://discordapp.com/developers/docs/resources/channel#embed-object
        data["embeds"] = [
            {
                "description" : f'{title}',
                "title" : f"{message}"
            }
        ]

        result = requests.post(self.webhook, json = data)

        try:
            result.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(err)
        else:
            print(f"Payload delivered successfully, code {result.status_code}.")