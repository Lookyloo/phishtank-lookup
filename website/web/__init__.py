#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pkg_resources
from typing import Dict

from flask import request, Flask
from flask_restx import Api, Namespace, Resource, fields  # type: ignore

from phishtank.phishtank import Phishtank

from .helpers import get_secret_key
from .proxied import ReverseProxied

api = Namespace('GenericAPI', description='Generic Phishtank API', path='/')

app: Flask = Flask(__name__)

app.wsgi_app = ReverseProxied(app.wsgi_app)  # type: ignore

app.config['SECRET_KEY'] = get_secret_key()

api = Api(app, title='Phishtank API',
          description='API to query a Phishtank lookup instance.',
          version=pkg_resources.get_distribution('phishtank').version)

phishtank: Phishtank = Phishtank()

checkurl_fields = api.model('CheckURLFields', {
    'url': fields.Url(description="The URL to check", required=True),
})


@api.route('/checkurl')
@api.doc(description='This method has the same JSON output as the (broken?) official interface.')
class CheckURL(Resource):

    def _format_response(self, url: str) -> Dict:
        entry = phishtank.get_url_entry(url)
        if not entry:
            return {'in_database': False}
        return {
            'url': url,
            'in_database': True,
            'phish_id': entry['phish_id'],
            'phish_detail_page': entry['phish_detail_url'],
            'verified': 'y',
            'verified_at': entry['verification_time'],
            'valid': 'y'
        }

    @api.param('url', 'The URL to check', required=True)
    def get(self):
        if 'url' not in request.args or not request.args.get('url'):
            return {'error': 'The URL is required...'}, 400
        return self._format_response(request.args['url'])

    @api.doc(body=checkurl_fields)
    def post(self):
        to_query: Dict = request.get_json(force=True)
        if 'url' not in to_query:
            return {'error': 'The URL is required...'}, 400
        return self._format_response(to_query['url'])
