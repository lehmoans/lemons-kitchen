import requests # dependency

DISCORD_WEBHOOK= "https://discord.com/api/webhooks/1307534355232587817/V3ZqQXFCrOEoA0477lQj3-EccHeztedK2K4DiNWYFcy-2z9VEtN-l5yYvia2uGKr4QHd"

def send_update(title, message):

    url =  DISCORD_WEBHOOK

    # for all params, see https://discordapp.com/developers/docs/resources/webhook#execute-webhook
    data = {}

    # leave this out if you dont want an embed
    # for all params, see https://discordapp.com/developers/docs/resources/channel#embed-object
    data["embeds"] = [
        {
            "description" : "{title}",
            "title" : "{message}"
        }
    ]

    result = requests.post(url, json = data)

    try:
        result.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)
    else:
        print(f"Payload delivered successfully, code {result.status_code}.")