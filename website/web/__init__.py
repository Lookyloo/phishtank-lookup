#!/usr/bin/env python3

import logging
import logging.config

from importlib.metadata import version
from typing import Dict

from flask import request, Flask
from flask_restx import Api, Resource, fields  # type: ignore

from phishtank.phishtank import Phishtank
from phishtank.default import get_config

from .helpers import get_secret_key
from .proxied import ReverseProxied

logging.config.dictConfig(get_config('logging'))

app: Flask = Flask(__name__)

app.wsgi_app = ReverseProxied(app.wsgi_app)  # type: ignore

app.config['SECRET_KEY'] = get_secret_key()

expire = get_config('generic', 'expire_urls')

api = Api(app, title='Phishtank Lookup API',
          description=f'API to query a Phishtank lookup instance. The instance keeps the URLs for {expire} hours',
          version=version('phishtank'))

phishtank: Phishtank = Phishtank()


@api.route('/redis_up')
@api.doc(description='Check if redis is up and running')
class RedisUp(Resource):

    def get(self):
        return phishtank.check_redis_up()


@api.route('/info')
@api.doc(description='Get info about the instance')
class Info(Resource):

    def get(self):
        return phishtank.info()


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
        to_query: Dict = request.get_json(force=True)  # type: ignore
        if 'url' not in to_query or not to_query.get('url'):
            return {'error': 'The URL is required...'}, 400
        return self._format_response(to_query['url'])


@api.route('/url')
@api.doc(description='Get the full URL entry')
class URL(Resource):
    @api.param('url', 'The URL to query', required=True)
    def get(self):
        if 'url' not in request.args or not request.args.get('url'):
            return {'error': 'The URL is required...'}, 400
        return phishtank.get_url_entry(request.args['url'])


@api.route('/urls')
@api.doc(description='Get all the URLs')
class URLs(Resource):

    def get(self):
        return phishtank.get_urls()


@api.route('/ips')
@api.doc(description='Get all the IPs')
class IPs(Resource):

    def get(self):
        return phishtank.get_ips()


@api.route('/asns')
@api.doc(description='Get all the ASNs')
class ASNs(Resource):

    def get(self):
        return phishtank.get_asns()


@api.route('/ccs')
@api.doc(description='Get all the Country Codes')
class CCs(Resource):

    def get(self):
        return phishtank.get_ccs()


@api.route('/urls_by_ip')
@api.doc(description='Get all the URLs by IP')
class URLsByIPs(Resource):

    @api.param('ip', 'The IP to query', required=True)
    def get(self):
        if 'ip' not in request.args or not request.args.get('ip'):
            return {'error': 'The IP is required...'}, 400
        return phishtank.get_urls_by_ip(request.args['ip'])


@api.route('/urls_by_asn')
@api.doc(description='Get all the URLs by ASN')
class URLsByASN(Resource):

    @api.param('asn', 'The ASN to query', required=True)
    def get(self):
        if 'asn' not in request.args or not request.args.get('asn'):
            return {'error': 'The ASN is required...'}, 400
        return phishtank.get_urls_by_asn(request.args['asn'])


@api.route('/urls_by_cc')
@api.doc(description='Get all the URLs by Country Code')
class URLsByCC(Resource):

    @api.param('cc', 'The CC to query', required=True)
    def get(self):
        if 'cc' not in request.args or not request.args.get('cc'):
            return {'error': 'The Country Code is required...'}, 400
        return phishtank.get_urls_by_cc(request.args['cc'])
