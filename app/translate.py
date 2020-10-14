import json
from flask import current_app
from flask_babel import _
import requests


def translate(text, source_language, dest_language):
    if 'MS_TRANSLATOR_KEY' not in current_app.config or not current_app.config['MS_TRANSLATOR_KEY']:
        return _('Error: the translation service is not configured.')
    auth = {'Ocp-Apim-Subscription-Key': current_app.config['MS_TRANSLATOR_KEY']}
    r = requests.get(
        'https://api.microsofttranslator.com/v2/Ajax.svc/Translate'
        f'?text={text}&from={source_language}&to={dest_language}', headers=auth,
    )
    if r.status_code != 200:
        return _('Error: the translation service failed.')
    return json.loads(r.content.decode('utf-8-sig'))


def detect_language(text):
    if 'MS_TRANSLATOR_KEY' not in current_app.config or not current_app.config['MS_TRANSLATOR_KEY']:
        return _('Error: the translation service is not configured.')
    body = json.dumps([{"text": text}])
    headers = {
        'Ocp-Apim-Subscription-Key': current_app.config['MS_TRANSLATOR_KEY'],
        'Content-Type': 'application/json',
        'Content-Length': str(len(text)),
    }
    r = requests.post(
        'https://api.cognitive.microsofttranslator.com/detect?api-version=3.0',
        headers=headers, data=body,
    )
    if r.status_code != 200:
        return 'UNKNOWN'
    return json.loads(r.content.decode('utf-8-sig'))[0]['language']